"""
Confidence Engine to compute global OCR confidence.
"""

from app.engines.iqa.models import ImageQualityReport
from app.engines.ocr.models import OCRPage


class ConfidenceEngine:
    """
    Calculates a holistic confidence score for the OCR output by factoring in:
    - Base OCR confidence
    - Image Quality metrics (blur, noise, contrast)
    """
    
    def calculate_score(self, page: OCRPage, iqa_report: dict) -> float:
        confs = []
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    confs.append(word.confidence)
                    
        if not confs:
            return 0.0
            
        base_confidence = sum(confs) / len(confs)
        
        if not iqa_report:
            return base_confidence
            
        penalty = 0.0
        
        # Penalize if IQA detected blur
        if iqa_report.get("is_blurred", False):
            penalty += 0.15
            
        # Penalize for noise
        noise_level = iqa_report.get("noise_level", 0.0)
        if noise_level > 0.1:
            penalty += min(0.2, noise_level)
            
        # Penalize for bad contrast
        contrast = iqa_report.get("contrast", 100.0)
        if contrast < 30.0:
            penalty += 0.1
            
        final_score = max(0.0, base_confidence - penalty)
        
        return final_score
