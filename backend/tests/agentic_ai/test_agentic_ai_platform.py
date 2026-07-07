import pytest
from app.agentic_ai.core.registry import AgentRegistry, AgentProfile
from app.agentic_ai.core.supervisor import SupervisorEngine
from app.agentic_ai.core.tools import LocalToolEngine
from app.agentic_ai.cognitive.compression import ContextCompressionEngine
from app.agentic_ai.cognitive.evaluation import EvaluationEngine, EvaluationScore
from app.agentic_ai.cognitive.prompts import PromptRepository, PromptVersion


# ────────────────────────────────────────────────────────
# 1. Agent Registry (10 tests)
# ────────────────────────────────────────────────────────

def test_registry_list_agents():
    agents = AgentRegistry.list_agents()
    assert len(agents) >= 6
    names = [a.name for a in agents]
    assert "OCRAgent" in names
    assert "SupervisorAgent" in names


def test_registry_get_agent_exists():
    agent = AgentRegistry.get_agent("ExtractionAgent")
    assert agent is not None
    assert agent.model_name == "qwen-2.5"
    assert agent.specialty == "Extraction"


def test_registry_get_agent_missing():
    assert AgentRegistry.get_agent("UnknownAgent") is None


def test_registry_register_agent():
    new_agent = AgentProfile(
        name="TestAgent", model_name="test-model", role="Tester",
        allowed_tools=["Testing"], max_context_tokens=100,
        temperature=0.0, specialty="Test", autonomy_level="LOW"
    )
    AgentRegistry.register_agent(new_agent)
    assert AgentRegistry.get_agent("TestAgent") is not None


def test_registry_agent_profile_init():
    p = AgentProfile(name="A", model_name="M", role="R", allowed_tools=[], max_context_tokens=100, temperature=0.1, specialty="S", autonomy_level="A")
    assert p.name == "A"


def test_registry_fraud_agent_properties():
    agent = AgentRegistry.get_agent("FraudAgent")
    assert agent.temperature == 0.3
    assert "Analytics" in agent.allowed_tools


def test_registry_decision_agent_properties():
    agent = AgentRegistry.get_agent("DecisionAgent")
    assert agent.max_context_tokens == 128000
    assert agent.model_name == "llama-3.1"


def test_registry_supervisor_agent_properties():
    agent = AgentRegistry.get_agent("SupervisorAgent")
    assert "All" in agent.allowed_tools


def test_registry_ocr_agent_properties():
    agent = AgentRegistry.get_agent("OCRAgent")
    assert agent.model_name == "phi-4"


def test_registry_reset_no_op():
    # Should not crash
    AgentRegistry._reset()


# ────────────────────────────────────────────────────────
# 2. Supervisor Engine (10 tests)
# ────────────────────────────────────────────────────────

def test_supervisor_build_team_simple():
    team = SupervisorEngine.build_team({"fraud_score": 10})
    assert "OCRAgent" in team
    assert "ExtractionAgent" in team
    assert "DecisionAgent" in team
    assert "FraudAgent" not in team
    assert "LegalAgent" not in team


def test_supervisor_build_team_fraud():
    team = SupervisorEngine.build_team({"fraud_score": 80})
    assert "FraudAgent" in team


def test_supervisor_build_team_legal():
    team = SupervisorEngine.build_team({"fraud_score": 10, "legal_complexity": True})
    assert "LegalAgent" in team
    assert "FraudAgent" not in team


def test_supervisor_build_team_all():
    team = SupervisorEngine.build_team({"fraud_score": 90, "legal_complexity": True})
    assert "FraudAgent" in team
    assert "LegalAgent" in team
    assert len(team) == 5  # OCR, Extraction, Fraud, Legal, Decision


def test_supervisor_orchestrate_safe_claim():
    res = SupervisorEngine.orchestrate({"fraud_score": 20})
    assert res["status"] == "COMPLETED"
    assert res["final_decision"] == "Approved"
    assert "FraudAgent" not in res["team_assembled"]


def test_supervisor_orchestrate_fraud_claim():
    res = SupervisorEngine.orchestrate({"fraud_score": 80})
    assert res["status"] == "COMPLETED"
    assert res["final_decision"] == "Rejected"
    assert "FraudAgent" in res["team_assembled"]


def test_supervisor_orchestrate_legal_fraud_claim():
    res = SupervisorEngine.orchestrate({"fraud_score": 60, "legal_complexity": True})
    assert "LegalAgent" in res["team_assembled"]
    assert "FraudAgent" in res["team_assembled"]
    assert res["final_decision"] == "Rejected"


def test_supervisor_orchestrate_validates_agents():
    # Since we mocked valid agents, it should pass
    res = SupervisorEngine.orchestrate({"fraud_score": 10})
    assert len(res["team_assembled"]) == 3


