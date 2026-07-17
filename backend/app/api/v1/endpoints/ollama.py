from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from typing import Dict, Any, List

from app.ollama.client import ollama_client
from app.ollama.gpu_manager import gpu_manager
from app.ollama.tool_calling import tool_calling_engine
from app.ollama.memory import conversation_memory
from app.ollama.prompt_runtime import prompt_runtime

router = APIRouter()

@router.get("/models")
async def list_models():
    return await ollama_client.list_models()

@router.post("/models/load")
async def load_model(payload: Dict[str, str]):
    model_name = payload.get("model")
    try:
        gpu_manager.load_model(model_name)
        return {"status": "loaded", "model": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/unload")
async def unload_model(payload: Dict[str, str]):
    model_name = payload.get("model")
    gpu_manager.unload_model(model_name)
    return {"status": "unloaded", "model": model_name}

@router.get("/gpu")
async def get_gpu_metrics():
    return gpu_manager.get_gpu_metrics()

@router.post("/chat")
async def chat(payload: Dict[str, Any]):
    model = payload.get("model", "llama3.1:latest")
    messages = payload.get("messages", [])
    stream = payload.get("stream", False)
    session_id = payload.get("session_id", "default")
    
    # Check Semantic Cache
    if len(messages) > 0 and messages[-1]["role"] == "user":
        last_msg = messages[-1]["content"]
        cached = conversation_memory.check_semantic_cache(last_msg)
        if cached:
            return {"message": {"role": "assistant", "content": cached}, "cached": True}
            
    # Load model if not in VRAM
    gpu_manager.load_model(model)
    
    if stream:
        generator = await ollama_client.generate_chat(model, messages, stream=True)
        return EventSourceResponse(generator)
    else:
        response = await ollama_client.generate_chat(model, messages, stream=False)
        assistant_msg = response.get("message", {}).get("content", "")
        
        # Check for tool calls
        tool_result = tool_calling_engine.detect_and_execute_tools(assistant_msg)
        if tool_result["status"] == "executed":
            # In a real app we'd feed this back to the LLM. For mock, just return it.
            assistant_msg += f"\n\n[Tool Executed: {tool_result['tool']}] -> {tool_result['result']}"
            
        conversation_memory.add_message(session_id, "user", messages[-1]["content"] if messages else "")
        conversation_memory.add_message(session_id, "assistant", assistant_msg)
        
        return {"message": {"role": "assistant", "content": assistant_msg}, "tools": tool_result}
