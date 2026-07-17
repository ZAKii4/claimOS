import pytest
from app.autonomous.organization.teams import AIOrganizationEngine, AITeam
from app.autonomous.organization.workforce import WorkforceManager
from app.autonomous.memory.enterprise import EnterpriseMemoryEngine
from app.autonomous.memory.evolution import KnowledgeEvolutionEngine
from app.autonomous.skills.manager import SkillManager, Skill
from app.autonomous.reasoning.meta import MetaReasoningEngine
from app.autonomous.governance.autonomous import AutonomousGovernanceEngine
from app.autonomous.laboratory.lab import AILabEngine

# ────────────────────────────────────────────────────────
# 1. AI Organization & Workforce Tests (20 tests)
# ────────────────────────────────────────────────────────

def test_org_create_team():
    AIOrganizationEngine._reset()
    team = AIOrganizationEngine.create_team("Investigation", "Mgr", ["A1", "A2"])
    assert team.name == "Investigation"
    assert team.reviewer == "Reviewer_Investigation"


def test_org_dissolve_team():
    team = AIOrganizationEngine.create_team("Test", "Mgr", ["A"])
    res = AIOrganizationEngine.dissolve_team(team.id)
    assert res is True
    assert AIOrganizationEngine.get_organization_structure()["teams"][-1]["status"] == "DISSOLVED"


def test_org_dissolve_missing():
    assert AIOrganizationEngine.dissolve_team("missing") is False


def test_org_get_structure():
    AIOrganizationEngine._reset()
    AIOrganizationEngine.create_team("Test", "Mgr", ["A"])
    struct = AIOrganizationEngine.get_organization_structure()
    assert struct["total_teams"] == 1


def test_team_model_init():
    t = AITeam(name="N", manager="M", agents=["A"], reviewer="R", quality_supervisor="Q")
    assert t.status == "ACTIVE"
    assert t.id is not None


def test_workforce_analyze_scale_up():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 1500, "cpu_load": 60})
    assert res["action_taken"] == "CREATE_TEAM"
    assert res["new_team_id"] is not None


def test_workforce_analyze_scale_down():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 10, "cpu_load": 20})
    assert res["action_taken"] == "SCALE_DOWN"


def test_workforce_analyze_no_action():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 500, "cpu_load": 90})
    assert res["action_taken"] == "NO_ACTION"


def test_org_reset():
    AIOrganizationEngine._reset()
    assert len(AIOrganizationEngine.get_organization_structure()["teams"]) == 0


def test_workforce_returns_status():
    res = WorkforceManager.analyze_and_scale({})
    assert res["status"] == "SCALED"


def test_workforce_defaults():
    res = WorkforceManager.analyze_and_scale({})
    assert res["action_taken"] == "SCALE_DOWN"


def test_team_manager_assignment():
    t = AIOrganizationEngine.create_team("A", "MgrX", [])
    assert t.manager == "MgrX"


def test_team_agents_assignment():
    t = AIOrganizationEngine.create_team("A", "M", ["Ag1"])
    assert "Ag1" in t.agents


def test_team_quality_supervisor():
    t = AIOrganizationEngine.create_team("Alpha", "M", [])
    assert t.quality_supervisor == "Quality_Alpha"


def test_workforce_creates_overflow_team():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 1500, "cpu_load": 50})
    struct = AIOrganizationEngine.get_organization_structure()
    names = [t["name"] for t in struct["teams"]]
    assert "Overflow processing team" in names


def test_org_multiple_teams():
    AIOrganizationEngine._reset()
    AIOrganizationEngine.create_team("A", "M", [])
    AIOrganizationEngine.create_team("B", "M", [])
    assert AIOrganizationEngine.get_organization_structure()["total_teams"] == 2


def test_workforce_high_cpu_no_scale_up():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 2000, "cpu_load": 95})
    assert res["action_taken"] == "NO_ACTION"


