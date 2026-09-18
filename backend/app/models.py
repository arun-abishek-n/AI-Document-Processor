"""SQLAlchemy models for auth, configuration, and processing history.

This is new state that didn't exist in the original single-document OCR
demo — the OCR/extraction/validation logic itself (backend/src/) is
untouched; these tables just give the API somewhere to persist users,
document-type/match-rule configuration, and batch processing results.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))  # admin | manager | executive
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DocumentType(Base):
    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    sample_filename: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | configured
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    fields: Mapped[list["DocumentTypeField"]] = relationship(
        back_populates="document_type", cascade="all, delete-orphan", order_by="DocumentTypeField.id"
    )


class DocumentTypeField(Base):
    __tablename__ = "document_type_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"))
    key: Mapped[str] = mapped_column(String(100))  # e.g. "invoice_number"
    label: Mapped[str] = mapped_column(String(150))  # e.g. "Invoice Number"
    pattern: Mapped[str | None] = mapped_column(Text, nullable=True)  # custom regex; null = auto-generated
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)

    document_type: Mapped["DocumentType"] = relationship(back_populates="fields")


class MatchConfig(Base):
    __tablename__ = "match_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    match_type: Mapped[str] = mapped_column(String(10))  # "2-way" | "3-way"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    document_types: Mapped[list["MatchConfigDocumentType"]] = relationship(
        back_populates="match_config", cascade="all, delete-orphan", order_by="MatchConfigDocumentType.position"
    )
    rules: Mapped[list["MatchRule"]] = relationship(
        back_populates="match_config", cascade="all, delete-orphan", order_by="MatchRule.id"
    )


class MatchConfigDocumentType(Base):
    __tablename__ = "match_config_document_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_config_id: Mapped[int] = mapped_column(ForeignKey("match_configs.id"))
    document_type_id: Mapped[int] = mapped_column(ForeignKey("document_types.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)

    match_config: Mapped["MatchConfig"] = relationship(back_populates="document_types")
    document_type: Mapped["DocumentType"] = relationship()


class MatchRule(Base):
    __tablename__ = "match_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_config_id: Mapped[int] = mapped_column(ForeignKey("match_configs.id"))
    name: Mapped[str] = mapped_column(String(100))  # e.g. "PO Number"
    comparison: Mapped[str] = mapped_column(String(20))  # equals | numeric_tolerance | date_equals
    tolerance_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    # {document_type_id (as str): field_key} — which field on each document type this rule compares.
    field_map: Mapped[dict] = mapped_column(JSON, default=dict)

    match_config: Mapped["MatchConfig"] = relationship(back_populates="rules")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    match_config_id: Mapped[int | None] = mapped_column(ForeignKey("match_configs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_confirmation")
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    match_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    processing_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    match_config: Mapped["MatchConfig | None"] = relationship()
    documents: Mapped[list["BatchDocument"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", order_by="BatchDocument.id"
    )
    rule_results: Mapped[list["MatchRuleResult"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", order_by="MatchRuleResult.id"
    )


class BatchDocument(Base):
    __tablename__ = "batch_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    extracted_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    suggested_document_type_id: Mapped[int | None] = mapped_column(ForeignKey("document_types.id"), nullable=True)
    document_type_id: Mapped[int | None] = mapped_column(ForeignKey("document_types.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="extracted")

    batch: Mapped["Batch"] = relationship(back_populates="documents")
    document_type: Mapped["DocumentType | None"] = relationship(foreign_keys=[document_type_id])
    suggested_document_type: Mapped["DocumentType | None"] = relationship(foreign_keys=[suggested_document_type_id])


class MatchRuleResult(Base):
    __tablename__ = "match_rule_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    match_rule_id: Mapped[int | None] = mapped_column(ForeignKey("match_rules.id"), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10))  # passed | failed | warning
    detail: Mapped[dict] = mapped_column(JSON, default=dict)

    batch: Mapped["Batch"] = relationship(back_populates="rule_results")
