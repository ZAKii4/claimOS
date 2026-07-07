import pytest
import asyncio
import uuid
from app.workflows.builder import WorkflowBuilder
from app.workflows.executor import WorkflowExecutor
from app.workflows.models import WorkflowInstance, WorkflowState, TaskState, WorkflowContext
from app.workflows.nodes.tasks import ServiceTask, HumanTask
from app.workflows.nodes.gateways import ExclusiveGateway, ParallelGateway
from app.workflows.expressions import ExpressionEngine
from app.workflows.exporters import MermaidExporter
from app.workflows.repository import WorkflowRepository


# ─────────────────────────────────────────────────────
# Expression Engine
# ─────────────────────────────────────────────────────

def test_expression_simple_comparison():
    ctx = {"amount": 100}
    assert ExpressionEngine.evaluate("amount > 50", ctx) is True
    assert ExpressionEngine.evaluate("amount < 50", ctx) is False


def test_expression_equality():
    ctx = {"risk": "HIGH"}
    assert ExpressionEngine.evaluate("risk == 'HIGH'", ctx) is True
    assert ExpressionEngine.evaluate("risk == 'LOW'", ctx) is False


def test_expression_nested_dict():
    ctx = {"claim": {"amount": 75000}}
    assert ExpressionEngine.evaluate("claim.amount > 50000", ctx) is True


def test_expression_boolean_logic():
    ctx = {"score": 0.95, "risk": "LOW"}
    assert ExpressionEngine.evaluate("score > 0.90 and risk == 'LOW'", ctx) is True
    assert ExpressionEngine.evaluate("score < 0.50 or risk == 'LOW'", ctx) is True
    assert ExpressionEngine.evaluate("score < 0.50 and risk == 'HIGH'", ctx) is False


def test_expression_empty_is_true():
    assert ExpressionEngine.evaluate("", {}) is True


# ─────────────────────────────────────────────────────
# Workflow Builder
# ─────────────────────────────────────────────────────

def test_builder_sequential():
    upload = ServiceTask(id="upload", name="Upload Document", action_name="upload")
    ocr = ServiceTask(id="ocr", name="OCR Processing", action_name="ocr")
    classify = ServiceTask(id="classify", name="Classification", action_name="classify")

    definition = (
        WorkflowBuilder("Claim Pipeline")
        .start(upload)
        .then(ocr)
        .then(classify)
        .end()
    )

    assert definition.name == "Claim Pipeline"
    assert len(definition.nodes) == 3
    assert len(definition.edges) == 2
    assert definition.start_node_id == "upload"


def test_builder_with_branch():
    upload = ServiceTask(id="upload", name="Upload", action_name="upload")
    gateway = ExclusiveGateway(id="gw1", name="Risk Check")
    auto = ServiceTask(id="auto", name="Auto Approve", action_name="auto_approve")
    manual = HumanTask(id="manual", name="Manual Review", assignee_role="reviewer")

    definition = (
        WorkflowBuilder("Branching Workflow")
        .start(upload)
        .branch(gateway)
        .condition(auto, "risk == 'LOW'")
        .condition(manual, "risk == 'HIGH'")
        .end()
    )

    assert len(definition.nodes) == 4
    assert len(definition.edges) == 3  # upload->gw1, gw1->auto, gw1->manual


# ─────────────────────────────────────────────────────
# Sequential Execution
# ─────────────────────────────────────────────────────

def test_sequential_execution():
    t1 = ServiceTask(id="t1", name="Step 1", action_name="step1")
    t2 = ServiceTask(id="t2", name="Step 2", action_name="step2")

    definition = WorkflowBuilder("Seq").start(t1).then(t2).end()
    instance = WorkflowInstance(id=str(uuid.uuid4()), definition_id=definition.id)

    executor = WorkflowExecutor(definition, instance)
    asyncio.run(executor.run())

    assert instance.state == WorkflowState.COMPLETED
    assert instance.context.get("t1_completed") is True
    assert instance.context.get("t2_completed") is True


# ─────────────────────────────────────────────────────
# Exclusive Gateway (XOR Branch)
# ─────────────────────────────────────────────────────

def test_exclusive_gateway_branch():
    start = ServiceTask(id="start", name="Start", action_name="start")
    gateway = ExclusiveGateway(id="gw", name="Decision")
    path_a = ServiceTask(id="path_a", name="Path A", action_name="path_a")
    path_b = ServiceTask(id="path_b", name="Path B", action_name="path_b")

    definition = (
        WorkflowBuilder("XOR Test")
        .start(start)
        .branch(gateway)
        .condition(path_a, "risk == 'LOW'")
        .condition(path_b, "risk == 'HIGH'")
        .end()
    )

    # Scenario: risk == LOW → should take path_a
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        definition_id=definition.id,
        context=WorkflowContext(variables={"risk": "LOW"})
    )
    executor = WorkflowExecutor(definition, instance)
    asyncio.run(executor.run())

    assert instance.state == WorkflowState.COMPLETED
    assert instance.context.get("path_a_completed") is True
    assert instance.context.get("path_b_completed") is None  # path_b was NOT taken


