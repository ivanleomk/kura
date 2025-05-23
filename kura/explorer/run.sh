#!/bin/bash

# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Kura Explorer...${NC}"

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env to set KURA_CHECKPOINT_DIR to your checkpoint directory${NC}"
    echo -e "${YELLOW}   Default is set to ./checkpoints${NC}"
fi

# Source the .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if checkpoint directory exists
if [ ! -d "$KURA_CHECKPOINT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Checkpoint directory not found: $KURA_CHECKPOINT_DIR${NC}"
    echo -e "${YELLOW}   Creating example checkpoint directory...${NC}"
    mkdir -p "$KURA_CHECKPOINT_DIR"
fi

# Pull latest base images for caching
echo -e "${BLUE}📦 Pulling base images...${NC}"
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine

# Build with caching
echo -e "${BLUE}🔨 Building services with caching...${NC}"
docker-compose build --parallel

# Start services
echo -e "${GREEN}✅ Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check health
HEALTH_CHECK=$(curl -s http://localhost:8001/api/health || echo "failed")
if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend health check failed. Checking logs...${NC}"
    docker-compose logs backend | tail -20
fi

echo -e "${GREEN}🎉 Kura Explorer is running!${NC}"
echo -e "${BLUE}📊 Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}🔧 API Docs: http://localhost:8001/docs${NC}"
echo -e "${BLUE}📝 Logs: docker-compose logs -f${NC}"
echo -e "${BLUE}🛑 Stop: docker-compose down${NC}"