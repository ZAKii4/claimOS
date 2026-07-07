import uuid
from typing import List
from datetime import datetime
from app.learning.models import LearningSample


class FeedbackCollector:
    def extract_from_audit(self, review_session_data: dict, audit_logs: List[dict]) -> List[LearningSample]:
        """
        Extracts LearningSamples from a finalized ReviewSession and its Audit Trail.
        """
        samples = []
        claim_id = review_session_data.get("claim_id")
        review_id = review_session_data.get("id")
        
        for audit in audit_logs:
            # Map action to a machine learning task type
            task_type = "UNKNOWN"
            if "BBOX" in audit.get("action", "") or "OCR" in audit.get("action", ""):
                task_type = "OCR"
            elif "CLASS" in audit.get("action", ""):
                task_type = "CLASSIFICATION"
            elif "ENTITY" in audit.get("action", ""):
                task_type = "EXTRACTION"
            elif "APPROVE" in audit.get("action", "") or "REJECT" in audit.get("action", ""):
                task_type = "DECISION"
                
            if task_type == "UNKNOWN":
                continue
                
            sample = LearningSample(
                id=str(uuid.uuid4()),
                claim_id=claim_id,
                document_id=audit.get("document_id", "N/A"),
                review_id=review_id,
                task_type=task_type,
                input_data={"context": "Derived from audit"}, # Real implementation would fetch raw image/text
                expected_output=audit.get("old_value", {}),
                corrected_output=audit.get("new_value", {}),
                confidence=0.5, # Placeholder, should be fetched from original prediction
                operator=audit.get("actor", "SYSTEM"),
                processing_time_ms=0, # Optional: track how long the operator spent
                created_at=datetime.utcnow()
            )
            samples.append(sample)
            
        return samples
