import httpx
from typing import Dict, Any, List, AsyncGenerator
import json

class OllamaClient:
    """
    HTTP Client for local Ollama instances.
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        # Local inference can genuinely take longer than a hosted API,
        # especially under contention — see app/llm/providers/ollama_provider.py.
        self.timeout = httpx.Timeout(120.0)

    async def list_models(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json()

    async def generate_chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Any:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Async generator for streaming
        if stream:
            async def event_stream() -> AsyncGenerator[str, None]:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    try:
                        async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                            async for line in response.aiter_lines():
                                if line:
                                    data = json.loads(line)
                                    # Yield Server-Sent Event formatted string
                                    yield f"data: {json.dumps(data)}\n\n"
                                    if data.get("done"):
                                        break
                    except Exception as e:
                        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            return event_stream()
        else:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()

ollama_client = OllamaClient()
