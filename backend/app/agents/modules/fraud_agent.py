import time
from app.agents.base import BaseAgent, AgentResult
from app.agents.context import AgentContext
from app.agents.memory import SharedMemory


class FraudAgent(BaseAgent):
    id = "fraud_agent"
    name = "Fraud Detection Agent"
    version = "1.0.0"
    capabilities = ["fraud_detection", "anomaly_detection"]
    
    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        # Run only if OCR is done
        return bool(context.ocr_results)
        
    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()
        
        # Analyze OCR text for fraud keywords
        ocr_text = context.ocr_results.get("text", "").lower()
        
        is_fraud = "fake" in ocr_text or "photoshop" in ocr_text
        confidence = 0.8 if is_fraud else 0.9
        
        context.metadata["fraud_score"] = 0.9 if is_fraud else 0.1
        
        memory.add_observation(self.id, {"fraud_suspected": is_fraud}, confidence=confidence)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AgentResult(
            status="SUCCESS",
            confidence=confidence,
            execution_time_ms=execution_time,
            artifacts={"fraud_score": context.metadata["fraud_score"]},
            messages=[f"Fraud evaluation completed. Suspected: {is_fraud}"]
        )
        
    async def validate(self, result: AgentResult) -> bool:
        return result.confidence > 0.0
