#!/bin/bash
echo "Checking claimOS health..."
docker compose ps
echo ""
echo "Backend Health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/health)"
echo "Frontend Health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost)"
