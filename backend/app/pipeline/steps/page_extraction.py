"""
Step 07: Page Extraction.

Extracts individual pages from a PDF/Image as standard image formats (e.g. JPEG).
Populates context.pages with PageContext objects.
"""

from app.pipeline.core import DocumentContext, ErrorSeverity, PageContext, PipelineError, PipelineStep


class PageExtractionStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "page_extraction"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.storage_uri:
            raise PipelineError("Storage URI missing", self.name, ErrorSeverity.FATAL)
            
        # Stub: Call a PDF rendering library like pdf2image or PyMuPDF.
        # Example for a 2-page document:
        
        context.pages = [
            PageContext(
                page_number=1,
                original_page_number=1,
                image_uri=f"{context.storage_uri}_page1.jpg",
                resolution_dpi=300
            ),
            PageContext(
                page_number=2,
                original_page_number=2,
                image_uri=f"{context.storage_uri}_page2.jpg",
                resolution_dpi=300
            )
        ]
        
        return context
