"""
Tesseract OCR Adapter.
"""

import time
import logging

import cv2
import numpy as np

from app.config.settings import get_settings
from app.engines.ocr.base import BaseOCRAdapter
from app.engines.ocr.models import BoundingBox, OCRBlock, OCRLine, OCRPage, OCRWord

logger = logging.getLogger(__name__)

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class TesseractAdapter(BaseOCRAdapter):
    
    @property
    def name(self) -> str:
        return "tesseract"
        
    @property
    def version(self) -> str:
        if not self.is_available():
            return "unknown"
        try:
            return pytesseract.get_tesseract_version().get("version", "unknown")
        except Exception:
            return "unknown"

    def initialize(self) -> None:
        pass

    def is_available(self) -> bool:
        if not PYTESSERACT_AVAILABLE:
            return False
        # Check if tesseract binary is in PATH
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def process(self, image: np.ndarray) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("Tesseract is not available or not installed on the system.")
            
        start_time = time.perf_counter()
        
        # Pytesseract expects RGB for colored, or Grayscale
        if len(image.shape) == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
            
        h, w = image.shape[:2]
        
        # output_type=dict returns a dictionary with keys: level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
        lang = get_settings().OCR_LANGUAGES
        data = pytesseract.image_to_data(rgb_image, lang=lang, output_type=pytesseract.Output.DICT)
        
        blocks_dict = {}
        
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            # level 5 corresponds to a word
            if data['level'][i] == 5:
                text = data['text'][i].strip()
                if not text:
                    continue
                    
                conf = float(data['conf'][i]) / 100.0  # pytesseract conf is 0-100
                if conf < 0:
                    conf = 0.0
                    
                x, y, w_box, h_box = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                
                # Normalize bounding box
                x_min = max(0.0, x / w)
                y_min = max(0.0, y / h)
                x_max = min(1.0, (x + w_box) / w)
                y_max = min(1.0, (y + h_box) / h)
                
                word = OCRWord(
                    text=text,
                    confidence=conf,
                    bbox=BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max),
                    polygon=[(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)],
                    language=None, # Tesseract output doesn't give language per word by default
                    engine_name=self.name
                )
                
                block_id = data['block_num'][i]
                line_id = data['line_num'][i]
                
                if block_id not in blocks_dict:
                    blocks_dict[block_id] = {}
                if line_id not in blocks_dict[block_id]:
                    blocks_dict[block_id][line_id] = []
                    
                blocks_dict[block_id][line_id].append(word)
                
        # Reconstruct Lines and Blocks
        blocks = []
        for block_id, lines_dict in blocks_dict.items():
            ocr_lines = []
            block_xmin, block_ymin, block_xmax, block_ymax = 1.0, 1.0, 0.0, 0.0
            
            for line_id, words in lines_dict.items():
                if not words:
                    continue
                    
                line_xmin = min([w.bbox.x_min for w in words])
                line_ymin = min([w.bbox.y_min for w in words])
                line_xmax = max([w.bbox.x_max for w in words])
                line_ymax = max([w.bbox.y_max for w in words])
                
                block_xmin = min(block_xmin, line_xmin)
                block_ymin = min(block_ymin, line_ymin)
                block_xmax = max(block_xmax, line_xmax)
                block_ymax = max(block_ymax, line_ymax)
                
                ocr_lines.append(OCRLine(
                    words=words,
                    bbox=BoundingBox(x_min=line_xmin, y_min=line_ymin, x_max=line_xmax, y_max=line_ymax)
                ))
                
            if ocr_lines:
                blocks.append(OCRBlock(
                    lines=ocr_lines,
                    bbox=BoundingBox(x_min=block_xmin, y_min=block_ymin, x_max=block_xmax, y_max=block_ymax)
                ))
                
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        return OCRPage(
            blocks=blocks,
            language=lang,
            engine_name=self.name,
            processing_time_ms=elapsed_ms
        )
