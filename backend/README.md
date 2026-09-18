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

FastAPI service: JWT auth + roles, configurable Document Types and Match
Configurations (SQLAlchemy/SQLite), a keyword-based document-classification
service, a 2-way/3-way matching engine, and the original OCR + field-
extraction pipeline (`src/`) that everything else is built on top of. The
frontend (`../frontend`) is a separate deployable that talks to this API
over HTTP — see the [root README](../README.md) for the full project
overview, architecture diagrams, and matching-engine explanation.

The YAML block above is Hugging Face Spaces' config format — it's what makes
this folder deployable as a Docker Space directly (see "Deploy to Hugging
Face Spaces" in the root README).

## Endpoints

See the [root README's API Endpoints section](../README.md#api-endpoints)
for the full table. Quick reference:

| Method | Path                  | Description                                    |
| ------ | ----------------------- | ----------------------------------------------- |
| GET    | `/api/health`          | Liveness + config check (no OCR model loaded)   |
| POST   | `/api/process`         | Standalone single-document OCR extraction        |
| POST   | `/api/auth/login`      | Get a JWT for one of the demo accounts           |
| \*     | `/api/document-types`, `/api/match-configs`, `/api/users` | Configuration CRUD (role-gated) |
| \*     | `/api/batches*`        | Upload → confirm type → run matching             |
| GET    | `/api/dashboard/summary` | Real KPI aggregates                            |
| GET    | `/docs`                | Interactive OpenAPI docs (Swagger UI)            |

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
pytest -m integration  # + real end-to-end OCR tests (single document + full batch match)
```
