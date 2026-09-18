"""Pure unit tests for the matching engine (app/services/matching.py).

Uses plain SimpleNamespace stand-ins for MatchRule/BatchDocument — the
engine only reads a handful of attributes off each, so no DB or HTTP layer
is needed to exercise its actual comparison logic.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.services.matching import evaluate_rule, run_matching

PO_ID, INVOICE_ID = 1, 2
DOC_TYPE_NAMES = {PO_ID: "Purchase Order", INVOICE_ID: "Invoice"}


def _doc(document_type_id: int, fields: dict) -> SimpleNamespace:
    return SimpleNamespace(
        document_type_id=document_type_id,
        extracted_fields={k: {"value": v} for k, v in fields.items()},
    )


def _rule(name: str, comparison: str, field_map: dict, tolerance_percent: float | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=1, name=name, comparison=comparison, field_map=field_map, tolerance_percent=tolerance_percent)


def test_equals_passes_on_identical_values():
    rule = _rule("PO Number", "equals", {str(PO_ID): "po_number", str(INVOICE_ID): "po_number"})
    docs = {PO_ID: _doc(PO_ID, {"po_number": "PO-1"}), INVOICE_ID: _doc(INVOICE_ID, {"po_number": "PO-1"})}

    result = evaluate_rule(rule, docs, DOC_TYPE_NAMES)

    assert result.status == "passed"


def test_equals_is_case_and_whitespace_insensitive():
    rule = _rule("Vendor", "equals", {str(PO_ID): "vendor", str(INVOICE_ID): "vendor"})
    docs = {PO_ID: _doc(PO_ID, {"vendor": "Acme Co"}), INVOICE_ID: _doc(INVOICE_ID, {"vendor": "  acme   co  "})}

    result = evaluate_rule(rule, docs, DOC_TYPE_NAMES)

    assert result.status == "passed"


def test_equals_fails_on_different_values():
    rule = _rule("PO Number", "equals", {str(PO_ID): "po_number", str(INVOICE_ID): "po_number"})
    docs = {PO_ID: _doc(PO_ID, {"po_number": "PO-1"}), INVOICE_ID: _doc(INVOICE_ID, {"po_number": "PO-2"})}

    result = evaluate_rule(rule, docs, DOC_TYPE_NAMES)

    assert result.status == "failed"


def test_numeric_tolerance_passes_on_exact_match():
    rule = _rule("Total", "numeric_tolerance", {str(PO_ID): "total", str(INVOICE_ID): "total"}, tolerance_percent=2.0)
    docs = {PO_ID: _doc(PO_ID, {"total": "5000.00"}), INVOICE_ID: _doc(INVOICE_ID, {"total": "5000.00"})}

    assert evaluate_rule(rule, docs, DOC_TYPE_NAMES).status == "passed"


def test_numeric_tolerance_warns_within_tolerance():
    rule = _rule("Total", "numeric_tolerance", {str(PO_ID): "total", str(INVOICE_ID): "total"}, tolerance_percent=2.0)
    docs = {PO_ID: _doc(PO_ID, {"total": "5000.00"}), INVOICE_ID: _doc(INVOICE_ID, {"total": "5050.00"})}  # 1% diff

    assert evaluate_rule(rule, docs, DOC_TYPE_NAMES).status == "warning"


def test_numeric_tolerance_fails_beyond_tolerance():
    rule = _rule("Total", "numeric_tolerance", {str(PO_ID): "total", str(INVOICE_ID): "total"}, tolerance_percent=2.0)
    docs = {PO_ID: _doc(PO_ID, {"total": "5000.00"}), INVOICE_ID: _doc(INVOICE_ID, {"total": "6200.00"})}  # 19% diff

    result = evaluate_rule(rule, docs, DOC_TYPE_NAMES)
    assert result.status == "failed"
    assert result.detail["difference_percent"] > 2.0


def test_date_equals_passes_on_same_date_different_format():
    rule = _rule("Date", "date_equals", {str(PO_ID): "date", str(INVOICE_ID): "date"})
    docs = {PO_ID: _doc(PO_ID, {"date": "15/03/2024"}), INVOICE_ID: _doc(INVOICE_ID, {"date": "2024-03-15"})}

    assert evaluate_rule(rule, docs, DOC_TYPE_NAMES).status == "passed"


def test_missing_document_for_required_type_fails():
    rule = _rule("PO Number", "equals", {str(PO_ID): "po_number", str(INVOICE_ID): "po_number"})
    docs = {PO_ID: _doc(PO_ID, {"po_number": "PO-1"})}  # invoice document missing entirely

    result = evaluate_rule(rule, docs, DOC_TYPE_NAMES)
    assert result.status == "failed"


def test_run_matching_overall_passed_requires_every_rule_to_pass():
    match_config = SimpleNamespace(
        rules=[
            _rule("PO Number", "equals", {str(PO_ID): "po_number", str(INVOICE_ID): "po_number"}),
            _rule("Total", "numeric_tolerance", {str(PO_ID): "total", str(INVOICE_ID): "total"}, tolerance_percent=2.0),
        ]
    )
    documents = [
        _doc(PO_ID, {"po_number": "PO-1", "total": "100.00"}),
        _doc(INVOICE_ID, {"po_number": "PO-1", "total": "500.00"}),
    ]

    results, overall_passed = run_matching(match_config, documents, DOC_TYPE_NAMES)

    assert overall_passed is False
    assert any(r.status == "failed" for r in results)


def test_run_matching_warning_alone_does_not_fail_the_batch():
    match_config = SimpleNamespace(
        rules=[_rule("Total", "numeric_tolerance", {str(PO_ID): "total", str(INVOICE_ID): "total"}, tolerance_percent=2.0)]
    )
    documents = [_doc(PO_ID, {"total": "5000.00"}), _doc(INVOICE_ID, {"total": "5050.00"})]

    _results, overall_passed = run_matching(match_config, documents, DOC_TYPE_NAMES)

    assert overall_passed is True
