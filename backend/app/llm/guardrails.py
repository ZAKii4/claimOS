import json
from typing import Any, Dict


class GuardrailsEngine:
    """
    Validation and safety checks on LLM inputs and outputs.
    """
    
    @staticmethod
    def check_prompt_injection(text: str) -> bool:
        """Naive keyword check for injection attempts."""
        suspect_phrases = ["ignore previous instructions", "system prompt", "you are now"]
        text_lower = text.lower()
        for phrase in suspect_phrases:
            if phrase in text_lower:
                return True
        return False
        
    @staticmethod
    def validate_json_output(output: str) -> Dict[str, Any]:
        """Ensures the output is valid JSON."""
        try:
            # Strip potential markdown code blocks
            clean_output = output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output[7:]
            if clean_output.endswith("```"):
                clean_output = clean_output[:-3]
                
            return json.loads(clean_output.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Output is not valid JSON: {e}")
