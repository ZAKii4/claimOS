from typing import List, Dict, Any
from app.simulation.models import (
    DigitalTwin, ExplanationReport, DecisionPathNode,
    RuleImpact, ConfidenceBreakdown,
)


class ExplainerEngine:
    """
    Explainable AI engine.
    Generates human-readable, fully traceable explanations for every decision.
    """

    @classmethod
    def explain_decision(cls, twin: DigitalTwin) -> ExplanationReport:
        """Build a complete explanation report for a claim's decision."""
        decision = twin.decision_report.get("decision", "UNKNOWN")
        claim_id = twin.claim_id

        # 1. Decision Path
        path = cls._build_decision_path(twin)

        # 2. Rules executed
        rules = cls._build_rule_impacts(twin)

        # 3. Confidence Breakdown
        breakdown = cls._build_confidence_breakdown(twin)

        # 4. Evidence sources
        evidence = cls._collect_evidence(twin)

        # 5. Mermaid Graph
        mermaid = cls._generate_decision_graph(path, decision)

        return ExplanationReport(
            claim_id=claim_id,
            decision=decision,
            decision_path=path,
            rules_executed=rules,
            confidence_breakdown=breakdown,
            evidence_sources=evidence,
            mermaid_graph=mermaid,
        )

    # ── Decision Path ─────────────────────────────────

    @classmethod
    def _build_decision_path(cls, twin: DigitalTwin) -> List[DecisionPathNode]:
        """Reconstruct the sequential steps that led to the decision."""
        path: List[DecisionPathNode] = []

        # IQA
        iqa = twin.metrics.get("iqa_score", 0.0)
        path.append(DecisionPathNode(step="Image Quality", value=f"{iqa:.2f}", confidence=iqa))

        # OCR
        ocr = twin.metrics.get("ocr_confidence", 0.0)
        path.append(DecisionPathNode(step="OCR", value=f"{ocr:.2f}", confidence=ocr))

        # Classification
        doc_type = twin.metrics.get("document_type", "unknown")
        cls_conf = twin.metrics.get("classification_confidence", 0.0)
        path.append(DecisionPathNode(step="Classification", value=str(doc_type), confidence=cls_conf))

        # Extraction
        entity_count = twin.metrics.get("entity_count", 0)
        ext_conf = twin.metrics.get("extraction_confidence", 0.0)
        path.append(DecisionPathNode(step="Extraction", value=f"{entity_count} entities", confidence=ext_conf))

        # Validation
        val_score = twin.validation_report.get("score", 0.0)
        warnings = twin.validation_report.get("warnings", 0)
        path.append(DecisionPathNode(step="Validation", value=f"score={val_score:.2f}, {warnings} warnings", confidence=val_score))

        # Risk
        risk = twin.decision_report.get("risk_level", "UNKNOWN")
        path.append(DecisionPathNode(step="Risk Assessment", value=risk, confidence=0.0))

        # Decision
        decision = twin.decision_report.get("decision", "UNKNOWN")
        path.append(DecisionPathNode(step="Decision", value=decision, confidence=0.0))

        return path

    # ── Rule Impacts ──────────────────────────────────

    @classmethod
    def _build_rule_impacts(cls, twin: DigitalTwin) -> List[RuleImpact]:
        """List all rules that were evaluated and their impact."""
        rules: List[RuleImpact] = []
        val_rules = twin.validation_report.get("rules", [])

        for r in val_rules:
            rules.append(RuleImpact(
                rule_name=r.get("name", "unnamed"),
                result=r.get("result", "UNKNOWN"),
                weight=r.get("weight", 1.0),
                impact_on_decision=r.get("impact", ""),
                evidence_ref=r.get("evidence_ref"),
            ))

        return rules

    # ── Confidence Breakdown ──────────────────────────

    @classmethod
    def _build_confidence_breakdown(cls, twin: DigitalTwin) -> ConfidenceBreakdown:
        m = twin.metrics
        scores = ConfidenceBreakdown(
            ocr=m.get("ocr_confidence", 0.0),
            iqa=m.get("iqa_score", 0.0),
            classification=m.get("classification_confidence", 0.0),
            extraction=m.get("extraction_confidence", 0.0),
            validation=twin.validation_report.get("score", 0.0),
            risk=m.get("risk_score", 0.0),
            decision=m.get("decision_confidence", 0.0),
            consensus=m.get("consensus_score", 0.0),
        )
        values = [scores.ocr, scores.iqa, scores.classification,
                  scores.extraction, scores.validation]
        non_zero = [v for v in values if v > 0]
        scores.global_score = sum(non_zero) / len(non_zero) if non_zero else 0.0
        return scores

    # ── Evidence Collection ───────────────────────────

    @classmethod
    def _collect_evidence(cls, twin: DigitalTwin) -> List[Dict[str, Any]]:
        """Collect all evidence sources linked to the decision."""
        sources: List[Dict[str, Any]] = []
        for doc in twin.documents:
            sources.append({
                "document_id": doc.get("id", ""),
                "type": doc.get("type", ""),
                "page": doc.get("page", 1),
                "provenance": doc.get("provenance", "pipeline"),
            })
        return sources

    # ── Decision Graph (Mermaid) ──────────────────────

    @classmethod
    def _generate_decision_graph(cls, path: List[DecisionPathNode], final_decision: str) -> str:
        """Generate a Mermaid flowchart of the decision path."""
        lines = ["graph TD"]
        prev_id = None

        for i, node in enumerate(path):
            node_id = f"step_{i}"
            label = f"{node.step}: {node.value}"
            lines.append(f'    {node_id}["{label}"]')
            if prev_id:
                lines.append(f"    {prev_id} --> {node_id}")
            prev_id = node_id

        return "\n".join(lines)
