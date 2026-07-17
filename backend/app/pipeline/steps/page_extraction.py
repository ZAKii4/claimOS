"""
Step 07: Page Extraction.

Rasterizes the stored document into per-page images:
- PDFs are rendered page-by-page via PyMuPDF at a fixed DPI.
- Single-page image uploads (JPEG/PNG) are used as their own page image.

Populates context.pages with PageContext objects pointing at real,
existing image files on disk.
"""

import os

import fitz  # PyMuPDF

from app.pipeline.core import (
    DocumentContext,
    ErrorSeverity,
    PageContext,
    PipelineError,
    PipelineStep,
)

RENDER_DPI = 300


class PageExtractionStep(PipelineStep):

    @property
    def name(self) -> str:
        return "page_extraction"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.storage_uri:
            raise PipelineError("Storage URI missing", self.name, ErrorSeverity.FATAL)

        file_path = context.storage_uri.replace("local://", "")
        if not os.path.exists(file_path):
            raise PipelineError(
                f"Stored file not found: {file_path}", self.name, ErrorSeverity.FATAL
            )

        if context.content_type == "application/pdf":
            context.pages = self._render_pdf_pages(file_path)
        elif context.content_type in ("image/jpeg", "image/png"):
            context.pages = [
                PageContext(
                    page_number=1,
                    original_page_number=1,
                    image_uri=f"local://{file_path}",
                    resolution_dpi=RENDER_DPI,
                )
            ]
        else:
            raise PipelineError(
                f"Unsupported content type for page extraction: {context.content_type}",
                self.name,
                ErrorSeverity.FATAL,
            )

        if not context.pages:
            raise PipelineError("Document produced zero pages", self.name, ErrorSeverity.FATAL)

        return context

    def _render_pdf_pages(self, pdf_path: str) -> list[PageContext]:
        pages: list[PageContext] = []
        zoom = RENDER_DPI / 72.0  # PDF points are natively 72 DPI
        matrix = fitz.Matrix(zoom, zoom)

        try:
            with fitz.open(pdf_path) as doc:
                for index, page in enumerate(doc):
                    pixmap = page.get_pixmap(matrix=matrix)
                    image_path = f"{pdf_path}_page{index + 1}.jpg"
                    pixmap.save(image_path)
                    pages.append(
                        PageContext(
                            page_number=index + 1,
                            original_page_number=index + 1,
                            image_uri=f"local://{image_path}",
                            resolution_dpi=RENDER_DPI,
                        )
                    )
        except Exception as e:
            raise PipelineError(
                f"Failed to render PDF pages: {e}", self.name, ErrorSeverity.FATAL
            )

        return pages

    def compensate(self, context: DocumentContext) -> None:
        """Rollback: delete any rendered page images if a later step fails."""
        storage_path = (context.storage_uri or "").replace("local://", "")
        for page in context.pages:
            if not page.image_uri or not page.image_uri.startswith("local://"):
                continue
            image_path = page.image_uri.replace("local://", "")
            # Never delete the original uploaded file itself (image uploads
            # point their page image_uri straight at context.storage_uri).
            if image_path == storage_path:
                continue
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception:
                    pass
