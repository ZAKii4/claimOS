import uuid
from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.engines.extraction.models import Provenance


class NodeType(str, Enum):
    CLAIM = "CLAIM"
    POLICY = "POLICY"
    PERSON = "PERSON"
    VEHICLE = "VEHICLE"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    POLICE_REPORT = "POLICE_REPORT"
    INVOICE = "INVOICE"
    DOCUMENT = "DOCUMENT"
    DAMAGE = "DAMAGE"
    UNKNOWN = "UNKNOWN"


class EdgeType(str, Enum):
    OWNS = "OWNS"
    DRIVES = "DRIVES"
    INVOLVED_IN = "INVOLVED_IN"
    ISSUED = "ISSUED"
    ATTACHED_TO = "ATTACHED_TO"
    MENTIONS = "MENTIONS"
    FILED = "FILED"
    IS_SAME_AS = "IS_SAME_AS"
    HAS_ATTRIBUTE = "HAS_ATTRIBUTE"


class NodeConfidence(BaseModel):
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    explanation: list[str] = Field(default_factory=list)


class EvidenceNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType
    attributes: dict[str, Any] = Field(default_factory=dict)
    provenances: list[Provenance] = Field(default_factory=list)
    confidence: NodeConfidence = Field(default_factory=NodeConfidence)
    
    def __hash__(self):
        return hash(self.id)
        
    def __eq__(self, other):
        if not isinstance(other, EvidenceNode):
            return False
        return self.id == other.id


class EvidenceEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: EdgeType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    attributes: dict[str, Any] = Field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.edge_type))


class GraphStatistics(BaseModel):
    node_count: int
    edge_count: int
    connected_components: int
    density: float


class EvidenceGraphResult(BaseModel):
    claim_id: str
    nodes: list[EvidenceNode] = Field(default_factory=list)
    edges: list[EvidenceEdge] = Field(default_factory=list)
    statistics: Optional[GraphStatistics] = None
    global_confidence: float = 0.0
    execution_time_ms: int = 0
