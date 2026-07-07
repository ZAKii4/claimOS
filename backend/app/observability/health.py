import asyncio
from typing import List, Protocol
from app.observability.models import ComponentHealth, HealthState


class HealthCheckProvider(Protocol):
    async def check_health(self) -> ComponentHealth:
        pass


class MockDBHealth(HealthCheckProvider):
    async def check_health(self) -> ComponentHealth:
        return ComponentHealth(name="Database", state=HealthState.GREEN, message="Connection OK")


class MockLLMHealth(HealthCheckProvider):
    async def check_health(self) -> ComponentHealth:
        return ComponentHealth(name="LLMGateway", state=HealthState.GREEN, message="Providers Available")


class HealthManager:
    """Consolidates health checks across the platform."""
    
    def __init__(self):
        self.providers: List[HealthCheckProvider] = [
            MockDBHealth(),
            MockLLMHealth()
        ]
        
    async def check_all(self) -> dict:
        results = await asyncio.gather(*(p.check_health() for p in self.providers))
        
        global_state = HealthState.GREEN
        for res in results:
            if res.state == HealthState.RED:
                global_state = HealthState.RED
                break
            elif res.state == HealthState.YELLOW and global_state == HealthState.GREEN:
                global_state = HealthState.YELLOW
                
        return {
            "status": global_state.value,
            "components": [r.model_dump() for r in results]
        }
