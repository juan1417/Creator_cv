"""Tests for ``creator_cv.cv_importer`` (file validation + PDF/DOCX extraction).

The Gemini parsing part is not unit-tested here — it requires a live
``GEMINI_API_KEY`` and is exercised manually / via the route.
"""

from __future__ import annotations

import io

import pytest
from docx import Document
from fpdf import FPDF
from werkzeug.datastructures import FileStorage

from creator_cv.cv_importer import (
    ALLOWED_EXTENSIONS,
    allowed_file,
    extract_text,
)


def _fs(name: str, data: bytes, content_type: str = "") -> FileStorage:
    return FileStorage(stream=io.BytesIO(data), filename=name, content_type=content_type)


def test_allowed_file_accepts_pdf_and_docx():
    assert allowed_file("cv.pdf")
    assert allowed_file("CV.PDF")
    assert allowed_file("cv.docx")
    assert allowed_file("path/with spaces/file.docx")


def test_allowed_file_rejects_other_types():
    assert not allowed_file("cv.txt")
    assert not allowed_file("cv.exe")
    assert not allowed_file("cv")
    assert not allowed_file("")


def test_allowed_extensions_set():
    assert ALLOWED_EXTENSIONS == {".pdf", ".docx"}


def test_extract_rejects_unsupported_extension():
    fs = _fs("malware.exe", b"abc")
    with pytest.raises(ValueError, match="no soportado"):
        extract_text(fs)


def test_extract_rejects_empty_file():
    fs = _fs("empty.pdf", b"")
    with pytest.raises(ValueError, match="vacío"):
        extract_text(fs)


def test_extract_rejects_oversize():
    big = b"x" * (11 * 1024 * 1024)
    fs = _fs("big.pdf", big)
    with pytest.raises(ValueError, match="demasiado grande"):
        extract_text(fs)


def _make_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, text)
    return bytes(pdf.output())


def _make_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_pdf_returns_text():
    pdf = _make_pdf("Hola mundo\nEsto es un CV")
    fs = _fs("cv.pdf", pdf, "application/pdf")
    out = extract_text(fs)
    assert "Hola" in out
    assert "CV" in out


def test_extract_docx_returns_text():
    docx = _make_docx("Línea 1\nLínea 2\nLínea 3")
    fs = _fs("cv.docx", docx)
    out = extract_text(fs)
    assert "Línea 1" in out
    assert "Línea 2" in out


def test_extract_pdf_with_no_text_raises():
    # FPDF produces a real PDF, but we can use a minimal valid PDF with no text
    # by passing empty content.
    pdf = _make_pdf("")
    fs = _fs("empty_real.pdf", pdf, "application/pdf")
    with pytest.raises(ValueError, match="No se pudo extraer"):
        extract_text(fs)
