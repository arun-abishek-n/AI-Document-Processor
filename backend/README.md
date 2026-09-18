---
title: AI Smart Document Processing API
emoji: 📄
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AI Smart Document Processing — Backend

FastAPI service wrapping the OCR + field-extraction + validation pipeline
(`src/`). The frontend (`../frontend`) is a separate deployable that talks to
this API over HTTP — see the [root README](../README.md) for the full
project overview and architecture.

The YAML block above is Hugging Face Spaces' config format — it's what makes
this folder deployable as a Docker Space directly (see "Deploy to Hugging
Face Spaces" in the root README).

## Endpoints

| Method | Path           | Description                                    |
| ------ | -------------- | ----------------------------------------------- |
| GET    | `/api/health`  | Liveness + config check (no OCR model loaded)   |
| POST   | `/api/process` | Upload a PDF/JPG/PNG, get back structured JSON  |
| GET    | `/docs`        | Interactive OpenAPI docs (Swagger UI)           |

## Local development

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # macOS / Linux

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is then at `http://localhost:8000` (docs at `/docs`).

## Environment variables

See [.env.example](.env.example). All are optional — sensible defaults are
baked into `config.py`.

## Testing

```bash
pip install -r requirements-dev.txt
pytest                 # fast unit + API tests (no OCR model download)
pytest -m integration  # + one real end-to-end OCR test
```
