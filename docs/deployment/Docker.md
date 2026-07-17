# claimOS Docker Architecture

## Overview
The claimOS platform is containerized using Docker to provide a reproducible, isolated, and scalable environment across dev, staging, and production.

## Dockerfiles
- `docker/backend/Dockerfile`: Multi-stage Python 3.11 slim image. Runs FastAPI via Uvicorn. Non-root user `claimos` is used for security.
- `docker/frontend/Dockerfile`: Multi-stage Node.js 18 alpine image. Uses Next.js standalone output to minimize image size and attack surface.
