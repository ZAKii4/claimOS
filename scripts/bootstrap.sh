#!/bin/bash
echo "Bootstrapping claimOS Platform..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
fi
docker compose build
docker compose up -d
echo "Bootstrap complete. Access the platform at http://localhost"
