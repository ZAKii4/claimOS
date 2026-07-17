from typing import List


class ToolSelectionEngine:
    """Autonomously selects the best tools for a given task context."""

    _tool_catalog = [
        "Simulation", "Knowledge", "OCR", "RAG", "SQL", 
        "Filesystem", "Browser", "GitHub", "Analytics", "Reporting"
    ]

    @classmethod
    def select_tools(cls, task_description: str) -> List[str]:
        """Heuristically selects tools based on task text."""
        selected = []
        text = task_description.lower()
        
        if "document" in text or "image" in text:
            selected.append("OCR")
        if "database" in text or "query" in text:
            selected.append("SQL")
        if "search" in text or "legal" in text:
            selected.append("RAG")
            selected.append("Knowledge")
        if "report" in text or "metrics" in text:
            selected.append("Analytics")
            selected.append("Reporting")
            
        if not selected:
            selected.append("Knowledge")  # Fallback
            
        return selected
