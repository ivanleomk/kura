# CLAUDE.md - Kura Explorer

This file provides guidance to Claude Code (claude.ai/code) when working with the Kura Explorer codebase.

## Overview

Kura Explorer is a modern web interface for exploring and analyzing Kura checkpoint data. It consists of:
- **Backend**: FastAPI application with SQLModel for efficient data querying
- **Frontend**: React + TypeScript + Vite with shadcn/ui components
- **Database**: SQLite (development) / PostgreSQL (production) for storing checkpoint data

## Architecture

### Backend (`/backend`)
- **main.py**: FastAPI application setup and middleware configuration
- **models.py**: Pydantic response models for API endpoints
- **routers/**: API endpoint implementations
  - `clusters.py`: Cluster-related endpoints
  - `conversations.py`: Conversation browsing and details
  - `insights.py`: Analytics and insights endpoints
  - `search.py`: Search functionality
- **API Documentation**: Available at http://localhost:8001/docs when running

### Database (`/db`)
- **models.py**: SQLModel database models
- **loader.py**: Checkpoint data loading logic
- Loads data from Kura checkpoint files into SQLite/PostgreSQL

### Frontend (`/frontend`)
- **src/pages/**: Main page components
  - `HomePage.tsx`: Dashboard overview
  - `ClustersPage.tsx`: Cluster listing and visualization
  - `ClusterDetailPage.tsx`: Individual cluster details
  - `ConversationsPage.tsx`: Conversation browser
  - `ConversationDetailPage.tsx`: Individual conversation view
  - `InsightsPage.tsx`: Analytics and insights
- **src/components/**: Reusable UI components
  - `ClusterMap.tsx`: 2D UMAP visualization
  - `ClusterTree.tsx`: Hierarchical cluster tree
  - `Layout.tsx`: App layout and navigation
- **src/lib/**: Utilities
  - `api.ts`: API client for backend communication
  - `utils.ts`: Helper functions

## Development Commands

### Quick Start (Recommended)
```bash
# Start everything with hot reloading
cd kura/explorer
./run-local.sh

# Or use Docker with hot reloading
./dev.sh
```

### Backend Development
```bash
cd backend
# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8001
```

### Frontend Development
```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

### Testing

#### Backend Tests
```bash
cd backend
# Run all tests
./run_tests.sh

# Run integration tests
./run_integration_tests.sh

# Run specific test file
pytest tests/test_clusters.py

# Run with coverage
pytest --cov=. --cov-report=html
```

#### Frontend Tests
```bash
cd frontend
# Run tests (when implemented)
npm test
```

## Key Features

1. **Interactive Dashboard**: Overview of conversations, clusters, and metrics
2. **Cluster Visualization**: 
   - 2D map view using UMAP coordinates
   - Hierarchical tree navigation
   - Frustration heatmaps
3. **Conversation Browser**: Search and filter conversations
4. **Advanced Analytics**:
   - Language distribution
   - Frustration pattern detection
   - Outlier identification
   - Theme extraction

## Data Flow

1. Kura generates checkpoint files from conversation analysis
2. Explorer backend loads checkpoint data into database
3. FastAPI serves data through REST endpoints
4. React frontend visualizes and allows exploration of data

## Environment Variables

### Backend
- `KURA_CHECKPOINT_DIR`: Path to checkpoint directory (required)
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `BACKEND_PORT`: API server port (default: 8001)

### Frontend
- `VITE_API_URL`: Backend API URL (default: http://localhost:8001)
- `FRONTEND_PORT`: Dev server port (default: 5173)

## Docker Development

```bash
# Start all services
docker-compose up

# With hot reloading
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access unified proxy
docker-compose --profile with-proxy up
# Access at http://localhost:8080
```

## Common Tasks

### Adding a New API Endpoint
1. Create/update router in `backend/routers/`
2. Add response models in `backend/models.py`
3. Update API client in `frontend/src/lib/api.ts`
4. Create/update frontend components to use new endpoint

### Adding a New Page
1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Update navigation in `frontend/src/components/Layout.tsx`

### Modifying Database Schema
1. Update models in `db/models.py`
2. Update loader logic in `db/loader.py` if needed
3. Recreate database or run migrations

## Troubleshooting

### Backend Issues
- **Checkpoint not found**: Verify `KURA_CHECKPOINT_DIR` path
- **Database errors**: Check SQLite file permissions or PostgreSQL connection
- **Import errors**: Ensure virtual environment is activated

### Frontend Issues
- **API connection failed**: Check backend is running on correct port
- **Build errors**: Clear node_modules and reinstall
- **Style issues**: Ensure Tailwind CSS is properly configured

### Docker Issues
- **Container won't start**: Check logs with `docker-compose logs`
- **Volume mount issues**: Verify checkpoint directory path in `.env`
- **Port conflicts**: Change ports in `.env` file

## Code Style

### Python (Backend)
- Use type hints for all functions
- Follow PEP 8 style guide
- Use async/await for I/O operations
- Add docstrings for complex functions

### TypeScript (Frontend)
- Use TypeScript strict mode
- Define interfaces for all API responses
- Use React hooks and functional components
- Follow ESLint configuration

## Performance Considerations

- Backend uses SQLModel for efficient queries
- Pagination implemented for large datasets
- Frontend uses React Query for caching (when implemented)
- Cluster visualizations are pre-computed in checkpoints

## Security Notes

- API endpoints are read-only
- No authentication required (local use only)
- For production: Add authentication and HTTPS