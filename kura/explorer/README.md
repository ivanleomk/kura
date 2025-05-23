# Kura Explorer

A modern web interface for exploring and analyzing Kura checkpoint data.

## Features

- **Interactive Dashboard**: Overview of conversations, clusters, and key metrics
- **Cluster Visualization**: 
  - 2D map view using UMAP coordinates
  - Hierarchical tree navigation
  - Frustration heatmaps
- **Conversation Browser**: Search and filter through all conversations
- **Advanced Analytics**:
  - Language distribution analysis
  - Frustration pattern detection
  - Outlier identification
  - Theme extraction across clusters

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository and navigate to explorer directory
cd kura/explorer

# Copy the example environment file and edit it
cp .env.example .env
# Edit .env to set KURA_CHECKPOINT_DIR to your checkpoint directory

# Start all services
docker-compose up

# Or run in detached mode
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8001/docs

To use the unified proxy (both frontend and API on same port):
```bash
docker-compose --profile with-proxy up
# Access everything at http://localhost:8080
```

## 🔥 Development with Hot Reloading

For development with automatic rebuilding when files change:

### Quick Start
```bash
cd kura/explorer
./dev.sh
```

### Manual Start
```bash
# Start with hot reloading enabled
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

**What you get:**
- ✅ **Backend hot reloading** - Python file changes trigger automatic reloads
- ✅ **Frontend hot reloading** - React/TypeScript changes trigger instant rebuilds  
- ✅ **Fast HMR** - React Fast Refresh preserves component state
- ✅ **Tailwind CSS** - Style changes apply instantly
- ✅ **File watching** - Works reliably in Docker environment

**Access:**
- Frontend (with HMR): http://localhost:5173
- Backend API: http://localhost:8001

📖 **See [README.dev.md](./README.dev.md) for complete development guide**

### Option 2: Using the CLI

```bash
# Start the explorer with your checkpoint directory
kura explore ./checkpoints --port 8001
```

### Option 3: Manual Setup

1. Start the backend API:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

2. Start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```

3. Open http://localhost:5173 in your browser

### Option 4: Using the start script

```bash
cd kura/explorer
./start.sh
```

## Architecture

- **Backend**: FastAPI with SQLModel for efficient data querying
- **Frontend**: Vite + React + TypeScript with shadcn/ui components
- **Database**: SQLite (development) with support for PostgreSQL
- **Visualization**: Recharts for interactive charts and graphs

## API Documentation

The API documentation is available at http://localhost:8001/docs when the backend is running.

## Development

### Hot Reloading Development (Recommended)

For the best development experience with automatic rebuilding:

```bash
# Start development environment with hot reloading
./dev.sh

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This setup provides:
- **Backend**: `uvicorn --reload` watches Python files
- **Frontend**: Vite dev server with React Fast Refresh
- **Volume mounting**: Local files are mounted for instant updates
- **API proxy**: Frontend automatically proxies to backend

📖 **See [README.dev.md](./README.dev.md) for detailed development guide**

### Backend Development

The backend uses FastAPI and SQLModel. Key files:
- `backend/main.py` - FastAPI application setup
- `backend/routers/` - API endpoint implementations
- `backend/models.py` - Response models
- `db/models.py` - Database models
- `db/loader.py` - Checkpoint loading logic

### Frontend Development

The frontend uses React with TypeScript. Key directories:
- `frontend/src/pages/` - Main page components
- `frontend/src/components/` - Reusable UI components
- `frontend/src/lib/api.ts` - API client

### Adding New Features

1. Add new API endpoints in `backend/routers/`
2. Update the API client in `frontend/src/lib/api.ts`
3. Create new components or pages as needed
4. Update the navigation in `frontend/src/components/Layout.tsx`

**💡 Tip**: Use the hot reloading setup (`./dev.sh`) for fastest development iteration!

## Docker Configuration

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Managing Services

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (careful - this removes any stored data)
docker-compose down -v
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required
KURA_CHECKPOINT_DIR=./path/to/your/checkpoints

# Optional
VITE_API_URL=http://localhost:8001
BACKEND_PORT=8001
FRONTEND_PORT=5173
PROXY_PORT=8080
```

### Troubleshooting Docker

1. **Backend can't find checkpoints**: Make sure `KURA_CHECKPOINT_DIR` in `.env` points to the correct directory
2. **Frontend can't connect to backend**: Check that backend is healthy: `docker-compose ps`
3. **Port conflicts**: Change ports in `.env` file if defaults are in use

## Production Deployment

For production deployment:

1. Update `frontend/Dockerfile` to use production API URL
2. Consider using PostgreSQL instead of SQLite for better performance
3. Add SSL/TLS termination with a reverse proxy
4. Set up proper logging and monitoring

Example production docker-compose override:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/kura
    restart: unless-stopped

  frontend:
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=kura
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`