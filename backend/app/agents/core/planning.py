from app.agents.core.goals import Goal, GoalStatus
from app.config.settings import get_settings
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message

PLANNING_SYSTEM_PROMPT = (
    "You are the planning engine of an insurance claims AI platform. Decompose "
    "the given objective into a short, ordered list of concrete sub-goals. "
    "Respond with ONLY a JSON object of the form: "
    '{"subgoals": [{"description": "<short imperative sub-goal>", '
    '"depends_on": [<0-based indices of prerequisite sub-goals in this list>]}]}. '
    "Use between 1 and 6 sub-goals. Leave depends_on empty ([]) for sub-goals "
    "that can start immediately."
)


class PlanningEngine:
    """Dynamically breaks down goals into sub-goals (execution plans) using the LLM."""

    @classmethod
    async def generate_plan(
        cls, tenant_id: str, objective: str, llm_manager: LLMManager | None = None
    ) -> Goal:
        """Decomposes a high-level objective into a structured plan via a real LLM call."""
        main_goal = Goal(tenant_id=tenant_id, description=objective, priority=10)

        llm = llm_manager or LLMManager()
        request = LLMRequest(
            model=get_settings().OLLAMA_DEFAULT_MODEL,
            messages=[
                Message(role="system", content=PLANNING_SYSTEM_PROMPT),
                Message(role="user", content=objective),
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        response = await llm.generate(request)
        parsed = GuardrailsEngine.validate_json_output(response.choices[0].content)

        subgoals_data = parsed.get("subgoals") or []
        if not subgoals_data:
            raise ValueError(
                f"Planning LLM returned no sub-goals for objective: '{objective}'"
            )

        goals_by_index: dict[int, Goal] = {}
        for index, sub in enumerate(subgoals_data):
            goals_by_index[index] = Goal(
                tenant_id=tenant_id,
                description=str(sub.get("description") or f"Step {index + 1}"),
                priority=index + 1,
            )

        for index, sub in enumerate(subgoals_data):
            goal = goals_by_index[index]
            for dep_index in sub.get("depends_on") or []:
                dependency = goals_by_index.get(dep_index)
                if dependency and dep_index != index:
                    goal.dependencies.append(dependency.id)
            main_goal.add_subgoal(goal)

        return main_goal

    @classmethod
    def replan(cls, goal: Goal, failed_subgoal_id: str) -> Goal:
        """Modifies a plan when a step fails (deterministic graph repair, no LLM needed)."""
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
