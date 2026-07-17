.PHONY: build up down restart logs backend frontend shell clean help

help:
	@echo "claimOS - Enterprise AI Operating System"
	@echo ""
	@echo "Usage:"
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services in detached mode"
	@echo "  make down       - Stop and remove all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs for all services"
	@echo "  make backend    - View backend logs"
	@echo "  make frontend   - View frontend logs"
	@echo "  make shell      - Open a bash shell inside the backend container"
	@echo "  make clean      - Stop services and remove all volumes (WARNING: Data Loss)"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

backend:
	docker compose logs -f backend

frontend:
	docker compose logs -f frontend

shell:
	docker compose exec backend /bin/bash

clean:
	docker compose down -v
