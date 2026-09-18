from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas import FieldResult


class BatchDocumentOut(BaseModel):
    id: int
    original_filename: str
    file_type: str
    page_count: int
    overall_confidence: float
    extracted_fields: dict[str, FieldResult]
    suggested_document_type_id: int | None
    suggested_document_type_name: str | None
    document_type_id: int | None
    document_type_name: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class BatchDocumentDetailOut(BatchDocumentOut):
    raw_text: str


class MatchRuleResultOut(BaseModel):
    id: int
    rule_name: str
    status: str  # passed | failed | warning
    detail: dict

    model_config = ConfigDict(from_attributes=True)


class BatchOut(BaseModel):
    id: int
    name: str
    match_config_id: int | None
    match_config_name: str | None
    status: str
    overall_confidence: float
    match_passed: bool | None
    document_count: int
    created_at: datetime
    processing_time_seconds: float

    model_config = ConfigDict(from_attributes=True)


class BatchDetailOut(BatchOut):
    documents: list[BatchDocumentDetailOut]
    rule_results: list[MatchRuleResultOut]


class DocumentTypeAssignment(BaseModel):
    document_type_id: int


class DashboardSummary(BaseModel):
    processed_count: int
    match_rate: float  # 0.0-1.0
    open_exceptions: int
    avg_confidence: float
    in_flight: int
    pipeline_status_counts: dict[str, int]
    doc_type_distribution: dict[str, int]
    confidence_buckets: dict[str, int]  # {"low": n, "medium": n, "high": n}
