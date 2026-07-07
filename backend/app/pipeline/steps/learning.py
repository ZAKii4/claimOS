from app.engines.base import EngineStatus
from app.learning.manager import LearningManager


class LearningStep:
    """
    Pipeline step that hooks into the end of the process.
    If the document was reviewed or auto-approved, we can collect learning data.
    """
    
    def __init__(self):
        self.manager = LearningManager()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Learning step to collect any potential feedback.
        In a real scenario, this step might be async or triggered by an Event Bus
        when a ReviewSession is finalized, but here we can mock the ingestion.
        """
        # MVP: Attempt to find if there is a review session data in context to learn from
        review_session_data = context.get("completed_review_session")
        audit_logs = context.get("review_audits", [])
        
        if review_session_data and audit_logs:
            try:
                # 1. Collect
                samples = self.manager.process_review_session(review_session_data, audit_logs)
                
                # 2. Build and export
                if samples:
                    metadata = self.manager.build_and_export_datasets(samples)
                    context["learning_datasets_created"] = {k: v.model_dump() for k, v in metadata.items()}
            except Exception as e:
                # Non-blocking
                context["learning_errors"] = str(e)
                
        return context
