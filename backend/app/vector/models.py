import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON
from pgvector.sqlalchemy import Vector
from app.persistence.base import Base

class DocumentEmbedding(Base):
    """
    Stores document chunks and their vector embeddings.
    """
    __tablename__ = "document_embeddings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=False)
    document_id = Column(String, index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(String, nullable=False)
    
    # 768 dimensions for nomic-embed or bge-m3, adjust if using larger models
    embedding = Column(Vector(768)) 
    
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
