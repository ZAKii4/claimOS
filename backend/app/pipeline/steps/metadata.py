"""
Step 04: Metadata Extraction.

Extracts native document metadata: PDF info dict (author, producer,
creation date, page count) via PyMuPDF, or JPEG EXIF (camera make/model,
capture date, GPS) via Pillow. Runs before StorageStep, while
``context.payload`` is still in memory.
"""

import io

from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


def _extract_pdf_metadata(payload: bytes) -> dict:
    import fitz

    doc = fitz.open(stream=payload, filetype="pdf")
    try:
        info = doc.metadata or {}
        return {
            "format": "pdf",
            "page_count": doc.page_count,
            "author": info.get("author") or None,
            "producer": info.get("producer") or None,
            "creation_date": info.get("creationDate") or None,
            "modification_date": info.get("modDate") or None,
            "title": info.get("title") or None,
        }
    finally:
        doc.close()


def _extract_image_metadata(payload: bytes) -> dict:
    from PIL import ExifTags, Image

    with Image.open(io.BytesIO(payload)) as img:
        result = {
            "format": (img.format or "unknown").lower(),
            "width": img.width,
            "height": img.height,
        }
        exif = img.getexif()
        if not exif:
            return result

        tag_names = {v: k for k, v in ExifTags.TAGS.items()}
        for key in ("Make", "Model", "DateTimeOriginal", "DateTime", "Software"):
            tag_id = tag_names.get(key)
            if tag_id is not None and tag_id in exif:
                value = exif.get(tag_id)
                if isinstance(value, bytes):
                    value = value.decode(errors="replace")
                result[key.lower()] = value
        return result


class MetadataExtractionStep(PipelineStep):

    @property
    def name(self) -> str:
        return "metadata_extraction"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.payload:
            return context

        try:
            if context.content_type == "application/pdf" or context.filename.lower().endswith(".pdf"):
                native_metadata = _extract_pdf_metadata(context.payload)
            elif context.content_type and context.content_type.startswith("image/"):
                native_metadata = _extract_image_metadata(context.payload)
            else:
                return context
        except Exception as e:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": f"Native metadata extraction failed: {e}",
            })
            return context

        context.metadata["native_metadata"] = native_metadata
        return context
