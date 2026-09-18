from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import BatchDocument, DocumentType, DocumentTypeField, MatchConfigDocumentType, User
from app.schemas_config import DocumentTypeIn, DocumentTypeOut

router = APIRouter(prefix="/api/document-types", tags=["document-types"])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("", response_model=list[DocumentTypeOut])
def list_document_types(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[DocumentType]:
    return db.query(DocumentType).order_by(DocumentType.id).all()


@router.post("", response_model=DocumentTypeOut, status_code=201)
def create_document_type(
    payload: DocumentTypeIn, db: Session = Depends(get_db), _user: User = Depends(require_role("admin", "manager"))
) -> DocumentType:
    slug = _slugify(payload.name)
    if db.query(DocumentType).filter(DocumentType.slug == slug).first() is not None:
        raise HTTPException(status_code=400, detail=f"A document type named '{payload.name}' already exists.")

    doc_type = DocumentType(name=payload.name, slug=slug, description=payload.description, status=payload.status)
    doc_type.fields = [
        DocumentTypeField(key=f.key, label=f.label, pattern=f.pattern, is_required=f.is_required)
        for f in payload.fields
    ]
    db.add(doc_type)
    db.commit()
    return doc_type


@router.put("/{doc_type_id}", response_model=DocumentTypeOut)
def update_document_type(
    doc_type_id: int,
    payload: DocumentTypeIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "manager")),
) -> DocumentType:
    doc_type = db.get(DocumentType, doc_type_id)
    if doc_type is None:
        raise HTTPException(status_code=404, detail="Document type not found.")

    doc_type.name = payload.name
    doc_type.description = payload.description
    doc_type.status = payload.status
    doc_type.fields = [
        DocumentTypeField(key=f.key, label=f.label, pattern=f.pattern, is_required=f.is_required)
        for f in payload.fields
    ]
    db.commit()
    return doc_type


@router.delete("/{doc_type_id}", status_code=204)
def delete_document_type(
    doc_type_id: int, db: Session = Depends(get_db), _user: User = Depends(require_role("admin", "manager"))
) -> None:
    doc_type = db.get(DocumentType, doc_type_id)
    if doc_type is None:
        raise HTTPException(status_code=404, detail="Document type not found.")

    in_use = db.query(MatchConfigDocumentType).filter(MatchConfigDocumentType.document_type_id == doc_type_id).count()
    if in_use > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Can't delete — {in_use} match configuration(s) use this type. Remove it from those first.",
        )
    processed = db.query(BatchDocument).filter(BatchDocument.document_type_id == doc_type_id).count()
    if processed > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Can't delete — {processed} processed document(s) reference this type.",
        )

    db.delete(doc_type)
    db.commit()
