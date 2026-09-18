"""API-level tests for the FastAPI endpoints.

Only test_process_valid_image below exercises the real OCR engine (slow,
downloads model weights on first run) — everything else validates the
request/response contract and error handling without needing OCR at all,
so the suite stays fast enough to run on every commit.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert ".pdf" in body["allowed_extensions"]


def test_process_rejects_unsupported_file_type():
    response = client.post(
        "/api/process", files={"file": ("notes.txt", b"hello world", "text/plain")}
    )

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_process_rejects_empty_file():
    response = client.post(
        "/api/process", files={"file": ("empty.png", b"", "image/png")}
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_process_rejects_corrupted_image():
    response = client.post(
        "/api/process", files={"file": ("fake.png", b"not a real png", "image/png")}
    )

    assert response.status_code == 400
    assert "could not read" in response.json()["detail"].lower()


def test_process_rejects_corrupted_pdf():
    response = client.post(
        "/api/process", files={"file": ("fake.pdf", b"not a real pdf", "application/pdf")}
    )

    assert response.status_code == 400
    assert "could not read" in response.json()["detail"].lower()


def test_process_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr("config.MAX_FILE_SIZE_MB", 0.0001)  # ~100 bytes

    response = client.post(
        "/api/process", files={"file": ("big.png", b"x" * 1000, "image/png")}
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]


@pytest.mark.integration
def test_process_valid_image_runs_real_ocr():
    """End-to-end: a real (synthetic) invoice image through the full OCR pipeline.

    Marked 'integration' since it downloads/loads the EasyOCR model on first
    run and takes noticeably longer than the rest of the suite. Run
    explicitly with: pytest -m integration
    """
    img = Image.new("RGB", (600, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "INVOICE", fill="black")
    draw.text((10, 50), "Invoice Number: INV-1001", fill="black")
    draw.text((10, 90), "Invoice Date: 01/01/2024", fill="black")
    draw.text((10, 130), "Total Amount: 100.00", fill="black")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    response = client.post(
        "/api/process", files={"file": ("invoice.png", buffer, "image/png")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file_type"] == "png"
    assert body["page_count"] == 1
    assert "fields" in body
