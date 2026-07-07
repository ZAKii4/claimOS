import functools
import inspect
from app.observability.tracing import TracingEngine


def traceable(name: str = None, tags: dict = None):
    """
    Decorator to automatically wrap a function or coroutine in a Span.
    """
    def decorator(func):
        span_name = name or func.__name__
        
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span = TracingEngine.start_span(span_name, tags)
                try:
                    result = await func(*args, **kwargs)
                    TracingEngine.end_span(span)
                    return result
                except Exception as e:
                    TracingEngine.end_span(span, error=e)
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span = TracingEngine.start_span(span_name, tags)
                try:
                    result = func(*args, **kwargs)
                    TracingEngine.end_span(span)
                    return result
                except Exception as e:
                    TracingEngine.end_span(span, error=e)
                    raise
            return sync_wrapper
            
    return decorator
