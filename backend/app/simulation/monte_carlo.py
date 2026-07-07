import random
from typing import Dict, List
from app.simulation.models import DigitalTwin, MonteCarloReport, Scenario, ScenarioMutation
from app.simulation.simulator import SimulationEngine
from app.simulation.digital_twin import DigitalTwinEngine


class MonteCarloEngine:
    """
    Probabilistic simulation engine.
    Varies parameters randomly over N iterations to measure
    decision stability, variance, and sensitivity.
    """

    VARIABLE_PARAMS = [
        ("metrics.ocr_confidence", 0.5, 1.0),
        ("metrics.iqa_score", 0.3, 1.0),
        ("validation_report.score", 0.4, 1.0),
        ("metrics.fraud_score", 0.0, 1.0),
    ]

    @classmethod
    def run(
        cls,
        twin: DigitalTwin,
        iterations: int = 1000,
        seed: int = 42,
    ) -> MonteCarloReport:
        """Run N simulations with randomised parameters."""
        rng = random.Random(seed)
        decision_counts: Dict[str, int] = {}

        for i in range(iterations):
            mutations: List[ScenarioMutation] = []
            for field, lo, hi in cls.VARIABLE_PARAMS:
                mutations.append(ScenarioMutation(
                    field=field,
                    new_value=round(rng.uniform(lo, hi), 4),
                ))

            scenario = Scenario(id=f"mc_{i}", name=f"MonteCarlo_{i}", mutations=mutations)
            result = SimulationEngine.simulate(twin, scenario)

            dec = result.simulated_decision
            decision_counts[dec] = decision_counts.get(dec, 0) + 1

        # Compute statistics
        total = sum(decision_counts.values())
        majority = max(decision_counts.values()) if decision_counts else 0
        stability = majority / total if total else 0.0

        # Variance = 1 - stability (simple proxy)
        variance = 1.0 - stability

        # Confidence intervals (simplified: proportion ± margin)
        ci: Dict[str, float] = {}
        for dec, count in decision_counts.items():
            proportion = count / total
            ci[dec] = round(proportion, 4)

        return MonteCarloReport(
            iterations=iterations,
            decision_distribution=decision_counts,
            stability=round(stability, 4),
            variance=round(variance, 4),
            confidence_interval=ci,
        )
