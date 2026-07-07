from app.engines.extraction.models import ExtractedEntity

class ConfidenceAdjuster:
    """
    Adjusts the confidence score of extracted entities based on heuristics.
    """
    
    @staticmethod
    def adjust(entity: ExtractedEntity, is_valid: bool) -> float:
        """
        Modifies base confidence based on validation and provenance.
        """
        score = entity.confidence
        
        if not is_valid:
            score *= 0.5  # Penalize invalid formats
            
        # Boost score if extracted from a structured form field (Layout Region)
        if entity.provenance.layout_region_id:
            score = min(1.0, score + 0.1)
            
        # Penalize slightly if it relies purely on OCR text heuristics without bounding box
        if not entity.provenance.bounding_box:
            score *= 0.9
            
        return round(score, 3)
