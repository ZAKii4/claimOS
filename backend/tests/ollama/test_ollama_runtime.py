import pytest
from app.ollama.client import ollama_client
from app.ollama.gpu_manager import gpu_manager
from app.ollama.tool_calling import tool_calling_engine
from app.ollama.memory import conversation_memory
from app.ollama.prompt_runtime import prompt_runtime

requires_ollama = pytest.mark.requires_ollama

@requires_ollama
@pytest.mark.asyncio
async def test_ollama_client_list():
    models = await ollama_client.list_models()
    assert "models" in models

@requires_ollama
@pytest.mark.asyncio
async def test_ollama_client_chat():
    messages = [{"role": "user", "content": "Hello"}]
    res = await ollama_client.generate_chat("llama3:latest", messages, stream=False)
    assert "message" in res
    assert "content" in res["message"]

def test_gpu_manager():
    gpu_manager.loaded_models = {} # reset
    
    # Load normal model
    gpu_manager.load_model("llama3.1:latest")
    assert "llama3.1:latest" in gpu_manager.loaded_models
    
    # Load more to force eviction (16GB max)
    gpu_manager.load_model("qwen2.5:latest")
    gpu_manager.load_model("mistral:latest")
    gpu_manager.load_model("phi4:latest")
    
    # Wait, size is 4.7 + 4.0 + 4.1 + 4.0 = 16.8GB -> >16GB. 
    # llama3.1 should be evicted.
    assert "llama3.1:latest" not in gpu_manager.loaded_models
    assert "phi4:latest" in gpu_manager.loaded_models
    
    metrics = gpu_manager.get_gpu_metrics()
    assert metrics["used_vram"] <= 16.0

def test_tool_calling():
    # Mock LLM response with tool call
    mock_response = '''
    Let me check the graph for you.
    <tool_call>{"name": "knowledge_graph", "args": {"entity_id": "P-123"}}</tool_call>
    '''
    
    res = tool_calling_engine.detect_and_execute_tools(mock_response)
    assert res["status"] == "executed"
    assert res["tool"] == "knowledge_graph"
    assert "P-123" in res["result"]
    assert "linked entities" in res["result"]

def test_conversation_memory():
    # Semantic hit
    res = conversation_memory.check_semantic_cache("Quelle est la franchise de M. Dupont ?")
    assert res is not None
    assert "150€" in res
    
    # Semantic miss
    res2 = conversation_memory.check_semantic_cache("Bonjour")
    assert res2 is None
    
    # History
    conversation_memory.add_message("S1", "user", "Hi")
    conversation_memory.add_message("S1", "assistant", "Hello")
    assert len(conversation_memory.get_history("S1")) == 2

def test_prompt_runtime():
    template = "You are an assistant. The user says: {msg}"
    compiled = prompt_runtime.compile_prompt(template, {"msg": "Help"})
    assert "Help" in compiled
    
    profile = prompt_runtime.profile_request("Short prompt", "A bit longer response here")
    assert profile["total_tokens"] > 0
    assert profile["estimated_local_cost_usd"] == 0.0
