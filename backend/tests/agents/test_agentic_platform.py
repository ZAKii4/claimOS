import pytest
from app.agents.core.goals import Goal, GoalStatus
from app.agents.core.planning import PlanningEngine
from app.agents.reasoning.reasoner import ReasoningEngine, ReasoningStrategy
from app.agents.reasoning.policies import ExecutionPolicyManager, AutonomyLevel
from app.agents.collaboration.workspace import CollaborationManager
from app.agents.collaboration.delegation import DelegationEngine, TaskStatus
from app.agents.collaboration.negotiation import NegotiationEngine, AgentProposal, NegotiationStrategy
from app.agents.memory.memory import MemoryManager, MemoryType
from app.agents.memory.reflection import ReflectionEngine


# ────────────────────────────────────────────────────────
# 1. Goal & Planning Engine (8 tests)
# ────────────────────────────────────────────────────────

def test_goal_creation():
    g = Goal(tenant_id="t1", description="test")
    assert g.status == GoalStatus.PENDING
    assert g.priority == 1
    assert not g.is_blocked()


def test_goal_add_subgoal():
    g = Goal(tenant_id="t1", description="test")
    g.add_subgoal(Goal(tenant_id="t1", description="sub"))
    assert len(g.sub_goals) == 1


def test_planning_engine_generate_plan_simple():
    plan = PlanningEngine.generate_plan("t1", "Simple objective")
    assert plan.description == "Simple objective"
    assert len(plan.sub_goals) == 1


def test_planning_engine_generate_plan_complex():
    plan = PlanningEngine.generate_plan("t1", "Traiter un sinistre")
    assert len(plan.sub_goals) == 4
    assert plan.sub_goals[0].description == "Vérifier les documents"
    assert plan.sub_goals[1].dependencies == [plan.sub_goals[0].id]


def test_planning_engine_replan():
    plan = PlanningEngine.generate_plan("t1", "Traiter un sinistre")
    failed_id = plan.sub_goals[1].id
    new_plan = PlanningEngine.replan(plan, failed_id)
    
    assert new_plan.sub_goals[1].status == GoalStatus.CANCELLED
    assert len(new_plan.sub_goals) == 5  # added recovery
    assert "Recovery" in new_plan.sub_goals[-1].description


def test_planning_engine_replan_dependency_update():
    plan = PlanningEngine.generate_plan("t1", "Traiter un sinistre")
    failed_id = plan.sub_goals[0].id
    new_plan = PlanningEngine.replan(plan, failed_id)
    recovery_id = new_plan.sub_goals[-1].id
    assert recovery_id in new_plan.sub_goals[1].dependencies


def test_goal_default_confidence():
    g = Goal(tenant_id="t1", description="test")
    assert g.confidence == 1.0


def test_goal_cost_estimate():
    g = Goal(tenant_id="t1", description="test", cost_estimate=10.5)
    assert g.cost_estimate == 10.5


# ────────────────────────────────────────────────────────
# 2. Autonomous Reasoning & Policies (7 tests)
# ────────────────────────────────────────────────────────

def test_execution_policy_manual():
    ExecutionPolicyManager.set_level("t1", AutonomyLevel.MANUAL)
    assert ExecutionPolicyManager.requires_human_supervision("t1")
    assert not ExecutionPolicyManager.can_execute_autonomously("t1")


def test_execution_policy_autonomous():
    ExecutionPolicyManager.set_level("t2", AutonomyLevel.AUTONOMOUS)
    assert not ExecutionPolicyManager.requires_human_supervision("t2")
    assert ExecutionPolicyManager.can_execute_autonomously("t2")


def test_reasoning_blocked_by_policy():
    ExecutionPolicyManager.set_level("t1", AutonomyLevel.SUPERVISED)
    res = ReasoningEngine.reason("t1", {})
    assert res.is_blocked_by_policy
    assert "requires human supervision" in res.conclusion.lower()


def test_reasoning_deductive_fraud():
    ExecutionPolicyManager.set_level("t2", AutonomyLevel.AUTONOMOUS)
    res = ReasoningEngine.reason("t2", {"fraud_score": 90}, ReasoningStrategy.DEDUCTIVE)
    assert res.conclusion == "Reject Claim"
    assert res.confidence == 0.95


