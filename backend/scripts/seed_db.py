import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import get_session_factory
from app.models.lookups import ClaimStatus, ClaimType, PartyRole, DocumentType
from app.models.claim import ClaimFile
from app.models.validation import ValidationDecision

def seed_database():
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        print("Cleaning existing data...")
        db.execute(text("TRUNCATE TABLE validation_decision, claim_file, claim_type, claim_status CASCADE;"))
        db.commit()

        print("Seeding lookups...")
        
        # 1. Claim Status
        status_pending = ClaimStatus(id=uuid.uuid4(), code="PENDING_REVIEW", is_terminal=False)
        status_approved = ClaimStatus(id=uuid.uuid4(), code="APPROVED", is_terminal=True)
        status_fraud = ClaimStatus(id=uuid.uuid4(), code="FRAUD_ALERT", is_terminal=False)
        status_processing = ClaimStatus(id=uuid.uuid4(), code="PROCESSING", is_terminal=False)
        status_rejected = ClaimStatus(id=uuid.uuid4(), code="REJECTED", is_terminal=True)
        
        db.add_all([status_pending, status_approved, status_fraud, status_processing, status_rejected])

        # 2. Claim Type
        type_water = ClaimType(id=uuid.uuid4(), code="WATER_DAMAGE", label_fr="Dégât des eaux", label_ar="أضرار المياه")
        type_car = ClaimType(id=uuid.uuid4(), code="CAR_ACCIDENT", label_fr="Accident Auto", label_ar="حادث سيارة")
        type_fire = ClaimType(id=uuid.uuid4(), code="FIRE", label_fr="Incendie", label_ar="حريق")
        type_theft = ClaimType(id=uuid.uuid4(), code="THEFT", label_fr="Vol", label_ar="سرقة")
        
        db.add_all([type_water, type_car, type_fire, type_theft])

        db.commit()

        print("Seeding claims and metrics...")
        # 3. Create mock claims
        claims = []
        for i, (type_obj, status_obj) in enumerate([
            (type_water, status_pending),
            (type_car, status_approved),
            (type_theft, status_fraud),
            (type_fire, status_processing),
            (type_water, status_approved),
            (type_car, status_rejected)
        ]):
            c = ClaimFile(
                id=uuid.uuid4(),
                external_ref=f"CLM-2026-890{i+1}",
                claim_type_id=type_obj.id,
                status_id=status_obj.id,
                date_of_loss=datetime.now(timezone.utc) - timedelta(days=i+5),
                date_received=datetime.now(timezone.utc) - timedelta(days=i),
                composite_confidence=0.98 - (i * 0.1),
                stp_eligible=(i % 2 == 0)
            )
            claims.append(c)
        db.add_all(claims)
        db.commit()

        # 4. Create mock validation decisions for metrics
        decisions = []
        for i, c in enumerate(claims):
            decision_code = 'STP_APPROVED' if i % 2 == 0 else 'REJECTED' if i == 5 else 'HITL_REVIEW'
            decided_by = 'AI_ENGINE' if decision_code == 'STP_APPROVED' else 'HUMAN_OPERATOR'
            d = ValidationDecision(
                id=uuid.uuid4(),
                claim_id=c.id,
                decision=decision_code,
                decided_by=decided_by,
                decided_at=datetime.now(timezone.utc),
                composite_confidence=0.9
            )
            decisions.append(d)
            
        db.add_all(decisions)
        db.commit()

        print("Database seeded successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
