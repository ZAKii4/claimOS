"""
Regression tests for real ClamAV-backed virus scanning.

VirusScanStep used to be a no-op stub that always set
virus_scan_passed=True regardless of content — these tests exercise the
real `clamd` INSTREAM protocol against a real ClamAV daemon (docker-compose
service `clamav`), including detecting the standard EICAR antivirus test
string. Skipped (not faked) when the daemon isn't reachable, same policy
as the Ollama-dependent tests (see tests/conftest.py).
"""

import clamd
import pytest

from app.config.settings import get_settings
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError
from app.pipeline.steps.virus_scan import VirusScanStep

# The official, harmless EICAR standard antivirus test file — every real AV
# engine, including ClamAV, is configured to flag this exact byte string.
EICAR_STRING = (
    r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
).encode()


def _clamav_is_reachable() -> bool:
    try:
        settings = get_settings()
        client = clamd.ClamdNetworkSocket(
            host=settings.CLAMAV_HOST, port=settings.CLAMAV_PORT, timeout=3
        )
        return client.ping() == "PONG"
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _clamav_is_reachable(), reason="ClamAV daemon not reachable locally")


def test_detects_real_eicar_test_string_and_blocks_pipeline():
    step = VirusScanStep()
    context = DocumentContext(payload=EICAR_STRING, filename="eicar.txt", content_type="text/plain")

    with pytest.raises(PipelineError) as exc_info:
        step.execute(context)

    assert exc_info.value.severity == ErrorSeverity.FATAL
    assert "EICAR" in exc_info.value.message or "Eicar" in exc_info.value.message


def test_clean_payload_passes_real_scan():
    step = VirusScanStep()
    context = DocumentContext(
        payload=b"This is a perfectly ordinary, harmless document.",
        filename="clean.txt",
        content_type="text/plain",
    )

    result = step.execute(context)

    assert result.metadata["virus_scan_passed"] is True
    assert result.errors == []


def test_unreachable_daemon_degrades_instead_of_faking_pass(monkeypatch):
    monkeypatch.setattr(get_settings(), "CLAMAV_PORT", 1)  # nothing listens on port 1

    step = VirusScanStep()
    context = DocumentContext(payload=b"some content", filename="f.txt", content_type="text/plain")

    result = step.execute(context)

    assert result.metadata["virus_scan_passed"] is None
    assert len(result.errors) == 1
    assert result.errors[0]["severity"] == ErrorSeverity.DEGRADED
    assert "NOT scanned" in result.errors[0]["message"]


def test_no_payload_is_a_noop():
    step = VirusScanStep()
    context = DocumentContext(payload=None, filename="f.txt", content_type="text/plain")

    result = step.execute(context)

    assert "virus_scan_passed" not in result.metadata
