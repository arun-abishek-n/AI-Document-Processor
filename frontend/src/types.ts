/** Mirrors backend/app/schemas.py — kept in sync by hand since this is a
 * small, single-team project (no shared OpenAPI codegen step). */

export interface FieldResult {
  value: string | null;
  confidence: number;
  is_present: boolean;
  is_valid: boolean;
  issue: string | null;
}

export interface ProcessResponse {
  source_file: string;
  file_type: string;
  page_count: number;
  processing_time_seconds: number;
  ocr_engine: string;
  is_valid_document: boolean;
  overall_confidence: number;
  missing_required_fields: string[];
  invalid_fields: string[];
  low_confidence_fields: string[];
  fields: Record<string, FieldResult>;
  raw_text: string;
}

export interface HealthResponse {
  status: string;
  ocr_engine: string;
  allowed_extensions: string[];
  max_file_size_mb: number;
}

export type ProcessingStage = "idle" | "uploading" | "processing" | "success" | "error";

// --- Auth ---------------------------------------------------------------

export type Role = "admin" | "manager" | "executive";

export interface User {
  id: number;
  username: string;
  name: string;
  role: Role;
  is_active: boolean;
  last_active_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// --- Document types & fields ---------------------------------------------

export interface DocumentTypeField {
  id?: number;
  key: string;
  label: string;
  pattern: string | null;
  is_required: boolean;
}

export interface DocumentType {
  id: number;
  name: string;
  slug: string;
  description: string;
  status: "draft" | "configured";
  sample_filename: string | null;
  fields: DocumentTypeField[];
}

// --- Match configurations -------------------------------------------------

export type Comparison = "equals" | "numeric_tolerance" | "date_equals";

export interface MatchRule {
  id?: number;
  name: string;
  comparison: Comparison;
  tolerance_percent: number | null;
  field_map: Record<string, string>; // { document_type_id (as string): field_key }
}

export interface MatchConfigDocumentTypeRef {
  document_type_id: number;
  position: number;
}

export interface MatchConfig {
  id: number;
  name: string;
  match_type: "2-way" | "3-way";
  is_active: boolean;
  document_types: MatchConfigDocumentTypeRef[];
  rules: MatchRule[];
}

// --- Batches / matching results -------------------------------------------

export type BatchStatus = "pending_confirmation" | "matching" | "matched" | "exception" | "failed";
export type RuleStatus = "passed" | "failed" | "warning";

export interface BatchDocument {
  id: number;
  original_filename: string;
  file_type: string;
  page_count: number;
  overall_confidence: number;
  extracted_fields: Record<string, FieldResult>;
  suggested_document_type_id: number | null;
  suggested_document_type_name: string | null;
  document_type_id: number | null;
  document_type_name: string | null;
  status: string;
  raw_text: string;
}

export interface MatchRuleResult {
  id: number;
  rule_name: string;
  status: RuleStatus;
  detail: {
    values?: Record<string, string | null>;
    reason?: string;
    difference_percent?: number;
    tolerance_percent?: number;
  };
}

export interface Batch {
  id: number;
  name: string;
  match_config_id: number | null;
  match_config_name: string | null;
  status: BatchStatus;
  overall_confidence: number;
  match_passed: boolean | null;
  document_count: number;
  created_at: string;
  processing_time_seconds: number;
}

export interface BatchDetail extends Batch {
  documents: BatchDocument[];
  rule_results: MatchRuleResult[];
}

export interface DashboardSummary {
  processed_count: number;
  match_rate: number;
  open_exceptions: number;
  avg_confidence: number;
  in_flight: number;
  pipeline_status_counts: Record<string, number>;
  doc_type_distribution: Record<string, number>;
  confidence_buckets: { low: number; medium: number; high: number };
}
