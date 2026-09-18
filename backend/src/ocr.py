"""
OCR engine wrapper and PDF rasterization.

Supports two interchangeable OCR backends (EasyOCR by default, Tesseract as
an alternative) behind a single `run_ocr` function, selected via
config.OCR_ENGINE. PDF pages are rasterized with PyMuPDF, which — unlike
pdf2image — needs no external Poppler binary, keeping the demo friction-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

import config
from src.utils import get_logger, pil_to_ndarray

logger = get_logger(__name__)


@dataclass
class OCRWord:
    """A single OCR-recognized word/line with its bounding box and confidence.

    Kept as its own dataclass (rather than a raw tuple) so downstream code
    like src.extractor can refer to `.text`/`.confidence`/`.bbox` instead of
    remembering index positions.
    """
    text: str
    confidence: float  # 0.0-1.0, normalized regardless of which engine produced it
    bbox: tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max) in pixel coordinates


@dataclass
class OCRResult:
    """Aggregate OCR output for one page/image.

    `full_text` is what the extractor's regex patterns run against;
    `words` is kept around so the extractor can estimate a confidence score
    for each matched field instead of only having one number for the whole
    page.
    """
    full_text: str
    words: list[OCRWord] = field(default_factory=list)
    average_confidence: float = 0.0


def pdf_to_images(pdf_bytes: bytes, dpi: int = config.PDF_DPI) -> list[np.ndarray]:
    """Rasterize every page of a PDF into RGB NumPy arrays.

    Args:
        pdf_bytes: raw bytes of the uploaded PDF file.
        dpi: rendering resolution; higher improves OCR accuracy at the cost of speed.

    Returns:
        One NumPy array per page, in page order.
    """
    # PyMuPDF renders at 72 DPI by default (the historical "1 point = 1
    # pixel" PDF convention), so the zoom factor needed to hit our target
    # DPI is simply target / 72.
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    images: list[np.ndarray] = []
    # Opening from an in-memory byte stream (stream=..., filetype="pdf")
    # avoids writing the uploaded file to disk before we can process it.
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        logger.info("Rasterizing PDF with %d page(s) at %d DPI", doc.page_count, dpi)
        for page in doc:
            pixmap = page.get_pixmap(matrix=matrix)
            # Round-trip through PNG bytes -> PIL is the simplest reliable way
            # to get a Pixmap into a format pil_to_ndarray already knows how
            # to normalize to RGB.
            pil_image = Image.open(BytesIO(pixmap.tobytes("png")))
            images.append(pil_to_ndarray(pil_image))

    return images


class _EasyOCREngine:
    """Lazy-loaded EasyOCR wrapper (model weights download on first use)."""

    # Class-level cache: the reader (and its model weights) is expensive to
    # construct, so it's built once per process and reused across every
    # document the user uploads in the same Streamlit session.
    _reader = None

    @classmethod
    def _get_reader(cls):
        if cls._reader is None:
            # Deferred import: easyocr pulls in PyTorch, a heavy dependency
            # that shouldn't be paid for at module-import time if the user
            # has configured Tesseract as their engine instead.
            import easyocr

            logger.info("Loading EasyOCR reader for languages=%s", config.EASYOCR_LANGUAGES)
            cls._reader = easyocr.Reader(
                config.EASYOCR_LANGUAGES,
                gpu=config.EASYOCR_GPU,
                # Cache model weights inside the project instead of the
                # default user-home cache dir, so a fresh clone of this repo
                # is self-contained (weights just re-download once, locally).
                model_storage_directory=str(config.MODELS_DIR),
            )
        return cls._reader

    @classmethod
    def run(cls, image: np.ndarray) -> OCRResult:
        reader = cls._get_reader()
        # readtext returns a list of (bbox_points, text, confidence) tuples,
        # where bbox_points is 4 (x, y) corner coordinates of a rotated box.
        detections = reader.readtext(image)

        words: list[OCRWord] = []
        lines: list[str] = []
        confidences: list[float] = []

        for bbox_points, text, confidence in detections:
            # Convert the 4-corner rotated box into a simple axis-aligned
            # (x_min, y_min, x_max, y_max) box — good enough for the
            # extractor's word-overlap confidence lookup, and far simpler
            # to work with than a rotated quadrilateral.
            xs = [point[0] for point in bbox_points]
            ys = [point[1] for point in bbox_points]
            words.append(OCRWord(
                text=text,
                confidence=float(confidence),
                bbox=(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))),
            ))
            lines.append(text)
            confidences.append(float(confidence))

        return OCRResult(
            full_text="\n".join(lines),
            words=words,
            average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
        )


class _TesseractEngine:
    """Tesseract OCR wrapper via pytesseract."""

    @classmethod
    def run(cls, image: np.ndarray) -> OCRResult:
        # Deferred import for the same reason as easyocr above: don't force
        # this dependency to resolve unless Tesseract is the selected engine.
        import pytesseract

        if config.TESSERACT_CMD:
            # On Windows, Tesseract usually isn't on PATH by default, so an
            # explicit path is supported via config/env var.
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

        # image_to_data (rather than image_to_string) returns per-word boxes
        # and confidences in parallel lists, which is what we need to build
        # OCRWord entries the same way the EasyOCR path does.
        data = pytesseract.image_to_data(
            image, config=config.TESSERACT_CONFIG, output_type=pytesseract.Output.DICT
        )

        words: list[OCRWord] = []
        lines: list[str] = []
        confidences: list[float] = []

        for i, text in enumerate(data["text"]):
            text = text.strip()
            raw_conf = float(data["conf"][i])
            # Tesseract emits conf == -1 for non-text regions (e.g. detected
            # layout blocks with no recognized word); skip those and any
            # entries that recognized nothing but whitespace.
            if not text or raw_conf < 0:
                continue

            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            # Tesseract reports confidence as 0-100; normalize to 0.0-1.0 so
            # both engines produce the same scale for the rest of the pipeline.
            confidence = raw_conf / 100.0
            words.append(OCRWord(text=text, confidence=confidence, bbox=(x, y, x + w, y + h)))
            lines.append(text)
            confidences.append(confidence)

        return OCRResult(
            full_text="\n".join(lines),
            words=words,
            average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
        )


# Registry mapping config.OCR_ENGINE's string value to its implementation.
# Adding a third backend later means adding one class + one entry here —
# nothing else in the codebase needs to change.
_ENGINES = {
    "easyocr": _EasyOCREngine,
    "tesseract": _TesseractEngine,
}


def run_ocr(image: np.ndarray, engine: str | None = None) -> OCRResult:
    """Run OCR on a preprocessed image using the configured engine.

    Args:
        image: preprocessed grayscale/binarized image array.
        engine: override for config.OCR_ENGINE ("easyocr" | "tesseract").

    Returns:
        An OCRResult with full text, per-word detections, and average confidence.
    """
    engine_name = (engine or config.OCR_ENGINE).lower()
    if engine_name not in _ENGINES:
        raise ValueError(f"Unknown OCR engine '{engine_name}'. Choose from {list(_ENGINES)}.")

    logger.info("Running OCR with engine=%s", engine_name)
    result = _ENGINES[engine_name].run(image)
    logger.info(
        "OCR complete: %d word(s), avg confidence=%.2f", len(result.words), result.average_confidence
    )
    return result
