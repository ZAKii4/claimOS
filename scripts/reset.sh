#!/bin/bash
echo "WARNING: This will DESTROY all data volumes."
read -p "Are you sure? (y/N) " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    docker compose down -v
    echo "Platform reset."
else
    echo "Aborted."
fi
