"""
md2gost HTTP Server — FastAPI wrapper around the md2gost CLI converter.

Provides REST API for Markdown → DOCX conversion with optional callback support.
"""

import json
import logging
import os
import struct
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .converter import Converter
from .warnings_collector import clear_warnings, get_warnings

logger = logging.getLogger("md2gost.server")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("md2gost server starting, results dir: %s", _RESULTS_DIR)
    yield

app = FastAPI(
    title="md2gost Conversion Service",
    description="Markdown → ГОСТ DOCX converter HTTP API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── In-memory job store ──────────────────────────────────────

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class JobInfo(BaseModel):
    id: str
    status: JobStatus
    created_at: str
    finished_at: Optional[str] = None
    error: Optional[str] = None
    result_path: Optional[str] = None


_jobs: dict[str, JobInfo] = {}
_RESULTS_DIR = Path(tempfile.mkdtemp(prefix="md2gost_results_"))
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "Template.docx")

# ── Health ───────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "md2gost", "version": "1.0.0"}


# ── Synchronous conversion ──────────────────────────────────

@app.post("/convert", tags=["conversion"])
async def convert_sync(
    file: UploadFile = File(..., description="Markdown file (.md)"),
    template: Optional[UploadFile] = File(None, description="Optional DOCX template"),
    title: Optional[UploadFile] = File(None, description="Optional title page DOCX"),
    assets: List[UploadFile] = File([], description="Additional project files (images, etc.) with relative paths as filenames"),
    title_pages: int = Form(1, description="Number of title pages"),
):
    """
    Synchronous conversion: upload Markdown, receive DOCX immediately.
    Asset files (images, etc.) are placed in the same temp directory using
    their filenames as relative paths so the converter can resolve references.
    """
    filename = file.filename or "document.md"
    if not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="File must have .md extension")

    with tempfile.TemporaryDirectory(prefix="md2gost_") as tmpdir:
        # Save input markdown
        md_path = os.path.join(tmpdir, filename)
        content = await file.read()
        with open(md_path, "wb") as f:
            f.write(content)

        # Save asset files (images, etc.) preserving relative paths
        for asset in assets:
            if not asset.filename:
                continue
            # ── Path-traversal guard ──
            cleaned = asset.filename.lstrip("/").lstrip("\\")
            asset_path = os.path.normpath(os.path.join(tmpdir, cleaned))
            if not asset_path.startswith(os.path.normpath(tmpdir) + os.sep):
                logger.warning("Blocked path-traversal in asset filename: %s", asset.filename)
                continue
            os.makedirs(os.path.dirname(asset_path), exist_ok=True)
            asset_data = await asset.read()
            with open(asset_path, "wb") as f:
                f.write(asset_data)
            logger.debug("Saved asset: %s (%d bytes)", asset.filename, len(asset_data))

        # Save optional template
        template_path = _TEMPLATE_PATH
        if template:
            template_path = os.path.join(tmpdir, "template.docx")
            with open(template_path, "wb") as f:
                f.write(await template.read())

        # Save optional title
        title_path = None
        if title:
            title_path = os.path.join(tmpdir, "title.docx")
            with open(title_path, "wb") as f:
                f.write(await title.read())

        # Output path
        output_path = os.path.join(tmpdir, "output.docx")

        try:
            clear_warnings()
            converter = Converter(
                input_paths=[md_path],
                output_path=output_path,
                template_path=template_path,
                title_path=title_path,
                title_pages=title_pages,
            )
            converter.convert()
            converter.document.save(output_path)
            warnings = get_warnings()
        except Exception as e:
            logger.exception("Conversion failed")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

        with open(output_path, "rb") as f:
            docx_bytes = f.read()

        # Binary framing: [4 bytes: warnings JSON length (big-endian uint32)][warnings JSON bytes][DOCX bytes]
        warnings_json = json.dumps(warnings, ensure_ascii=False).encode("utf-8")
        body = struct.pack(">I", len(warnings_json)) + warnings_json + docx_bytes

        return Response(
            content=body,
            media_type="application/octet-stream",
            headers={"Content-Disposition": 'attachment; filename="result.bin"'},
        )


# ── Async job-based conversion ──────────────────────────────

@app.post("/jobs", tags=["jobs"], response_model=JobInfo, status_code=202)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Markdown file (.md)"),
    template: Optional[UploadFile] = File(None, description="Optional DOCX template"),
    title: Optional[UploadFile] = File(None, description="Optional title page DOCX"),
    title_pages: int = Form(1),
    callback_url: Optional[str] = Form(None, description="URL to POST result notification to"),
):
    """
    Asynchronous conversion: creates a job and returns immediately.
    Poll GET /jobs/{id} for status, or supply callback_url for push notification.
    """
    filename = file.filename or "document.md"
    if not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="File must have .md extension")

    job_id = str(uuid.uuid4())
    job_dir = _RESULTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Persist uploaded files to job directory
    md_path = job_dir / filename
    with open(md_path, "wb") as f:
        f.write(await file.read())

    template_path = _TEMPLATE_PATH
    if template:
        template_path = str(job_dir / "template.docx")
        with open(template_path, "wb") as f:
            f.write(await template.read())

    title_path = None
    if title:
        title_path = str(job_dir / "title.docx")
        with open(title_path, "wb") as f:
            f.write(await title.read())

    job = JobInfo(
        id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _jobs[job_id] = job

    background_tasks.add_task(
        _run_conversion_job,
        job_id=job_id,
        md_path=str(md_path),
        template_path=template_path,
        title_path=title_path,
        title_pages=title_pages,
        callback_url=callback_url,
    )

    return job


@app.get("/jobs/{job_id}", tags=["jobs"], response_model=JobInfo)
async def get_job(job_id: str):
    """Get conversion job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs/{job_id}/result", tags=["jobs"])
async def get_job_result(job_id: str):
    """Download the DOCX result of a completed job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DONE:
        raise HTTPException(status_code=409, detail=f"Job is {job.status}, not DONE")
    if not job.result_path or not os.path.exists(job.result_path):
        raise HTTPException(status_code=500, detail="Result file not found")

    return FileResponse(
        path=job.result_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="result.docx",
    )


# ── Background worker ───────────────────────────────────────

def _run_conversion_job(
    job_id: str,
    md_path: str,
    template_path: str,
    title_path: Optional[str],
    title_pages: int,
    callback_url: Optional[str],
):
    """Runs the actual conversion in a background thread."""
    job = _jobs[job_id]
    job.status = JobStatus.PROCESSING

    output_path = str(_RESULTS_DIR / job_id / "result.docx")

    try:
        converter = Converter(
            input_paths=[md_path],
            output_path=output_path,
            template_path=template_path,
            title_path=title_path,
            title_pages=title_pages,
        )
        converter.convert()
        converter.document.save(output_path)

        job.status = JobStatus.DONE
        job.result_path = output_path
        job.finished_at = datetime.now(timezone.utc).isoformat()
        logger.info("Job %s completed successfully", job_id)

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.finished_at = datetime.now(timezone.utc).isoformat()

    # Callback notification
    if callback_url:
        _send_callback(callback_url, job)


def _send_callback(url: str, job: JobInfo):
    """Sends a POST notification to the callback URL."""
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json=job.model_dump())
        logger.info("Callback sent to %s for job %s", url, job.id)
    except Exception as e:
        logger.warning("Failed to send callback to %s: %s", url, e)


def run_server():
    """Entry point for running the server directly."""
    import uvicorn
    host = os.environ.get("MD2GOST_HOST", "0.0.0.0")
    port = int(os.environ.get("MD2GOST_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
