import re
from typing import Any

from app.config.settings import get_settings
from app.graph.neo4j_repository import graph_repo
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message
from app.vector.repository import vector_repo
from app.vector.similarity_engine import similarity_engine

# Reuses the same patterns as the real extraction engine's regex extractors
# (app/engines/extraction/extractors/*) to spot known entity formats in a raw
# query, without requiring a full OCR/layout/classification pipeline run.
_PLATE_PATTERN = re.compile(
    r"\b([A-Z]{2}[\s\-]?[0-9]{3}[\s\-]?[A-Z]{2}|[0-9]{1,4}[\s\-]?[A-Z]{2,3}[\s\-]?[0-9]{2,4})\b",
    re.IGNORECASE,
)
_POLICY_PATTERN = re.compile(r"\b([A-Z]{2,4}[\-/]?\d{6,12})\b", re.IGNORECASE)

MAX_GRAPH_NODES = 25


class EnterpriseHybridRAG:
    """Fuses vector search (pgvector) and graph search (Neo4j) into one
    context, then asks a real LLM to answer grounded in it."""

    def __init__(self, llm_manager: LLMManager | None = None):
        self.llm = llm_manager or LLMManager()

    @staticmethod
    def _extract_query_entities(query: str) -> list[str]:
        """Pulls known-format identifiers (plates, policy numbers) out of the query."""
        matches = _PLATE_PATTERN.findall(query) + _POLICY_PATTERN.findall(query)
        return [m.strip() for m in matches if m.strip()]

    async def retrieve_context(self, tenant_id: str, query: str) -> dict[str, Any]:
        # 1. Generate a real query embedding
        query_emb = await similarity_engine.generate_embedding(query)

        # 2. Vector Search (Semantic)
        vector_results = await vector_repo.search_similar(tenant_id, query_emb, top_k=3)

        # 3. Graph Search (Relationships): filter by any identifiers found in the
        # query rather than unconditionally dumping the entire graph.
        entities = self._extract_query_entities(query)
        if entities:
            graph_results = await graph_repo.run_query(
                "MATCH (n) WHERE any(prop IN keys(n) WHERE n[prop] IN $entities) "
                f"RETURN n LIMIT {MAX_GRAPH_NODES}",
                {"entities": entities},
            )
        else:
            graph_results = await graph_repo.run_query(
                f"MATCH (n) RETURN n LIMIT {MAX_GRAPH_NODES}"
            )

        # 4. Fusion
        context_parts = [f"Document ({v['score']:.2f}): {v['text']}" for v in vector_results]
        context_parts.append(f"Graph Entities: {len(graph_results)} found.")

        return {
            "query": query,
            "context": "\n".join(context_parts),
            "vector_sources": len(vector_results),
            "graph_sources": len(graph_results),
        }

    async def generate_answer(self, tenant_id: str, query: str) -> dict[str, Any]:
        """Retrieves hybrid context and asks a real LLM to answer grounded in it."""
        context = await self.retrieve_context(tenant_id, query)
        context_text = context["context"] or "(no matching context found)"

        request = LLMRequest(
            model=get_settings().OLLAMA_DEFAULT_MODEL,
            messages=[
                Message(
                    role="system",
                    content=(
                        "Answer the user's question using ONLY the retrieved context "
                        "below. If the context doesn't contain enough information, "
                        "say so explicitly rather than guessing."
                    ),
                ),
                Message(
                    role="user",
                    content=f"Context:\n{context_text}\n\nQuestion: {query}",
                ),
            ],
            temperature=0.2,
        )
        response = await self.llm.generate(request)

        return {**context, "answer": response.choices[0].content}


hybrid_rag = EnterpriseHybridRAG()
