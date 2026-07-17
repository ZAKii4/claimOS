from typing import Dict, Any

class PromptRuntime:
    """
    Compiles prompts and profiles token usage/cost.
    """
    def __init__(self):
        # A simple estimation: 1 token ~= 4 characters in english
        self.char_per_token = 4

    def compile_prompt(self, template: str, variables: Dict[str, str]) -> str:
        for k, v in variables.items():
            template = template.replace(f"{{{k}}}", str(v))
        return template

    def estimate_tokens(self, text: str) -> int:
        return len(text) // self.char_per_token

    def profile_request(self, prompt: str, response: str) -> Dict[str, Any]:
        prompt_tokens = self.estimate_tokens(prompt)
        response_tokens = self.estimate_tokens(response)
        
        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens,
            "estimated_local_cost_usd": 0.0, # Local is free!
            "grounding_score": 95 if "RAG Results" in prompt else 0 # Mock
        }

prompt_runtime = PromptRuntime()
