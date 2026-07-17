# Streaming (Server Sent Events)

Pour garantir une expérience conversationnelle fluide pour l'Investigation Workspace, nous utilisons le standard **Server Sent Events (SSE)** via `sse-starlette`.

Le client appelle `/api/v1/ollama/chat` avec `{"stream": true}`.
FastAPI ouvre un AsyncGenerator qui se branche sur le stream HTTPx d'Ollama. Chaque token est streamé au frontend au fur et à mesure de sa génération.

## Gestion des pannes
- Si Ollama timeout (60s), un event d'erreur est envoyé au stream SSE et la connexion se ferme proprement sans faire tomber FastAPI.
