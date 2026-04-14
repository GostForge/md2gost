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
from anyio import to_thread
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .config import Md2GostConfig, get_config_reference, load_project_config
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
_PROJECT_CONFIG_FILE = "gostforge.yml"


def _resolve_target_path(base_dir: Path, raw_name: str) -> Optional[Path]:
    normalized_name = raw_name.replace("\\", "/").lstrip("/")
    if not normalized_name:
        return None

    target = (base_dir / normalized_name).resolve(strict=False)
    base = base_dir.resolve(strict=False)
    if target != base and base not in target.parents:
        return None
    return target


def _duplicate_upload_error(role: str) -> str:
    if role == "template":
        return "Multiple template.docx files provided"
    if role == "title":
        return "Multiple title.docx files provided"
    if role == "config":
        return "Multiple gostforge.yml files provided"
    return "Multiple files provided"


def _classify_uploaded_files(
    files: List[UploadFile],
) -> tuple[List[UploadFile], Optional[UploadFile], Optional[UploadFile], Optional[UploadFile], List[UploadFile]]:
    markdown_files: List[UploadFile] = []
    special_files: dict[str, UploadFile] = {}
    asset_files: List[UploadFile] = []

    special_basename_to_role = {
        "template.docx": "template",
        "title.docx": "title",
        "gostforge.yml": "config",
        "gostforge.yaml": "config",
    }

    for uploaded in files:
        if not uploaded.filename:
            continue

        normalized_name = uploaded.filename.replace("\\", "/")
        basename = Path(normalized_name).name.lower()

        role = special_basename_to_role.get(basename)
        if role is not None:
            if role in special_files:
                raise HTTPException(status_code=400, detail=_duplicate_upload_error(role))
            special_files[role] = uploaded
            continue

        if normalized_name.lower().endswith(".md"):
            markdown_files.append(uploaded)
            continue

        asset_files.append(uploaded)

    if not markdown_files:
        raise HTTPException(status_code=400, detail="At least one Markdown file (.md) is required in files[]")

    markdown_files.sort(key=lambda upload: (upload.filename or "").replace("\\", "/").casefold())

    return (
        markdown_files,
        special_files.get("template"),
        special_files.get("title"),
        special_files.get("config"),
        asset_files,
    )


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


async def _save_markdown_files(base_dir: Path, markdown_files: List[UploadFile]) -> List[str]:
    md_paths: List[str] = []
    for markdown_file in markdown_files:
        md_path = await _save_uploaded_file(base_dir, markdown_file)
        if md_path is None:
            raise HTTPException(status_code=400, detail="Invalid Markdown filename")
        md_paths.append(str(md_path))
    return md_paths


async def _save_asset_files(base_dir: Path, asset_files: List[UploadFile]) -> None:
    for asset in asset_files:
        if not asset.filename:
            continue
        saved_asset = await _save_uploaded_file(base_dir, asset)
        if saved_asset is None:
            logger.warning("Skipped asset with invalid filename: %s", asset.filename)


async def _resolve_optional_upload_path(
    base_dir: Path,
    upload: Optional[UploadFile],
    *,
    override_name: str,
    invalid_error_detail: str,
) -> Optional[str]:
    if upload is None:
        return None

    saved_path = await _save_uploaded_file(base_dir, upload, override_name=override_name)
    if saved_path is None:
        raise HTTPException(status_code=400, detail=invalid_error_detail)
    return str(saved_path)


async def _load_uploaded_project_config(base_dir: Path, config_file: Optional[UploadFile]) -> Md2GostConfig:
    if config_file is None:
        return Md2GostConfig()

    saved_config = await _save_uploaded_file(base_dir, config_file, override_name=_PROJECT_CONFIG_FILE)
    if saved_config is None:
        raise HTTPException(status_code=400, detail="Invalid gostforge.yml filename")

    try:
        return load_project_config(saved_config, allow_missing=False)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid gostforge.yml: {exc}") from exc


