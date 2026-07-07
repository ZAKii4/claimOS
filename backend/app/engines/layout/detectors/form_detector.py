import re
from typing import Optional

import numpy as np

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import FormFieldRegion, LayoutRegion
from app.engines.layout.relationships import is_horizontally_aligned
from app.engines.ocr.models import OCRPage


class FormDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "form_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        if not ocr_page:
            return []

        regions = []
        
        # Known labels to look for
        LABEL_PATTERNS = [
            r"nom\s*:",
            r"prénom\s*:",
            r"adresse\s*:",
            r"date\s*:",
            r"police\s*:",
            r"téléphone\s*:",
            r"profession\s*:",
            r"itt\s*:",
            r"opposition\s*:",
            r"ville\s*:"
        ]
        
        # Flatten all words to search
        words = []
        for block in ocr_page.blocks:
            for line in block.lines:
                words.extend(line.words)
                
        # Simple Key-Value matching based on horizontal alignment
        for i, word in enumerate(words):
            text_lower = word.text.lower()
            
            is_label = any(re.search(pattern, text_lower) for pattern in LABEL_PATTERNS)
            
            if is_label:
                # Find the next word that is horizontally aligned and to the right
                value_word = None
                for candidate in words:
                    if candidate == word:
                        continue
                        
                    if candidate.bbox.x_min > word.bbox.x_max and is_horizontally_aligned(word.bbox, candidate.bbox, tolerance=0.03):
                        if not value_word or candidate.bbox.x_min < value_word.bbox.x_min:
                            value_word = candidate
                            
                field = FormFieldRegion(
                    bounding_box=word.bbox, # Ideally this would encompass both
                    label=word.text,
                    value=value_word.text if value_word else None
                )
                regions.append(field)
                
        return regions
