from typing import List, Dict, Any
from app.agents.core.goals import Goal, GoalStatus


class PlanningEngine:
    """Dynamically breaks down goals into sub-goals (execution plans)."""

    @classmethod
    def generate_plan(cls, tenant_id: str, objective: str) -> Goal:
        """Decomposes a high-level objective into a structured plan (mocked)."""
        main_goal = Goal(
            tenant_id=tenant_id,
            description=objective,
            priority=10
        )

        # Mocking the LLM reasoning to decompose the plan
        if "sinistre" in objective.lower() or "claim" in objective.lower():
            step1 = Goal(tenant_id=tenant_id, description="Vérifier les documents", priority=1)
            step2 = Goal(tenant_id=tenant_id, description="Contrôler la fraude", priority=2, dependencies=[step1.id])
            step3 = Goal(tenant_id=tenant_id, description="Consulter la base documentaire", priority=3)
            step4 = Goal(tenant_id=tenant_id, description="Simuler décisions", priority=4, dependencies=[step2.id, step3.id])
            
            main_goal.add_subgoal(step1)
            main_goal.add_subgoal(step2)
            main_goal.add_subgoal(step3)
            main_goal.add_subgoal(step4)
        else:
            main_goal.add_subgoal(Goal(tenant_id=tenant_id, description="Analyser la requête", priority=1))

        return main_goal

    @classmethod
    def replan(cls, goal: Goal, failed_subgoal_id: str) -> Goal:
        """Modifies a plan when a step fails."""
        for sg in goal.sub_goals:
            if sg.id == failed_subgoal_id:
                sg.status = GoalStatus.CANCELLED
                # Inject a recovery goal
                recovery = Goal(
                    tenant_id=goal.tenant_id,
                    description=f"Recovery strategy for: {sg.description}",
                    priority=sg.priority
                )
                goal.add_subgoal(recovery)
                
                # Update dependencies for subsequent goals
                for subsequent in goal.sub_goals:
                    if failed_subgoal_id in subsequent.dependencies:
                        subsequent.dependencies.remove(failed_subgoal_id)
                        subsequent.dependencies.append(recovery.id)
                break
        return goal
