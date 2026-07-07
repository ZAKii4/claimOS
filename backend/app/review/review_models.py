from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.review.database import Base


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String, unique=True, index=True)
    status = Column(String, default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED
    queue_name = Column(String)  # HUMAN_REVIEW, FRAUD, etc.
    priority = Column(Integer, default=0)
    sla_deadline = Column(DateTime)
    
    # Locking
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
    
    # Payload
    evidence_graph = Column(JSON)
    validation_report = Column(JSON)
    decision_reason = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audits = relationship("ReviewAudit", back_populates="session", cascade="all, delete-orphan")


class ReviewAudit(Base):
    __tablename__ = "review_audits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("review_sessions.id"))
    actor = Column(String)
    action = Column(String)  # CORRECTED_BBOX, CHANGED_CLASS, APPROVED, REJECTED
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ReviewSession", back_populates="audits")
