"""FastAPI application entry point.

Run with: uvicorn app.main:app --reload   (from the backend/ directory)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, init_db
from app.routers import auth, batches, dashboard, document_types, documents, match_configs, users
from app.seed import seed_if_empty

# Comma-separated list of origins allowed to call this API, e.g.
# "https://ai-smart-document-processing.vercel.app,http://localhost:5173".
# Defaults to the Vite dev server so local frontend development works
# out of the box without any .env file.
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AI Smart Document Processing API",
    description=(
        "OCR-based document intelligence: preprocessing, text extraction, "
        "configurable field extraction, 2-way/3-way document matching, "
        "and structured JSON export."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(document_types.router)
app.include_router(match_configs.router)
app.include_router(batches.router)
app.include_router(dashboard.router)


@app.get("/")
def root() -> dict:
    return {
        "service": "AI Smart Document Processing API",
        "docs": "/docs",
        "health": "/api/health",
    }
