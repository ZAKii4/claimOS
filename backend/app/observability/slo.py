class SLOManager:
    """
    Tracks Service Level Objectives (Availability, Latency, Error Budgets).
    """
    def __init__(self):
        self.target_availability = 99.9
        self.total_requests = 1000000
        self.failed_requests = 500
        
    def get_availability(self) -> float:
        if self.total_requests == 0:
            return 100.0
        success = self.total_requests - self.failed_requests
        return (success / self.total_requests) * 100.0
        
    def get_error_budget_remaining(self) -> float:
        """Returns the percentage of the error budget remaining."""
        allowed_failures = self.total_requests * (1 - (self.target_availability / 100))
        if allowed_failures == 0:
            return 0.0
        remaining = allowed_failures - self.failed_requests
        return max(0.0, (remaining / allowed_failures) * 100)
        
    def get_slo_report(self):
        return {
            "availability_target": self.target_availability,
            "current_availability": self.get_availability(),
            "error_budget_remaining_percent": self.get_error_budget_remaining()
        }

slo_manager = SLOManager()
