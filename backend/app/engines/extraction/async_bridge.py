"""
Bridges an async coroutine into a synchronous call site.

``BaseExtractor.extract()`` is a synchronous contract (the whole document
pipeline is synchronous, see app/pipeline/core.py), but ``LLMManager.generate``
is async. ``asyncio.run()`` alone would crash if the caller happens to
already be inside a running event loop (e.g. an async FastAPI endpoint that
calls the pipeline directly instead of offloading it to a thread) — so we
detect that case and run the coroutine in its own thread instead.
"""

import asyncio
import concurrent.futures
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()  # type: ignore[arg-type]