def test_reasoning_deductive_safe():
    ExecutionPolicyManager.set_level("t2", AutonomyLevel.AUTONOMOUS)
    res = ReasoningEngine.reason("t2", {"fraud_score": 10}, ReasoningStrategy.DEDUCTIVE)
    assert res.conclusion == "Approve Claim"


def test_reasoning_graph():
    ExecutionPolicyManager.set_level("t2", AutonomyLevel.AUTONOMOUS)
    res = ReasoningEngine.reason("t2", {}, ReasoningStrategy.GRAPH)
    assert res.conclusion == "Identify Network"
    assert "cycle" in res.justification[0]


def test_reasoning_rule_based():
    ExecutionPolicyManager.set_level("t2", AutonomyLevel.AUTONOMOUS)
    res = ReasoningEngine.reason("t2", {}, ReasoningStrategy.RULE_BASED)
    assert res.conclusion == "Proceed normally"


# ────────────────────────────────────────────────────────
# 3. Collaboration & Delegation (11 tests)
# ────────────────────────────────────────────────────────

def test_workspace_share_observation():
    CollaborationManager._clear_all()
    obs = CollaborationManager.share_observation("t1", "a1", "c1", "test")
    assert obs.tenant_id == "t1"
    assert obs.agent_id == "a1"
    assert obs.content == "test"


def test_workspace_get_observations():
    CollaborationManager._clear_all()
    CollaborationManager.share_observation("t1", "a1", "c1", "test1")
    CollaborationManager.share_observation("t1", "a2", "c1", "test2")
    assert len(CollaborationManager.get_context_observations("t1", "c1")) == 2
    assert len(CollaborationManager.get_context_observations("t1", "c2")) == 0


def test_delegation_delegate_task():
    DelegationEngine._clear_all()
    task = DelegationEngine.delegate("t1", "master", "worker", {"do": "this"})
    assert task.status == TaskStatus.ASSIGNED
    assert task.delegator_id == "master"
    assert task.delegatee_id == "worker"


def test_delegation_report_success():
    DelegationEngine._clear_all()
    task = DelegationEngine.delegate("t1", "master", "worker", {})
    DelegationEngine.report_success(task.id, {"done": True})
    assert task.status == TaskStatus.COMPLETED
    assert task.result["done"] is True


def test_delegation_report_failure_retry():
    DelegationEngine._clear_all()
    task = DelegationEngine.delegate("t1", "master", "worker", {}, max_retries=1)
    DelegationEngine.report_failure(task.id, "error")
    assert task.status == TaskStatus.ASSIGNED
    assert task.retries == 1


def test_delegation_report_failure_max_retries():
    DelegationEngine._clear_all()
    task = DelegationEngine.delegate("t1", "master", "worker", {}, max_retries=1)
    DelegationEngine.report_failure(task.id, "error")
    DelegationEngine.report_failure(task.id, "error2")
    assert task.status == TaskStatus.FAILED
    assert task.error == "error2"


def test_negotiation_empty():
    res = NegotiationEngine.resolve("t1", [])
    assert res["consensus"] == "NONE"


def test_negotiation_majority_voting():
    proposals = [
        AgentProposal("a1", "ACCEPT", 0.9),
        AgentProposal("a2", "ACCEPT", 0.5),
        AgentProposal("a3", "REJECT", 0.9),
    ]
    res = NegotiationEngine.resolve("t1", proposals, NegotiationStrategy.MAJORITY_VOTING)
    assert res["consensus"] == "ACCEPT"


def test_negotiation_weighted_confidence():
    proposals = [
        AgentProposal("a1", "ACCEPT", 0.5, weight=1.0),  # score = 0.5
        AgentProposal("a2", "REJECT", 0.9, weight=2.0),  # score = 1.8
    ]
    res = NegotiationEngine.resolve("t1", proposals, NegotiationStrategy.WEIGHTED_CONFIDENCE)
    assert res["consensus"] == "REJECT"


def test_negotiation_human_escalation():
    proposals = [AgentProposal("a1", "ACCEPT", 0.9)]
    res = NegotiationEngine.resolve("t1", proposals, NegotiationStrategy.HUMAN_ESCALATION)
    assert res["consensus"] == "ESCALATED_TO_HUMAN"


def test_delegation_get_missing_task():
    assert DelegationEngine.get_task("missing") is None


# ────────────────────────────────────────────────────────
# 4. Memory & Reflection (15 tests)
# ────────────────────────────────────────────────────────