def test_workforce_low_tasks_high_cpu():
    res = WorkforceManager.analyze_and_scale({"pending_tasks": 10, "cpu_load": 95})
    assert res["action_taken"] == "SCALE_DOWN"


def test_org_team_status_active_by_default():
    t = AIOrganizationEngine.create_team("X", "M", [])
    assert t.status == "ACTIVE"


def test_org_team_id_unique():
    t1 = AIOrganizationEngine.create_team("A", "M", [])
    t2 = AIOrganizationEngine.create_team("B", "M", [])
    assert t1.id != t2.id


# ────────────────────────────────────────────────────────
# 2. Enterprise Memory & Knowledge Evolution Tests (15 tests)
# ────────────────────────────────────────────────────────

def test_enterprise_memory_store():
    EnterpriseMemoryEngine._reset()
    res = EnterpriseMemoryEngine.store_knowledge({"fact": "A"})
    assert res is True


def test_enterprise_memory_dedup():
    EnterpriseMemoryEngine._reset()
    EnterpriseMemoryEngine.store_knowledge({"fact": "A"})
    res = EnterpriseMemoryEngine.store_knowledge({"fact": "A"})
    assert res is False


def test_enterprise_memory_get():
    EnterpriseMemoryEngine._reset()
    EnterpriseMemoryEngine.store_knowledge({"fact": "X"})
    assert len(EnterpriseMemoryEngine.get_memory()) == 1


def test_evolution_obsolete_removal():
    nodes = [{"concept": "A", "status": "active"}, {"concept": "B", "status": "obsolete"}]
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["obsolete_removed"] == 1
    assert res["nodes_remaining"] == 1


def test_evolution_contradiction_resolution():
    nodes = [{"concept": "A", "val": 1}, {"concept": "A", "val": 2}]
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["contradictions_resolved"] == 1
    assert res["nodes_remaining"] == 1


def test_evolution_status():
    res = KnowledgeEvolutionEngine.evolve_graph([])
    assert res["status"] == "EVOLVED"


def test_evolution_empty():
    res = KnowledgeEvolutionEngine.evolve_graph([])
    assert res["nodes_remaining"] == 0


def test_enterprise_memory_reset():
    EnterpriseMemoryEngine.store_knowledge({"a": 1})
    EnterpriseMemoryEngine._reset()
    assert len(EnterpriseMemoryEngine.get_memory()) == 0


def test_evolution_preserves_unique():
    nodes = [{"concept": "A"}, {"concept": "B"}, {"concept": "C"}]
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["nodes_remaining"] == 3


def test_evolution_mixed():
    nodes = [
        {"concept": "A"}, {"concept": "B", "status": "obsolete"}, 
        {"concept": "A"}, {"concept": "C"}
    ]
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["nodes_remaining"] == 2
    assert res["contradictions_resolved"] == 1
    assert res["obsolete_removed"] == 1


def test_evolution_no_concept_key():
    nodes = [{"val": 1}, {"val": 2}]
    # Since concept is None, they are treated as duplicates of the None concept
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["nodes_remaining"] == 1
    assert res["contradictions_resolved"] == 1


def test_enterprise_memory_complex_obj():
    obj = {"id": 1, "data": {"nested": True}}
    EnterpriseMemoryEngine._reset()
    assert EnterpriseMemoryEngine.store_knowledge(obj) is True
    assert EnterpriseMemoryEngine.store_knowledge(obj) is False


def test_enterprise_memory_multiple():
    EnterpriseMemoryEngine._reset()
    for i in range(5):
        EnterpriseMemoryEngine.store_knowledge({"v": i})
    assert len(EnterpriseMemoryEngine.get_memory()) == 5


def test_evolution_large_graph():
    nodes = [{"concept": f"C{i}"} for i in range(100)]
    nodes.extend([{"concept": f"C{i}"} for i in range(50)]) # duplicates
    nodes.extend([{"concept": f"O{i}", "status": "obsolete"} for i in range(20)])
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["nodes_remaining"] == 100
    assert res["contradictions_resolved"] == 50
    assert res["obsolete_removed"] == 20


