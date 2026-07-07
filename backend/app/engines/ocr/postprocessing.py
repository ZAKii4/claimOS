"""
Post-processing engine for text cleanup.
"""

import re
import unicodedata

from app.engines.ocr.models import OCRPage


class PostProcessingEngine:
    """
    Cleans up OCR text (unicode normalization, spacing, punctuation).
    """
    
    def clean(self, page: OCRPage) -> OCRPage:
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    word.text = self._clean_text(word.text)
        return page

    def _clean_text(self, text: str) -> str:
        if not text:
            return text
            
        # 1. Unicode normalization (NFKC)
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Remove isolated weird characters often produced by OCR noise
        # This regex removes characters that are NOT alphanumeric or common punctuation
        # But we must be careful with french accents (which NFKC handles well).
        # We will keep it simple for now.
        text = text.strip()
        
        # 3. Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        return text
