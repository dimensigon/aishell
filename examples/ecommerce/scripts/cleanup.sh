#!/bin/bash

# E-Commerce Platform Cleanup Script
# Stops containers and removes all data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "E-Commerce Platform Cleanup"
echo "========================================="
echo ""
echo -e "${YELLOW}WARNING: This will remove all containers and data!${NC}"
echo ""
echo -n "Are you sure? (yes/no): "
read confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
echo "Stopping containers..."
docker-compose down -v

echo "Removing volumes..."
docker volume rm ecommerce_postgres_data 2>/dev/null || true
docker volume rm ecommerce_mongodb_data 2>/dev/null || true
docker volume rm ecommerce_redis_data 2>/dev/null || true

echo "Cleaning up generated files..."
rm -rf backups/ 2>/dev/null || true
rm -rf data/generated/ 2>/dev/null || true

echo ""
echo -e "${GREEN}✓ Cleanup complete!${NC}"
echo ""
echo "To start fresh, run:"
echo "  ./scripts/setup.sh"
echo ""
