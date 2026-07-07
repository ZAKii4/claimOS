"""OCR Engine Package."""
from app.engines.ocr.engine import HybridOCREngine
from app.engines.ocr.models import OCRResult

__all__ = ["HybridOCREngine", "OCRResult"]
