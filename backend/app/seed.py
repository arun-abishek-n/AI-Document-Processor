"""Idempotent demo-data seeding.

Runs once at startup (see app/main.py). If the `users` table already has
rows, this is a no-op — so restarting the app never duplicates or resets
data a user has already created through the UI. On a fresh/empty database
(e.g. after a Hugging Face Space cold restart with no persistent volume),
it re-creates the demo users, document types, and match configs so the app
is immediately usable again.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import DocumentType, DocumentTypeField, MatchConfig, MatchConfigDocumentType, MatchRule, User

DEMO_USERS = [
    {"username": "admin", "password": "admin123", "name": "Admin User", "role": "admin"},
    {"username": "manager", "password": "manager123", "name": "Alex Morgan", "role": "manager"},
    {"username": "executive", "password": "executive123", "name": "Priya Shah", "role": "executive"},
]

INVOICE_FIELDS = [
    ("invoice_number", "Invoice Number", True),
    ("invoice_date", "Invoice Date", True),
    ("due_date", "Due Date", False),
    ("po_number", "PO Number", False),
    ("supplier_name", "Supplier Name", True),
    ("supplier_gstin", "Supplier GSTIN", False),
    ("buyer_name", "Buyer Name", False),
    ("total_amount", "Total Amount", True),
    ("tax_amount", "Tax Amount", False),
]

PO_FIELDS = [
    ("po_number", "PO Number", True),
    ("po_date", "PO Date", True),
    ("vendor_name", "Vendor Name", True),
    ("buyer_name", "Buyer Name", False),
    ("requisition_number", "Requisition Number", False),
    ("total_amount", "Total Amount", True),
]

GRN_FIELDS = [
    ("grn_number", "GRN Number", True),
    ("grn_date", "GRN Date", True),
    ("purchase_order_number", "Purchase Order Number", True),
    ("supplier_name", "Supplier Name", True),
    ("total_goods_value", "Total Goods Value", False),
]

DELIVERY_NOTE_FIELDS = [
    ("delivery_note_number", "Delivery Note Number", True),
    ("delivery_date", "Delivery Date", False),
    ("po_number", "PO Number", False),
    ("vendor_name", "Vendor Name", False),
]


def _seed_document_type(db: Session, name: str, slug: str, description: str, fields: list, status: str) -> DocumentType:
    doc_type = DocumentType(name=name, slug=slug, description=description, status=status)
    doc_type.fields = [
        DocumentTypeField(key=key, label=label, is_required=required) for key, label, required in fields
    ]
    db.add(doc_type)
    return doc_type


def seed_if_empty(db: Session) -> None:
    if db.query(User).first() is not None:
        return  # already seeded — never overwrite user-created data

    for u in DEMO_USERS:
        db.add(User(username=u["username"], password_hash=hash_password(u["password"]), name=u["name"], role=u["role"]))

    invoice = _seed_document_type(
        db, "Invoice", "invoice",
        "A formal, time-stamped commercial document sent by a seller to a buyer to request payment for goods or services provided.",
        INVOICE_FIELDS, "configured",
    )
    po = _seed_document_type(
        db, "Purchase Order", "purchase-order",
        "An official, legally binding document sent by a buyer to a seller that lists the types, quantities, and agreed prices for products or services.",
        PO_FIELDS, "configured",
    )
    grn = _seed_document_type(
        db, "Goods Receipt", "goods-receipt",
        "The formal confirmation and record that items ordered from a supplier have physically arrived at a facility and been accepted.",
        GRN_FIELDS, "configured",
    )
    _seed_document_type(
        db, "Delivery Note", "delivery-note",
        "A supplier-issued document accompanying a shipment that lists the delivered items.",
        DELIVERY_NOTE_FIELDS, "draft",
    )
    db.flush()  # assign ids to invoice/po/grn before referencing them below

    two_way = MatchConfig(name="PO ↔ Invoice", match_type="2-way")
    two_way.document_types = [
        MatchConfigDocumentType(document_type_id=po.id, position=0),
        MatchConfigDocumentType(document_type_id=invoice.id, position=1),
    ]
    two_way.rules = [
        MatchRule(name="PO Number", comparison="equals", field_map={str(po.id): "po_number", str(invoice.id): "po_number"}),
        MatchRule(name="Vendor / Supplier", comparison="equals", field_map={str(po.id): "vendor_name", str(invoice.id): "supplier_name"}),
        MatchRule(
            name="Total Amount", comparison="numeric_tolerance", tolerance_percent=2.0,
            field_map={str(po.id): "total_amount", str(invoice.id): "total_amount"},
        ),
    ]
    db.add(two_way)

    three_way = MatchConfig(name="PO ↔ Goods Receipt ↔ Invoice", match_type="3-way")
    three_way.document_types = [
        MatchConfigDocumentType(document_type_id=po.id, position=0),
        MatchConfigDocumentType(document_type_id=grn.id, position=1),
        MatchConfigDocumentType(document_type_id=invoice.id, position=2),
    ]
    three_way.rules = [
        MatchRule(
            name="PO Number", comparison="equals",
            field_map={str(po.id): "po_number", str(grn.id): "purchase_order_number", str(invoice.id): "po_number"},
        ),
        MatchRule(
            name="Vendor / Supplier", comparison="equals",
            field_map={str(po.id): "vendor_name", str(grn.id): "supplier_name", str(invoice.id): "supplier_name"},
        ),
        MatchRule(
            name="Total Amount", comparison="numeric_tolerance", tolerance_percent=2.0,
            field_map={str(po.id): "total_amount", str(grn.id): "total_goods_value", str(invoice.id): "total_amount"},
        ),
    ]
    db.add(three_way)

    db.commit()
