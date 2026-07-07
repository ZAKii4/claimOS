from typing import Optional
from app.engines.decision.base_strategy import BaseDecisionStrategy
from app.engines.decision.registry import StrategyRegistry
from app.engines.decision.context import DecisionContext


class DecisionTree:
    """
    Orchestrates the evaluation of multiple strategies based on priority.
    """
    
    def __init__(self, registry: StrategyRegistry):
        self.registry = registry
        
    def evaluate(self, context: DecisionContext) -> Optional[BaseDecisionStrategy]:
        """
        Finds the highest priority strategy that evaluates to True.
        """
        for strategy in self.registry.get_strategies():
            if strategy.evaluate(context):
                return strategy
                
        return None
