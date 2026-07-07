from pydantic import BaseModel, Field


class BusinessPolicies(BaseModel):
    """
    Configuration object representing the business rules for decision making.
    This can easily be loaded from a JSON/YAML file or Database.
    """
    version: str = "1.0.0"
    
    # Auto-Approve Policies
    min_validation_score_for_auto_approve: float = Field(default=0.95, description="Min validation score for auto approval")
    allow_auto_approve_with_warnings: bool = Field(default=False, description="Whether warnings prevent auto-approval")
    
    # Fraud Policies
    max_fraud_alerts_before_review: int = Field(default=0, description="Max allowed fraud heuristic alerts")
    
    # Human Review Policies
    human_review_threshold: float = Field(default=0.70, description="Score below which a human review is forced")
    
    # Reject Policies
    reject_on_blocker: bool = Field(default=True, description="Instantly reject if there is a validation blocker")
    
    # Routing Policies
    default_expert_threshold: float = Field(default=0.60, description="Score below which we might route to a specific expert instead of general human review")
