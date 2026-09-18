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
