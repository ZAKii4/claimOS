import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.model_registry.registry import ModelRegistry
from app.model_registry.lifecycle import LifecycleManager
from app.model_registry.prompt_governance import PromptGovernanceManager
from app.model_registry.dataset_governance import DatasetGovernanceManager

client = TestClient(app)

# ────────────────────────────────────────────────────────
# Core Model Registry Tests
# ────────────────────────────────────────────────────────

def test_model_registry_flow():
    ModelRegistry._reset()
    model = ModelRegistry.register_model("phi4-claims", "1.0", "Ollama", "LLM")
    assert model["name"] == "phi4-claims"
    assert model["status"] == "DRAFT"
    
    m_id = model["id"]
    fetched = ModelRegistry.get_model(m_id)
    assert fetched["id"] == m_id
    
    assert len(ModelRegistry.get_all_models()) == 1

def test_lifecycle_manager():
    ModelRegistry._reset()
    model = ModelRegistry.register_model("phi4", "1.0", "Ollama", "LLM")
    assert model["status"] == "DRAFT"
    
    assert LifecycleManager.transition_model(model["id"], "STAGING")
    assert ModelRegistry.get_model(model["id"])["status"] == "STAGING"
    
    assert not LifecycleManager.transition_model("invalid", "PROD")

# ────────────────────────────────────────────────────────
# Prompts & Datasets
# ────────────────────────────────────────────────────────

def test_prompt_governance():
    PromptGovernanceManager._reset()
    p = PromptGovernanceManager.register_prompt("Extract entities from [[TEXT]]", "AI Team")
    assert p["status"] == "APPROVED"
    assert p["risk_score"] == "LOW"
    assert len(PromptGovernanceManager.get_all()) == 1
    
    fetched = PromptGovernanceManager.get_prompt(p["id"])
    assert fetched["id"] == p["id"]

def test_dataset_governance():
    DatasetGovernanceManager._reset()
    d = DatasetGovernanceManager.register_dataset("Claims_Training_Q1", "v1")
    assert d["completeness"] == 0.99
    assert len(DatasetGovernanceManager.get_all()) == 1

# ────────────────────────────────────────────────────────
# API Endpoint Tests
# ────────────────────────────────────────────────────────

def test_api_endpoints():
    ModelRegistry._reset()
    PromptGovernanceManager._reset()
    DatasetGovernanceManager._reset()

    # 1. Models
    res = client.post("/api/v1/ai-governance/models/register", json={
        "name": "llama3.2-ocr", "version": "1.0", "provider": "Local", "m_type": "LLM"
    })
    assert res.status_code == 200
    model_id = res.json()["id"]

    res = client.get("/api/v1/ai-governance/models")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 2. Evaluations & Monitoring
    assert client.get(f"/api/v1/ai-governance/evaluations?model_id={model_id}").status_code == 200
    assert client.get(f"/api/v1/ai-governance/monitoring?model_id={model_id}").status_code == 200
    assert client.get(f"/api/v1/ai-governance/scorecards?model_id={model_id}").status_code == 200
    assert client.get(f"/api/v1/ai-governance/compliance?model_id={model_id}").status_code == 200
    assert client.get(f"/api/v1/ai-governance/risks?model_id={model_id}").status_code == 200

    # 3. Approvals
    res = client.post("/api/v1/ai-governance/approval", json={"model_id": model_id, "reviewer": "admin"})
    assert res.status_code == 200

    res = client.post(f"/api/v1/ai-governance/rollback?model_id={model_id}")
    assert res.status_code == 200
    assert ModelRegistry.get_model(model_id)["status"] == "ROLLED_BACK"

    # 4. Datasets / Prompts
    assert client.get("/api/v1/ai-governance/datasets").status_code == 200
    assert client.get("/api/v1/ai-governance/prompts").status_code == 200
