"""Builds a per-DocumentType regex pattern dict and runs it through the
*existing, unmodified* backend/src/extractor.extract_fields().

The original project only knew one fixed schema (config.FIELD_PATTERNS, an
invoice). Document Types are now configurable, so each field needs its own
pattern — a custom one if the admin set one on the DocumentTypeField, else a
pattern generated here from the field's key/label shape (number/date/amount/
name/gstin/email/phone), falling back to a generic "label: value" pattern
for anything else. The actual matching/scoring logic is untouched.
"""

from __future__ import annotations

import re

from src.extractor import extract_fields
from src.ocr import OCRResult

_DATE_PATTERN = (
    r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|"
    r"\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}|"
    r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})"
)
_AMOUNT_PATTERN = r"[\$₹€£]?\s*([\d,]+\.\d{2})"
# Space only (not \s) in the capture class — \s would also match the
# newline joining OCR lines, letting the match greedily swallow the next
# line's label (e.g. "Nexacore Technologies\nBuyer Name").
_NAME_PATTERN = r"([A-Za-z0-9&.,\- ]{3,60})"
_CODE_PATTERN = r"([A-Za-z0-9\-\/]{3,20})"
_EMAIL_PATTERN = r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"
_PHONE_PATTERN = r"(\+?\d[\d\s\-\(\)]{8,15}\d)"
_GSTIN_PATTERN = r"([A-Za-z0-9]{15})"
_QUANTITY_PATTERN = r"([\d,]+)"


def _words_pattern(text: str) -> str:
    """Turn "purchase_order" into a regex matching flexible whitespace between words."""
    words = [w for w in text.replace("_", " ").split(" ") if w]
    return r"\s*".join(re.escape(w) for w in words)


def default_pattern_for(key: str, label: str) -> str:
    """Generate a reasonable extraction regex from a field's key/label shape."""
    key_lower = key.lower()

    if key_lower.endswith("_number") or key_lower.endswith("_no"):
        # The no./number/# qualifier is mandatory (not optional) so a short,
        # common prefix like "po" doesn't match incidental occurrences of
        # that word in unrelated text (e.g. "...has no PO reference...").
        prefix = _words_pattern(key_lower.rsplit("_", 1)[0])
        return rf"(?:{prefix}\s*(?:no\.?|number|#))\s*[:\-]?\s*{_CODE_PATTERN}"

    if key_lower.endswith("_date"):
        prefix = _words_pattern(key_lower[: -len("_date")])
        return rf"(?:{prefix}\s*date)\s*[:\-]?\s*{_DATE_PATTERN}"

    if "gstin" in key_lower:
        return rf"(?:gstin)\s*[:\-]?\s*{_GSTIN_PATTERN}"

    if "email" in key_lower:
        return _EMAIL_PATTERN

    if "phone" in key_lower or "contact" in key_lower:
        return rf"(?:phone|tel|contact)?\s*[:\-]?\s*{_PHONE_PATTERN}"

    if any(word in key_lower for word in ("amount", "value", "total", "price")):
        prefix = _words_pattern(key_lower)
        return rf"(?:{prefix})\s*[:\-]?\s*{_AMOUNT_PATTERN}"

    if "quantity" in key_lower or "qty" in key_lower:
        prefix = _words_pattern(key_lower)
        return rf"(?:{prefix})\s*[:\-]?\s*{_QUANTITY_PATTERN}"

    if key_lower.endswith("_name"):
        prefix = _words_pattern(key_lower[: -len("_name")])
        return rf"(?:{prefix}\s*name)\s*[:\-]?\s*{_NAME_PATTERN}"

    # Generic fallback: use the human-readable label as the field's own prefix.
    prefix = _words_pattern(label)
    return rf"(?:{prefix})\s*[:\-]?\s*{_NAME_PATTERN}"


def build_pattern_map(fields: list) -> dict[str, str]:
    """fields: list of DocumentTypeField-like objects with .key/.label/.pattern."""
    return {field.key: field.pattern or default_pattern_for(field.key, field.label) for field in fields}


def extract_for_document_type(raw_text: str, average_confidence: float, fields: list) -> dict:
    """Run extraction for one document against one DocumentType's fields.

    Returns the same {field_key: {value, confidence, is_present, is_valid, issue}}
    shape the rest of the API already uses, built from extractor.ExtractedField
    (is_valid mirrors is_present here — format validation is deliberately out
    of scope for arbitrary configurable fields; src/validator.py's format
    checks only apply to the original fixed invoice schema).
    """
    ocr_result = OCRResult(full_text=raw_text, words=[], average_confidence=average_confidence)
    patterns = build_pattern_map(fields)
    extracted = extract_fields(ocr_result, patterns)

    return {
        name: {
            "value": field.value,
            "confidence": round(field.confidence, 4),
            "is_present": field.found,
            "is_valid": field.found,
            "issue": None if field.found else "Field not found in document",
        }
        for name, field in extracted.items()
    }
