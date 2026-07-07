"""
Step 04: Metadata Extraction.

Extracts native document metadata (Exif, XMP, PDF info dict).
"""

from app.pipeline.core import DocumentContext, PipelineStep


class MetadataExtractionStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "metadata_extraction"

    def execute(self, context: DocumentContext) -> DocumentContext:
        # Stub: Extract metadata based on file type
        # For PDF: /CreationDate, /Author, /Producer
        # For JPEG: EXIF DateTimeOriginal, GPS coordinates
        
        # We record this in the context dictionary without failing if missing
        context.metadata["extracted_native_metadata"] = True
        return context
