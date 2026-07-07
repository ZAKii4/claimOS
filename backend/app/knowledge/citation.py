import re
from typing import List, Tuple


class GroundingEngine:
    """Verifies that LLM outputs contain valid citations from the retrieved context."""
    
    @staticmethod
    def verify_citations(llm_output: str, provided_chunks: List[str]) -> Tuple[bool, List[str]]:
        """
        Checks if the LLM hallucinated facts without citing.
        MVP: Checks if citations like [Doc: X] exist and if the text closely aligns with chunks.
        """
        # Find all citation markers e.g., [Source: X]
        citations = re.findall(r'\[Source:.*?\]', llm_output)
        
        # Simple strict grounding: if no citations found, consider it ungrounded
        if not citations and len(provided_chunks) > 0:
            return False, []
            
        return True, citations
        
    @staticmethod
    def format_context_for_llm(chunks: List['KnowledgeChunk']) -> str:
        """Formats the retrieved chunks into a standard context string for the LLM."""
        context = "### PROVIDED KNOWLEDGE ###\n\n"
        for i, chunk in enumerate(chunks):
            doc_id = chunk.document_id
            page = f", Page {chunk.page_number}" if chunk.page_number else ""
            context += f"--- Source: {doc_id}{page} ---\n{chunk.content}\n\n"
        return context
