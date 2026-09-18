"""Pydantic response models for the public API.

Kept separate from src/exporter.py's dict-building so the API's response
contract is explicit and documented in FastAPI's generated OpenAPI schema,
independent of the internal dataclasses the processing pipeline uses.
"""

from __future__ import annotations

from pydantic import BaseModel


class FieldResult(BaseModel):
    value: str | None
    confidence: float
    is_present: bool
    is_valid: bool
    issue: str | None = None


class ProcessResponse(BaseModel):
    source_file: str
    file_type: str
    page_count: int
    processing_time_seconds: float
    ocr_engine: str
    is_valid_document: bool
    overall_confidence: float
    missing_required_fields: list[str]
    invalid_fields: list[str]
    low_confidence_fields: list[str]
    fields: dict[str, FieldResult]
    raw_text: str


class HealthResponse(BaseModel):
    status: str
    ocr_engine: str
    allowed_extensions: list[str]
    max_file_size_mb: int
