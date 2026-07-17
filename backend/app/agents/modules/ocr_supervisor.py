import time

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.engines.base import EngineContext, EngineStatus
from app.engines.ocr.engine import HybridOCREngine


def _extract_text(ocr_page: dict) -> str:
    """Flattens an OCRPage dict (blocks -> lines -> words) into plain text."""
    words = [
        word["text"]
        for block in ocr_page.get("blocks", [])
        for line in block.get("lines", [])
        for word in line.get("words", [])
    ]
    return " ".join(words)


class OCRSupervisorAgent(BaseAgent):
    id = "ocr_supervisor"
    name = "OCR Supervisor Agent"
    version = "1.0.0"
    capabilities = ["ocr", "layout_analysis"]

    def __init__(self) -> None:
        self.engine = HybridOCREngine()

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        # Run if no OCR results are present
        return not bool(context.ocr_results)

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        raw = context.metadata.get("raw", {})
        image_path = raw.get("image_path")

        # Claim-level orchestration (see docs/COURS_05_ORCHESTRATION.md) already
        # has OCR text — computed once by the linear document pipeline, not by
        # this agent — and passes it directly as "ocr_text" instead of an
        # image to re-OCR. Adopting it here (rather than re-running the OCR
        # engine on a synthetic image) avoids doing real, expensive OCR work a
        # second time for output the pipeline already produced and persisted.
        if not image_path and raw.get("ocr_text"):
            context.ocr_results = {
                "text": raw["ocr_text"],
                "confidence": float(raw.get("ocr_confidence", 1.0)),
            }
            memory.add_observation(
                self.id,
                {"status": "OCR text adopted from claim raw data (pre-computed upstream)"},
                confidence=context.ocr_results["confidence"],
            )
            return AgentResult(
                status="SUCCESS",
                confidence=context.ocr_results["confidence"],
                execution_time_ms=int((time.time() - start_time) * 1000),
                artifacts={"ocr_keys": ["text", "confidence"], "source": "claim_raw_data"},
                messages=["Adopted pre-computed OCR text; did not re-run the OCR engine."],
            )

        if not image_path:
            return AgentResult(
                status="FAILED",
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                artifacts={},
                messages=[
                    "No 'image_path' or 'ocr_text' provided in claim raw data; cannot run "
                    "OCR without a real document to process."
                ],
            )

        engine_context = EngineContext(
            claim_id=context.claim_id,
            input_data={
                "image_path": image_path,
                "engine_preference": ["doctr", "paddleocr", "tesseract"],
            },
        )
        result = self.engine.process(engine_context)

        execution_time = int((time.time() - start_time) * 1000)

        if result.status != EngineStatus.SUCCESS:
            return AgentResult(
                status="FAILED",
                confidence=0.0,
                execution_time_ms=execution_time,
                artifacts={"errors": result.errors},
                messages=[f"OCR engine failed: {result.errors}"],
            )

        text = _extract_text(result.output_data.get("page", {}))
        confidence = result.output_data.get("confidence_score", 0.0)

        context.ocr_results = {"text": text, "confidence": confidence}

        memory.add_observation(self.id, {"status": "OCR Completed"}, confidence=confidence)

        return AgentResult(
            status="SUCCESS",
            confidence=confidence,
            execution_time_ms=execution_time,
            artifacts={"ocr_keys": ["text", "confidence"]},
            messages=["OCR processed successfully via HybridOCREngine."],
        )

    async def validate(self, result: AgentResult) -> bool:
        return result.confidence > 0.5
