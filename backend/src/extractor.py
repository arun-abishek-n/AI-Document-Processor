"""
Key-value field extraction from OCR text.

Applies the regex patterns defined in config.FIELD_PATTERNS to raw OCR text
and produces a structured, per-field result carrying the matched value plus
a heuristic confidence score derived from the underlying OCR word confidences.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.ocr import OCRResult
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedField:
    """A single extracted key-value pair with a confidence score.

    `found` is tracked separately from `value is not None` so a field that
    was searched for but genuinely absent from the document is
    distinguishable from one that hasn't been processed yet.
    """
    name: str
    value: str | None
    confidence: float
    found: bool


def _confidence_for_match(matched_text: str, ocr_result: OCRResult) -> float:
    """Estimate a field's confidence as the average OCR confidence of the
    words whose text overlaps the matched substring.

    The regex match operates on `full_text` (a single joined string), which
    has no per-character confidence of its own — confidence lives on the
    individual OCRWord entries the engine produced. This re-associates a
    matched value with the word-level confidences it most likely came from.

    Falls back to the document's overall average confidence when no
    individual word can be matched (e.g. the field spans multiple OCR tokens
    joined during line reconstruction, or punctuation shifted the match
    boundary).
    """
    matched_tokens = matched_text.lower().split()
    if not matched_tokens:
        return ocr_result.average_confidence

    # A word "belongs" to the match if any of its text appears as a
    # substring of one of the matched tokens (or vice versa) — this is a
    # heuristic, not an exact alignment, since regex match spans don't carry
    # OCR word boundaries with them.
    relevant = [
        word.confidence
        for word in ocr_result.words
        if any(token in word.text.lower() for token in matched_tokens)
    ]
    if not relevant:
        return ocr_result.average_confidence

    return sum(relevant) / len(relevant)


def extract_fields(
    ocr_result: OCRResult, patterns: dict[str, str]
) -> dict[str, ExtractedField]:
    """Extract every configured field from OCR text.

    Args:
        ocr_result: the OCRResult produced by src.ocr.run_ocr.
        patterns: mapping of field_name -> regex pattern (config.FIELD_PATTERNS).
            Each pattern is expected to have exactly one capture group: the
            piece of text that becomes the field's value.

    Returns:
        Mapping of field_name -> ExtractedField, including fields that were
        not found (value=None, found=False) so downstream validation can
        report on missing data rather than silently omitting it.
    """
    logger.info("Extracting %d field(s) from OCR text", len(patterns))
    fields: dict[str, ExtractedField] = {}

    for field_name, pattern in patterns.items():
        # re.IGNORECASE because OCR output casing is unreliable (all-caps
        # headers, inconsistent capitalization in scanned forms, etc.), and
        # the field labels ("Invoice Number", "INVOICE NO", "invoice no.")
        # shouldn't need a separate pattern per casing variant.
        match = re.search(pattern, ocr_result.full_text, flags=re.IGNORECASE)
        if match:
            # group(1) is the field's captured value; group(0) would be the
            # whole match including the label text ("Invoice Number: "),
            # which we don't want.
            value = match.group(1).strip()
            confidence = _confidence_for_match(value, ocr_result)
            fields[field_name] = ExtractedField(
                name=field_name, value=value, confidence=confidence, found=True
            )
        else:
            fields[field_name] = ExtractedField(
                name=field_name, value=None, confidence=0.0, found=False
            )

    found_count = sum(1 for f in fields.values() if f.found)
    logger.info("Found %d/%d field(s)", found_count, len(patterns))
    return fields
