#!/bin/bash

# E-Commerce Platform Setup Script
# This script initializes all databases and loads sample data

set -e  # Exit on error

echo "========================================="
echo "E-Commerce Platform Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi
echo ""

# Stop existing containers if running
echo "Stopping existing containers..."
docker-compose down -v 2>/dev/null || true
echo -e "${GREEN}✓${NC} Cleaned up existing containers"
echo ""

# Start containers
echo "Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
echo -n "PostgreSQL"
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U admin -d ecommerce &>/dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo -n "MongoDB"
for i in {1..30}; do
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" &>/dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo -n "Redis"
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo -e "${GREEN}✓${NC} All services are ready"
echo ""

# Generate sample data using Node.js script
echo "Generating sample data..."
if [ -f "scripts/generate-data.js" ]; then
    node scripts/generate-data.js
    echo -e "${GREEN}✓${NC} Sample data generated"
else
    echo -e "${YELLOW}⚠${NC} Data generation script not found, using minimal sample data"
fi
echo ""

# Load sample data into PostgreSQL
echo "Loading sample data into PostgreSQL..."
if [ -f "data/postgres-sample-data.sql" ]; then
    docker-compose exec -T postgres psql -U admin -d ecommerce < data/postgres-sample-data.sql
    echo -e "${GREEN}✓${NC} PostgreSQL sample data loaded"
fi

# Load sample data into MongoDB
echo "Loading sample data into MongoDB..."
if [ -f "data/mongo-sample-data.js" ]; then
    docker-compose exec -T mongodb mongosh ecommerce < data/mongo-sample-data.js
    echo -e "${GREEN}✓${NC} MongoDB sample data loaded"
fi

# Populate Redis cache
echo "Warming up Redis cache..."
if [ -f "scripts/warm-cache.sh" ]; then
    bash scripts/warm-cache.sh
    echo -e "${GREEN}✓${NC} Redis cache warmed"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Services are running:"
echo "  • PostgreSQL:  localhost:5432"
echo "  • MongoDB:     localhost:27017"
echo "  • Redis:       localhost:6379"
echo "  • Adminer:     http://localhost:8080"
echo "  • Redis UI:    http://localhost:8081"
echo ""
echo "Database credentials:"
echo "  • PostgreSQL:  admin / ecommerce123"
echo "  • Database:    ecommerce"
echo ""
echo "Sample data loaded:"
echo "  • 10,000 products"
echo "  • 50,000 orders"
echo "  • 100,000 reviews"
echo "  • 5,000 customers"
echo ""
echo "Next steps:"
echo "  1. Run the demo:  ./scripts/demo.sh"
echo "  2. Or start AI-Shell:  ai-shell"
echo ""
echo "To stop services:  docker-compose down"
echo "To view logs:      docker-compose logs -f"
echo ""
