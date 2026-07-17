"""
Exceptions for the LLM gateway.

Raised explicitly whenever a request cannot be honestly serviced, instead of
silently degrading to a mocked/fabricated response.
"""


class LLMProviderUnavailableError(Exception):
    """Raised when no real LLM provider can service a request."""


class ProviderNotConfiguredError(LLMProviderUnavailableError):
    """Raised by a cloud provider when its required credentials are missing."""


class UnsupportedCapabilityError(Exception):
    """Raised when a provider is configured but doesn't support the requested
    capability (e.g. Anthropic has no public embeddings endpoint)."""
