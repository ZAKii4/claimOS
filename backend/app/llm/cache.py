import hashlib
import json
from collections import OrderedDict
from typing import Optional
from app.llm.models import LLMRequest, LLMResponse


class LLMCache:
    """
    In-memory LRU Cache for LLM responses to save cost and latency.
    """
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _generate_key(self, request: LLMRequest) -> str:
        # Hash messages and model parameters
        msg_str = json.dumps([m.model_dump() for m in request.messages], sort_keys=True)
        key_content = f"{request.model}-{request.temperature}-{msg_str}"
        return hashlib.sha256(key_content.encode()).hexdigest()

    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        key = self._generate_key(request)
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, request: LLMRequest, response: LLMResponse):
        key = self._generate_key(request)
        self.cache[key] = response
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
            
    def get_stats(self):
        return {"hits": self.hits, "misses": self.misses, "size": len(self.cache)}
