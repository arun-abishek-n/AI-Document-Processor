"""The core "Process" workflow: upload a batch, confirm each document's
type, run the matching engine, view results.

Each uploaded file goes through the same OCR pipeline as the standalone
/api/process endpoint (app/pipeline.run_ocr_pipeline — same preprocessing,
same OCR engine), then per-document-type field extraction and matching are
layered on top; nothing here re-implements OCR itself.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Batch, BatchDocument, DocumentType, MatchConfig, MatchRuleResult, User
from app.pipeline import DocumentProcessingError, run_ocr_pipeline
from app.schemas_batch import BatchDetailOut, BatchOut, DocumentTypeAssignment
from app.services.classification import suggest_document_type
from app.services.extraction import extract_for_document_type
from app.services.matching import run_matching
from src.utils import FileTooLargeError, UnsupportedFileError, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/batches", tags=["batches"])


def _doc_type_names(db: Session) -> dict[int, str]:
    return {dt.id: dt.name for dt in db.query(DocumentType).all()}


def _batch_out(batch: Batch) -> BatchOut:
    return BatchOut(
        id=batch.id,
        name=batch.name,
        match_config_id=batch.match_config_id,
        match_config_name=batch.match_config.name if batch.match_config else None,
        status=batch.status,
        overall_confidence=batch.overall_confidence,
        match_passed=batch.match_passed,
        document_count=len(batch.documents),
        created_at=batch.created_at,
        processing_time_seconds=batch.processing_time_seconds,
    )


def _batch_document_dict(doc: BatchDocument) -> dict:
    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "overall_confidence": doc.overall_confidence,
        "extracted_fields": doc.extracted_fields,
        "suggested_document_type_id": doc.suggested_document_type_id,
        "suggested_document_type_name": doc.suggested_document_type.name if doc.suggested_document_type else None,
        "document_type_id": doc.document_type_id,
        "document_type_name": doc.document_type.name if doc.document_type else None,
        "status": doc.status,
        "raw_text": doc.raw_text,
    }


def _batch_detail_out(batch: Batch) -> BatchDetailOut:
    base = _batch_out(batch)
    return BatchDetailOut(
        **base.model_dump(),
        documents=[_batch_document_dict(d) for d in batch.documents],
        rule_results=[{"id": r.id, "rule_name": r.rule_name, "status": r.status, "detail": r.detail} for r in batch.rule_results],
    )


@router.get("", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[BatchOut]:
    batches = db.query(Batch).order_by(Batch.created_at.desc()).all()
    return [_batch_out(b) for b in batches]


@router.get("/{batch_id}", response_model=BatchDetailOut)
def get_batch(batch_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> BatchDetailOut:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return _batch_detail_out(batch)


@router.post("", response_model=BatchDetailOut, status_code=201)
async def create_batch(
    files: list[UploadFile] = File(..., description="2-4 documents to process as one batch"),
    match_config_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BatchDetailOut:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one file.")

    match_config = db.get(MatchConfig, match_config_id)
    if match_config is None:
        raise HTTPException(status_code=400, detail="Selected match configuration not found.")

    expected_count = 2 if match_config.match_type == "2-way" else 3
    if len(files) != expected_count:
        raise HTTPException(
            status_code=400,
            detail=f"'{match_config.name}' is a {match_config.match_type} configuration — upload exactly {expected_count} document(s), not {len(files)}.",
        )

    document_types = db.query(DocumentType).all()

    batch = Batch(
        name=f"Batch of {len(files)}", match_config_id=match_config_id, status="pending_confirmation",
        created_by_id=user.id,
    )
    db.add(batch)
    db.flush()  # assign batch.id before adding documents

    total_confidence = 0.0
    total_processing_time = 0.0
    for upload in files:
        file_bytes = await upload.read()
        try:
            outcome = await run_in_threadpool(run_ocr_pipeline, upload.filename, file_bytes)
        except (UnsupportedFileError, FileTooLargeError, DocumentProcessingError) as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"'{upload.filename}': {exc}") from exc

        suggested_id, _score = suggest_document_type(outcome.raw_text, upload.filename, document_types)
        extracted_fields = {}
        if suggested_id is not None:
            suggested_type = next(dt for dt in document_types if dt.id == suggested_id)
            extracted_fields = extract_for_document_type(outcome.raw_text, outcome.average_confidence, suggested_type.fields)

        db.add(BatchDocument(
            batch_id=batch.id,
            original_filename=upload.filename,
            file_type=outcome.file_type,
            page_count=outcome.page_count,
            raw_text=outcome.raw_text,
            extracted_fields=extracted_fields,
            overall_confidence=outcome.average_confidence,
            suggested_document_type_id=suggested_id,
            document_type_id=suggested_id,  # pre-filled with the suggestion; user confirms/overrides
            status="extracted",
        ))
        total_confidence += outcome.average_confidence
        total_processing_time += outcome.processing_time_seconds

    batch.overall_confidence = round(total_confidence / len(files), 4)
    batch.processing_time_seconds = round(total_processing_time, 2)
    db.commit()
    db.refresh(batch)

    logger.info("Created batch %d with %d document(s)", batch.id, len(files))
    return _batch_detail_out(batch)


@router.patch("/{batch_id}/documents/{doc_id}", response_model=BatchDetailOut)
def assign_document_type(
    batch_id: int,
    doc_id: int,
    payload: DocumentTypeAssignment,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> BatchDetailOut:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    doc = next((d for d in batch.documents if d.id == doc_id), None)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found in this batch.")
    doc_type = db.get(DocumentType, payload.document_type_id)
    if doc_type is None:
        raise HTTPException(status_code=400, detail="Document type not found.")

    doc.document_type_id = doc_type.id
    # Re-run extraction against the newly assigned type's fields, from the
    # already-stored raw OCR text — no need to re-run OCR itself.
    doc.extracted_fields = extract_for_document_type(doc.raw_text, doc.overall_confidence, doc_type.fields)

    # Any prior match verdict was computed against the old type/fields and
    # is now stale — clear it rather than let a changed document keep
    # showing a "matched"/"exception" result that no longer reflects it.
    if batch.rule_results:
        batch.rule_results = []
        batch.match_passed = None
        batch.status = "pending_confirmation"

    db.commit()
    db.refresh(batch)
    return _batch_detail_out(batch)


@router.post("/{batch_id}/match", response_model=BatchDetailOut)
def match_batch(batch_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> BatchDetailOut:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    if batch.match_config is None:
        raise HTTPException(status_code=400, detail="This batch has no match configuration assigned.")

    unassigned = [d.original_filename for d in batch.documents if d.document_type_id is None]
    if unassigned:
        raise HTTPException(
            status_code=400, detail=f"Assign a document type to every file first: {', '.join(unassigned)}"
        )

    results, overall_passed = run_matching(batch.match_config, batch.documents, _doc_type_names(db))

    batch.rule_results = [
        MatchRuleResult(match_rule_id=r.rule_id, rule_name=r.rule_name, status=r.status, detail=r.detail)
        for r in results
    ]
    batch.match_passed = overall_passed
    batch.status = "matched" if overall_passed else "exception"
    db.commit()
    db.refresh(batch)

    logger.info("Matched batch %d: passed=%s (%d rule(s))", batch.id, overall_passed, len(results))
    return _batch_detail_out(batch)