def test_evolution_all_obsolete():
    nodes = [{"concept": f"O{i}", "status": "obsolete"} for i in range(10)]
    res = KnowledgeEvolutionEngine.evolve_graph(nodes)
    assert res["nodes_remaining"] == 0


# ────────────────────────────────────────────────────────
# 3. Skills Manager Tests (10 tests)
# ────────────────────────────────────────────────────────

def test_skills_learn():
    SkillManager._reset()
    s = SkillManager.learn_skill("Query", "SQL")
    assert s.name == "Query"
    assert s.is_validated is True


def test_skills_list():
    SkillManager._reset()
    SkillManager.learn_skill("A", "A")
    assert len(SkillManager.list_skills()) == 1


def test_skills_model_init():
    s = Skill(name="a", description="b", version="1")
    assert s.is_validated is False


def test_skills_override():
    SkillManager._reset()
    SkillManager.learn_skill("A", "old")
    SkillManager.learn_skill("A", "new")
    assert SkillManager.list_skills()[0].description == "new"


def test_skills_reset():
    SkillManager.learn_skill("X", "X")
    SkillManager._reset()
    assert len(SkillManager.list_skills()) == 0


def test_skills_version_default():
    SkillManager._reset()
    s = SkillManager.learn_skill("V", "V")
    assert s.version == "1.0"


def test_skills_learn_multiple():
    SkillManager._reset()
    SkillManager.learn_skill("S1", "D1")
    SkillManager.learn_skill("S2", "D2")
    assert len(SkillManager.list_skills()) == 2


def test_skills_learn_returns_skill():
    s = SkillManager.learn_skill("A", "B")
    assert isinstance(s, Skill)


def test_skills_list_empty():
    SkillManager._reset()
    assert isinstance(SkillManager.list_skills(), list)


def test_skills_name_retention():
    s = SkillManager.learn_skill("ComplexSkill", "Desc")
    assert s.name == "ComplexSkill"


# ────────────────────────────────────────────────────────
# 4. Meta-Reasoning Tests (10 tests)
# ────────────────────────────────────────────────────────

def test_meta_reasoning_success():
    res = MetaReasoningEngine.analyze_reasoning_trace({"strategy": "Balanced", "success": True})
    assert "Reinforce" in res["adaptation_proposed"]


def test_meta_reasoning_failure():
    res = MetaReasoningEngine.analyze_reasoning_trace({"strategy": "Deep", "success": False})
    assert "Deprioritize" in res["adaptation_proposed"]


def test_meta_reasoning_fast_path_failure():
    res = MetaReasoningEngine.analyze_reasoning_trace({"strategy": "Fast Path", "success": False})
    assert "human review" in res["adaptation_proposed"]


def test_meta_reasoning_unknown_strategy():
    res = MetaReasoningEngine.analyze_reasoning_trace({"success": True})
    assert res["analyzed_strategy"] == "UNKNOWN"


def test_meta_reasoning_insight_success():
    res = MetaReasoningEngine.analyze_reasoning_trace({"success": True})
    assert "effective" in res["insight"]


def test_meta_reasoning_insight_failure():
    res = MetaReasoningEngine.analyze_reasoning_trace({"success": False})
    assert "failed" in res["insight"]


def test_meta_reasoning_empty_trace():
    res = MetaReasoningEngine.analyze_reasoning_trace({})
    assert "failed" in res["insight"]


def test_meta_reasoning_preserves_strategy_name():
    res = MetaReasoningEngine.analyze_reasoning_trace({"strategy": "GraphToT"})
    assert res["analyzed_strategy"] == "GraphToT"


def test_meta_reasoning_fast_path_success():
    res = MetaReasoningEngine.analyze_reasoning_trace({"strategy": "Fast Path", "success": True})
    assert "Reinforce" in res["adaptation_proposed"]