# ─────────────────────────────────────────────────────
# Parallel Gateway (AND Fork)
# ─────────────────────────────────────────────────────

def test_parallel_gateway():
    start = ServiceTask(id="start", name="Start", action_name="start")
    fork = ParallelGateway(id="fork", name="Parallel Fork")
    branch_a = ServiceTask(id="br_a", name="Branch A", action_name="branch_a")
    branch_b = ServiceTask(id="br_b", name="Branch B", action_name="branch_b")

    definition = (
        WorkflowBuilder("Parallel Test")
        .start(start)
        .parallel(fork)
        .path(branch_a)
        .path(branch_b)
        .end()
    )

    instance = WorkflowInstance(id=str(uuid.uuid4()), definition_id=definition.id)
    executor = WorkflowExecutor(definition, instance)
    asyncio.run(executor.run())

    assert instance.state == WorkflowState.COMPLETED
    assert instance.context.get("br_a_completed") is True
    assert instance.context.get("br_b_completed") is True


# ─────────────────────────────────────────────────────
# Compensation on Failure
# ─────────────────────────────────────────────────────

class FailingTask(ServiceTask):
    async def execute(self, context):
        raise RuntimeError("Simulated failure")


class CompensableTask(ServiceTask):
    async def execute(self, context):
        context.set("saved", True)
        return {"saved": True}

    async def compensate(self, context):
        context.set("saved", False)
        context.set("compensated", True)


def test_compensation_on_failure():
    good = CompensableTask(id="good", name="Save", action_name="save")
    bad = FailingTask(id="bad", name="Crash", action_name="crash")

    definition = WorkflowBuilder("Compensation Test").start(good).then(bad).end()
    instance = WorkflowInstance(id=str(uuid.uuid4()), definition_id=definition.id)

    executor = WorkflowExecutor(definition, instance)
    asyncio.run(executor.run())

    assert instance.state == WorkflowState.FAILED
    assert instance.context.get("compensated") is True
    assert instance.context.get("saved") is False  # Compensation undid the save


# ─────────────────────────────────────────────────────
# Human Task Suspension & Resume
# ─────────────────────────────────────────────────────

def test_human_task_suspends_workflow():
    upload = ServiceTask(id="upload", name="Upload", action_name="upload")
    review = HumanTask(id="review", name="Manual Review", assignee_role="fraud_team")

    definition = WorkflowBuilder("HITL Test").start(upload).then(review).end()
    instance = WorkflowInstance(id=str(uuid.uuid4()), definition_id=definition.id)

    executor = WorkflowExecutor(definition, instance)
    asyncio.run(executor.run())

    assert instance.state == WorkflowState.SUSPENDED
    assert instance.context.get("assigned_to") == "fraud_team"


# ─────────────────────────────────────────────────────
# Mermaid Export
# ─────────────────────────────────────────────────────

def test_mermaid_export():
    upload = ServiceTask(id="upload", name="Upload", action_name="upload")
    ocr = ServiceTask(id="ocr", name="OCR", action_name="ocr")
    gw = ExclusiveGateway(id="gw", name="Risk?")
    approve = ServiceTask(id="approve", name="Approve", action_name="approve")

    definition = (
        WorkflowBuilder("Export Test")
        .start(upload)
        .then(ocr)
        .branch(gw)
        .condition(approve, "risk == 'LOW'")
        .end()
    )

    mermaid = MermaidExporter.export(definition)

    assert "graph TD" in mermaid
    assert 'upload["Upload"]' in mermaid
    assert 'gw{"Risk?"}' in mermaid
    assert "upload -->" in mermaid
    assert "|risk == 'LOW'|" in mermaid


# ─────────────────────────────────────────────────────
# Repository Persistence
# ─────────────────────────────────────────────────────

def test_repository():
    t1 = ServiceTask(id="t1", name="T1", action_name="t1")
    definition = WorkflowBuilder("Repo Test").start(t1).end()

    WorkflowRepository.save_definition(definition)
    loaded = WorkflowRepository.get_definition(definition.id)

    assert loaded is not None
    assert loaded.name == "Repo Test"

    instance = WorkflowInstance(id="inst-1", definition_id=definition.id)
    WorkflowRepository.save_instance(instance)

    loaded_inst = WorkflowRepository.get_instance("inst-1")
    assert loaded_inst is not None
    assert loaded_inst.definition_id == definition.id
