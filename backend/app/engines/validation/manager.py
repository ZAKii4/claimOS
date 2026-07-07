import time

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.evidence_graph.models import EvidenceGraphResult

from app.engines.validation.registry import RuleRegistry
from app.engines.validation.rule_engine import RuleEngine as VRuleEngine
from app.engines.validation.context import ValidationContext
from app.engines.validation.severity import ValidationSeverity
from app.engines.validation.report import ValidationReport, ValidationSummary, ValidationStatistics


class ValidationEngine(BaseEngine):
    """
    Enterprise Validation Engine Manager.
    """

    def __init__(self):
        self.registry = RuleRegistry()
        self.registry.discover_rules()
        self.rule_engine = VRuleEngine(self.registry)

    @property
    def name(self) -> str:
        return "validation_engine"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return len(self.registry.get_all_rules()) > 0

    def process(self, context: EngineContext) -> EngineResult:
        start_time = time.time()
        
        try:
            graph_data = context.input_data.get("evidence_graph_result")
            if not graph_data:
                return self._create_failure("evidence_graph_result is required.")
                
            graph_result = EvidenceGraphResult(**graph_data) if isinstance(graph_data, dict) else graph_data
            
            validation_context = ValidationContext(
                claim_id=str(context.claim_id),
                evidence_graph=graph_result,
                raw_extraction_result=context.input_data.get("extraction_result")
            )
            
            # Execute Rules
            issues = self.rule_engine.execute(validation_context)
            
            # Compute Statistics
            stats = ValidationStatistics(
                total_rules_evaluated=len(self.registry.get_all_rules()),
                total_issues_found=len(issues)
            )
            
            has_blockers = False
            has_criticals = False
            
            for issue in issues:
                sev_name = issue.severity.name
                stats.issues_by_severity[sev_name] = stats.issues_by_severity.get(sev_name, 0) + 1
                stats.issues_by_category[issue.category] = stats.issues_by_category.get(issue.category, 0) + 1
                
                if issue.severity >= ValidationSeverity.BLOCKER:
                    has_blockers = True
                if issue.severity >= ValidationSeverity.CRITICAL:
                    has_criticals = True
                    
            # Compute Global Validation Score (Heuristic based on severities)
            penalty = (
                stats.issues_by_severity.get(ValidationSeverity.BLOCKER.name, 0) * 0.4 +
                stats.issues_by_severity.get(ValidationSeverity.CRITICAL.name, 0) * 0.2 +
                stats.issues_by_severity.get(ValidationSeverity.ERROR.name, 0) * 0.1 +
                stats.issues_by_severity.get(ValidationSeverity.WARNING.name, 0) * 0.02
            )
            
            global_score = max(0.0, 1.0 - penalty)
            is_valid = not has_blockers
            
            summary = ValidationSummary(
                is_valid=is_valid,
                global_score=round(global_score, 3),
                has_blockers=has_blockers,
                has_criticals=has_criticals
            )
            
            report = ValidationReport(
                claim_id=str(context.claim_id),
                summary=summary,
                statistics=stats,
                issues=issues,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data={"validation_report": report.model_dump(mode='json')},
                confidence=global_score,
                processing_time_ms=report.execution_time_ms,
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
