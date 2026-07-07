class SDKGenerator:
    """Generates OpenAPI docs and SDK stubs."""

    @classmethod
    def generate_openapi(cls) -> str:
        """Returns a simplified OpenAPI 3.1 YAML stub."""
        return """openapi: 3.1.0
info:
  title: claimOS Enterprise Integration API
  version: 1.0.0
paths:
  /api/v1/claims:
    post:
      summary: Create a new claim
      responses:
        '201':
          description: Claim created
"""

    @classmethod
    def generate_python_sdk(cls) -> str:
        """Returns a simplified Python SDK stub."""
        return """import requests

class ClaimOSClient:
    def __init__(self, api_key: str, base_url: str = "https://api.claimos.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def create_claim(self, payload: dict):
        return requests.post(f"{self.base_url}/claims", json=payload, headers=self.headers).json()
"""
