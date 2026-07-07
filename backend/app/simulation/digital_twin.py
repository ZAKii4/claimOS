import copy
import uuid
from typing import Dict, Any, Optional
from app.simulation.models import DigitalTwin, TwinSnapshot


class DigitalTwinEngine:
    """
    Creates fully isolated clones of claim state for simulation.
    Every mutation happens on a deep copy — production data is never touched.
    """

    _twins: Dict[str, DigitalTwin] = {}
    _snapshots: Dict[str, TwinSnapshot] = {}

    @classmethod
    def create_twin(
        cls,
        claim_id: str,
        documents: list = None,
        evidence_graph: dict = None,
        validation_report: dict = None,
        decision_report: dict = None,
        workflow_state: dict = None,
        metrics: dict = None,
    ) -> DigitalTwin:
        """Creates an immutable Digital Twin from production state."""
        twin = DigitalTwin(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            documents=copy.deepcopy(documents or []),
            evidence_graph=copy.deepcopy(evidence_graph or {}),
            validation_report=copy.deepcopy(validation_report or {}),
            decision_report=copy.deepcopy(decision_report or {}),
            workflow_state=copy.deepcopy(workflow_state or {}),
            metrics=copy.deepcopy(metrics or {}),
        )
        cls._twins[twin.id] = twin
        return twin

    @classmethod
    def get_twin(cls, twin_id: str) -> Optional[DigitalTwin]:
        return cls._twins.get(twin_id)

    @classmethod
    def snapshot(cls, twin: DigitalTwin, label: str) -> TwinSnapshot:
        """Takes an immutable snapshot of a twin's current state."""
        snap = TwinSnapshot(
            twin_id=twin.id,
            label=label,
            state={
                "documents": copy.deepcopy(twin.documents),
                "evidence_graph": copy.deepcopy(twin.evidence_graph),
                "validation_report": copy.deepcopy(twin.validation_report),
                "decision_report": copy.deepcopy(twin.decision_report),
                "workflow_state": copy.deepcopy(twin.workflow_state),
                "metrics": copy.deepcopy(twin.metrics),
            },
        )
        cls._snapshots[f"{twin.id}:{label}"] = snap
        return snap

    @classmethod
    def clone_for_simulation(cls, twin: DigitalTwin) -> DigitalTwin:
        """Returns a fully independent deep copy for mutation during simulation."""
        cloned = copy.deepcopy(twin)
        cloned.id = str(uuid.uuid4())
        return cloned
