from typing import List, Optional
from app.knowledge.models import SearchQuery, SearchResponse, KnowledgeDocument
from app.knowledge.indexer import DocumentIndexer
from app.knowledge.hybrid_search import HybridSearchEngine
from app.knowledge.embeddings import EmbeddingsEngine
from app.knowledge.vector_store import PgVectorStore, BaseVectorStore
from app.knowledge.keyword_index import BM25Index
from app.knowledge.summarizer import SummarizerEngine
from app.llm.manager import LLMManager
from app.core.database import get_session_factory
from app.models.knowledge import KnowledgeDocument as DBKnowledgeDocument

_UNSET = object()


class KnowledgeManager:
    """Orchestrator for the entire Enterprise Knowledge Platform."""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        vector_store: Optional[BaseVectorStore] = None,
        session_factory=_UNSET,
    ):
        self.llm_manager = llm_manager
        self.embeddings = EmbeddingsEngine(self.llm_manager)
        
        self.vector_store = vector_store or PgVectorStore()
        self.bm25_index = BM25Index()
        
        self.indexer = DocumentIndexer(self.embeddings)
        self.search_engine = HybridSearchEngine(self.vector_store, self.bm25_index, self.embeddings)
        self.summarizer = SummarizerEngine(self.llm_manager)
        
        if session_factory is _UNSET:
            self.SessionLocal = get_session_factory()
        else:
            self.SessionLocal = session_factory
        
        # In-memory document registry for lightweight usage (no DB)
        self._documents: List[KnowledgeDocument] = []
        
    @property
    def documents(self) -> List[KnowledgeDocument]:
        """Return in-memory document list. Use get_documents_from_db() for DB query."""
        return list(self._documents)

    def get_documents_from_db(self) -> List[DBKnowledgeDocument]:
        """Query the database for persisted documents."""
        db = self.SessionLocal()
        try:
            return db.query(DBKnowledgeDocument).all()
        finally:
            db.close()
            
    async def add_document(self, title: str, text: str, persist_to_db: bool = True) -> KnowledgeDocument:
        """Indexes a document and adds it to both stores."""
        doc = await self.indexer.index_text(title, text)
        
        # Track in-memory
        self._documents.append(doc)
        
        if persist_to_db:
            db = self.SessionLocal()
            try:
                db_doc = DBKnowledgeDocument(
                    id=doc.id,
                    title=doc.title,
                    source_type=doc.source_type,
                    metadata_json=doc.metadata
                )
                db.add(db_doc)
                db.commit()
            finally:
                db.close()
        
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
        # First check in-memory documents for chunks
        for doc in self._documents:
            if doc.id == doc_id and doc.chunks:
                texts = [c.content for c in doc.chunks]
                return await self.summarizer.summarize_chunks(texts)
        
        # Fallback to DB query
        db = self.SessionLocal()
        try:
            from app.models.knowledge import KnowledgeChunk as DBKnowledgeChunk
            chunks = db.query(DBKnowledgeChunk).filter(DBKnowledgeChunk.document_id == doc_id).order_by(DBKnowledgeChunk.position_index).all()
            if not chunks:
                raise ValueError(f"Document {doc_id} not found or has no chunks")
                
            texts = [c.content for c in chunks]
            return await self.summarizer.summarize_chunks(texts)
        finally:
            db.close()
