from __future__ import annotations


def test_list_document_types_includes_seed_data(client, admin_headers):
    response = client.get("/api/document-types", headers=admin_headers)

    assert response.status_code == 200
    names = {dt["name"] for dt in response.json()}
    assert {"Invoice", "Purchase Order", "Goods Receipt"}.issubset(names)


def test_create_update_delete_document_type(client, admin_headers):
    create = client.post(
        "/api/document-types", headers=admin_headers,
        json={
            "name": "Test Delivery Challan",
            "description": "A test-only document type.",
            "status": "draft",
            "fields": [{"key": "challan_number", "label": "Challan Number", "is_required": True}],
        },
    )
    assert create.status_code == 201
    doc_type = create.json()
    assert doc_type["slug"] == "test-delivery-challan"
    assert doc_type["fields"][0]["key"] == "challan_number"

    update = client.put(
        f"/api/document-types/{doc_type['id']}", headers=admin_headers,
        json={
            "name": "Test Delivery Challan",
            "description": "Updated.",
            "status": "configured",
            "fields": [{"key": "challan_number", "label": "Challan Number", "is_required": True}],
        },
    )
    assert update.status_code == 200
    assert update.json()["status"] == "configured"

    delete = client.delete(f"/api/document-types/{doc_type['id']}", headers=admin_headers)
    assert delete.status_code == 204

    listing = client.get("/api/document-types", headers=admin_headers)
    assert doc_type["id"] not in {dt["id"] for dt in listing.json()}


def test_duplicate_name_rejected(client, admin_headers):
    payload = {"name": "Duplicate Type", "description": "", "status": "draft", "fields": []}
    first = client.post("/api/document-types", headers=admin_headers, json=payload)
    assert first.status_code == 201

    second = client.post("/api/document-types", headers=admin_headers, json=payload)
    assert second.status_code == 400

    client.delete(f"/api/document-types/{first.json()['id']}", headers=admin_headers)


def test_cannot_delete_document_type_used_by_a_match_config(client, admin_headers):
    """Regression: deleting a type still referenced by a match config used to
    leave that config's MatchConfigDocumentType row pointing at a dead id,
    silently breaking its display and matching behavior."""
    types = {dt["name"]: dt["id"] for dt in client.get("/api/document-types", headers=admin_headers).json()}
    po_id, invoice_id = types["Purchase Order"], types["Invoice"]

    create = client.post(
        "/api/match-configs", headers=admin_headers,
        json={"name": "Blocks deletion", "match_type": "2-way", "document_type_ids": [po_id, invoice_id], "rules": []},
    )
    config_id = create.json()["id"]

    response = client.delete(f"/api/document-types/{po_id}", headers=admin_headers)
    assert response.status_code == 400
    assert "match configuration" in response.json()["detail"].lower()

    client.delete(f"/api/match-configs/{config_id}", headers=admin_headers)
