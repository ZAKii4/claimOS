import time
import uuid

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.validation.report import ValidationReport

from app.engines.decision.context import DecisionContext
from app.engines.decision.policy import BusinessPolicies
from app.engines.decision.models import DecisionResult, DecisionType, QueueName
from app.engines.decision.registry import StrategyRegistry
from app.engines.decision.decision_tree import DecisionTree
from app.engines.decision.scoring import RiskEngine
from app.engines.decision.routing import RoutingEngine
from app.engines.decision.sla import SLAEngine
from app.engines.decision.confidence import ConfidenceEngine
from app.engines.decision.audit import AuditLogger


class DecisionEngine(BaseEngine):
    """
    Enterprise Decision Engine Manager.
    """

    def __init__(self):
        self.registry = StrategyRegistry()
        self.registry.discover_strategies()
        self.decision_tree = DecisionTree(self.registry)

    @property
    def name(self) -> str:
        return "decision_engine"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return len(self.registry.get_strategies()) > 0

    def process(self, context: EngineContext) -> EngineResult:
        start_time = time.time()
        
        try:
            val_data = context.input_data.get("validation_report")
            graph_data = context.input_data.get("evidence_graph_result")
            
            if not val_data or not graph_data:
                return self._create_failure("validation_report and evidence_graph_result are required.")
                
            validation_report = ValidationReport(**val_data) if isinstance(val_data, dict) else val_data
            graph_result = EvidenceGraphResult(**graph_data) if isinstance(graph_data, dict) else graph_data
            
            decision_context = DecisionContext(
                claim_id=str(context.claim_id),
                evidence_graph=graph_result,
                validation_report=validation_report,
                policies=BusinessPolicies()  # In production, load from DB
            )
            
            # 1. Compute Risk
            decision_context.computed_risk_level = RiskEngine.evaluate(decision_context)
            
            # 2. Evaluate Strategies via Tree
            strategy = self.decision_tree.evaluate(decision_context)
            
            if strategy:
                decision = strategy.get_decision(decision_context)
                reason = strategy.get_reason()
                explanations = strategy.get_explanations(decision_context)
                applied_rules = strategy.get_applied_rules()
                strategy_name = strategy.name
            else:
                # Default fallback Strategy
                decision = DecisionType.HUMAN_REVIEW
                reason = "No specific strategy matched, defaulting to human review."
                explanations = ["Fallback due to lack of confident automated decision paths."]
                applied_rules = ["fallback"]
                strategy_name = "FallbackStrategy"
            
            # 3. Compute Routing
            queue = RoutingEngine.route(decision, decision_context)
            
            # 4. Compute SLA
            priority, sla_hours = SLAEngine.calculate(decision, decision_context)
            
            # 5. Compute Confidence
            confidence = ConfidenceEngine.calculate(decision_context)
            
            # 6. Generate Audit Log
            audit_entry = AuditLogger.log_decision(
                strategy_name=strategy_name,
                decision=decision,
                reason=reason,
                policy_version=decision_context.policies.version,
                applied_rules=applied_rules
            )
            
            # 7. Construct Result
            exec_time = int((time.time() - start_time) * 1000)
            result_obj = DecisionResult(
                decision_id=str(uuid.uuid4()),
                claim_id=str(context.claim_id),
                decision=decision,
                reason=reason,
                confidence=confidence,
                explanations=explanations,
                applied_rules=applied_rules,
                routing=queue,
                priority=priority,
                sla_deadline_hours=sla_hours,
                audit_entries=[audit_entry],
                risk_level=decision_context.computed_risk_level,
                execution_time_ms=exec_time
            )
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data={"decision_result": result_obj.model_dump(mode='json')},
                confidence=confidence,
                processing_time_ms=exec_time,
                errors=[]
            )

        except Exception as e:
            return self._create_failure(str(e))

    def _create_failure(self, error_msg: str) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.FAILURE,
            errors=[error_msg]
        )
