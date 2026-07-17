"""
Shared test helpers.

Some tests exercise real AI/ML code paths (LLM generation, embeddings) against
a live local Ollama server rather than a mocked provider — per policy, this
codebase no longer has a production Mock/fake fallback to hide behind. Those
tests are skipped (not faked, not silently passed) when Ollama isn't reachable,
e.g. in CI, which currently has no Ollama service configured.
"""

import httpx
import pytest

from app.config.settings import get_settings


def ollama_is_reachable() -> bool:
    try:
        settings = get_settings()
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{settings.OLLAMA_API_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_ollama: skip at run time (not just at collection) if Ollama isn't reachable",
    )


def pytest_runtest_setup(item):
    """
    Re-checks Ollama connectivity right before each marked test runs, rather
    than once at collection time — a `skipif` evaluated at import time can't
    catch Ollama going down mid-suite (it did, mid-session, during this very
    project) and would turn an infra hiccup into a spurious hard failure.
    """
    if item.get_closest_marker("requires_ollama") and not ollama_is_reachable():
        pytest.skip("Ollama not reachable locally")
