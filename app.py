"""
AI Document Processor — Streamlit entry point.

Ties together preprocessing, OCR, field extraction, validation, and export
behind a single-page UI: upload -> preview -> extract -> review -> download.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image

import config
from src.exporter import build_export_payload, save_outputs, to_csv, to_json
from src.extractor import extract_fields
from src.ocr import pdf_to_images, run_ocr
from src.preprocess import preprocess_image
from src.utils import (
    FileTooLargeError,
    UnsupportedFileError,
    get_logger,
    is_pdf,
    pil_to_ndarray,
    validate_upload,
)
from src.validator import validate_fields

logger = get_logger(__name__)

st.set_page_config(
    page_title="AI Document Processor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar() -> None:
    with st.sidebar:
        st.title("📄 AI Document Processor")
        st.caption("Intelligent Document Processing demo — OCR, extraction & validation")

        st.subheader("Settings")
        st.selectbox(
            "OCR Engine",
            options=["easyocr", "tesseract"],
            index=["easyocr", "tesseract"].index(config.OCR_ENGINE),
            key="ocr_engine",
            help="EasyOCR requires no external binary. Tesseract requires the "
                 "Tesseract binary to be installed and on PATH.",
        )
        st.slider(
            "Low-confidence threshold",
            min_value=0.0, max_value=1.0,
            value=config.MIN_CONFIDENCE_THRESHOLD, step=0.05,
            key="confidence_threshold",
            help="Fields with OCR confidence below this value are flagged.",
        )

        st.divider()
        st.markdown(
            "**How it works**\n"
            "1. Upload a PDF, JPG, or PNG\n"
            "2. Image is preprocessed (denoise, deskew, threshold)\n"
            "3. OCR extracts raw text\n"
            "4. Regex-based extractor pulls key-value fields\n"
            "5. Validator checks formats & required fields\n"
            "6. Export as JSON or CSV"
        )
        st.divider()
        st.caption("Built by Arun Abishek — portfolio project, no proprietary data or code.")


def render_upload_section() -> "st.runtime.uploaded_file_manager.UploadedFile | None":
    st.header("1. Upload a document")
    uploaded_file = st.file_uploader(
        "Upload a PDF, JPG, or PNG invoice/document",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=False,
    )
    return uploaded_file


def load_pages(uploaded_file) -> list:
    """Return a list of RGB NumPy arrays, one per page/image."""
    file_bytes = uploaded_file.getvalue()
    validate_upload(uploaded_file.name, len(file_bytes))

    if is_pdf(uploaded_file.name):
        return pdf_to_images(file_bytes)

    image = Image.open(uploaded_file)
    return [pil_to_ndarray(image)]


def render_preview(pages: list) -> None:
    st.header("2. Document preview")
    cols = st.columns(min(len(pages), 3) or 1)
    for i, page in enumerate(pages):
        with cols[i % len(cols)]:
            st.image(page, caption=f"Page {i + 1}", use_container_width=True)


def process_pages(pages: list, engine: str) -> tuple[str, float, dict, object]:
    """Run preprocessing + OCR across all pages, merge text, then extract & validate."""
    progress = st.progress(0.0, text="Starting OCR...")
    combined_text_parts = []
    confidences = []

    for i, page in enumerate(pages):
        progress.progress((i) / len(pages), text=f"Preprocessing page {i + 1}/{len(pages)}...")
        processed = preprocess_image(page)

        progress.progress((i + 0.5) / len(pages), text=f"Running OCR on page {i + 1}/{len(pages)}...")
        ocr_result = run_ocr(processed, engine=engine)

        combined_text_parts.append(ocr_result.full_text)
        confidences.append(ocr_result.average_confidence)

    progress.progress(1.0, text="OCR complete.")

    from src.ocr import OCRResult  # local import to avoid polluting module namespace

    merged_result = OCRResult(
        full_text="\n".join(combined_text_parts),
        words=[],
        average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
    )

    fields = extract_fields(merged_result, config.FIELD_PATTERNS)
    validation = validate_fields(fields)

    return merged_result.full_text, merged_result.average_confidence, fields, validation


def render_text_panel(full_text: str, avg_confidence: float) -> None:
    st.header("3. Extracted text")
    st.metric("Average OCR confidence", f"{avg_confidence:.0%}")
    st.text_area("Raw OCR output", value=full_text, height=250)


def render_fields_panel(validation) -> pd.DataFrame:
    st.header("4. Extracted & validated fields")

    if validation.missing_required:
        st.warning(f"Missing required field(s): {', '.join(validation.missing_required)}")
    if validation.invalid_fields:
        st.error(f"Invalid field(s): {', '.join(validation.invalid_fields)}")
    if validation.is_valid_document:
        st.success("All required fields are present and valid.")

    rows = []
    for name, result in validation.fields.items():
        rows.append({
            "Field": name,
            "Value": result.value or "—",
            "Confidence": f"{result.confidence:.0%}" if result.is_present else "—",
            "Valid": "✅" if result.is_valid else "❌",
            "Issue": result.issue or "",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    return df


def render_download_section(payload: dict, base_name: str) -> None:
    st.header("5. Export results")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇ Download JSON",
            data=to_json(payload),
            file_name=f"{base_name}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇ Download CSV",
            data=to_csv(payload),
            file_name=f"{base_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    render_sidebar()
    uploaded_file = render_upload_section()

    if uploaded_file is None:
        st.info("Upload a document above to get started.")
        return

    try:
        pages = load_pages(uploaded_file)
    except (UnsupportedFileError, FileTooLargeError) as exc:
        st.error(str(exc))
        logger.warning("Upload rejected: %s", exc)
        return
    except Exception:
        st.error("Could not read the uploaded file. Please try a different document.")
        logger.exception("Unexpected error while loading uploaded file")
        return

    render_preview(pages)

    try:
        full_text, avg_confidence, fields, validation = process_pages(
            pages, engine=st.session_state.get("ocr_engine", config.OCR_ENGINE)
        )
    except Exception:
        st.error(
            "OCR processing failed. If you selected Tesseract, verify the Tesseract "
            "binary is installed and on your PATH, or switch to EasyOCR in the sidebar."
        )
        logger.exception("Unexpected error during OCR/extraction pipeline")
        return

    render_text_panel(full_text, avg_confidence)
    render_fields_panel(validation)

    base_name = f"{uploaded_file.name.rsplit('.', 1)[0]}_{datetime.now():%Y%m%d_%H%M%S}"
    payload = build_export_payload(uploaded_file.name, validation)
    save_outputs(payload, base_name)
    render_download_section(payload, base_name)


if __name__ == "__main__":
    main()
