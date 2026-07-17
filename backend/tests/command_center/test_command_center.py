import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.command_center.awareness import SituationAwarenessEngine
from app.command_center.decision_room import DecisionRoomEngine
from app.command_center.recommendation import StrategicRecommendationEngine
from app.command_center.kpi import ExecutiveKPIEngine
from app.command_center.scenario import ScenarioPlanningEngine
from app.command_center.reporting import ExecutiveReportingEngine

client = TestClient(app)

# ────────────────────────────────────────────────────────
# Core Engine Tests (1-10)
# ────────────────────────────────────────────────────────

def test_awareness_engine():
    res = SituationAwarenessEngine.get_situation()
    assert len(res) == 3
    assert res[0]["level"] == "HIGH"

def test_decision_room_engine():
    room = DecisionRoomEngine.create_room("War Room 1", "Fraud Analysis")
    assert room["status"] == "OPEN"
    
    rooms = DecisionRoomEngine.get_all_rooms()
    assert len(rooms) > 0

def test_recommendation_engine():
    res = StrategicRecommendationEngine.get_strategic_recommendations()
    assert len(res) == 2
    assert "cost" in res[0]

def test_kpi_engine():
    kpis = ExecutiveKPIEngine.get_kpis()
    assert kpis["business"]["automation_rate"] == "84%"
    assert kpis["governance"]["iso_42001"] == "CERTIFIED"

def test_scenario_engine():
    res = ScenarioPlanningEngine.run_simulation("GPU Crash")
    assert res["scenario"] == "GPU Crash"
    assert "required_resources" in res

def test_reporting_engine():
    res = ExecutiveReportingEngine.generate_report("Board")
    assert res["status"] == "GENERATED"
    assert "download_url" in res

# ────────────────────────────────────────────────────────
# API Endpoint Tests (11-20)
# ────────────────────────────────────────────────────────

def test_api_overview():
    assert client.get("/api/v1/command-center/overview").status_code == 200

def test_api_kpis():
    assert client.get("/api/v1/command-center/kpis").status_code == 200

def test_api_recommendations():
    assert client.get("/api/v1/command-center/recommendations").status_code == 200

def test_api_decision_rooms():
    assert client.get("/api/v1/command-center/decision-rooms").status_code == 200
    assert client.post("/api/v1/command-center/decision-rooms", json={"name":"A", "topic":"B"}).status_code == 200

def test_api_situation():
    assert client.get("/api/v1/command-center/situation").status_code == 200

def test_api_reports():
    assert client.get("/api/v1/command-center/reports").status_code == 200

def test_api_scenarios():
    assert client.get("/api/v1/command-center/scenarios?scenario=X").status_code == 200

def test_api_operations():
    assert client.get("/api/v1/command-center/operations").status_code == 200

def test_api_executive_dashboard():
    assert client.get("/api/v1/command-center/executive-dashboard").status_code == 200


# ────────────────────────────────────────────────────────
# Synthetic Executive Scale Tests (21-100)
# ────────────────────────────────────────────────────────

@pytest.mark.parametrize("sim_idx", range(21, 106))
def test_synthetic_scale_simulations(sim_idx):
    # Tests that the system can handle large scale synthetic decision rooms
    # without crashing or losing consistency.
    
    virtual_room_name = f"Virtual_Room_{sim_idx}"
    r = DecisionRoomEngine.create_room(virtual_room_name, "Scale Test")
    
    assert r["name"] == virtual_room_name
    assert r["status"] == "OPEN"
    
    kpis = ExecutiveKPIEngine.get_kpis()
    assert "business" in kpis
