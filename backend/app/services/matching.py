"""The 2-way/3-way document matching engine.

Given a batch's confirmed documents and the MatchConfig's rules, computes a
real pass/warning/fail per rule by comparing the actual extracted field
values named in each rule's field_map — nothing here is a hardcoded result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

import config

_AMOUNT_CLEAN_RE = re.compile(r"[^\d.\-]")


@dataclass
class RuleResult:
    rule_id: int | None
    rule_name: str
    status: str  # passed | failed | warning
    detail: dict = field(default_factory=dict)


def _parse_amount(value: str) -> float | None:
    cleaned = _AMOUNT_CLEAN_RE.sub("", value)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_date(value: str) -> datetime | None:
    for fmt in config.DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _collect_values(rule, documents_by_type: dict[int, object], doc_type_names: dict[int, str]):
    """Returns (values_by_type_name: dict[str,str|None], all_present: bool)."""
    values: dict[str, str | None] = {}
    for doc_type_id_str, field_key in rule.field_map.items():
        doc_type_id = int(doc_type_id_str)
        type_name = doc_type_names.get(doc_type_id, f"Type {doc_type_id}")
        doc = documents_by_type.get(doc_type_id)
        if doc is None:
            values[type_name] = None
            continue
        entry = (doc.extracted_fields or {}).get(field_key)
        values[type_name] = entry.get("value") if entry else None
    return values


def evaluate_rule(rule, documents_by_type: dict[int, object], doc_type_names: dict[int, str]) -> RuleResult:
    values = _collect_values(rule, documents_by_type, doc_type_names)

    missing = [name for name, val in values.items() if not val]
    if missing:
        return RuleResult(
            rule_id=rule.id, rule_name=rule.name, status="failed",
            detail={"values": values, "reason": f"Missing value for: {', '.join(missing)}"},
        )

    present_values = list(values.values())

    if rule.comparison == "equals":
        normalized = {_normalize_text(v) for v in present_values}
        status = "passed" if len(normalized) == 1 else "failed"
        return RuleResult(rule_id=rule.id, rule_name=rule.name, status=status, detail={"values": values})

    if rule.comparison == "numeric_tolerance":
        parsed = {name: _parse_amount(v) for name, v in values.items()}
        if any(v is None for v in parsed.values()):
            return RuleResult(
                rule_id=rule.id, rule_name=rule.name, status="failed",
                detail={"values": values, "reason": "Could not parse one or more values as a number"},
            )
        numbers = list(parsed.values())
        max_val = max(abs(n) for n in numbers) or 1e-9
        diff_percent = (max(numbers) - min(numbers)) / max_val * 100
        tolerance = rule.tolerance_percent if rule.tolerance_percent is not None else 0.0
        if diff_percent == 0:
            status = "passed"
        elif diff_percent <= tolerance:
            status = "warning"
        else:
            status = "failed"
        return RuleResult(
            rule_id=rule.id, rule_name=rule.name, status=status,
            detail={"values": values, "difference_percent": round(diff_percent, 2), "tolerance_percent": tolerance},
        )

    if rule.comparison == "date_equals":
        parsed_dates = {name: _parse_date(v) for name, v in values.items()}
        if any(d is None for d in parsed_dates.values()):
            return RuleResult(
                rule_id=rule.id, rule_name=rule.name, status="failed",
                detail={"values": values, "reason": "Could not parse one or more values as a date"},
            )
        status = "passed" if len(set(parsed_dates.values())) == 1 else "failed"
        return RuleResult(rule_id=rule.id, rule_name=rule.name, status=status, detail={"values": values})

    return RuleResult(
        rule_id=rule.id, rule_name=rule.name, status="failed",
        detail={"values": values, "reason": f"Unknown comparison type '{rule.comparison}'"},
    )


def run_matching(match_config, batch_documents, doc_type_names: dict[int, str]) -> tuple[list[RuleResult], bool]:
    """Evaluates every rule in match_config against the batch's confirmed documents.

    Returns (rule_results, overall_passed). A "warning" doesn't fail the
    batch (mirrors src/validator.py's existing "low confidence flags for
    review but doesn't invalidate the document" philosophy) — only a
    "failed" rule does.
    """
    documents_by_type = {doc.document_type_id: doc for doc in batch_documents if doc.document_type_id is not None}

    results = [evaluate_rule(rule, documents_by_type, doc_type_names) for rule in match_config.rules]
    overall_passed = all(r.status != "failed" for r in results)
    return results, overall_passed
