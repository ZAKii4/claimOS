"""
Visualization module for OCR results.
"""

import cv2
import numpy as np

from app.engines.ocr.models import OCRPage


class OCRVisualizer:
    """
    Draws bounding boxes and text on images for debugging and visualization.
    """
    
    def draw(self, image: np.ndarray, page: OCRPage) -> np.ndarray:
        h, w = image.shape[:2]
        viz = image.copy()
        
        # Draw Blocks (Blue)
        for block_idx, block in enumerate(page.blocks):
            bx_min, by_min = int(block.bbox.x_min * w), int(block.bbox.y_min * h)
            bx_max, by_max = int(block.bbox.x_max * w), int(block.bbox.y_max * h)
            
            cv2.rectangle(viz, (bx_min, by_min), (bx_max, by_max), (255, 0, 0), 2)
            cv2.putText(viz, f"B{block_idx}", (bx_min, by_min - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                        
            # Draw Lines (Green)
            for line in block.lines:
                lx_min, ly_min = int(line.bbox.x_min * w), int(line.bbox.y_min * h)
                lx_max, ly_max = int(line.bbox.x_max * w), int(line.bbox.y_max * h)
                cv2.rectangle(viz, (lx_min, ly_min), (lx_max, ly_max), (0, 255, 0), 1)
                
                # Draw Words (Red)
                for word in line.words:
                    if word.polygon:
                        # Draw polygon
                        pts = np.array([
                            [int(p[0] * w), int(p[1] * h)] for p in word.polygon
                        ], np.int32)
                        pts = pts.reshape((-1, 1, 2))
                        cv2.polylines(viz, [pts], isClosed=True, color=(0, 0, 255), thickness=1)
                    else:
                        wx_min, wy_min = int(word.bbox.x_min * w), int(word.bbox.y_min * h)
                        wx_max, wy_max = int(word.bbox.x_max * w), int(word.bbox.y_max * h)
                        cv2.rectangle(viz, (wx_min, wy_min), (wx_max, wy_max), (0, 0, 255), 1)
                        
        return viz
