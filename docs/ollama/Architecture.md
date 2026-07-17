# Ollama Local Runtime Architecture

```mermaid
graph TD
    Client[Next.js Client] --> SSE[Server Sent Events]
    SSE --> OllamaRouter[Ollama API]
    
    OllamaRouter --> Memory[Semantic Cache / Memory]
    OllamaRouter --> GPU[GPU Orchestrator]
    OllamaRouter --> ToolCall[Tool Calling Engine]
    OllamaRouter --> Profiler[Prompt Profiler]
    
    ToolCall --> Tools[Internal Systems / MCP]
    
    GPU --> Ollama[Local Ollama Cluster]
```

## Composants
- **OllamaClient** : Interface HTTP/2 asynchrone avec le cluster Ollama, gérant les Timeouts et le streaming.
- **GPU Orchestrator** : Abstraction garantissant qu'on ne dépasse jamais la VRAM disponible (éviction LRU automatique).
- **Tool Calling Engine** : Parser qui intercepte les requêtes de l'Ollama et les branche sur le graphe Neo4j, pgvector ou le moteur de règles.
