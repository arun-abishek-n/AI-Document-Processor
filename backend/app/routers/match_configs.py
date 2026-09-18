from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Batch, DocumentType, MatchConfig, MatchConfigDocumentType, MatchRule, User
from app.schemas_config import MatchConfigIn, MatchConfigOut

router = APIRouter(prefix="/api/match-configs", tags=["match-configs"])


def _validate_document_types(db: Session, document_type_ids: list[int]) -> None:
    if len(document_type_ids) != len(set(document_type_ids)):
        # Without this, a rule's field_map (keyed by document_type_id) would
        # collapse the duplicated type's two positions into one entry, so a
        # 3-way rule could end up comparing a document's value to itself and
        # trivially "pass" without ever cross-checking a second document.
        raise HTTPException(status_code=400, detail="Document types must be distinct — the same type can't be used twice in one configuration.")

    found = db.query(DocumentType.id).filter(DocumentType.id.in_(document_type_ids)).count()
    if found != len(set(document_type_ids)):
        raise HTTPException(status_code=400, detail="One or more document type ids are invalid.")


@router.get("", response_model=list[MatchConfigOut])
def list_match_configs(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[MatchConfig]:
    return db.query(MatchConfig).order_by(MatchConfig.id).all()


@router.post("", response_model=MatchConfigOut, status_code=201)
def create_match_config(
    payload: MatchConfigIn, db: Session = Depends(get_db), _user: User = Depends(require_role("admin", "manager"))
) -> MatchConfig:
    expected_count = 2 if payload.match_type == "2-way" else 3
    if len(payload.document_type_ids) != expected_count:
        raise HTTPException(
            status_code=400,
            detail=f"A {payload.match_type} configuration needs exactly {expected_count} document types.",
        )
    _validate_document_types(db, payload.document_type_ids)

    match_config = MatchConfig(name=payload.name, match_type=payload.match_type, is_active=payload.is_active)
    match_config.document_types = [
        MatchConfigDocumentType(document_type_id=doc_type_id, position=i)
        for i, doc_type_id in enumerate(payload.document_type_ids)
    ]
    match_config.rules = [
        MatchRule(
            name=r.name, comparison=r.comparison, tolerance_percent=r.tolerance_percent, field_map=r.field_map
        )
        for r in payload.rules
    ]
    db.add(match_config)
    db.commit()
    return match_config


@router.put("/{config_id}", response_model=MatchConfigOut)
def update_match_config(
    config_id: int,
    payload: MatchConfigIn,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "manager")),
) -> MatchConfig:
    match_config = db.get(MatchConfig, config_id)
    if match_config is None:
        raise HTTPException(status_code=404, detail="Match configuration not found.")

    expected_count = 2 if payload.match_type == "2-way" else 3
    if len(payload.document_type_ids) != expected_count:
        raise HTTPException(
            status_code=400,
            detail=f"A {payload.match_type} configuration needs exactly {expected_count} document types.",
        )
    _validate_document_types(db, payload.document_type_ids)

    match_config.name = payload.name
    match_config.match_type = payload.match_type
    match_config.is_active = payload.is_active
    match_config.document_types = [
        MatchConfigDocumentType(document_type_id=doc_type_id, position=i)
        for i, doc_type_id in enumerate(payload.document_type_ids)
    ]
    match_config.rules = [
        MatchRule(
            name=r.name, comparison=r.comparison, tolerance_percent=r.tolerance_percent, field_map=r.field_map
        )
        for r in payload.rules
    ]
    db.commit()
    return match_config


@router.delete("/{config_id}", status_code=204)
def delete_match_config(
    config_id: int, db: Session = Depends(get_db), _user: User = Depends(require_role("admin", "manager"))
) -> None:
    match_config = db.get(MatchConfig, config_id)
    if match_config is None:
        raise HTTPException(status_code=404, detail="Match configuration not found.")

    batch_count = db.query(Batch).filter(Batch.match_config_id == config_id).count()
    if batch_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Can't delete — {batch_count} batch(es) reference this configuration. Deactivate it instead.",
        )

    db.delete(match_config)
    db.commit()
