"""Batch workflow tests.

test_confirm_override_and_match_* below insert BatchDocuments directly with
pre-set extracted_fields (bypassing real OCR) so they run fast and exercise
the confirm/override + matching-engine wiring in isolation. The one
@pytest.mark.integration test uploads real synthetic images through the
full /api/batches endpoint end-to-end, proving the whole pipeline (OCR ->
classification -> extraction -> matching) is real, not mocked.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.models import Batch, BatchDocument, DocumentType, MatchConfig


def _get_ids(db_session):
    po = db_session.query(DocumentType).filter(DocumentType.name == "Purchase Order").first()
    invoice = db_session.query(DocumentType).filter(DocumentType.name == "Invoice").first()
    config = db_session.query(MatchConfig).filter(MatchConfig.match_type == "2-way").first()
    return po.id, invoice.id, config.id


def test_list_batches_empty_state_is_fine(client, admin_headers):
    response = client.get("/api/batches", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_batch_upload_rejects_wrong_file_count_for_match_type(client, admin_headers, db_session):
    """Regression: a 2-way config used to silently accept 1 or 3+ files,
    burning OCR time before failing later (if at all) at /match."""
    _po_id, _invoice_id, config_id = _get_ids(db_session)  # this fixture's config is 2-way

    response = client.post(
        "/api/batches", headers=admin_headers,
        files=[("files", ("only_one.png", b"fake", "image/png"))],
        data={"match_config_id": str(config_id)},
    )

    assert response.status_code == 400
    assert "2-way" in response.json()["detail"]


def test_match_requires_every_document_to_have_a_type_assigned(client, admin_headers, db_session):
    po_id, invoice_id, config_id = _get_ids(db_session)

    batch = Batch(name="Batch of 2", match_config_id=config_id, status="pending_confirmation")
    batch.documents = [
        BatchDocument(
            original_filename="po.png", file_type="png", raw_text="", overall_confidence=0.9,
            document_type_id=po_id, extracted_fields={"po_number": {"value": "PO-1", "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None}},
        ),
        BatchDocument(
            original_filename="invoice.png", file_type="png", raw_text="", overall_confidence=0.9,
            document_type_id=None,  # not yet confirmed
            extracted_fields={"po_number": {"value": "PO-1", "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None}},
        ),
    ]
    db_session.add(batch)
    db_session.commit()

    response = client.post(f"/api/batches/{batch.id}/match", headers=admin_headers)

    assert response.status_code == 400
    assert "invoice.png" in response.json()["detail"]


def test_confirm_override_then_match_passes(client, admin_headers, db_session):
    po_id, invoice_id, config_id = _get_ids(db_session)

    batch = Batch(name="Batch of 2", match_config_id=config_id, status="pending_confirmation")
    po_doc = BatchDocument(
        original_filename="po.png", file_type="png", raw_text="PO Number: PO-1\nVendor Name: Acme Co\nTotal Amount: 100.00",
        overall_confidence=0.9, document_type_id=po_id,
        extracted_fields={
            "po_number": {"value": "PO-1", "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None},
            "vendor_name": {"value": "Acme Co", "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None},
            "total_amount": {"value": "100.00", "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None},
        },
    )
    # This document starts out unassigned, matching the real upload flow
    # where the user must confirm the suggested type before matching runs.
    invoice_doc = BatchDocument(
        original_filename="invoice.png", file_type="png",
        raw_text="Supplier Name: Acme Co\nPO Number: PO-1\nTotal Amount: 100.00",
        overall_confidence=0.9, document_type_id=None, extracted_fields={},
    )
    batch.documents = [po_doc, invoice_doc]
    db_session.add(batch)
    db_session.commit()

    assign = client.patch(
        f"/api/batches/{batch.id}/documents/{invoice_doc.id}", headers=admin_headers,
        json={"document_type_id": invoice_id},
    )
    assert assign.status_code == 200
    assigned_doc = next(d for d in assign.json()["documents"] if d["id"] == invoice_doc.id)
    assert assigned_doc["extracted_fields"]["po_number"]["value"] == "PO-1"

    result = client.post(f"/api/batches/{batch.id}/match", headers=admin_headers)
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "matched"
    assert body["match_passed"] is True


def test_reassigning_a_document_after_match_clears_the_stale_verdict(client, admin_headers, db_session):
    """Regression: changing a document's type after /match used to leave the
    old rule_results and matched/exception status in place, showing a
    verdict that no longer reflects the (now re-extracted) document."""
    po_id, invoice_id, config_id = _get_ids(db_session)
    grn = db_session.query(DocumentType).filter(DocumentType.name == "Goods Receipt").first()

    batch = Batch(name="Batch of 2", match_config_id=config_id, status="pending_confirmation")
    field = lambda value: {"value": value, "confidence": 0.9, "is_present": True, "is_valid": True, "issue": None}
    po_doc = BatchDocument(
        original_filename="po.png", file_type="png", raw_text="PO Number: PO-1\nVendor Name: Acme\nTotal Amount: 100.00",
        overall_confidence=0.9, document_type_id=po_id,
        extracted_fields={"po_number": field("PO-1"), "vendor_name": field("Acme"), "total_amount": field("100.00")},
    )
    invoice_doc = BatchDocument(
        original_filename="invoice.png", file_type="png", raw_text="PO Number: PO-1\nSupplier Name: Acme\nTotal Amount: 100.00",
        overall_confidence=0.9, document_type_id=invoice_id,
        extracted_fields={"po_number": field("PO-1"), "supplier_name": field("Acme"), "total_amount": field("100.00")},
    )
    batch.documents = [po_doc, invoice_doc]
    db_session.add(batch)
    db_session.commit()

    matched = client.post(f"/api/batches/{batch.id}/match", headers=admin_headers)
    assert matched.json()["status"] == "matched"
    assert len(matched.json()["rule_results"]) > 0

    reassigned = client.patch(
        f"/api/batches/{batch.id}/documents/{invoice_doc.id}", headers=admin_headers,
        json={"document_type_id": grn.id},
    )
    body = reassigned.json()
    assert body["status"] == "pending_confirmation"
    assert body["match_passed"] is None
    assert body["rule_results"] == []
    assert all(r["status"] == "passed" for r in body["rule_results"])


def _make_image(lines: list[str]) -> io.BytesIO:
    # PIL's built-in default font is a tiny bitmap face that OCRs poorly
    # (and was previously misclassifying these test documents as a result)
    # — a real TrueType font at a normal document-text size is what makes
    # this test representative of an actual scanned/photographed document.
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default(size=28)

    img = Image.new("RGB", (900, 350), "white")
    draw = ImageDraw.Draw(img)
    y = 30
    for line in lines:
        draw.text((30, y), line, fill="black", font=font)
        y += 50
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@pytest.mark.integration
def test_real_batch_upload_classification_and_matching_detects_exception(client, admin_headers, db_session):
    """End-to-end with real OCR: a genuinely mismatched PO/Invoice pair
    should classify correctly on its own and be flagged as an exception —
    not because we told it to, but because the extracted totals actually
    differ by more than the configured tolerance."""
    _po_id, _invoice_id, config_id = _get_ids(db_session)

    po_image = _make_image([
        "PURCHASE ORDER", "PO Number: PO-TEST-1", "Vendor Name: Acme Co", "Total Amount: 1000.00",
    ])
    invoice_image = _make_image([
        "INVOICE", "PO Number: PO-TEST-1", "Supplier Name: Acme Co", "Total Amount: 1500.00",
    ])

    response = client.post(
        "/api/batches", headers=admin_headers,
        files=[("files", ("po.png", po_image, "image/png")), ("files", ("invoice.png", invoice_image, "image/png"))],
        data={"match_config_id": str(config_id)},
    )
    assert response.status_code == 201
    batch = response.json()
    assert batch["documents"][0]["suggested_document_type_name"] == "Purchase Order"
    assert batch["documents"][1]["suggested_document_type_name"] == "Invoice"
    assert batch["processing_time_seconds"] > 0  # regression: this used to stay 0.0

    matched = client.post(f"/api/batches/{batch['id']}/match", headers=admin_headers)
    assert matched.status_code == 200
    body = matched.json()
    assert body["status"] == "exception"
    assert any(r["status"] == "failed" and r["rule_name"] == "Total Amount" for r in body["rule_results"])
