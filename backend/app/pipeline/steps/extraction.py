"""
Step 12: Business Extraction.

Runs the domain-specific Extraction Engine (registry of field extractors)
against each page's OCR/Layout/Classification results and stores the
extracted key-value entities on the DocumentContext.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.extraction.extractors.insurance.national_id import NationalIdExtractor
from app.engines.extraction.extractors.insurance.owner_identity import OwnerNameExtractor
from app.engines.extraction.extractors.insurance.policy_number import PolicyNumberExtractor
from app.engines.extraction.extractors.llm.llm_field_extractor import LLMFieldExtractor
from app.engines.extraction.extractors.vehicle.license_plate import LicensePlateExtractor
from app.engines.extraction.extractors.vehicle.vehicle_brand import VehicleBrandExtractor
from app.engines.extraction.manager import ExtractionEngine
from app.engines.extraction.registry import ExtractorRegistry
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class BusinessExtractionStep(PipelineStep):

    @property
    def name(self) -> str:
        return "business_extraction"

    def __init__(self) -> None:
        registry = ExtractorRegistry()
        registry.register(LicensePlateExtractor)
        registry.register(PolicyNumberExtractor)
        registry.register(NationalIdExtractor)
        registry.register(OwnerNameExtractor)
        registry.register(VehicleBrandExtractor)
        registry.register(LLMFieldExtractor)
        self.engine = ExtractionEngine(registry=registry)

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            return context

        for page in context.pages:
            ocr_result = page.engine_results.get("ocr")
            layout_result = page.engine_results.get("layout")
            classification_result = page.engine_results.get("classification")

            if not (
                ocr_result and ocr_result.status == EngineStatus.SUCCESS
                and layout_result and layout_result.status == EngineStatus.SUCCESS
                and classification_result and classification_result.status == EngineStatus.SUCCESS
            ):
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Skipped extraction for page {page.page_number}: missing inputs.",
                })
                continue

            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={
                    "ocr_result": ocr_result.output_data,
                    "layout_result": layout_result.output_data.get("layout_analysis_result"),
                    "classification_result": classification_result.output_data.get(
                        "classification_result"
                    ),
                },
            )

            result = self.engine.process(engine_context)

            if result.status == EngineStatus.SUCCESS:
                page.engine_results["extraction"] = result
                extracted = result.output_data.get("extraction_result")
                context.extracted_data[str(page.page_number)] = extracted
            else:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Extraction failed on page {page.page_number}: {result.errors}",
                })

        return context
