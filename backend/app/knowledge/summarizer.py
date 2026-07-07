from typing import List
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message


class SummarizerEngine:
    """Generates document and section summaries using Map-Reduce."""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        
    async def summarize_chunks(self, texts: List[str]) -> str:
        """Map-Reduce summarization."""
        if not texts:
            return ""
            
        # Map Phase
        chunk_summaries = []
        for text in texts:
            req = LLMRequest(
                model="gpt-4", # Routed via gateway
                messages=[
                    Message(role="system", content="Summarize the following text concisely."),
                    Message(role="user", content=text)
                ]
            )
            resp = await self.llm.generate(req)
            chunk_summaries.append(resp.choices[0].content)
            
        # Reduce Phase
        combined = "\n".join(chunk_summaries)
        req = LLMRequest(
            model="gpt-4",
            messages=[
                Message(role="system", content="Create a final cohesive summary from the following summaries."),
                Message(role="user", content=combined)
            ]
        )
        final_resp = await self.llm.generate(req)
        return final_resp.choices[0].content
