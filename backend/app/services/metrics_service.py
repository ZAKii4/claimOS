"""
Metrics service.
"""

from sqlalchemy.orm import Session
from app.repositories.metrics_repository import MetricsRepository

class MetricsService:
    def __init__(self, db: Session) -> None:
        self._repo = MetricsRepository(db)
        
    def get_global_metrics(self) -> dict:
        return self._repo.get_global_metrics()

    def get_dashboard_metrics(self) -> dict:
        return self._repo.get_dashboard_metrics()
