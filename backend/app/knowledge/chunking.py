import uuid
from typing import List, Optional
from app.knowledge.models import KnowledgeDocument, KnowledgeChunk


class ChunkingEngine:
    """Handles different document splitting strategies."""
    
    @staticmethod
    def fixed_size_chunking(
        doc_id: str, 
        text: str, 
        chunk_size: int = 500, 
        overlap: int = 50,
        page_number: Optional[int] = None
    ) -> List[KnowledgeChunk]:
        """Simple sliding window chunking by characters."""
        chunks = []
        if not text:
            return chunks
            
        start = 0
        position = 0
        while start < len(text):
            end = start + chunk_size
            chunk_content = text[start:end]
            
            chunks.append(
                KnowledgeChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    content=chunk_content.strip(),
                    page_number=page_number,
                    position_index=position
                )
            )
            start += (chunk_size - overlap)
            position += 1
            
        return chunks
        
    @staticmethod
    def semantic_chunking(doc_id: str, text: str) -> List[KnowledgeChunk]:
        """Mock: would normally split by semantic meaning or paragraphs."""
        paragraphs = text.split("\n\n")
        chunks = []
        for i, p in enumerate(paragraphs):
            if p.strip():
                chunks.append(
                    KnowledgeChunk(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        content=p.strip(),
                        position_index=i
                    )
                )
        return chunks
