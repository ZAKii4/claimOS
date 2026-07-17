"""
Regression tests for real native metadata extraction.

MetadataExtractionStep used to be a no-op stub that always set
extracted_native_metadata=True regardless of what (if anything) was in the
file — these tests exercise the real PyMuPDF/Pillow-backed implementation.
"""

import io

import fitz
import pytest
from PIL import Image

from app.pipeline.core import DocumentContext
from app.pipeline.steps.metadata import MetadataExtractionStep


def test_extracts_real_pdf_metadata():
    doc = fitz.open()
    doc.set_metadata({"author": "Jean Dupont", "title": "Constat Amiable"})
    doc.new_page()
    doc.new_page()
    payload = doc.tobytes()
    doc.close()

    step = MetadataExtractionStep()
    context = step.execute(
        DocumentContext(payload=payload, filename="constat.pdf", content_type="application/pdf")
    )

    assert context.errors == []
    meta = context.metadata["native_metadata"]
    assert meta["format"] == "pdf"
    assert meta["page_count"] == 2
    assert meta["author"] == "Jean Dupont"
    assert meta["title"] == "Constat Amiable"


def test_extracts_real_image_metadata():
    img = Image.new("RGB", (300, 150), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    payload = buf.getvalue()

    step = MetadataExtractionStep()
    context = step.execute(
        DocumentContext(payload=payload, filename="photo.jpg", content_type="image/jpeg")
    )

    assert context.errors == []
    meta = context.metadata["native_metadata"]
    assert meta["format"] == "jpeg"
    assert meta["width"] == 300
    assert meta["height"] == 150


def test_corrupt_pdf_degrades_instead_of_crashing():
    step = MetadataExtractionStep()
    context = step.execute(
        DocumentContext(payload=b"not a real pdf", filename="bad.pdf", content_type="application/pdf")
    )

    assert "native_metadata" not in context.metadata
    assert len(context.errors) == 1
    assert context.errors[0]["step"] == "metadata_extraction"
    assert context.errors[0]["severity"] == "DEGRADED"


def test_unsupported_content_type_is_skipped_without_error():
    step = MetadataExtractionStep()
    context = step.execute(
        DocumentContext(payload=b"binary blob", filename="f.bin", content_type="application/octet-stream")
    )

    assert context.errors == []
    assert "native_metadata" not in context.metadata


def test_no_payload_is_a_noop():
    step = MetadataExtractionStep()
    context = step.execute(DocumentContext(payload=None, filename="f.pdf", content_type="application/pdf"))

    assert context.errors == []
    assert "native_metadata" not in context.metadata
