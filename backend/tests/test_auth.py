from __future__ import annotations


def test_login_success(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "admin"
    assert body["access_token"]


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})

    assert response.status_code == 401


def test_me_without_token_is_rejected(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_token_returns_current_user(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_manager_cannot_list_users(client, manager_headers):
    response = client.get("/api/users", headers=manager_headers)

    assert response.status_code == 403


def test_executive_cannot_create_document_type(client, executive_headers):
    response = client.post(
        "/api/document-types", headers=executive_headers,
        json={"name": "Should Fail", "description": "", "status": "draft", "fields": []},
    )

    assert response.status_code == 403


def test_executive_can_still_read_document_types(client, executive_headers):
    response = client.get("/api/document-types", headers=executive_headers)

    assert response.status_code == 200
    assert len(response.json()) > 0
