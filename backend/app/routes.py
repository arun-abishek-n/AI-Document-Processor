"""API endpoints: document processing and health check."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool

import config
from app.pipeline import DocumentProcessingError, process_document
from app.schemas import HealthResponse, ProcessResponse
from src.utils import FileTooLargeError, UnsupportedFileError, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Lightweight liveness/config check — does not load the OCR model."""
    return HealthResponse(
        status="ok",
        ocr_engine=config.OCR_ENGINE,
        allowed_extensions=list(config.ALLOWED_EXTENSIONS),
        max_file_size_mb=config.MAX_FILE_SIZE_MB,
    )


@router.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="PDF, JPG, or PNG document to process"),
    ocr_engine: str | None = Query(
        default=None, description="Override the server's configured OCR engine"
    ),
) -> ProcessResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        # process_document is CPU-bound and blocking (OpenCV + OCR), so it runs
        # in FastAPI's threadpool rather than directly on the async event loop.
        result = await run_in_threadpool(process_document, file.filename, file_bytes, ocr_engine)
    except (UnsupportedFileError, FileTooLargeError, DocumentProcessingError) as exc:
        logger.warning("Rejected upload '%s': %s", file.filename, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error processing '%s'", file.filename)
        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed unexpectedly on the server. "
                "Please try again, or try a different file."
            ),
        ) from None

    return ProcessResponse(**result)
