"""Unit tests for field validation (formats, required fields, confidence)."""

from __future__ import annotations

import config
from src.extractor import ExtractedField
from src.validator import validate_fields


def _field(name: str, value: str | None, confidence: float = 0.9, found: bool = True) -> ExtractedField:
    return ExtractedField(name=name, value=value, confidence=confidence, found=found)


def test_valid_document_passes():
    extracted = {
        "invoice_number": _field("invoice_number", "INV-001"),
        "invoice_date": _field("invoice_date", "15/03/2024"),
        "total_amount": _field("total_amount", "1416.00"),
    }
    summary = validate_fields(extracted)

    assert summary.is_valid_document is True
    assert summary.missing_required == []
    assert summary.invalid_fields == []


def test_missing_required_field_fails_document():
    extracted = {
        "invoice_number": _field("invoice_number", None, found=False),
        "invoice_date": _field("invoice_date", "15/03/2024"),
        "total_amount": _field("total_amount", "1416.00"),
    }
    summary = validate_fields(extracted)

    assert summary.is_valid_document is False
    assert "invoice_number" in summary.missing_required


def test_malformed_amount_is_invalid():
    extracted = {
        "total_amount": _field("total_amount", "not-a-number"),
    }
    summary = validate_fields(extracted)

    assert summary.fields["total_amount"].is_valid is False
    assert "total_amount" in summary.invalid_fields


def test_malformed_date_is_invalid():
    extracted = {"invoice_date": _field("invoice_date", "not-a-date")}
    summary = validate_fields(extracted)

    assert summary.fields["invoice_date"].is_valid is False


def test_low_confidence_flagged_but_still_valid():
    low_conf = config.MIN_CONFIDENCE_THRESHOLD - 0.1
    extracted = {"invoice_number": _field("invoice_number", "INV-001", confidence=low_conf)}
    summary = validate_fields(extracted)

    assert summary.fields["invoice_number"].is_low_confidence is True
    assert summary.fields["invoice_number"].is_valid is True  # low confidence != invalid
    assert "invoice_number" in summary.low_confidence_fields


def test_free_text_field_has_no_format_check():
    extracted = {"vendor_name": _field("vendor_name", "Acme Supplies Co.")}
    summary = validate_fields(extracted)

    assert summary.fields["vendor_name"].is_valid is True
