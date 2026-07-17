import pytest
import asyncio
from app.agents.manager import AgentManager
from app.agents.consensus import ConsensusEngine
from app.agents.communication import EventBus, AgentEvent, AgentMessage


def _write_test_document_image(path) -> None:
    import cv2
    import numpy as np

    img = np.ones((300, 800, 3), dtype=np.uint8) * 255
    cv2.putText(img, "INVOICE #4471", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
    cv2.putText(img, "Total: 950 EUR", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.imwrite(str(path), img)


def test_agent_manager_no_document_fails_honestly():
    """
    Without a real document, OCR must fail explicitly (not fabricate canned
    "Invoice #1234" text), and the fraud agent must skip rather than reason
    over data that was never produced.
    """
    manager = AgentManager()
    result = asyncio.run(manager.process_claim("C-999", {"doc": "invoice"}))

    assert result["status"] == "COMPLETED"
    assert result["agent_results"]["ocr_supervisor"]["status"] == "FAILED"
    assert result["agent_results"]["fraud_agent"] is None  # skipped: no OCR text to analyze
    assert "fraud_score" not in result["context"]["metadata"]


@pytest.mark.requires_ollama
def test_agent_manager_full_flow(tmp_path):
    manager = AgentManager()

    image_path = tmp_path / "document.jpg"
    _write_test_document_image(image_path)

    # Process a claim with a real document image
    result = asyncio.run(
        manager.process_claim("C-999", {"image_path": str(image_path)})
    )

    assert result["status"] == "COMPLETED"
    assert result["agent_results"]["ocr_supervisor"]["status"] == "SUCCESS"
    assert result["agent_results"]["fraud_agent"]["status"] == "SUCCESS"

    # Check that fraud agent depended on real OCR text and produced a real score
    fraud_score = result["context"]["metadata"]["fraud_score"]
    assert fraud_score is not None
    assert 0.0 <= fraud_score <= 1.0


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
