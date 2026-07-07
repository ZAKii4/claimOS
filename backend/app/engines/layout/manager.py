import time
from typing import Any

import cv2
import numpy as np

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.layout.detectors.checkbox_detector import CheckboxDetector
from app.engines.layout.detectors.form_detector import FormDetector
from app.engines.layout.detectors.header_detector import HeaderDetector
from app.engines.layout.detectors.paragraph_detector import ParagraphDetector
from app.engines.layout.detectors.signature_detector import SignatureDetector
from app.engines.layout.detectors.stamp_detector import StampDetector
from app.engines.layout.detectors.table_detector import TableDetector
from app.engines.layout.models import (
    CheckboxRegion,
    FormFieldRegion,
    HeaderRegion,
    ImageRegion,
    LayoutAnalysisResult,
    LayoutDocument,
    LayoutPage,
    ParagraphRegion,
    SignatureRegion,
    StampRegion,
    TableRegion,
)
from app.engines.layout.reading_graph import ReadingGraphBuilder
from app.engines.ocr.models import OCRResult


class LayoutEngine(BaseEngine):
    """
    Main entry point for the Layout Analysis Engine.
    Coordinates all detectors to build a semantic hierarchy from OCR and Image.
    """

    def __init__(self):
        self._detectors = [
            HeaderDetector(),
            ParagraphDetector(),
            TableDetector(),
            FormDetector(),
            SignatureDetector(),
            StampDetector(),
            CheckboxDetector(),
        ]

    @property
    def name(self) -> str:
        return "layout"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return True

    def process(self, context: EngineContext) -> EngineResult:
        start_time = time.time()
        errors = []
        
        try:
            image_path = context.input_data.get("image_path")
            ocr_data = context.input_data.get("ocr_result")
            
            if not image_path:
                return self._create_failure("image_path is missing")
                
            if not ocr_data:
                return self._create_failure("ocr_result is missing")

            # Try to parse OCR data
            if isinstance(ocr_data, dict):
                ocr_result = OCRResult(**ocr_data)
            elif isinstance(ocr_data, OCRResult):
                ocr_result = ocr_data
            else:
                return self._create_failure("Invalid format for ocr_result")

            image = cv2.imread(image_path)
            if image is None:
                return self._create_failure(f"Could not load image at {image_path}")
            
            h, w = image.shape[:2]
            layout_page = LayoutPage(width=w, height=h)
            
            # 1. Run all detectors
            all_regions = []
            for detector in self._detectors:
                regions = detector.detect(image, ocr_result.page)
                all_regions.extend(regions)
                
            layout_page.regions = all_regions
            
            # 2. Build Reading Graph & Relationships
            graph_builder = ReadingGraphBuilder(layout_page)
            graph_builder.build_spatial_relationships()
            graph_builder.calculate_reading_order()
            
            # 3. Categorize into specific lists for easy consumption
            for region in layout_page.regions:
                if isinstance(region, TableRegion):
                    layout_page.tables.append(region)
                elif isinstance(region, ParagraphRegion):
                    layout_page.paragraphs.append(region)
                elif isinstance(region, HeaderRegion):
                    layout_page.headers.append(region)
                elif isinstance(region, SignatureRegion):
                    layout_page.signatures.append(region)
                elif isinstance(region, StampRegion):
                    layout_page.stamps.append(region)
                elif isinstance(region, CheckboxRegion):
                    layout_page.checkboxes.append(region)
                elif isinstance(region, FormFieldRegion):
                    layout_page.form_fields.append(region)
                elif isinstance(region, ImageRegion):
                    layout_page.images.append(region)

            layout_doc = LayoutDocument(pages=[layout_page])
            result_obj = LayoutAnalysisResult(
                document=layout_doc,
                global_confidence=ocr_result.confidence_score,
                detected_language=ocr_result.page.language
            )

            processing_time = int((time.time() - start_time) * 1000)
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data={"layout_analysis_result": result_obj.model_dump(mode='json')},
                confidence=result_obj.global_confidence,
                processing_time_ms=processing_time,
                errors=[]
            )

        except Exception as e:
            return self._create_failure(str(e))

    def _create_failure(self, error_msg: str) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.FAILURE,
            errors=[error_msg]
        )
