"""
API v1 router — aggregates all v1 endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, ollama, observability, claims, documents, health, lookups, validation, decision, learning, agents, llm, knowledge, monitoring, workflows, simulation, governance, platform, integrations, analytics, optimization, local_ai, agentic_ai, mcp, cognitive, autonomous, collaboration, devops, ai_governance, platform_sdk, federation, investigation, command_center, live_logs, form_mapping

router = APIRouter()

router.include_router(health.router)
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(ollama.router, prefix="/ollama", tags=["ollama"])
router.include_router(observability.router, prefix="/observability", tags=["observability"])
router.include_router(claims.router)
router.include_router(documents.router)
router.include_router(lookups.router)
router.include_router(validation.router)
router.include_router(decision.router)
router.include_router(learning.router)
router.include_router(agents.router)
router.include_router(agents.claim_agents_router)
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
router.include_router(mcp.router)
router.include_router(cognitive.router)
router.include_router(autonomous.router)
router.include_router(collaboration.router)
router.include_router(devops.router)
router.include_router(ai_governance.router)
router.include_router(platform_sdk.router)
router.include_router(federation.router)
router.include_router(investigation.router)
router.include_router(command_center.router)
router.include_router(live_logs.router)
router.include_router(form_mapping.router)
