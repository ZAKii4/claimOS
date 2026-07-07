from typing import List, Optional
from app.knowledge.models import SearchQuery, SearchResponse, KnowledgeDocument
from app.knowledge.indexer import DocumentIndexer
from app.knowledge.hybrid_search import HybridSearchEngine
from app.knowledge.embeddings import EmbeddingsEngine
from app.knowledge.vector_store import MockVectorStore
from app.knowledge.keyword_index import BM25Index
from app.knowledge.summarizer import SummarizerEngine
from app.llm.manager import LLMManager


class KnowledgeManager:
    """Orchestrator for the entire Enterprise Knowledge Platform."""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.embeddings = EmbeddingsEngine(self.llm_manager)
        
        self.vector_store = MockVectorStore()
        self.bm25_index = BM25Index()
        
        self.indexer = DocumentIndexer(self.embeddings)
        self.search_engine = HybridSearchEngine(self.vector_store, self.bm25_index, self.embeddings)
        self.summarizer = SummarizerEngine(self.llm_manager)
        
        self.documents = {}
        
    async def add_document(self, title: str, text: str) -> KnowledgeDocument:
        """Indexes a document and adds it to both stores."""
        doc = await self.indexer.index_text(title, text)
        self.documents[doc.id] = doc
        
        self.vector_store.add_chunks(doc.chunks)
        self.bm25_index.add_chunks(doc.chunks)
        
        return doc
        
    async def retrieve(self, query: str, top_k: int = 5, use_hybrid: bool = True) -> SearchResponse:
        """Retrieves grounded knowledge for an agent to use."""
        search_query = SearchQuery(
            query=query, 
            top_k=top_k,
            enable_vector=use_hybrid,
            enable_bm25=use_hybrid
        )
        return await self.search_engine.search(search_query)
        
    async def summarize_document(self, doc_id: str) -> str:
        """Generates a summary of an entire document."""
        doc = self.documents.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
            
        texts = [c.content for c in doc.chunks]
        return await self.summarizer.summarize_chunks(texts)
