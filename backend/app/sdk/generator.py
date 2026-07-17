from typing import Dict, Any, List

class ProjectGenerator:
    """Generates SDK project templates for rapid plugin development."""

    @classmethod
    def generate_template(cls, template_type: str) -> Dict[str, Any]:
        templates = {
            "ocr": {"files": ["main.py", "manifest.json", "tests/test_ocr.py"]},
            "fraud": {"files": ["fraud_model.py", "manifest.json", "rules.json"]},
            "agent": {"files": ["agent.py", "prompts.json", "manifest.json"]}
        }
        
        if template_type in templates:
            return {"status": "SUCCESS", "type": template_type, "template": templates[template_type]}
        return {"status": "ERROR", "message": "Unknown template type."}