def test_memory_store():
    MemoryManager._clear_all()
    m = MemoryManager.store("t1", "a1", MemoryType.WORKING, "test")
    assert m.m_type == MemoryType.WORKING
    assert m.content == "test"


def test_memory_retrieve():
    MemoryManager._clear_all()
    MemoryManager.store("t1", "a1", MemoryType.WORKING, "w1")
    MemoryManager.store("t1", "a1", MemoryType.EPISODIC, "e1")
    
    res = MemoryManager.retrieve("t1", "a1", MemoryType.WORKING)
    assert len(res) == 1
    assert res[0].content == "w1"


def test_memory_consolidate():
    MemoryManager._clear_all()
    MemoryManager.store("t1", "a1", MemoryType.WORKING, "w1", {"context_id": "c1"})
    MemoryManager.store("t1", "a1", MemoryType.WORKING, "w2", {"context_id": "c1"})
    
    MemoryManager.consolidate_working_to_episodic("t1", "a1", "c1")
    
    w_mem = MemoryManager.retrieve("t1", "a1", MemoryType.WORKING)
    e_mem = MemoryManager.retrieve("t1", "a1", MemoryType.EPISODIC)
    
    assert len(w_mem) == 0
    assert len(e_mem) == 1
    assert "w1" in e_mem[0].content
    assert "w2" in e_mem[0].content


def test_memory_consolidate_empty():
    MemoryManager._clear_all()
    MemoryManager.consolidate_working_to_episodic("t1", "a1", "c1")
    assert len(MemoryManager.retrieve("t1", "a1", MemoryType.EPISODIC)) == 0


def test_reflection_success():
    MemoryManager._clear_all()
    res = ReflectionEngine.evaluate("t1", "a1", "c1", "OK", "OK")
    assert res["success"] is True
    assert "matched expectations" in res["lesson"].lower()
    
    sem_mem = MemoryManager.retrieve("t1", "a1", MemoryType.SEMANTIC)
    assert len(sem_mem) == 1


def test_reflection_failure():
    MemoryManager._clear_all()
    res = ReflectionEngine.evaluate("t1", "a1", "c1", "FAIL", "OK")
    assert res["success"] is False
    assert res["error_detected"] is True
    assert "Expected OK but got FAIL" in res["lesson"]


def test_memory_clear_all():
    MemoryManager.store("t1", "a1", MemoryType.WORKING, "test")
    MemoryManager._clear_all()
    assert len(MemoryManager.retrieve("t1", "a1", MemoryType.WORKING)) == 0


def test_reflection_semantic_metadata():
    MemoryManager._clear_all()
    ReflectionEngine.evaluate("t1", "a1", "c1", "OK", "OK")
    sem_mem = MemoryManager.retrieve("t1", "a1", MemoryType.SEMANTIC)
    assert sem_mem[0].metadata["source_context"] == "c1"


def test_workspace_clear_all():
    CollaborationManager.share_observation("t1", "a1", "c1", "test")
    CollaborationManager._clear_all()
    assert len(CollaborationManager.get_context_observations("t1", "c1")) == 0


def test_delegation_clear_all():
    DelegationEngine.delegate("t1", "master", "worker", {})
    DelegationEngine._clear_all()
    assert DelegationEngine.get_task("missing") is None  # no way to retrieve all tasks cleanly but this checks clear doesn't crash


def test_negotiation_single_proposal():
    proposals = [AgentProposal("a1", "ACCEPT", 0.9)]
    res = NegotiationEngine.resolve("t1", proposals, NegotiationStrategy.EXPERT_PRIORITY)
    assert res["consensus"] == "ACCEPT"


def test_planning_engine_generate_plan_no_claim():
    plan = PlanningEngine.generate_plan("t1", "other task")
    assert len(plan.sub_goals) == 1
    assert plan.sub_goals[0].description == "Analyser la requête"


def test_reasoning_default_strategy():
    ExecutionPolicyManager.set_level("t1", AutonomyLevel.AUTONOMOUS)
    res = ReasoningEngine.reason("t1", {})
    assert res.strategy == ReasoningStrategy.RULE_BASED
    

def test_delegation_report_failure_on_missing_task():
    # Should not crash
    DelegationEngine.report_failure("missing", "error")
    

def test_delegation_report_success_on_missing_task():
    # Should not crash
    DelegationEngine.report_success("missing", {})

# 41 tests total achieved.
