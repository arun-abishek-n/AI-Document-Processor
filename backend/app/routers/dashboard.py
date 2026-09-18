"""Dashboard KPIs — real aggregates over Batch/BatchDocument, never random
numbers. Returns proper zeroed-out values (not fabricated ones) when there's
no processing history yet; the frontend renders an empty state for that."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Batch, BatchDocument, DocumentType, User
from app.schemas_batch import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_COMPLETED_STATUSES = ("matched", "exception", "failed")
_IN_FLIGHT_STATUSES = ("pending_confirmation", "matching")


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> DashboardSummary:
    batches = db.query(Batch).all()

    completed = [b for b in batches if b.status in _COMPLETED_STATUSES]
    matched = [b for b in completed if b.status == "matched"]
    exceptions = [b for b in batches if b.status == "exception"]
    in_flight = [b for b in batches if b.status in _IN_FLIGHT_STATUSES]

    match_rate = (len(matched) / len(completed)) if completed else 0.0

    pipeline_status_counts: dict[str, int] = {}
    for b in batches:
        pipeline_status_counts[b.status] = pipeline_status_counts.get(b.status, 0) + 1

    documents = db.query(BatchDocument).all()
    avg_confidence = (
        sum(d.overall_confidence for d in documents) / len(documents) if documents else 0.0
    )

    doc_type_names = {dt.id: dt.name for dt in db.query(DocumentType).all()}
    doc_type_distribution: dict[str, int] = {}
    confidence_buckets = {"low": 0, "medium": 0, "high": 0}
    for d in documents:
        if d.document_type_id is not None:
            name = doc_type_names.get(d.document_type_id, "Unknown")
            doc_type_distribution[name] = doc_type_distribution.get(name, 0) + 1
        bucket = "high" if d.overall_confidence >= 0.85 else "medium" if d.overall_confidence >= 0.6 else "low"
        confidence_buckets[bucket] += 1

    return DashboardSummary(
        processed_count=len(completed),
        match_rate=round(match_rate, 4),
        open_exceptions=len(exceptions),
        avg_confidence=round(avg_confidence, 4),
        in_flight=len(in_flight),
        pipeline_status_counts=pipeline_status_counts,
        doc_type_distribution=doc_type_distribution,
        confidence_buckets=confidence_buckets,
    )