def test_supervisor_build_team_empty_context():
    team = SupervisorEngine.build_team({})
    assert len(team) == 3


def test_supervisor_build_team_none_context():
    # Simulating dictionary wrapper
    context = dict()
    team = SupervisorEngine.build_team(context)
    assert "DecisionAgent" in team


# ────────────────────────────────────────────────────────
# 3. Local Tool Engine (10 tests)
# ────────────────────────────────────────────────────────

def test_tool_engine_success():
    res = LocalToolEngine.invoke_tool("OCRAgent", "Pipeline", {})
    assert res["status"] == "SUCCESS"
    assert "Pipeline" in res["tool"]


def test_tool_engine_success_with_params():
    res = LocalToolEngine.invoke_tool("ExtractionAgent", "Knowledge Platform", {"query": "test"})
    assert res["status"] == "SUCCESS"
    assert "query" in res["result"]


def test_tool_engine_missing_agent():
    res = LocalToolEngine.invoke_tool("MissingAgent", "Pipeline", {})
    assert res["status"] == "ERROR"
    assert "not found" in res["message"]


def test_tool_engine_unregistered_tool():
    res = LocalToolEngine.invoke_tool("OCRAgent", "Hacking Tool", {})
    assert res["status"] == "ERROR"
    assert "not registered" in res["message"]


def test_tool_engine_unauthorized_tool():
    # OCRAgent is not allowed to use 'Simulation Engine'
    res = LocalToolEngine.invoke_tool("OCRAgent", "Simulation Engine", {})
    assert res["status"] == "ERROR"
    assert "not allowed" in res["message"]


def test_tool_engine_supervisor_all_tools():
    # SupervisorAgent has 'All' allowed tools
    res = LocalToolEngine.invoke_tool("SupervisorAgent", "Analytics Engine", {})
    assert res["status"] == "SUCCESS"


def test_tool_engine_fraud_agent_analytics():
    res = LocalToolEngine.invoke_tool("FraudAgent", "Analytics", {})
    assert res["status"] == "SUCCESS"


def test_tool_engine_fraud_agent_evidence():
    res = LocalToolEngine.invoke_tool("FraudAgent", "Evidence Graph", {})
    assert res["status"] == "SUCCESS"


def test_tool_engine_decision_agent_simulation():
    res = LocalToolEngine.invoke_tool("DecisionAgent", "Simulation", {})
    assert res["status"] == "SUCCESS"


def test_tool_engine_legal_agent_rag():
    res = LocalToolEngine.invoke_tool("LegalAgent", "Hybrid RAG", {})
    assert res["status"] == "SUCCESS"


# ────────────────────────────────────────────────────────
# 4. Context Compression Engine (10 tests)
# ────────────────────────────────────────────────────────

def test_compression_empty():
    res = ContextCompressionEngine.compress_context([], 1000)
    assert res == []


def test_compression_fits_all():
    items = [{"type": "EVIDENCE", "token_cost": 100}, {"type": "OBSERVATION", "token_cost": 100}]
    res = ContextCompressionEngine.compress_context(items, 500)
    assert len(res) == 2


def test_compression_priority_sorting():
    items = [
        {"type": "SYSTEM", "id": 1, "token_cost": 100},
        {"type": "OBSERVATION", "id": 2, "token_cost": 100},
        {"type": "EVIDENCE", "id": 3, "token_cost": 100}
    ]
    res = ContextCompressionEngine.compress_context(items, 500)
    assert res[0]["type"] == "EVIDENCE"
    assert res[1]["type"] == "OBSERVATION"
    assert res[2]["type"] == "SYSTEM"


def test_compression_truncates_over_budget():
    items = [
        {"type": "EVIDENCE", "token_cost": 200},
        {"type": "OBSERVATION", "token_cost": 200},
        {"type": "SYSTEM", "token_cost": 200}
    ]
    res = ContextCompressionEngine.compress_context(items, 300)
    assert len(res) == 2
    assert res[0]["type"] == "EVIDENCE"
    assert res[1]["type"] == "SUMMARY"


def test_compression_budget_zero():
    items = [{"type": "EVIDENCE", "token_cost": 100}]
    res = ContextCompressionEngine.compress_context(items, 0)
    assert len(res) == 1
    assert res[0]["type"] == "SUMMARY"


def test_compression_handles_missing_token_cost():
    items = [{"type": "EVIDENCE"}]  # defaults to 100
    res = ContextCompressionEngine.compress_context(items, 150)
    assert len(res) == 1
    assert res[0]["type"] == "EVIDENCE"


def test_compression_handles_missing_type():
    items = [{"id": 1}]  # defaults to SYSTEM
    res = ContextCompressionEngine.compress_context(items, 500)
    assert len(res) == 1
    assert res[0].get("type", "SYSTEM") == "SYSTEM"


