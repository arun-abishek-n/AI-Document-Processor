from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DocumentTypeFieldIn(BaseModel):
    key: str
    label: str
    pattern: str | None = None
    is_required: bool = False


class DocumentTypeFieldOut(DocumentTypeFieldIn):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DocumentTypeIn(BaseModel):
    name: str
    description: str = ""
    status: str = "draft"
    fields: list[DocumentTypeFieldIn] = []


class DocumentTypeOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    status: str
    sample_filename: str | None = None
    fields: list[DocumentTypeFieldOut]

    model_config = ConfigDict(from_attributes=True)


class MatchRuleIn(BaseModel):
    name: str
    comparison: str  # equals | numeric_tolerance | date_equals
    tolerance_percent: float | None = None
    field_map: dict[str, str]  # {document_type_id (str): field_key}


class MatchRuleOut(MatchRuleIn):
    id: int

    model_config = ConfigDict(from_attributes=True)


class MatchConfigIn(BaseModel):
    name: str
    match_type: str  # "2-way" | "3-way"
    is_active: bool = True
    document_type_ids: list[int]  # ordered
    rules: list[MatchRuleIn] = []


class MatchConfigDocumentTypeOut(BaseModel):
    document_type_id: int
    position: int

    model_config = ConfigDict(from_attributes=True)


class MatchConfigOut(BaseModel):
    id: int
    name: str
    match_type: str
    is_active: bool
    document_types: list[MatchConfigDocumentTypeOut]
    rules: list[MatchRuleOut]

    model_config = ConfigDict(from_attributes=True)
