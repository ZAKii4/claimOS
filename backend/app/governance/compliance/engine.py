from typing import List, Dict
from app.governance.models import ComplianceCheck, ComplianceStatus


class ComplianceEngine:
    """Automatic compliance evaluation against regulatory frameworks."""

    @classmethod
    def evaluate_all(cls, context: Dict) -> List[ComplianceCheck]:
        """Run all framework checks."""
        checks: List[ComplianceCheck] = []
        checks.extend(cls._check_rgpd(context))
        checks.extend(cls._check_iso27001(context))
        checks.extend(cls._check_soc2(context))
        checks.extend(cls._check_nis2(context))
        return checks

    @classmethod
    def _check_rgpd(cls, ctx: Dict) -> List[ComplianceCheck]:
        checks = []

        # Data minimization
        checks.append(ComplianceCheck(
            framework="RGPD",
            control="Data Minimization",
            status=ComplianceStatus.PASS if ctx.get("pii_masked", False) else ComplianceStatus.FAIL,
            justification="PII must be masked before LLM processing" if not ctx.get("pii_masked") else "PII is masked",
        ))

        # Right to erasure
        checks.append(ComplianceCheck(
            framework="RGPD",
            control="Right to Erasure",
            status=ComplianceStatus.PASS if ctx.get("retention_policy_defined", False) else ComplianceStatus.WARNING,
            justification="Retention policy ensures data lifecycle management",
        ))

        # Consent
        checks.append(ComplianceCheck(
            framework="RGPD",
            control="Consent Management",
            status=ComplianceStatus.PASS if ctx.get("consent_recorded", False) else ComplianceStatus.FAIL,
            justification="User consent must be recorded",
        ))

        return checks

    @classmethod
    def _check_iso27001(cls, ctx: Dict) -> List[ComplianceCheck]:
        checks = []

        checks.append(ComplianceCheck(
            framework="ISO27001",
            control="Encryption at Rest",
            status=ComplianceStatus.PASS if ctx.get("encryption_enabled", False) else ComplianceStatus.FAIL,
            justification="Data must be encrypted at rest",
        ))

        checks.append(ComplianceCheck(
            framework="ISO27001",
            control="Access Control",
            status=ComplianceStatus.PASS if ctx.get("rbac_enabled", False) else ComplianceStatus.FAIL,
            justification="RBAC must be enforced",
        ))

        return checks

    @classmethod
    def _check_soc2(cls, ctx: Dict) -> List[ComplianceCheck]:
        return [ComplianceCheck(
            framework="SOC2",
            control="Audit Logging",
            status=ComplianceStatus.PASS if ctx.get("audit_enabled", False) else ComplianceStatus.FAIL,
            justification="All actions must be logged in the audit chain",
        )]

    @classmethod
    def _check_nis2(cls, ctx: Dict) -> List[ComplianceCheck]:
        return [ComplianceCheck(
            framework="NIS2",
            control="Incident Response",
            status=ComplianceStatus.PASS if ctx.get("alerts_enabled", False) else ComplianceStatus.WARNING,
            justification="Alert engine must be active for incident detection",
        )]
