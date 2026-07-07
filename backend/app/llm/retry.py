import asyncio
import logging
from typing import Callable, Awaitable, Any

logger = logging.getLogger(__name__)

class RetryPolicy:
    """Exponential backoff and fallback executor."""
    
    @staticmethod
    async def execute_with_retry(
        func: Callable[[], Awaitable[Any]], 
        max_retries: int = 3, 
        base_delay: float = 1.0,
        fallback_func: Callable[[], Awaitable[Any]] = None
    ) -> Any:
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    if fallback_func:
                        logger.warning("Max retries reached. Executing fallback.")
                        return await fallback_func()
                    raise e
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