def _resolve_title_pages(config: Md2GostConfig, title_pages_override: Optional[int]) -> int:
    title_pages = title_pages_override if title_pages_override is not None else config.title_pages
    if title_pages < 1:
        raise HTTPException(status_code=400, detail="title_pages must be >= 1")
    return title_pages


async def _prepare_conversion_inputs(
    files: List[UploadFile],
    base_dir: Path,
    *,
    title_pages_override: Optional[int],
) -> tuple[List[str], str, Optional[str], Md2GostConfig, int]:
    markdown_files, template_file, title_file, config_file, asset_files = _classify_uploaded_files(files)

    md_paths = await _save_markdown_files(base_dir, markdown_files)
    await _save_asset_files(base_dir, asset_files)

    template_path = _TEMPLATE_PATH
    uploaded_template_path = await _resolve_optional_upload_path(
        base_dir,
        template_file,
        override_name="template.docx",
        invalid_error_detail="Invalid template filename",
    )
    if uploaded_template_path is not None:
        template_path = uploaded_template_path

    title_path = await _resolve_optional_upload_path(
        base_dir,
        title_file,
        override_name="title.docx",
        invalid_error_detail="Invalid title filename",
    )

    config = await _load_uploaded_project_config(base_dir, config_file)
    title_pages = _resolve_title_pages(config, title_pages_override)

    return md_paths, template_path, title_path, config, title_pages


def _run_conversion(
    md_paths: List[str],
    output_path: str,
    template_path: str,
    title_path: Optional[str],
    title_pages: int,
    config: Md2GostConfig,
) -> list[str]:
    clear_warnings()
    converter = Converter(
        input_paths=md_paths,
        output_path=output_path,
        template_path=template_path,
        title_path=title_path,
        title_pages=title_pages,
        debug=config.debug,
        config=config,
    )
    converter.convert()
    converter.document.save(output_path)
    return list(get_warnings())

# ── Health ───────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "md2gost", "version": "1.0.0"}


@app.get("/config/reference", tags=["system"])
async def config_reference():
    return {"config": get_config_reference()}


# ── Synchronous conversion ──────────────────────────────────

@app.post("/convert", tags=["conversion"])
async def convert_sync(
    files: List[UploadFile] = File(
        ...,
        description="Project files: one or more Markdown (.md) files; optional template.docx/title.docx; others treated as assets",
    ),
    title_pages: Optional[int] = Form(None, description="Number of title pages"),
):
    """
    Synchronous conversion: upload project files in files[], receive DOCX immediately.
    Markdown files are sorted by filename and merged in that order; template.docx
    and title.docx are recognized by name, all other files are treated as assets.
    """
    with tempfile.TemporaryDirectory(prefix="md2gost_") as tmpdir:
        md_paths, template_path, title_path, config, effective_title_pages = await _prepare_conversion_inputs(
            files,
            Path(tmpdir),
            title_pages_override=title_pages,
        )

        # Output path
        output_path = os.path.join(tmpdir, "output.docx")

        try:
            warnings = _run_conversion(
                md_paths=md_paths,
                output_path=output_path,
                template_path=template_path,
                title_path=title_path,
                title_pages=effective_title_pages,
                config=config,
            )
        except Exception as e:
            logger.exception("Conversion failed")
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

        docx_bytes = await to_thread.run_sync(Path(output_path).read_bytes)

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
    title_pages: Optional[int] = Form(None),
    callback_url: Optional[str] = Form(None, description="URL to POST result notification to"),
):
    """
    Asynchronous conversion: creates a job from files[] and returns immediately.
    Poll GET /jobs/{id} for status, or supply callback_url for push notification.
    """
    job_id = str(uuid.uuid4())
    job_dir = _RESULTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    md_paths, template_path, title_path, config, effective_title_pages = await _prepare_conversion_inputs(
        files,
        job_dir,
        title_pages_override=title_pages,
    )

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
        title_pages=effective_title_pages,
        config=config,
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
    config: Md2GostConfig,
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
            config=config,
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
