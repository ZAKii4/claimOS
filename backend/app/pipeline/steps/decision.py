from app.engines.base import EngineContext, EngineStatus
from app.engines.decision.manager import DecisionEngine


class DecisionStep:
    """
    Pipeline step that evaluates Validation Reports and Evidence Graphs 
    to make automated decisions about the claim.
    """
    
    def __init__(self):
        self.engine = DecisionEngine()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Decision step on the provided pipeline context.
        """
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "evidence_graph_result": context.get("evidence_graph_result"),
                "validation_report": context.get("validation_report")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            decision_data = result.output_data.get("decision_result")
            context["decision_result"] = decision_data
            
            # Phase 12 Integration: Route to Review Inbox if needed
            from app.engines.decision.models import DecisionType
            if decision_data.get("decision") in [DecisionType.HUMAN_REVIEW.value, DecisionType.FRAUD_REVIEW.value]:
                try:
                    from app.review.database import SessionLocal, engine, Base
                    from app.review.review_models import ReviewSession
                    from app.review.review_schemas import ReviewSessionCreate
                    from app.review.review_repository import ReviewRepository
                    from datetime import datetime, timedelta
                    
                    # Ensure tables exist for MVP sqlite
                    Base.metadata.create_all(bind=engine)
                    
                    db = SessionLocal()
                    repo = ReviewRepository(db)
                    
                    # Avoid duplicates
                    existing = repo.get_session(context.get("claim_id"))
                    if not existing:
                        repo.create_session(ReviewSessionCreate(
                            claim_id=context.get("claim_id"),
                            queue_name=decision_data.get("routing"),
                            priority=decision_data.get("priority", 0),
                            sla_deadline=datetime.utcnow() + timedelta(hours=decision_data.get("sla_deadline_hours", 48)),
                            evidence_graph=context.get("evidence_graph_result"),
                            validation_report=context.get("validation_report"),
                            decision_reason=decision_data.get("reason", "")
                        ))
                    db.close()
                except Exception as e:
                    # Non-blocking for the pipeline, but logged
                    print(f"Failed to create ReviewSession: {e}")
                    
        else:
            context["decision_result"] = None
            context["decision_errors"] = result.errors
            
        return context
