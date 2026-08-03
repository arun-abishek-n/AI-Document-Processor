"""
Central configuration for the AI Document Processor.

All tunable constants live here so the rest of the codebase never hardcodes
paths, thresholds, or regex patterns inline.
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
OUTPUT_DIR: Path = BASE_DIR / "outputs"
SAMPLE_DOCS_DIR: Path = BASE_DIR / "sample_documents"
MODELS_DIR: Path = BASE_DIR / "models"
LOG_DIR: Path = BASE_DIR / "logs"

for _dir in (OUTPUT_DIR, MODELS_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Upload constraints
# --------------------------------------------------------------------------
ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".jpg", ".jpeg", ".png")
MAX_FILE_SIZE_MB: int = 20
PDF_DPI: int = 300  # resolution used when rasterizing PDF pages

# --------------------------------------------------------------------------
# OCR engine
# --------------------------------------------------------------------------
# "easyocr" is the default: pure pip install, no external system binary
# required. "tesseract" is a supported alternative for environments where
# pytesseract + the Tesseract binary are already installed.
OCR_ENGINE: str = os.getenv("OCR_ENGINE", "easyocr")
EASYOCR_LANGUAGES: list[str] = ["en"]
EASYOCR_GPU: bool = False
TESSERACT_CMD: str | None = os.getenv("TESSERACT_CMD")  # e.g. C:\Program Files\Tesseract-OCR\tesseract.exe
TESSERACT_CONFIG: str = "--oem 3 --psm 6"

# --------------------------------------------------------------------------
# Image preprocessing
# --------------------------------------------------------------------------
DENOISE_STRENGTH: int = 10
ADAPTIVE_THRESH_BLOCK_SIZE: int = 35
ADAPTIVE_THRESH_C: int = 11
DESKEW_ENABLED: bool = True
RESIZE_MAX_DIMENSION: int = 2400  # cap longest side to keep OCR runtime bounded

# --------------------------------------------------------------------------
# Field extraction — regex patterns per field name
# --------------------------------------------------------------------------
FIELD_PATTERNS: dict[str, str] = {
    # The qualifier after "invoice" is mandatory so a bare "INVOICE" document
    # title/header (with no number on the same line) isn't mistaken for a match.
    "invoice_number": r"(?:invoice\s*(?:no\.?|number|#)\s*[:\-]?\s*)([A-Za-z0-9\-\/]{3,20})",
    # The "date" fallback excludes anything preceded by "due " so it doesn't
    # pick up a due date when no explicit "invoice date" label is present.
    "invoice_date": r"(?:invoice\s*date|(?<!due\s)date)\s*[:\-]?\s*"
                     r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|"
                     r"\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}|"
                     r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
    "due_date": r"(?:due\s*date)\s*[:\-]?\s*"
                r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|"
                r"\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
    # \b before "total" keeps this from matching the "total" inside "subtotal".
    "total_amount": r"(?:\btotal\b\s*(?:amount|due)?|grand\s*total|amount\s*due)\s*[:\-]?\s*"
                     r"[\$₹€£]?\s*([\d,]+\.\d{2})",
    "subtotal": r"(?:sub\s*-?\s*total)\s*[:\-]?\s*[\$₹€£]?\s*([\d,]+\.\d{2})",
    "tax_amount": r"(?:tax|vat|gst)\s*(?:\(\d{1,2}%\))?\s*[:\-]?\s*[\$₹€£]?\s*([\d,]+\.\d{2})",
    "email": r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    "phone": r"(?:phone|tel|contact)?\s*[:\-]?\s*(\+?\d[\d\s\-\(\)]{8,15}\d)",
    "vendor_name": r"(?:vendor|from|bill\s*from|company)\s*[:\-]?\s*([A-Za-z0-9&.,\-\s]{3,40})",
    "customer_name": r"(?:bill\s*to|customer|client)\s*[:\-]?\s*([A-Za-z0-9&.,\-\s]{3,40})",
}

# Fields considered mandatory for a document to be marked "valid"
REQUIRED_FIELDS: tuple[str, ...] = ("invoice_number", "invoice_date", "total_amount")

# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
DATE_INPUT_FORMATS: tuple[str, ...] = (
    "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
    "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%B %d, %Y", "%b %d, %Y",
)
MIN_CONFIDENCE_THRESHOLD: float = 0.60  # below this, a field is flagged low-confidence

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOG_FILE: Path = LOG_DIR / "app.log"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
