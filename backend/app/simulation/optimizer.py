from typing import Dict, List
from app.simulation.models import DigitalTwin, OptimizationReport, Scenario, ScenarioMutation
from app.simulation.simulator import SimulationEngine
from app.simulation.digital_twin import DigitalTwinEngine


class OptimizationEngine:
    """
    Grid-search optimizer for business thresholds.
    Finds the best combination of thresholds to maximise automation
    while respecting quality constraints.
    """

    @classmethod
    def optimize(
        cls,
        twins: List[DigitalTwin],
        objective: str = "maximize_automation",
        validation_range: tuple = (0.70, 0.99),
        fraud_range: tuple = (0.5, 0.95),
        step: float = 0.05,
    ) -> OptimizationReport:
        """
        Grid search over validation_threshold × fraud_threshold.
        For each combo, simulate all twins and measure automation rate.
        """
        best_auto_rate = 0.0
        best_thresholds: Dict[str, float] = {}
        best_error_rate = 1.0
        iterations = 0

        val_th = validation_range[0]
        while val_th <= validation_range[1]:
            fraud_th = fraud_range[0]
            while fraud_th <= fraud_range[1]:
                auto_count = 0
                error_count = 0

                for twin in twins:
                    scenario = Scenario(
                        id=f"opt_{iterations}",
                        name="optimization",
                        mutations=[
                            ScenarioMutation(field="validation_report.score", new_value=twin.validation_report.get("score", 0.0)),
                            ScenarioMutation(field="metrics.fraud_score", new_value=twin.metrics.get("fraud_score", 0.0)),
                        ],
                    )
                    result = SimulationEngine.simulate(twin, scenario)

                    if result.simulated_decision == "AUTO_APPROVED":
                        auto_count += 1
                    elif result.simulated_decision == "AUTO_REJECTED":
                        error_count += 1

                total = len(twins) if twins else 1
                auto_rate = auto_count / total
                error_rate = error_count / total

                if auto_rate > best_auto_rate:
                    best_auto_rate = auto_rate
                    best_error_rate = error_rate
                    best_thresholds = {
                        "validation_threshold": round(val_th, 2),
                        "fraud_threshold": round(fraud_th, 2),
                    }

                iterations += 1
                fraud_th = round(fraud_th + step, 2)
            val_th = round(val_th + step, 2)

        return OptimizationReport(
            objective=objective,
            best_thresholds=best_thresholds,
            predicted_automation_rate=round(best_auto_rate, 4),
            predicted_error_rate=round(best_error_rate, 4),
            iterations_run=iterations,
        )
