from pydantic import BaseModel
from typing import Optional

from app.engines.evidence_graph.models import EvidenceGraphResult


class ValidationContext(BaseModel):
    """
    Context passed to all Validation Rules. 
    It holds the Evidence Graph and optionally other raw data.
    """
    claim_id: str
    evidence_graph: EvidenceGraphResult
    
    # Optional raw data if a rule needs to bypass the graph
    raw_extraction_result: Optional[dict] = None
    raw_classification_result: Optional[dict] = None
