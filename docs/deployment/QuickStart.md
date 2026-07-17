# Quick Start Guide

## Prerequisites
- Docker Engine & Docker Compose
- Make (optional, but recommended)

## Starting the Platform
1. Initialize environment variables:
   ```bash
   cp .env.example .env
   ```
2. Build and start via Makefile:
   ```bash
   make build
   make up
   ```
   Or via the bootstrap script:
   ```bash
   ./scripts/bootstrap.sh
   ```

## Accessing Services
- **Web App**: http://localhost
- **API Docs**: http://localhost/docs
- **Backend Logs**: `make backend`

## Shutting Down
```bash
make down
```
To wipe all data completely (volumes included):
```bash
./scripts/reset.sh
# OR
make clean
```
