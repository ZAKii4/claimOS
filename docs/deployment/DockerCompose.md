# Docker Compose Orchestration

## Services
- `frontend`: Next.js web application (Port 3000 internal)
- `backend`: FastAPI Python server (Port 8000 internal)
- `nginx`: Reverse proxy handling routing to frontend and backend (Ports 80/443 exposed)
- `postgres`: Relational database
- `redis`: Key-Value store and PubSub for WebSockets
- `neo4j`: Graph database for Knowledge Graph
- `ollama`: Local AI provider for LLM inference (Volume mounted for persistent models)

## Networking
All services run on a custom bridge network `claimos_net`. They communicate using their container names as hostnames (e.g., `http://backend:8000`).

## Volumes
Data persistence is ensured via Docker volumes for databases and AI models to prevent data loss on container restart.
