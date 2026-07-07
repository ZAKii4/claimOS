from app.engines.validation.registry import RuleRegistry
from app.engines.validation.context import ValidationContext
from app.engines.validation.report import ValidationIssue


class RuleEngine:
    """
    Executes all registered rules against a given context.
    """
    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def execute(self, context: ValidationContext) -> list[ValidationIssue]:
        issues = []
        rules = self.registry.get_all_rules()
        
        for rule in rules:
            if rule.is_applicable(context):
                try:
                    rule_issues = rule.validate(context)
                    if rule_issues:
                        issues.extend(rule_issues)
                except Exception as e:
                    # If a rule crashes, we capture it as an ENGINE error issue to not break the pipeline
                    from app.engines.validation.severity import ValidationSeverity
                    issues.append(
                        ValidationIssue(
                            rule_id="SYS_ERR",
                            rule_name="Rule Execution Error",
                            category="SYSTEM",
                            severity=ValidationSeverity.ERROR,
                            message=f"Rule {rule.name} failed to execute.",
                            explanation=str(e)
                        )
                    )
                    
        return issues
