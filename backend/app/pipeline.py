"""API-facing orchestration of the existing preprocess -> OCR -> extract ->
validate -> export pipeline (src/).

This module intentionally does not change any of the underlying pipeline
logic in src/ — it only wires the same steps app.py's Streamlit UI used to
call directly into a single function the FastAPI route can invoke, and turns
pipeline-internal exceptions into the two error categories routes.py needs:
client-fault (bad upload) vs. server-fault (unexpected failure).
"""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

from PIL import Image

import config
from src.extractor import extract_fields
from src.ocr import OCRResult, pdf_to_images, run_ocr
from src.preprocess import preprocess_image
from src.utils import get_logger, is_pdf, pil_to_ndarray, validate_upload
from src.validator import validate_fields
from src.exporter import build_export_payload

logger = get_logger(__name__)


class DocumentProcessingError(Exception):
    """Raised when a document's bytes can't be decoded (corrupted/unreadable upload)."""


def _load_pages(filename: str, file_bytes: bytes) -> list:
    """Return one RGB NumPy array per page, or raise DocumentProcessingError."""
    if is_pdf(filename):
        try:
            pages = pdf_to_images(file_bytes)
        except Exception as exc:
            raise DocumentProcessingError(
                "Could not read this PDF. It may be corrupted, empty, or password-protected."
            ) from exc
        if not pages:
            raise DocumentProcessingError("This PDF has no pages to process.")
        return pages

    try:
        image = Image.open(BytesIO(file_bytes))
        image.load()  # force full decode now so a truncated/corrupt image fails here
    except Exception as exc:
        raise DocumentProcessingError(
            "Could not read this image. It may be corrupted or in an unsupported format."
        ) from exc

    return [pil_to_ndarray(image)]


def process_document(filename: str, file_bytes: bytes, engine: str | None = None) -> dict:
    """Run the full pipeline end-to-end and return an API-ready result dict.

    Raises:
        UnsupportedFileError, FileTooLargeError: from src.utils.validate_upload,
            for a rejected upload (caller maps these to HTTP 400).
        DocumentProcessingError: the file passed validation but couldn't be
            decoded as a real PDF/image.
        ValueError: an unknown OCR engine name was requested.
        Any other exception: unexpected pipeline failure (caller maps to 500).
    """
    started = time.perf_counter()

    validate_upload(filename, len(file_bytes))
    pages = _load_pages(filename, file_bytes)

    engine_name = (engine or config.OCR_ENGINE).lower()

    combined_text_parts: list[str] = []
    confidences: list[float] = []
    for i, page in enumerate(pages):
        logger.info("Processing page %d/%d of '%s'", i + 1, len(pages), filename)
        processed = preprocess_image(page)
        ocr_result = run_ocr(processed, engine=engine_name)
        combined_text_parts.append(ocr_result.full_text)
        confidences.append(ocr_result.average_confidence)

    merged_result = OCRResult(
        full_text="\n".join(combined_text_parts),
        words=[],
        average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
    )

    fields = extract_fields(merged_result, config.FIELD_PATTERNS)
    validation = validate_fields(fields)

    payload = build_export_payload(filename, validation)
    payload["file_type"] = Path(filename).suffix.lower().lstrip(".")
    payload["page_count"] = len(pages)
    payload["processing_time_seconds"] = round(time.perf_counter() - started, 2)
    payload["ocr_engine"] = engine_name
    payload["raw_text"] = merged_result.full_text

    logger.info(
        "Processed '%s' in %.2fs (%d page(s), valid=%s)",
        filename, payload["processing_time_seconds"], len(pages), payload["is_valid_document"],
    )
    return payload