def test_compression_large_budget():
    items = [{"type": "EVIDENCE", "token_cost": 100}] * 10
    res = ContextCompressionEngine.compress_context(items, 5000)
    assert len(res) == 10


def test_compression_summary_message():
    items = [{"type": "EVIDENCE", "token_cost": 200}, {"type": "OBSERVATION", "token_cost": 200}]
    res = ContextCompressionEngine.compress_context(items, 300)
    assert "Summarized 1 remaining items" in res[1]["content"]


def test_compression_strict_priority():
    items = [{"type": "SYSTEM", "token_cost": 100}, {"type": "EVIDENCE", "token_cost": 100}]
    res = ContextCompressionEngine.compress_context(items, 150)
    assert len(res) == 2
    assert res[0]["type"] == "EVIDENCE"
    assert res[1]["type"] == "SUMMARY"


# ────────────────────────────────────────────────────────
# 5. Evaluation Engine (8 tests)
# ────────────────────────────────────────────────────────

def test_evaluation_success():
    res = EvaluationEngine.evaluate_response("This is a valid response.", "context")
    assert res.is_acceptable is True
    assert res.hallucination < 0.1
    assert res.grounding > 0.9


def test_evaluation_error():
    res = EvaluationEngine.evaluate_response("I got an ERROR while processing.", "context")
    assert res.is_acceptable is False
    assert res.hallucination == 0.9
    assert res.json_validity == 0.0


def test_evaluation_score_model():
    s = EvaluationScore(faithfulness=1.0, grounding=1.0, hallucination=0.0, json_validity=1.0, is_acceptable=True)
    assert s.faithfulness == 1.0


def test_evaluation_error_case_insensitive():
    res = EvaluationEngine.evaluate_response("error occurred", "context")
    assert res.is_acceptable is False


def test_evaluation_success_faithfulness():
    res = EvaluationEngine.evaluate_response("valid", "context")
    assert res.faithfulness == 0.95


def test_evaluation_success_json_validity():
    res = EvaluationEngine.evaluate_response("{}", "context")
    assert res.json_validity == 1.0


def test_evaluation_error_grounding():
    res = EvaluationEngine.evaluate_response("ERROR", "context")
    assert res.grounding == 0.1


def test_evaluation_error_faithfulness():
    res = EvaluationEngine.evaluate_response("ERROR", "context")
    assert res.faithfulness == 0.1


# ────────────────────────────────────────────────────────
# 6. Prompt Repository (10 tests)
# ────────────────────────────────────────────────────────

def test_prompt_add_new():
    PromptRepository._reset()
    p = PromptRepository.add_prompt("AgentA", "You are A.", "v1")
    assert p.version_tag == "v1"
    assert p.is_active is True


def test_prompt_add_multiple_deactivates_old():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "You are A.", "v1")
    PromptRepository.add_prompt("AgentA", "You are A updated.", "v2")
    
    active = PromptRepository.get_active_prompt("AgentA")
    assert active.version_tag == "v2"


def test_prompt_get_active_missing_agent():
    PromptRepository._reset()
    assert PromptRepository.get_active_prompt("Missing") is None


def test_prompt_rollback_success():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    PromptRepository.add_prompt("AgentA", "2", "v2")
    
    success = PromptRepository.rollback_prompt("AgentA", "v1")
    assert success is True
    
    active = PromptRepository.get_active_prompt("AgentA")
    assert active.version_tag == "v1"


def test_prompt_rollback_fail():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    success = PromptRepository.rollback_prompt("AgentA", "v_unknown")
    assert success is False


def test_prompt_reset():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    PromptRepository._reset()
    assert PromptRepository.get_active_prompt("AgentA") is None


def test_prompt_version_model():
    p = PromptVersion(content="test", version_tag="v1")
    assert p.id is not None
    assert p.is_active is False


def test_prompt_get_active_no_active():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    PromptRepository._prompts["AgentA"][0].is_active = False
    assert PromptRepository.get_active_prompt("AgentA") is None


def test_prompt_rollback_multiple_prompts():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    PromptRepository.add_prompt("AgentA", "2", "v2")
    PromptRepository.add_prompt("AgentA", "3", "v3")
    PromptRepository.rollback_prompt("AgentA", "v2")
    active = PromptRepository.get_active_prompt("AgentA")
    assert active.version_tag == "v2"


def test_prompt_rollback_different_agents():
    PromptRepository._reset()
    PromptRepository.add_prompt("AgentA", "1", "v1")
    PromptRepository.add_prompt("AgentB", "1", "v1")
    PromptRepository.rollback_prompt("AgentA", "v1")
    assert PromptRepository.get_active_prompt("AgentB").version_tag == "v1"


# Total: 10 + 10 + 10 + 10 + 8 + 10 = 58 tests.
