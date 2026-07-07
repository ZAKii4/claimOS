from typing import Any
from app.engines.ocr.models import OCRPage
from app.engines.layout.models import LayoutPage

class FeatureExtractor:
    """
    Extracts features from OCR and Layout results for downstream classifiers.
    """

    def extract_ocr_features(self, ocr_page: OCRPage) -> dict[str, Any]:
        """Extracts text-based features."""
        text_content = ""
        for block in ocr_page.blocks:
            for line in block.lines:
                text_content += " ".join(w.text for w in line.words) + "\n"

        words = text_content.lower().split()
        return {
            "text_length": len(words),
            "raw_text": text_content,
            # In a real implementation, we would extract TF-IDF vectors or embeddings here.
        }

    def extract_layout_features(self, layout_page: LayoutPage) -> dict[str, Any]:
        """Extracts structural features."""
        return {
            "num_tables": len(layout_page.tables),
            "num_form_fields": len(layout_page.form_fields),
            "num_signatures": len(layout_page.signatures),
            "num_stamps": len(layout_page.stamps),
            "num_checkboxes": len(layout_page.checkboxes),
        }

    def extract_all(self, ocr_page: OCRPage, layout_page: LayoutPage) -> dict[str, Any]:
        features = {}
        if ocr_page:
            features.update(self.extract_ocr_features(ocr_page))
        if layout_page:
            features.update(self.extract_layout_features(layout_page))
        return features
