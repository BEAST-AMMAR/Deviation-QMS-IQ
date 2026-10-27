"""
DeviationIQ — Document Parser Service

Extracts text from uploaded PDF, DOCX, and TXT files.
Uses pdfplumber for PDFs (not OCR — see SAD §4 decision).
Single code path: all formats → plain text → same extractor prompt.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber."""
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from a plain text file."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


# Mapping of content types and extensions to extractors
_EXTRACTORS = {
    "application/pdf": extract_text_from_pdf,
    "pdf": extract_text_from_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_text_from_docx,
    "docx": extract_text_from_docx,
    "text/plain": extract_text_from_txt,
    "txt": extract_text_from_txt,
}

# Maximum upload file size: 10 MB (SC-04)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_document(file_bytes: bytes, filename: str, content_type: str | None = None) -> str:
    """
    Parse an uploaded document into plain text.

    Tries content_type first, then falls back to file extension.
    Raises ValueError on unsupported formats or oversized files (SC-04).
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File too large ({len(file_bytes) / (1024*1024):.1f} MB). "
            f"Maximum allowed: {MAX_FILE_SIZE_BYTES / (1024*1024):.0f} MB."
        )

    # Try content type
    if content_type and content_type in _EXTRACTORS:
        extractor = _EXTRACTORS[content_type]
        logger.info("Parsing %s via content-type %s", filename, content_type)
        return extractor(file_bytes)

    # Fall back to extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported formats: PDF, DOCX, TXT."
        )

    ext_key = ext.lstrip(".")
    extractor = _EXTRACTORS.get(ext_key)
    if not extractor:
        raise ValueError(f"No parser available for extension '{ext}'.")

    logger.info("Parsing %s via extension %s", filename, ext)
    return extractor(file_bytes)
