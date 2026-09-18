"""Unit tests for app/services/extraction.py's default pattern generator.

Regression coverage for a real bug found while testing the matching engine
end-to-end: the initial *_name pattern didn't account for the literal word
"Name" in labels like "Vendor Name:", so it captured "Name" instead of the
actual value; and the capture class's \\s allowed it to swallow the next
OCR line entirely (e.g. "Nexacore Technologies\\nBuyer Name").
"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.extraction import extract_for_document_type


def test_name_field_does_not_capture_the_label_word_itself():
    fields = [SimpleNamespace(key="vendor_name", label="Vendor Name", pattern=None)]
    raw_text = "Vendor Name: Nexacore Technologies\nBuyer Name: Meridian Enterprises"

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["vendor_name"]["value"] == "Nexacore Technologies"


def test_name_field_does_not_span_into_the_next_line():
    fields = [SimpleNamespace(key="supplier_name", label="Supplier Name", pattern=None)]
    raw_text = "Supplier Name: Nexacore Technologies\nTotal Goods Value: 5000.00"

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["supplier_name"]["value"] == "Nexacore Technologies"


def test_number_field_uses_generated_pattern():
    fields = [SimpleNamespace(key="po_number", label="PO Number", pattern=None)]
    raw_text = "PO Number: PO-2026-1001"

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["po_number"]["value"] == "PO-2026-1001"


def test_amount_field_uses_generated_pattern():
    fields = [SimpleNamespace(key="total_goods_value", label="Total Goods Value", pattern=None)]
    raw_text = "Total Goods Value: 5000.00"

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["total_goods_value"]["value"] == "5000.00"


def test_custom_pattern_overrides_the_generated_one():
    fields = [SimpleNamespace(key="custom_code", label="Custom Code", pattern=r"CODE-(\d+)")]
    raw_text = "Reference CODE-4471 on file"

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["custom_code"]["value"] == "4471"


def test_missing_field_is_reported_not_found():
    fields = [SimpleNamespace(key="po_number", label="PO Number", pattern=None)]
    raw_text = "This document has no PO reference at all."

    result = extract_for_document_type(raw_text, 0.9, fields)

    assert result["po_number"]["is_present"] is False
    assert result["po_number"]["value"] is None
