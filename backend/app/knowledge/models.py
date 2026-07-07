from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class KnowledgeCitation(BaseModel):
    document_id: str
    chunk_id: str
    text_snippet: str
    relevance_score: float
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class KnowledgeChunk(BaseModel):
    id: str
    document_id: str
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    position_index: int
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    source_type: str # pdf, docx, html, database
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[KnowledgeChunk] = Field(default_factory=list)


class SearchResult(BaseModel):
    chunk: KnowledgeChunk
    score: float # Hybrid score
    vector_score: float = 0.0
    bm25_score: float = 0.0


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    filters: Dict[str, Any] = Field(default_factory=dict)
    enable_vector: bool = True
    enable_bm25: bool = True


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    processing_time_ms: int
