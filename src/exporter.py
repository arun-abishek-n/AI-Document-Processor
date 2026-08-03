"""
Export extracted + validated document data to JSON and CSV.

This is the final pipeline stage: it takes a ValidationSummary (the
combined output of extractor.py + validator.py) and turns it into the two
formats a user would actually want to download and use elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import config
from src.validator import ValidationSummary
from src.utils import get_logger

logger = get_logger(__name__)


def build_export_payload(
    source_filename: str, validation: ValidationSummary
) -> dict:
    """Assemble a JSON-serializable dict describing one processed document.

    This is the single source of truth for "what does an export contain" —
    both to_json and to_csv below build on top of this same structure, so
    the two export formats can never drift apart from each other.
    """
    return {
        "source_file": source_filename,
        "is_valid_document": validation.is_valid_document,
        # round()'d to keep the exported JSON/CSV readable — OCR confidence
        # precision beyond 4 decimal places carries no real meaning.
        "overall_confidence": round(validation.overall_confidence, 4),
        "missing_required_fields": validation.missing_required,
        "invalid_fields": validation.invalid_fields,
        "low_confidence_fields": validation.low_confidence_fields,
        "fields": {
            name: {
                "value": result.value,
                "confidence": round(result.confidence, 4),
                "is_present": result.is_present,
                "is_valid": result.is_valid,
                "issue": result.issue,
            }
            for name, result in validation.fields.items()
        },
    }


def to_json(payload: dict) -> str:
    """Serialize the export payload to a pretty-printed JSON string.

    indent=2 trades a slightly larger file for output a human can actually
    read when opened directly (this is a portfolio/demo tool, not a
    high-volume API, so readability wins over minimal byte size).
    ensure_ascii=False preserves non-ASCII characters (accented vendor
    names, currency symbols) instead of escaping them to \\uXXXX sequences.
    """
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_csv(payload: dict) -> str:
    """Flatten the export payload's fields into a CSV string (one row per field).

    JSON's nested "fields" dict has no direct CSV equivalent, so this
    reshapes it into a flat table — one row per extracted field — which is
    the natural way to open it in Excel/Sheets.
    """
    rows = [
        {
            "field": name,
            "value": data["value"],
            "confidence": data["confidence"],
            "is_present": data["is_present"],
            "is_valid": data["is_valid"],
            "issue": data["issue"],
        }
        for name, data in payload["fields"].items()
    ]
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def save_outputs(payload: dict, base_name: str) -> tuple[Path, Path]:
    """Write JSON and CSV exports to config.OUTPUT_DIR.

    Args:
        payload: dict produced by build_export_payload.
        base_name: filename stem (without extension) to use for both outputs.
            app.py passes a timestamped name so results from repeated
            uploads of the same file don't silently overwrite each other.

    Returns:
        (json_path, csv_path) of the written files.
    """
    json_path = config.OUTPUT_DIR / f"{base_name}.json"
    csv_path = config.OUTPUT_DIR / f"{base_name}.csv"

    json_path.write_text(to_json(payload), encoding="utf-8")
    csv_path.write_text(to_csv(payload), encoding="utf-8")

    logger.info("Saved exports: %s, %s", json_path.name, csv_path.name)
    return json_path, csv_path
