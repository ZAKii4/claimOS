"""
DocTR OCR Adapter.
"""

import time
import logging

import numpy as np

from app.engines.ocr.base import BaseOCRAdapter
from app.engines.ocr.models import BoundingBox, OCRBlock, OCRLine, OCRPage, OCRWord

logger = logging.getLogger(__name__)

try:
    from doctr.models import ocr_predictor
    DOCTR_AVAILABLE = True
except ImportError:
    DOCTR_AVAILABLE = False


class DocTRAdapter(BaseOCRAdapter):
    
    def __init__(self) -> None:
        self.model = None

    @property
    def name(self) -> str:
        return "doctr"
        
    @property
    def version(self) -> str:
        try:
            import doctr
            return doctr.__version__
        except ImportError:
            return "unknown"

    def is_available(self) -> bool:
        return DOCTR_AVAILABLE

    def initialize(self) -> None:
        if not self.is_available():
            raise RuntimeError("DocTR is not installed.")
        if self.model is None:
            # Load the predictor (default models)
            self.model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

    def process(self, image: np.ndarray) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("DocTR is not available.")
            
        self.initialize()
        
        start_time = time.perf_counter()
        
        # DocTR expects RGB images, float32 or uint8
        result = self.model([image])
        
        blocks = []
        for page in result.pages:
            for block in page.blocks:
                ocr_lines = []
                for line in block.lines:
                    words = []
                    for word in line.words:
                        # DocTR bbox format: ((xmin, ymin), (xmax, ymax))
                        (xmin, ymin), (xmax, ymax) = word.geometry
                        
                        words.append(OCRWord(
                            text=word.value,
                            confidence=word.confidence,
                            bbox=BoundingBox(x_min=xmin, y_min=ymin, x_max=xmax, y_max=ymax),
                            polygon=[(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)],
                            language=None,
                            engine_name=self.name
                        ))
                    
                    if words:
                        (l_xmin, l_ymin), (l_xmax, l_ymax) = line.geometry
                        ocr_lines.append(OCRLine(
                            words=words,
                            bbox=BoundingBox(x_min=l_xmin, y_min=l_ymin, x_max=l_xmax, y_max=l_ymax)
                        ))
                        
                if ocr_lines:
                    (b_xmin, b_ymin), (b_xmax, b_ymax) = block.geometry
                    blocks.append(OCRBlock(
                        lines=ocr_lines,
                        bbox=BoundingBox(x_min=b_xmin, y_min=b_ymin, x_max=b_xmax, y_max=b_ymax)
                    ))
                    
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        return OCRPage(
            blocks=blocks,
            language=None,
            engine_name=self.name,
            processing_time_ms=elapsed_ms
        )
