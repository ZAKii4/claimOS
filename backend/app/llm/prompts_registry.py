from pydantic import BaseModel
from typing import Dict, List, Optional


class PromptDefinition(BaseModel):
    id: str
    version: str
    owner: str
    description: str
    system_template: str
    user_template: str
    variables: List[str]
    examples: List[Dict[str, str]] = []
    language: str = "en"
    default_temperature: float = 0.7
    default_model: str = "gpt-4"
    tags: List[str] = []


class PromptRegistry:
    """
    Stores and manages versioned prompts.
    MVP uses an in-memory dictionary.
    """
    def __init__(self):
        self._prompts: Dict[str, PromptDefinition] = {}
        self._load_defaults()
        
    def _load_defaults(self):
        # Example prompt
        ocr_extract = PromptDefinition(
            id="ocr_extraction",
            version="1.0.0",
            owner="core",
            description="Extracts structured data from raw OCR text.",
            system_template="You are an expert data extraction system. Extract data as JSON.",
            user_template="Extract the following fields: $fields\n\nFrom this text:\n$text",
            variables=["fields", "text"],
            tags=["ocr", "extraction"]
        )
        self.register(ocr_extract)
        
    def register(self, prompt: PromptDefinition):
        key = f"{prompt.id}@{prompt.version}"
        self._prompts[key] = prompt
        
    def get(self, prompt_id: str, version: str = "1.0.0") -> Optional[PromptDefinition]:
        key = f"{prompt_id}@{version}"
        return self._prompts.get(key)
        
    def get_latest(self, prompt_id: str) -> Optional[PromptDefinition]:
        # Simple MVP logic to find latest
        candidates = [p for k, p in self._prompts.items() if p.id == prompt_id]
        if not candidates:
            return None
        # Sort by version string assuming simple format
        candidates.sort(key=lambda x: x.version, reverse=True)
        return candidates[0]
