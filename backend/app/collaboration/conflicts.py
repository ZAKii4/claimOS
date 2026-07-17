from typing import Dict, Any, Tuple


class ConflictResolutionEngine:
    """Handles concurrent edits using Optimistic Locking and Last-Write-Wins strategies."""

    # Simulates a document store with versioning: { doc_id: { version: int, data: Any } }
    _documents: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def set_document(cls, doc_id: str, data: Any, version: int = 1):
        cls._documents[doc_id] = {"version": version, "data": data}

    @classmethod
    def process_edit(cls, doc_id: str, new_data: Any, client_version: int, strategy: str = "OPTIMISTIC") -> Tuple[str, Any]:
        """
        Processes an edit.
        Returns a tuple: (status, current_doc)
        status: "MERGED", "CONFLICT", "ROLLBACK", "OVERWRITTEN"
        """
        if doc_id not in cls._documents:
            # First write
            cls._documents[doc_id] = {"version": 1, "data": new_data}
            return "MERGED", cls._documents[doc_id]

        current_doc = cls._documents[doc_id]
        
        if strategy == "OPTIMISTIC":
            if client_version == current_doc["version"]:
                # Success
                current_doc["version"] += 1
                current_doc["data"] = new_data
                return "MERGED", current_doc
            else:
                # Conflict
                return "CONFLICT", current_doc
                
        elif strategy == "LWW": # Last Write Wins
            current_doc["version"] += 1
            current_doc["data"] = new_data
            return "OVERWRITTEN", current_doc
            
        return "ROLLBACK", current_doc

    @classmethod
    def _reset(cls):
        cls._documents.clear()
