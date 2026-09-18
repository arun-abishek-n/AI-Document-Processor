"""
Validation of extracted fields.

Checks each ExtractedField for structural correctness (date parses, amount
is numeric, email looks like an email, etc.), flags missing required
fields, and computes an overall document confidence/validity summary.

This is a deliberately separate stage from extraction: extractor.py answers
"what does the regex think this field is?" while validator.py answers "is
that value actually usable?" — keeping them apart means new validation
rules never require touching the extraction patterns, and vice versa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import config
from src.extractor import ExtractedField
from src.utils import get_logger

logger = get_logger(__name__)

# Precompiled once at import time rather than per-call, since these run
# against every document processed in a session.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_AMOUNT_RE = re.compile(r"^[\d,]+\.\d{2}$")


@dataclass
class FieldValidation:
    """Validation outcome for a single field."""
    name: str
    value: str | None
    confidence: float
    is_present: bool
    is_valid: bool
    is_low_confidence: bool
    issue: str | None = None


@dataclass
class ValidationSummary:
    """Aggregate validation result for a whole document."""
    fields: dict[str, FieldValidation]
    missing_required: list[str]
    invalid_fields: list[str]
    low_confidence_fields: list[str]
    overall_confidence: float
    is_valid_document: bool


def _validate_date(value: str) -> bool:
    """Return True if `value` matches any of config.DATE_INPUT_FORMATS.

    Invoices in the wild use inconsistent date conventions (DD/MM/YYYY,
    MM-DD-YYYY, "March 15, 2024", ...), so this tries each known format in
    turn rather than assuming a single locale.
    """
    for fmt in config.DATE_INPUT_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            # This format didn't match — try the next one. Only exhausting
            # every format means the value truly isn't a recognizable date.
            continue
    return False


def _validate_amount(value: str) -> bool:
    """Return True if `value` looks like a monetary amount (e.g. "1,416.00").

    Deliberately strict (exactly two decimal places) since a value that
    fails this check either wasn't captured cleanly by OCR or the regex
    grabbed the wrong substring — both cases worth flagging rather than
    silently accepting a malformed total.
    """
    return bool(_AMOUNT_RE.match(value.replace(" ", "")))


def _validate_email(value: str) -> bool:
    """Return True if `value` has the basic shape of an email address."""
    return bool(_EMAIL_RE.match(value.strip()))


# Only fields with a meaningful format to check get an entry here. Fields
# like vendor_name/customer_name are free-text and have no format to
# validate beyond "was something extracted at all".
_FIELD_VALIDATORS = {
    "invoice_date": _validate_date,
    "due_date": _validate_date,
    "total_amount": _validate_amount,
    "subtotal": _validate_amount,
    "tax_amount": _validate_amount,
    "email": _validate_email,
}


def _validate_single_field(field: ExtractedField) -> FieldValidation:
    """Apply the appropriate validator (if any) to one extracted field."""
    if not field.found or field.value is None:
        # A field that was never found can't fail a format check — it's
        # reported as missing instead, via is_present=False.
        return FieldValidation(
            name=field.name,
            value=None,
            confidence=0.0,
            is_present=False,
            is_valid=False,
            is_low_confidence=True,
            issue="Field not found in document",
        )

    validator = _FIELD_VALIDATORS.get(field.name)
    # Fields with no registered validator (e.g. vendor_name) are considered
    # valid by default — there's no format to check, only presence.
    is_valid = validator(field.value) if validator else True
    is_low_confidence = field.confidence < config.MIN_CONFIDENCE_THRESHOLD

    issue = None
    if not is_valid:
        issue = f"Value '{field.value}' failed format validation for '{field.name}'"
    elif is_low_confidence:
        # Format-valid but low-confidence values are still surfaced as an
        # issue: the OCR engine may have "guessed right" by luck, and a
        # human reviewer should double-check it.
        issue = f"Low OCR confidence ({field.confidence:.0%})"

    return FieldValidation(
        name=field.name,
        value=field.value,
        confidence=field.confidence,
        is_present=True,
        is_valid=is_valid,
        is_low_confidence=is_low_confidence,
        issue=issue,
    )


def validate_fields(extracted: dict[str, ExtractedField]) -> ValidationSummary:
    """Validate every extracted field and summarize document-level quality.

    Args:
        extracted: mapping of field_name -> ExtractedField from src.extractor.

    Returns:
        A ValidationSummary with per-field results plus aggregate confidence
        and a pass/fail flag based on config.REQUIRED_FIELDS.
    """
    logger.info("Validating %d extracted field(s)", len(extracted))

    results = {name: _validate_single_field(field) for name, field in extracted.items()}

    # Required-ness is checked against config.REQUIRED_FIELDS rather than
    # "every field the extractor knows about" — some fields (e.g. due_date,
    # tax_amount) are commonly optional on real invoices.
    missing_required = [
        name for name in config.REQUIRED_FIELDS
        if name in results and not results[name].is_present
    ]
    invalid_fields = [name for name, r in results.items() if r.is_present and not r.is_valid]
    low_confidence_fields = [name for name, r in results.items() if r.is_low_confidence and r.is_present]

    # Overall confidence only averages fields that were actually found —
    # missing fields already contribute to `missing_required` and shouldn't
    # also drag down the confidence score of the fields that WERE extracted.
    present_confidences = [r.confidence for r in results.values() if r.is_present]
    overall_confidence = (
        sum(present_confidences) / len(present_confidences) if present_confidences else 0.0
    )

    # A document is "valid" only if nothing required is missing AND nothing
    # present failed its format check. Low confidence alone does not fail a
    # document — it's a hint for human review, not a hard error.
    is_valid_document = not missing_required and not invalid_fields

    logger.info(
        "Validation complete: valid=%s, missing=%s, invalid=%s",
        is_valid_document, missing_required, invalid_fields,
    )

    return ValidationSummary(
        fields=results,
        missing_required=missing_required,
        invalid_fields=invalid_fields,
        low_confidence_fields=low_confidence_fields,
        overall_confidence=overall_confidence,
        is_valid_document=is_valid_document,
    )
