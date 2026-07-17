import math
from typing import List, Dict
from app.knowledge.models import KnowledgeChunk, SearchResult


class BaseVectorStore:
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        pass
        
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        pass


from sqlalchemy.orm import Session
from app.core.database import get_session_factory
from app.models.knowledge import KnowledgeChunk as DBKnowledgeChunk

class PgVectorStore(BaseVectorStore):
    """PostgreSQL pgvector based vector store using cosine distance."""
    
    def __init__(self):
        self.SessionLocal = get_session_factory()
        
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        # This function might not be used directly if KnowledgeManager persists the chunks,
        # but if it is, we can update the vectors here.
        db = self.SessionLocal()
        try:
            for chunk in chunks:
                if chunk.vector:
                    db_chunk = db.query(DBKnowledgeChunk).filter(DBKnowledgeChunk.id == chunk.id).first()
                    if db_chunk:
                        db_chunk.vector_embedding = chunk.vector
                    else:
                        # Assuming document_id exists
                        db_chunk = DBKnowledgeChunk(
                            id=chunk.id,
                            document_id=chunk.document_id,
                            content=chunk.content,
                            page_number=chunk.page_number,
                            section_title=chunk.section_title,
                            position_index=chunk.position_index,
                            vector_embedding=chunk.vector,
                            metadata_json=chunk.metadata
                        )
                        db.add(db_chunk)
            db.commit()
        finally:
            db.close()
            
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        if not query_vector:
            return []
            
        db = self.SessionLocal()
        try:
            # Using cosine distance: 1 - cosine_distance = cosine similarity
            results = db.query(
                DBKnowledgeChunk, 
                DBKnowledgeChunk.vector_embedding.cosine_distance(query_vector).label('distance')
            ).order_by('distance').limit(top_k).all()
            
            search_results = []
            for db_chunk, distance in results:
                score = 1.0 - (distance or 0.0)
                chunk = KnowledgeChunk(
                    id=str(db_chunk.id),
                    document_id=str(db_chunk.document_id),
                    content=db_chunk.content,
                    page_number=db_chunk.page_number,
                    section_title=db_chunk.section_title,
                    position_index=db_chunk.position_index,
                    metadata=db_chunk.metadata_json,
                )
                search_results.append(SearchResult(chunk=chunk, score=score, vector_score=score))
                
            return search_results
        finally:
            db.close()
