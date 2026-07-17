# Hybrid RAG (Retrieval-Augmented Generation)

Le moteur **EnterpriseHybridRAG** est le cerveau de la plateforme de connaissances.

## 1. Interception
Chaque question passe d'abord par le **Semantic Cache**. Si l'embedding de la question a une similarité cosinus supérieure à 95% avec une question récente, la réponse est servie instantanément.

## 2. Recherche Vectorielle (Semantic)
La similarité sémantique (Cosine Similarity) trouve les paragraphes et les documents les plus proches de l'intention de la question (via pgvector).

## 3. Recherche Graphe (Relationships)
Le réseau Neo4j trouve les entités liées explicitement (Personnes, Véhicules, Réseaux de Fraude).

## 4. Ranking & Compression
Les preuves (Evidences) sont notées et triées. Seules les meilleures sont conservées pour rentrer dans la fenêtre de contexte restreinte d'Ollama (Context Compression).
