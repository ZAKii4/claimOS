from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AgentProfile(BaseModel):
    name: str
    model_name: str
    role: str
    allowed_tools: List[str]
    max_context_tokens: int
    temperature: float
    specialty: str
    autonomy_level: str


class AgentRegistry:
    """Central registry for all autonomous agents."""

    _agents: Dict[str, AgentProfile] = {
        "OCRAgent": AgentProfile(
            name="OCRAgent", model_name="phi-4", role="Data Cleaner",
            allowed_tools=["Pipeline", "Storage"], max_context_tokens=4000,
            temperature=0.1, specialty="OCR", autonomy_level="HIGH"
        ),
        "ExtractionAgent": AgentProfile(
            name="ExtractionAgent", model_name="qwen-2.5", role="Entity Extractor",
            allowed_tools=["Knowledge Platform"], max_context_tokens=32000,
            temperature=0.2, specialty="Extraction", autonomy_level="HIGH"
        ),
        "FraudAgent": AgentProfile(
            name="FraudAgent", model_name="deepseek-r1", role="Fraud Analyst",
            allowed_tools=["Analytics", "Evidence Graph"], max_context_tokens=16000,
            temperature=0.3, specialty="Fraud", autonomy_level="MEDIUM"
        ),
        "LegalAgent": AgentProfile(
            name="LegalAgent", model_name="granite", role="Legal Expert",
            allowed_tools=["Hybrid RAG", "Knowledge Platform"], max_context_tokens=8000,
            temperature=0.2, specialty="Legal", autonomy_level="HIGH"
        ),
        "DecisionAgent": AgentProfile(
            name="DecisionAgent", model_name="llama-3.1", role="Decision Maker",
            allowed_tools=["Decision Engine", "Simulation"], max_context_tokens=128000,
            temperature=0.4, specialty="Decision", autonomy_level="MEDIUM"
        ),
        "SupervisorAgent": AgentProfile(
            name="SupervisorAgent", model_name="qwen-2.5", role="Orchestrator",
            allowed_tools=["Workflow Engine", "All"], max_context_tokens=32000,
            temperature=0.1, specialty="Supervision", autonomy_level="HIGH"
        )
    }

    @classmethod
    def list_agents(cls) -> List[AgentProfile]:
        return list(cls._agents.values())

    @classmethod
    def get_agent(cls, name: str) -> Optional[AgentProfile]:
        return cls._agents.get(name)

    @classmethod
    def register_agent(cls, profile: AgentProfile):
        cls._agents[profile.name] = profile

    @classmethod
    def _reset(cls):
        # Keeps original list untouched for test resets if needed, but we don't modify it dynamically yet besides register
        pass
