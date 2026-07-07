from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class Message(BaseModel):
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CostMetrics(BaseModel):
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0


class LLMRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    id: str
    provider_name: str
    model: str
    choices: List[Message]
    usage: TokenUsage
    cost: CostMetrics
    latency_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
