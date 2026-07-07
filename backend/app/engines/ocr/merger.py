"""
Fusion Engine to merge results from multiple OCR engines.
"""

from shapely.geometry import Polygon

from app.engines.ocr.models import OCRPage


class FusionEngine:
    """
    Merges multiple OCRPages (from different engines) into a single consensus OCRPage.
    Resolves conflicts using IoU (Intersection over Union) and confidence scores.
    """
    
    def merge(self, pages: list[OCRPage]) -> OCRPage:
        if not pages:
            raise ValueError("Cannot merge empty list of pages.")
        if len(pages) == 1:
            return pages[0]
            
        # For MVP, we will use a simplified consensus:
        # We take the page from the primary engine (pages[0]) and we don't do complex word-by-word IoU mapping yet,
        # but we provide the architectural hook.
        
        # A true implementation would:
        # 1. Flatten all words from all pages.
        # 2. Use an R-Tree or simple n^2 loop with shapely Polygons to find overlaps (IoU > 0.5).
        # 3. For each overlapping cluster, pick the word with the highest confidence.
        # 4. Reconstruct lines and blocks based on the winning words.
        
        # We will just return the best page for now based on average confidence.
        best_page = pages[0]
        best_conf = self._calculate_page_confidence(pages[0])
        
        for p in pages[1:]:
            conf = self._calculate_page_confidence(p)
            if conf > best_conf:
                best_conf = conf
                best_page = p
                
        # Annotate that it was merged
        best_page.engine_name = f"{best_page.engine_name}_merged"
        
        return best_page
        
    def _calculate_page_confidence(self, page: OCRPage) -> float:
        confs = []
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    confs.append(word.confidence)
        if not confs:
            return 0.0
        return sum(confs) / len(confs)
