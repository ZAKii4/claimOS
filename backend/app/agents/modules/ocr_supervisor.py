import time
from app.agents.base import BaseAgent, AgentResult
from app.agents.context import AgentContext
from app.agents.memory import SharedMemory


class OCRSupervisorAgent(BaseAgent):
    id = "ocr_supervisor"
    name = "OCR Supervisor Agent"
    version = "1.0.0"
    capabilities = ["ocr", "layout_analysis"]
    
    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        # Run if no OCR results are present
        return not bool(context.ocr_results)
        
    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()
        
        # In a real implementation, this would call the OCREngine
        # For MVP, we mock the result
        context.ocr_results = {
            "text": "Invoice #1234\nAmount: $1000",
            "confidence": 0.95
        }
        
        memory.add_observation(self.id, {"status": "OCR Completed"}, confidence=0.95)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AgentResult(
            status="SUCCESS",
            confidence=0.95,
            execution_time_ms=execution_time,
            artifacts={"ocr_keys": ["text", "confidence"]},
            messages=["OCR processed successfully."]
        )
        
    async def validate(self, result: AgentResult) -> bool:
        return result.confidence > 0.5
