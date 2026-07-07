import asyncio
from app.observability.health import HealthManager
from app.observability.metrics import MetricsEngine


class BackgroundCollectors:
    """Async background jobs to periodically analyze telemetry."""
    
    def __init__(self):
        self.health_manager = HealthManager()
        self.running = False
        
    async def start(self):
        self.running = True
        asyncio.create_task(self._collect_health())
        
    async def stop(self):
        self.running = False
        
    async def _collect_health(self):
        while self.running:
            # Periodically verify health
            await self.health_manager.check_all()
            await asyncio.sleep(60) # every minute
