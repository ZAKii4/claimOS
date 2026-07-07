from abc import ABC, abstractmethod
from typing import Optional

from app.engines.decision.context import DecisionContext
from app.engines.decision.models import DecisionType


class BaseDecisionStrategy(ABC):
    """
    Contract for Decision Strategies.
    Follows Strategy and Open/Closed Principles.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the strategy."""
        pass
        
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Priority of the strategy (higher runs first).
        e.g., Rejecting due to blocker (100) > Auto Approve (10)
        """
        pass
        
    @abstractmethod
    def evaluate(self, context: DecisionContext) -> bool:
        """
        Returns True if this strategy should trigger based on the context.
        """
        pass
        
    @abstractmethod
    def get_decision(self, context: DecisionContext) -> DecisionType:
        """
        Returns the actual decision enum if the strategy triggers.
        """
        pass
        
    @abstractmethod
    def get_reason(self) -> str:
        """
        Brief reason for this decision.
        """
        pass
        
    @abstractmethod
    def get_explanations(self, context: DecisionContext) -> list[str]:
        """
        Detailed list of reasons why this decision was taken.
        """
        pass
        
    @abstractmethod
    def get_applied_rules(self) -> list[str]:
        """
        Identifiers for the business rules this strategy checked.
        """
        pass
