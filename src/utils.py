"""
Shared helper utilities: logging setup, file validation, and small
conversions reused across the preprocessing / OCR / extraction pipeline.

Keeping these in one place avoids every module re-implementing its own
logging setup or PIL<->NumPy conversion, and gives the rest of the codebase
a single source of truth for "is this upload acceptable?".
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import config


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger configured to write to file + stdout.

    Every module calls this with its own __name__, so log lines are
    traceable back to the exact stage of the pipeline (preprocess, ocr,
    extractor, ...) that produced them.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # get_logger(__name__) is called once per module at import time, but
        # Streamlit re-executes app.py on every user interaction. Without this
        # guard, each rerun would attach a fresh pair of handlers to the same
        # logger, and every log line would be printed/written multiple times.
        return logger

    logger.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(config.LOG_FORMAT)

    # Persist logs to disk so issues can be diagnosed after the Streamlit
    # session has ended, not just while watching the terminal live.
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also echo to stdout so `streamlit run app.py` shows progress live.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


logger = get_logger(__name__)


class UnsupportedFileError(Exception):
    """Raised when an uploaded file has an extension outside ALLOWED_EXTENSIONS."""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds MAX_FILE_SIZE_MB."""


def validate_upload(filename: str, size_bytes: int) -> None:
    """Validate an uploaded file's extension and size before any processing starts.

    This is deliberately the very first thing app.py calls after a file is
    uploaded: rejecting a bad file here is instant and cheap, versus letting
    it fail deep inside OCR/PDF parsing where the error would be far less
    clear to the user.

    Raises:
        UnsupportedFileError: if the extension isn't in config.ALLOWED_EXTENSIONS.
        FileTooLargeError: if size_bytes exceeds config.MAX_FILE_SIZE_MB.
    """
    # Path(...).suffix.lower() normalizes ".PDF", ".Pdf", ".pdf" to the same
    # comparison so casing in the uploaded filename can't slip past the check.
    ext = Path(filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise UnsupportedFileError(
            f"'{ext}' is not supported. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

    size_mb = size_bytes / (1024 * 1024)
    if size_mb > config.MAX_FILE_SIZE_MB:
        raise FileTooLargeError(
            f"File is {size_mb:.1f} MB, which exceeds the {config.MAX_FILE_SIZE_MB} MB limit."
        )


def pil_to_ndarray(image: Image.Image) -> np.ndarray:
    """Convert a PIL image to an RGB NumPy array.

    Uploaded images can arrive in any PIL mode (L, P, RGBA, CMYK, ...)
    depending on how they were saved. Forcing .convert("RGB") first
    guarantees OpenCV (which expects a consistent 3-channel array) always
    receives the same shape, regardless of the source file's format.
    """
    return np.array(image.convert("RGB"))


def ndarray_to_pil(array: np.ndarray) -> Image.Image:
    """Convert a NumPy array (grayscale or RGB) back to a PIL image.

    Used when a preprocessed/OCR-stage array needs to be handed to a PIL-based
    API (e.g. for display or re-encoding) rather than an OpenCV one.
    """
    return Image.fromarray(array)


def is_pdf(filename: str) -> bool:
    """Return True if the filename has a .pdf extension.

    Used by app.py to decide whether to rasterize the upload via
    src.ocr.pdf_to_images or load it directly as a single image.
    """
    return Path(filename).suffix.lower() == ".pdf"
