import string
from typing import Dict, Any


class TemplateEngine:
    """
    MVP Template engine using Python's string.Template.
    Replaces Jinja2 to avoid adding external dependencies.
    Supports basic $variable substitution.
    """
    
    @staticmethod
    def render(template_str: str, variables: Dict[str, Any]) -> str:
        # Convert all variables to strings to avoid interpolation errors
        str_vars = {k: str(v) for k, v in variables.items()}
        try:
            template = string.Template(template_str)
            return template.safe_substitute(str_vars)
        except Exception as e:
            raise ValueError(f"Failed to render template: {e}")
            
    @staticmethod
    def compose(system_prompt: str, user_prompt: str, variables: Dict[str, Any]) -> str:
        """Compose a full prompt from system and user parts."""
        sys_rendered = TemplateEngine.render(system_prompt, variables)
        user_rendered = TemplateEngine.render(user_prompt, variables)
        
        return f"{sys_rendered}\n\n{user_rendered}"
