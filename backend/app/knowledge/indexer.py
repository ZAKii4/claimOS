import uuid
from typing import List
from app.knowledge.models import KnowledgeDocument, KnowledgeChunk
from app.knowledge.chunking import ChunkingEngine
from app.knowledge.embeddings import EmbeddingsEngine


class DocumentIndexer:
    """Parses raw content, chunks it, and generates embeddings."""
    
    def __init__(self, embeddings_engine: EmbeddingsEngine):
        self.embeddings_engine = embeddings_engine
        
    async def index_text(self, title: str, text: str, source_type: str = "txt") -> KnowledgeDocument:
        """End-to-end processing of a text document."""
        doc = KnowledgeDocument(
            id=str(uuid.uuid4()),
            title=title,
            source_type=source_type
        )
        
        # 1. Chunking
        chunks = ChunkingEngine.fixed_size_chunking(doc.id, text, chunk_size=200, overlap=20)
        
        # 2. Embeddings
        texts_to_embed = [c.content for c in chunks]
        vectors = await self.embeddings_engine.embed_texts(texts_to_embed)
        
        for chunk, vector in zip(chunks, vectors):
            chunk.vector = vector
            
        doc.chunks = chunks
        return doc
