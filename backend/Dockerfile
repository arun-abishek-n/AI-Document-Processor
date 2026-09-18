# Runs the FastAPI backend (OCR + extraction + validation pipeline) as a
# Docker image, intended for Hugging Face Spaces (Docker SDK) — see README.md
# in this folder for the exact deploy steps.

FROM python:3.11-slim

WORKDIR /app

# libglib/libgl are common transitive runtime needs for OpenCV + EasyOCR's
# image-processing stack even though opencv-python-headless has no GUI deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download EasyOCR's model weights at build time (not first request) so a
# cold container doesn't hang or time out on its first real upload — this
# matches config.MODELS_DIR (backend/models), which is also gitignored.
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False, model_storage_directory='models')"

ENV PYTHONUNBUFFERED=1

# Hugging Face Spaces (Docker SDK) routes traffic to port 7860 by default —
# see the `app_port` field in this folder's README.md frontmatter.
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
