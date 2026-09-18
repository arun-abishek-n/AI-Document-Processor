"""Heuristic document-type suggestion.

Deliberately not a trained classifier: scores each configured DocumentType
against a document's OCR text + filename by counting keyword overlap (the
type's name, description words, and its field labels). The result is a
*suggestion* the user confirms or overrides in the UI — never applied
silently — so an honest heuristic is appropriate here.
"""

from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", text.lower())}


def suggest_document_type(raw_text: str, filename: str, document_types: list) -> tuple[int | None, float]:
    """Returns (best_document_type_id, score 0.0-1.0), or (None, 0.0) if there are no types to choose from."""
    if not document_types:
        return None, 0.0

    haystack = _tokenize(f"{raw_text}\n{filename}")
    best_id: int | None = None
    best_score = -1.0

    for doc_type in document_types:
        keywords = _tokenize(doc_type.name) | _tokenize(doc_type.description)
        keywords |= {w for field in doc_type.fields for w in _tokenize(field.label)}
        keywords.discard("name")  # too generic ("Vendor Name", "Supplier Name", ...) to be a useful signal

        if not keywords:
            continue

        overlap = len(haystack & keywords)
        score = overlap / len(keywords)
        if score > best_score:
            best_score = score
            best_id = doc_type.id

    return best_id, max(best_score, 0.0)
