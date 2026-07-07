from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AgentContext(BaseModel):
    """
    Shared Context for all agents during a claim processing session.
    Contains the state of the claim.
    """
    claim_id: str
    documents: Dict[str, Any] = Field(default_factory=dict)
    ocr_results: Dict[str, Any] = Field(default_factory=dict)
    classification: Dict[str, Any] = Field(default_factory=dict)
    entities: Dict[str, Any] = Field(default_factory=dict)
    evidence_graph: Dict[str, Any] = Field(default_factory=dict)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    decision: Dict[str, Any] = Field(default_factory=dict)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
