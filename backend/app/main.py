"""FastAPI application entry point.

Run with: uvicorn app.main:app --reload   (from the backend/ directory)
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

# Comma-separated list of origins allowed to call this API, e.g.
# "https://ai-smart-document-processing.vercel.app,http://localhost:5173".
# Defaults to the Vite dev server so local frontend development works
# out of the box without any .env file.
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins.split(",") if origin.strip()]

app = FastAPI(
    title="AI Smart Document Processing API",
    description=(
        "OCR-based document intelligence: preprocessing, text extraction, "
        "field extraction, validation, and structured JSON export."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {
        "service": "AI Smart Document Processing API",
        "docs": "/docs",
        "health": "/api/health",
    }
