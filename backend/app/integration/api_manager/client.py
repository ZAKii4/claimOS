import time
from typing import Dict, Any, Callable


class CircuitBreakerError(Exception):
    pass


class APIIntegrationManager:
    """Centralizes external API calls with Circuit Breaker, Retry, and Rate Limiting."""

    _circuit_state: Dict[str, str] = {}  # endpoint -> "CLOSED", "OPEN", "HALF_OPEN"
    _failure_counts: Dict[str, int] = {}
    
    MAX_FAILURES = 3
    RETRY_DELAY = 1.0  # seconds

    @classmethod
    def execute(
        cls, 
        endpoint: str, 
        method: Callable, 
        *args, 
        retries: int = 3, 
        **kwargs
    ) -> Any:
        state = cls._circuit_state.get(endpoint, "CLOSED")
        
        if state == "OPEN":
            raise CircuitBreakerError(f"Circuit OPEN for endpoint: {endpoint}")

        last_error = None
        for attempt in range(retries):
            try:
                # Simulate rate limiter wait
                time.sleep(0.01)
                
                result = method(*args, **kwargs)
                
                # Success: reset circuit
                cls._failure_counts[endpoint] = 0
                cls._circuit_state[endpoint] = "CLOSED"
                return result
                
            except Exception as e:
                last_error = e
                # Increment failure count
                fails = cls._failure_counts.get(endpoint, 0) + 1
                cls._failure_counts[endpoint] = fails
                
                if fails >= cls.MAX_FAILURES:
                    cls._circuit_state[endpoint] = "OPEN"
                    raise CircuitBreakerError(f"Circuit breached for {endpoint} after {fails} failures.") from e
                
                time.sleep(cls.RETRY_DELAY)

        raise last_error

    @classmethod
    def reset_circuit(cls, endpoint: str):
        cls._circuit_state[endpoint] = "CLOSED"
        cls._failure_counts[endpoint] = 0
