"""
API v1 router — aggregates all v1 endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import claims, health, lookups, validation, decision, learning, agents, llm, knowledge, monitoring, workflows, simulation, governance, platform, integrations, analytics, optimization, local_ai, agentic_ai

router = APIRouter()

router.include_router(health.router)
router.include_router(claims.router)
router.include_router(lookups.router)
router.include_router(validation.router)
router.include_router(decision.router)
router.include_router(learning.router)
router.include_router(agents.router)
router.include_router(llm.router)
router.include_router(knowledge.router)
router.include_router(monitoring.router)
router.include_router(workflows.router)
router.include_router(simulation.router)
router.include_router(governance.router)
router.include_router(platform.router)
router.include_router(integrations.router)
router.include_router(analytics.router)
router.include_router(optimization.router)
router.include_router(local_ai.router)
router.include_router(agentic_ai.router)
