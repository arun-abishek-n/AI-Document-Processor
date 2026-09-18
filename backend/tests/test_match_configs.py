from __future__ import annotations

from app.models import Batch


def _get_document_type_id(client, headers, name: str) -> int:
    response = client.get("/api/document-types", headers=headers)
    return next(dt["id"] for dt in response.json() if dt["name"] == name)


def test_list_match_configs_includes_seed_data(client, admin_headers):
    response = client.get("/api/match-configs", headers=admin_headers)

    assert response.status_code == 200
    match_types = {c["match_type"] for c in response.json()}
    assert {"2-way", "3-way"}.issubset(match_types)


def test_create_2_way_config_requires_exactly_two_types(client, admin_headers):
    po_id = _get_document_type_id(client, admin_headers, "Purchase Order")

    response = client.post(
        "/api/match-configs", headers=admin_headers,
        json={"name": "Bad Config", "match_type": "2-way", "document_type_ids": [po_id], "rules": []},
    )

    assert response.status_code == 400


def test_duplicate_document_type_in_config_is_rejected(client, admin_headers):
    """Regression: [po_id, po_id] used to pass validation (the existence
    check dedups via .in_()), silently producing a rule that compares a
    document's value to itself instead of cross-checking a second document."""
    po_id = _get_document_type_id(client, admin_headers, "Purchase Order")

    response = client.post(
        "/api/match-configs", headers=admin_headers,
        json={"name": "Duplicate Types", "match_type": "2-way", "document_type_ids": [po_id, po_id], "rules": []},
    )

    assert response.status_code == 400
    assert "distinct" in response.json()["detail"].lower()


def test_create_update_delete_match_config(client, admin_headers):
    po_id = _get_document_type_id(client, admin_headers, "Purchase Order")
    invoice_id = _get_document_type_id(client, admin_headers, "Invoice")

    create = client.post(
        "/api/match-configs", headers=admin_headers,
        json={
            "name": "Test 2-way",
            "match_type": "2-way",
            "document_type_ids": [po_id, invoice_id],
            "rules": [
                {
                    "name": "PO Number",
                    "comparison": "equals",
                    "field_map": {str(po_id): "po_number", str(invoice_id): "po_number"},
                }
            ],
        },
    )
    assert create.status_code == 201
    config = create.json()
    assert len(config["rules"]) == 1

    update = client.put(
        f"/api/match-configs/{config['id']}", headers=admin_headers,
        json={
            "name": "Test 2-way renamed",
            "match_type": "2-way",
            "is_active": False,
            "document_type_ids": [po_id, invoice_id],
            "rules": [],
        },
    )
    assert update.status_code == 200
    assert update.json()["is_active"] is False
    assert update.json()["rules"] == []

    delete = client.delete(f"/api/match-configs/{config['id']}", headers=admin_headers)
    assert delete.status_code == 204


def test_cannot_delete_match_config_referenced_by_a_batch(client, admin_headers, db_session):
    po_id = _get_document_type_id(client, admin_headers, "Purchase Order")
    invoice_id = _get_document_type_id(client, admin_headers, "Invoice")

    create = client.post(
        "/api/match-configs", headers=admin_headers,
        json={"name": "In-use config", "match_type": "2-way", "document_type_ids": [po_id, invoice_id], "rules": []},
    )
    config_id = create.json()["id"]

    db_session.add(Batch(name="Batch of 2", match_config_id=config_id, status="pending_confirmation"))
    db_session.commit()

    response = client.delete(f"/api/match-configs/{config_id}", headers=admin_headers)

    assert response.status_code == 400
    assert "batch" in response.json()["detail"].lower()
