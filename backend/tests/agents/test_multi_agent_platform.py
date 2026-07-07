import pytest
import asyncio
from app.agents.manager import AgentManager
from app.agents.consensus import ConsensusEngine
from app.agents.communication import EventBus, AgentEvent, AgentMessage
from app.agents.context import AgentContext
from app.agents.planner import ExecutionGraph, ExecutionNode
from app.agents.memory import SharedMemory


def test_agent_manager_full_flow():
    manager = AgentManager()
    
    # Process a dummy claim
    result = asyncio.run(manager.process_claim("C-999", {"doc": "invoice"}))
    
    assert result["status"] == "COMPLETED"
    assert "ocr_supervisor" in result["agent_results"]
    assert "fraud_agent" in result["agent_results"]
    
    # Check that fraud agent depended on OCR and got data
    assert result["context"]["metadata"]["fraud_score"] is not None


def test_consensus_engine():
    opinions = ["FRAUD", "FRAUD", "CLEAN"]
    assert ConsensusEngine.majority_voting(opinions) == "FRAUD"
    
    opinions_conf = [
        {"value": "FRAUD", "confidence": 0.4},
        {"value": "CLEAN", "confidence": 0.8}
    ]
    assert ConsensusEngine.confidence_aggregation(opinions_conf) == "CLEAN"


def test_event_bus():
    bus = EventBus()
    received = []
    
    async def handler(event: AgentEvent):
        received.append(event.payload["msg"])
        
    async def runner():
        bus.subscribe("TEST_EVENT", handler)
        
        event = AgentEvent(event_type="TEST_EVENT", source_agent_id="test_agent", payload={"msg": "hello"})
        await bus.publish(event)
        
        # Yield control to event loop so handler can run
        await asyncio.sleep(0.01)
        
        assert received == ["hello"]
        
        # Test point to point
        msg = AgentMessage(id="1", sender_id="A", target_id="B", content={"cmd": "do_work"})
        await bus.send_message(msg)
        
        msgs_b = await bus.get_messages("B")
        assert len(msgs_b) == 1
        assert msgs_b[0].content["cmd"] == "do_work"
        
    asyncio.run(runner())
