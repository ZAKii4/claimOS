from typing import List, Dict, Any

class ContextCompression:
    """
    Compresses retrieved context to fit inside LLM context window while preserving information.
    """
    async def compress(self, context_parts: List[str], max_tokens: int = 2000) -> str:
        # Simplistic mock compression
        compressed = []
        current_len = 0
        for part in context_parts:
            # Approx 1 token = 4 chars
            part_len = len(part) // 4
            if current_len + part_len <= max_tokens:
                compressed.append(part)
                current_len += part_len
            else:
                break
        return "\n".join(compressed)

context_compression = ContextCompression()