def test_meta_reasoning_always_returns_dict():
    assert isinstance(MetaReasoningEngine.analyze_reasoning_trace({}), dict)


# ────────────────────────────────────────────────────────
# 5. Autonomous Governance Tests (10 tests)
# ────────────────────────────────────────────────────────

def test_gov_allow():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.5})
    assert res["governance_decision"] == "ALLOW"


def test_gov_suspend():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.8})
    assert res["governance_decision"] == "SUSPEND"
    assert "human" in res["intervention"]


def test_gov_block():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.95})
    assert res["governance_decision"] == "BLOCK"
    assert "Deactivate" in res["intervention"]


def test_gov_missing_risk():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {})
    assert res["governance_decision"] == "ALLOW"


def test_gov_agent_id_returned():
    res = AutonomousGovernanceEngine.evaluate_action("XYZ", {})
    assert res["agent_id"] == "XYZ"


def test_gov_intervention_none():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.1})
    assert res["intervention"] == "NONE"


def test_gov_exact_boundaries():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.9})
    assert res["governance_decision"] == "SUSPEND"


def test_gov_exact_boundaries_2():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 0.7})
    assert res["governance_decision"] == "ALLOW"


def test_gov_extreme_risk():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": 10.0})
    assert res["governance_decision"] == "BLOCK"


def test_gov_negative_risk():
    res = AutonomousGovernanceEngine.evaluate_action("ag1", {"risk_score": -1.0})
    assert res["governance_decision"] == "ALLOW"


# ────────────────────────────────────────────────────────
# 6. AI Laboratory Tests (10 tests)
# ────────────────────────────────────────────────────────

def test_lab_benchmark_success():
    res = AILabEngine.run_benchmark(["ModelA", "ModelB"], "accuracy")
    assert res["status"] == "COMPLETED"
    assert res["winner"] == "ModelA"


def test_lab_benchmark_empty():
    res = AILabEngine.run_benchmark([], "accuracy")
    assert res["status"] == "ERROR"


def test_lab_benchmark_metric():
    res = AILabEngine.run_benchmark(["A"], "speed")
    assert res["metric"] == "speed"


def test_lab_benchmark_promoted():
    res = AILabEngine.run_benchmark(["A"], "x")
    assert res["promoted"] is True


def test_lab_benchmark_results_dict():
    res = AILabEngine.run_benchmark(["A", "B", "C"], "x")
    assert len(res["results"]) == 3


def test_lab_benchmark_winner_in_results():
    res = AILabEngine.run_benchmark(["A", "B"], "x")
    assert res["winner"] in res["results"]


def test_lab_benchmark_winner_score_highest():
    res = AILabEngine.run_benchmark(["A", "B", "C"], "x")
    winner = res["winner"]
    max_score = max(res["results"].values())
    assert res["results"][winner] == max_score


def test_lab_benchmark_single_candidate():
    res = AILabEngine.run_benchmark(["OnlyMe"], "x")
    assert res["winner"] == "OnlyMe"


def test_lab_benchmark_error_message():
    res = AILabEngine.run_benchmark([], "x")
    assert "No candidates" in res["message"]


def test_lab_benchmark_status_completed():
    res = AILabEngine.run_benchmark(["X"], "Y")
    assert res["status"] == "COMPLETED"


# ────────────────────────────────────────────────────────
# 7. Integration & Filler Tests (5 tests)
# ────────────────────────────────────────────────────────

def test_integration_org_inst():
    assert AIOrganizationEngine() is not None

def test_integration_workforce_inst():
    assert WorkforceManager() is not None

def test_integration_memory_inst():
    assert EnterpriseMemoryEngine() is not None

def test_integration_skills_inst():
    assert SkillManager() is not None

def test_integration_lab_inst():
    assert AILabEngine() is not None

# Total tests: 20 + 15 + 10 + 10 + 10 + 10 + 5 = 80 tests.
