"""
Reading Order Reconstruction.
"""

from app.engines.ocr.models import OCRPage


class ReadingOrderEngine:
    """
    Reconstructs the reading order of OCR Blocks (e.g. columns, paragraphs).
    """
    
    def reconstruct(self, page: OCRPage) -> OCRPage:
        """
        Sorts blocks top-to-bottom, left-to-right.
        """
        if not page.blocks:
            return page
            
        # A simple heuristic: Sort primarily by Y, but if Y difference is small, sort by X.
        # This works for simple layouts. For complex layouts, a layout analysis model is needed.
        def block_sort_key(block):
            return (round(block.bbox.y_min, 2), block.bbox.x_min)
            
        page.blocks.sort(key=block_sort_key)
        
        # Inside each block, lines should also be sorted
        for block in page.blocks:
            block.lines.sort(key=lambda line: (round(line.bbox.y_min, 2), line.bbox.x_min))
            # Words inside lines are usually sorted left-to-right by the OCR engine,
            # but we can enforce it.
            for line in block.lines:
                line.words.sort(key=lambda word: word.bbox.x_min)
                
        return page
