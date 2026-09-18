"""Unit tests for regex-based field extraction.

Uses synthetic OCRResult objects (no OCR engine involved) so these run fast
and require no model download, matching README's "Testing" section.
"""

from __future__ import annotations

import config
from src.extractor import extract_fields
from src.ocr import OCRResult, OCRWord

SAMPLE_TEXT = (
    "INVOICE\n"
    "Invoice Number: INV-2024-0587\n"
    "Invoice Date: 15/03/2024\n"
    "Due Date: 30/03/2024\n"
    "Bill From: Acme Supplies Co.\n"
    "Bill To: Northwind Traders\n"
    "Subtotal: 1200.00\n"
    "Tax: 216.00\n"
    "Total Amount: $1416.00\n"
    "Contact: jane.doe@acmesupplies.com\n"
    "Phone: +1 555 123 4567"
)


def _sample_ocr_result(text: str = SAMPLE_TEXT, confidence: float = 0.9) -> OCRResult:
    words = [OCRWord(text=w, confidence=confidence, bbox=(0, 0, 1, 1)) for w in text.split()]
    return OCRResult(full_text=text, words=words, average_confidence=confidence)


def test_extracts_required_fields():
    result = extract_fields(_sample_ocr_result(), config.FIELD_PATTERNS)

    assert result["invoice_number"].value == "INV-2024-0587"
    assert result["invoice_date"].value == "15/03/2024"
    assert result["total_amount"].value == "1416.00"
    assert all(f.found for f in (result["invoice_number"], result["invoice_date"], result["total_amount"]))


def test_extracts_optional_fields():
    result = extract_fields(_sample_ocr_result(), config.FIELD_PATTERNS)

    assert result["due_date"].value == "30/03/2024"
    assert result["subtotal"].value == "1200.00"
    assert result["tax_amount"].value == "216.00"
    assert result["email"].value == "jane.doe@acmesupplies.com"
    assert result["phone"].value == "+1 555 123 4567"


def test_missing_field_is_reported_not_found():
    text_without_email = SAMPLE_TEXT.replace("Contact: jane.doe@acmesupplies.com\n", "")
    result = extract_fields(_sample_ocr_result(text_without_email), config.FIELD_PATTERNS)

    assert result["email"].found is False
    assert result["email"].value is None
    assert result["email"].confidence == 0.0


def test_total_amount_does_not_match_subtotal_label():
    text = "Subtotal: 500.00\nTotal Amount: 600.00"
    result = extract_fields(_sample_ocr_result(text), config.FIELD_PATTERNS)

    assert result["total_amount"].value == "600.00"
    assert result["subtotal"].value == "500.00"


def test_confidence_reflects_matched_word_scores():
    words = [
        OCRWord(text="Invoice", confidence=0.5, bbox=(0, 0, 1, 1)),
        OCRWord(text="Number:", confidence=0.5, bbox=(0, 0, 1, 1)),
        OCRWord(text="INV-2024-0587", confidence=0.99, bbox=(0, 0, 1, 1)),
    ]
    ocr_result = OCRResult(
        full_text="Invoice Number: INV-2024-0587", words=words, average_confidence=0.66
    )
    result = extract_fields(ocr_result, {"invoice_number": config.FIELD_PATTERNS["invoice_number"]})

    assert result["invoice_number"].confidence == 0.99
