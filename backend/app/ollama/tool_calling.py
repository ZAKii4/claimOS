import json
from typing import Dict, Any

from app.core.database import get_session_factory
from app.services.validation_service import ValidationService
from app.graph.neo4j_repository import graph_repo
import asyncio

class ToolCallingEngine:
    """
    Parses LLM responses for Tool Calls and routes them to internal systems.
    """
    def __init__(self):
        self.tool_usage_logs = []

    def detect_and_execute_tools(self, llm_response: str) -> Dict[str, Any]:
        """
        Extracts <tool_call> tags and executes the mapped functions.
        """
        if "<tool_call>" in llm_response:
            try:
                start = llm_response.find("<tool_call>") + 11
                end = llm_response.find("</tool_call>")
                tool_data = json.loads(llm_response[start:end])
                
                tool_name = tool_data.get("name")
                tool_args = tool_data.get("args", {})
                
                if hasattr(self, f"call_{tool_name}"):
                    method = getattr(self, f"call_{tool_name}")
                    result = method(**tool_args)
                    self.tool_usage_logs.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "status": "success"
                    })
                    return {"status": "executed", "tool": tool_name, "result": result}
                else:
                    return {"status": "error", "error": f"Tool {tool_name} not found"}
            except Exception as e:
                self.tool_usage_logs.append({"status": "error", "error": str(e)})
                return {"status": "error", "error": str(e)}
                
        return {"status": "no_tools_found"}

    def call_hybrid_rag(self, query: str, **kwargs):
        # We will connect this to KnowledgeManager after it's fully implemented with PgVector
        return f"Executing RAG query: {query}. (PgVector integration pending)"
        
    def call_decision_engine(self, claim_id: str, **kwargs):
        from uuid import UUID
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            service = ValidationService(db)
            report = service.get_validation_report(UUID(claim_id))
            return f"Validation decision: {report.get('decision')} with {len(report.get('issues', []))} issues."
        except Exception as e:
            return f"Error executing decision engine: {str(e)}"
        finally:
            db.close()
        
    def call_knowledge_graph(self, entity_id: str, **kwargs):
        try:
            query = "MATCH (n)-[r]-(m) WHERE n.id = $id RETURN type(r) as rel, m.id as linked_id"
            
            try:
                loop = asyncio.get_running_loop()
                # Already in an event loop — cannot block
                return f"Knowledge graph query for {entity_id} dispatched."
            except RuntimeError:
                # No running event loop — safe to use asyncio.run()
                records = asyncio.run(graph_repo.run_query(query, {"id": entity_id}))
                return f"Graph connections for {entity_id}: {len(records)} linked entities found."
        except Exception as e:
            return f"Error executing knowledge graph: {str(e)}"

tool_calling_engine = ToolCallingEngine()
