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


def _resolve_target_path(base_dir: Path, raw_name: str) -> Optional[Path]:
    normalized_name = raw_name.replace("\\", "/").lstrip("/")
    if not normalized_name:
        return None

    target = (base_dir / normalized_name).resolve(strict=False)
    base = base_dir.resolve(strict=False)
    if target != base and base not in target.parents:
        return None
    return target


def _classify_uploaded_files(
    files: List[UploadFile],
) -> tuple[List[UploadFile], Optional[UploadFile], Optional[UploadFile], List[UploadFile]]:
    markdown_files: List[UploadFile] = []
    template_file: Optional[UploadFile] = None
    title_file: Optional[UploadFile] = None
    asset_files: List[UploadFile] = []

    for uploaded in files:
        if not uploaded.filename:
            continue

        normalized_name = uploaded.filename.replace("\\", "/")
        basename = Path(normalized_name).name.lower()

        if basename == "template.docx":
            if template_file is not None:
                raise HTTPException(status_code=400, detail="Multiple template.docx files provided")
            template_file = uploaded
            continue

        if basename == "title.docx":
            if title_file is not None:
                raise HTTPException(status_code=400, detail="Multiple title.docx files provided")
            title_file = uploaded
            continue

        if normalized_name.lower().endswith(".md"):
            markdown_files.append(uploaded)
            continue

        asset_files.append(uploaded)

    if not markdown_files:
        raise HTTPException(status_code=400, detail="At least one Markdown file (.md) is required in files[]")

    markdown_files.sort(key=lambda upload: (upload.filename or "").replace("\\", "/").casefold())

    return markdown_files, template_file, title_file, asset_files


async def _save_uploaded_file(
    base_dir: Path,
    upload: UploadFile,
    *,
    override_name: Optional[str] = None,
) -> Optional[Path]:
    source_name = override_name or upload.filename or ""
    target_path = _resolve_target_path(base_dir, source_name)
    if target_path is None:
        logger.warning("Blocked path-traversal in uploaded filename: %s", source_name or "<empty>")
        return None

    target_path.parent.mkdir(parents=True, exist_ok=True)
    data = await upload.read()
    target_path.write_bytes(data)
    logger.debug("Saved uploaded file: %s (%d bytes)", source_name, len(data))
    return target_path


async def _prepare_conversion_inputs(files: List[UploadFile], base_dir: Path) -> tuple[List[str], str, Optional[str]]:
    markdown_files, template_file, title_file, asset_files = _classify_uploaded_files(files)

    md_paths: List[str] = []
    for markdown_file in markdown_files:
        md_path = await _save_uploaded_file(base_dir, markdown_file)
        if md_path is None:
            raise HTTPException(status_code=400, detail="Invalid Markdown filename")
        md_paths.append(str(md_path))

    for asset in asset_files:
        if not asset.filename:
            continue
        saved_asset = await _save_uploaded_file(base_dir, asset)
        if saved_asset is None:
            logger.warning("Skipped asset with invalid filename: %s", asset.filename)

    template_path = _TEMPLATE_PATH
    if template_file:
        saved_template = await _save_uploaded_file(base_dir, template_file, override_name="template.docx")
        if saved_template is None:
            raise HTTPException(status_code=400, detail="Invalid template filename")
        template_path = str(saved_template)

    title_path = None
    if title_file:
        saved_title = await _save_uploaded_file(base_dir, title_file, override_name="title.docx")
        if saved_title is None:
            raise HTTPException(status_code=400, detail="Invalid title filename")
        title_path = str(saved_title)

    return md_paths, template_path, title_path


def _run_conversion(
    md_paths: List[str],
    output_path: str,
    template_path: str,
    title_path: Optional[str],
    title_pages: int,
) -> list[str]:
    clear_warnings()
    converter = Converter(
        input_paths=md_paths,
        output_path=output_path,
        template_path=template_path,
        title_path=title_path,
        title_pages=title_pages,
    )
    converter.convert()
    converter.document.save(output_path)
    return list(get_warnings())

# ── Health ───────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "md2gost", "version": "1.0.0"}


# ── Synchronous conversion ──────────────────────────────────

@app.post("/convert", tags=["conversion"])
async def convert_sync(
    files: List[UploadFile] = File(
        ...,
        description="Project files: one or more Markdown (.md) files; optional template.docx/title.docx; others treated as assets",
    ),
    title_pages: int = Form(1, description="Number of title pages"),
):
    """
    Synchronous conversion: upload project files in files[], receive DOCX immediately.
    Markdown files are sorted by filename and merged in that order; template.docx
    and title.docx are recognized by name, all other files are treated as assets.
    """
    with tempfile.TemporaryDirectory(prefix="md2gost_") as tmpdir:
        md_paths, template_path, title_path = await _prepare_conversion_inputs(files, Path(tmpdir))

        # Output path
        output_path = os.path.join(tmpdir, "output.docx")

        try:
            warnings = _run_conversion(
                md_paths=md_paths,
                output_path=output_path,
                template_path=template_path,
                title_path=title_path,
                title_pages=title_pages,
            )
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
    files: List[UploadFile] = File(
        ...,
        description="Project files: one or more Markdown (.md) files; optional template.docx/title.docx; others treated as assets",
    ),
    title_pages: int = Form(1),
    callback_url: Optional[str] = Form(None, description="URL to POST result notification to"),
):
    """
    Asynchronous conversion: creates a job from files[] and returns immediately.
    Poll GET /jobs/{id} for status, or supply callback_url for push notification.
    """
    job_id = str(uuid.uuid4())
    job_dir = _RESULTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    md_paths, template_path, title_path = await _prepare_conversion_inputs(files, job_dir)

    job = JobInfo(
        id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _jobs[job_id] = job

    background_tasks.add_task(
        _run_conversion_job,
        job_id=job_id,
        md_paths=md_paths,
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
    md_paths: List[str],
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
        _run_conversion(
            md_paths=md_paths,
            output_path=output_path,
            template_path=template_path,
            title_path=title_path,
            title_pages=title_pages,
        )

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


def _get_workers() -> int:
    raw_value = os.environ.get("MD2GOST_WORKERS", "1")
    try:
        workers = int(raw_value)
    except ValueError:
        logger.warning("Invalid MD2GOST_WORKERS=%r, using 1", raw_value)
        return 1

    if workers < 1:
        logger.warning("Invalid MD2GOST_WORKERS=%r, using 1", raw_value)
        return 1

    return workers


def run_server():
    """Entry point for running the server directly."""
    import uvicorn
    host = os.environ.get("MD2GOST_HOST", "0.0.0.0")
    port = int(os.environ.get("MD2GOST_PORT", "8000"))
    workers = _get_workers()

    if workers > 1:
        # Uvicorn requires import string app reference for multi-process workers.
        uvicorn.run("md2gost.server:app", host=host, port=port, log_level="info", workers=workers)
    else:
        uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
