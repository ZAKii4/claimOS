import time

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.extraction.models import ExtractionResult
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.evidence_graph.builder import GraphBuilder
from app.engines.evidence_graph.resolver import EntityResolver
from app.engines.evidence_graph.merger import GraphMerger
from app.engines.evidence_graph.reasoning import GraphReasoningEngine
from app.engines.evidence_graph.integrity import GraphIntegrityChecker
from app.engines.evidence_graph.confidence import GraphConfidenceScorer
from app.engines.evidence_graph.serialization import GraphSerializer


class EvidenceGraphEngine(BaseEngine):
    """
    Transforms extracted entities into a connected Knowledge Graph (Evidence Graph).
    """

    def __init__(self):
        self.builder = GraphBuilder()
        self.resolver = EntityResolver()
        self.merger = GraphMerger()
        self.reasoning = GraphReasoningEngine()
        self.integrity = GraphIntegrityChecker()
        self.scorer = GraphConfidenceScorer()
        self.serializer = GraphSerializer()

    @property
    def name(self) -> str:
        return "evidence_graph"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return True

    def process(self, context: EngineContext) -> EngineResult:
        start_time = time.time()
        
        try:
            extraction_data = context.input_data.get("extraction_result")
            
            if not extraction_data:
                return self._create_failure("extraction_result is required.")

            extraction_result = ExtractionResult(**extraction_data) if isinstance(extraction_data, dict) else extraction_data
            claim_id = str(context.claim_id)

            # 1. Build Initial Graph
            graph = self.builder.build(extraction_result, claim_id)
            
            # 2. Resolve & Merge duplicates (e.g. Same Vehicle Plate)
            duplicates = self.resolver.resolve_duplicates(graph)
            if duplicates:
                self.merger.merge(graph, duplicates)
                
            # 3. Apply Deterministic Reasoning (Infer relationships)
            self.reasoning.apply_rules(graph)
            
            # 4. Integrity Checks
            errors = self.integrity.check_integrity(graph)
            # In a real system we might log these or flag the claim for Human Review
            
            # 5. Calculate Graph Confidence
            global_confidence, stats = self.scorer.score_graph(graph)
            
            # Create Result
            result_obj = EvidenceGraphResult(
                claim_id=claim_id,
                nodes=graph.get_all_nodes(),
                edges=graph.get_all_edges(),
                statistics=stats,
                global_confidence=global_confidence,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            # Also attach the JSON and Mermaid representations for upstream consumption
            serialized_json = self.serializer.to_json(graph)
            mermaid_diagram = self.serializer.to_mermaid(graph)
            
            output_data = {
                "evidence_graph_result": result_obj.model_dump(mode='json'),
                "evidence_graph_json": serialized_json,
                "evidence_graph_mermaid": mermaid_diagram,
                "integrity_warnings": errors
            }
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data=output_data,
                confidence=global_confidence,
                processing_time_ms=result_obj.execution_time_ms,
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
