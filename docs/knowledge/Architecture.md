# Enterprise Knowledge Platform Architecture

```mermaid
graph TD
    Client[Investigation Workspace / Decision Copilot] --> RAG[Hybrid RAG Engine]
    
    RAG --> SemanticCache{Semantic Cache}
    SemanticCache -- Hit --> LLM[Local Ollama]
    SemanticCache -- Miss --> Vector[Vector Search]
    SemanticCache -- Miss --> Graph[Graph Search]
    
    Vector --> pgvector[(PostgreSQL pgvector)]
    Graph --> Neo4j[(Neo4j Knowledge Graph)]
    
    Vector --> EvidenceRanking[Evidence Ranking]
    Graph --> EvidenceRanking
    
    EvidenceRanking --> ContextCompression[Context Compression]
    ContextCompression --> LLM
```

## Composants
- **Vector Platform** : Gère les embeddings sémantiques.
- **Neo4j Graph** : Détecte les réseaux de fraude et les relations métier complexes (Entity Resolution).
- **Hybrid RAG** : Fusionne les deux sources de vérité avec un classement par pertinence (`Evidence Ranking`) et une compression du contexte (`Context Compression`) avant génération LLM.
