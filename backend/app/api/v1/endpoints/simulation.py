import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.simulation.digital_twin import DigitalTwinEngine
from app.simulation.simulator import SimulationEngine
from app.simulation.explainer import ExplainerEngine
from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.models import Scenario, ScenarioMutation

router = APIRouter(prefix="/simulation", tags=["Enterprise Simulation & XAI"])


class CreateTwinRequest(BaseModel):
    claim_id: str
    documents: List[Dict[str, Any]] = []
    evidence_graph: Dict[str, Any] = {}
    validation_report: Dict[str, Any] = {}
    decision_report: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}


class SimulateRequest(BaseModel):
    twin_id: str
    scenario_name: str
    mutations: List[Dict[str, Any]]  # [{field, new_value}]


class MonteCarloRequest(BaseModel):
    twin_id: str
    iterations: int = 100
    seed: int = 42


@router.post("/digital-twin")
def create_twin(req: CreateTwinRequest):
    twin = DigitalTwinEngine.create_twin(
        claim_id=req.claim_id,
        documents=req.documents,
        evidence_graph=req.evidence_graph,
        validation_report=req.validation_report,
        decision_report=req.decision_report,
        metrics=req.metrics,
    )
    return {"twin_id": twin.id, "claim_id": twin.claim_id}


@router.post("/simulate")
def simulate(req: SimulateRequest):
    twin = DigitalTwinEngine.get_twin(req.twin_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Twin not found")

    mutations = [ScenarioMutation(field=m["field"], new_value=m["new_value"]) for m in req.mutations]
    scenario = Scenario(id=str(uuid.uuid4()), name=req.scenario_name, mutations=mutations)
    result = SimulationEngine.simulate(twin, scenario)
    return result.model_dump()


@router.get("/explanation/{claim_id}")
def get_explanation(claim_id: str):
    # Find the most recent twin for this claim
    for twin in DigitalTwinEngine._twins.values():
        if twin.claim_id == claim_id:
            report = ExplainerEngine.explain_decision(twin)
            return report.model_dump()
    raise HTTPException(status_code=404, detail="No twin found for this claim")


@router.post("/monte-carlo")
def run_monte_carlo(req: MonteCarloRequest):
    twin = DigitalTwinEngine.get_twin(req.twin_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Twin not found")

    report = MonteCarloEngine.run(twin, iterations=req.iterations, seed=req.seed)
    return report.model_dump()
