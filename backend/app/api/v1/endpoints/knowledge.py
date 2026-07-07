from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.knowledge.manager import KnowledgeManager
from app.knowledge.models import SearchQuery, SearchResponse
from app.llm.manager import LLMManager

router = APIRouter(prefix="/knowledge", tags=["Enterprise Knowledge Platform"])

# In a real app, this would be injected via dependencies
llm_manager = LLMManager()
knowledge_manager = KnowledgeManager(llm_manager)


class DocumentUploadRequest(BaseModel):
    title: str
    text: str


@router.post("/documents")
async def add_document(req: DocumentUploadRequest):
    """Add a new document to the knowledge base."""
    doc = await knowledge_manager.add_document(req.title, req.text)
    return {"id": doc.id, "title": doc.title, "chunks": len(doc.chunks)}


@router.get("/documents")
def list_documents():
    """List all indexed documents."""
    return [{"id": d.id, "title": d.title} for d in knowledge_manager.documents.values()]


@router.post("/retrieve")
async def retrieve_knowledge(query: SearchQuery):
    """Hybrid RAG Search."""
    return await knowledge_manager.search_engine.search(query)


@router.get("/statistics")
def get_statistics():
    """Get metrics about the knowledge graph."""
    return {
        "documents": len(knowledge_manager.documents),
        "vector_chunks": len(knowledge_manager.vector_store.chunks),
        "bm25_terms": len(knowledge_manager.bm25_index.doc_freqs)
    }
