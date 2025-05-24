# Kura Explorer Backend

FastAPI backend for the Kura Explorer web interface.

## Overview

This backend provides REST API endpoints for exploring Kura checkpoint data, including:
- Cluster hierarchy navigation
- Conversation browsing and search
- Statistical analysis
- Metadata filtering

## Architecture

```
backend/
├── main.py              # FastAPI application and middleware
├── models.py            # Pydantic response models
├── routers/            # API endpoint implementations
│   ├── clusters.py     # Cluster-related endpoints
│   ├── conversations.py # Conversation endpoints
│   └── search.py       # Search functionality
└── tests/              # Test suite
```

## API Documentation

When running, interactive API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- OpenAPI JSON: http://localhost:8001/openapi.json

### Key Endpoints

- `GET /api/health` - Health check and status
- `GET /api/stats` - Overall statistics
- `GET /api/clusters` - List clusters (paginated)
- `GET /api/clusters/tree` - Hierarchical cluster tree
- `GET /api/clusters/{id}` - Cluster details
- `GET /api/conversations` - List conversations (paginated)
- `GET /api/conversations/{id}` - Conversation details
- `GET /api/search` - Search across all data

## Development

### Setup

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Running

```bash
# Development server with auto-reload
uvicorn main:app --reload --port 8001

# Production server
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Environment Variables

- `KURA_CHECKPOINT_DIR`: Path to checkpoint files (required)
- `DATABASE_URL`: Database connection string (optional)
- `BACKEND_PORT`: Server port (default: 8001)

## Testing

```bash
# Run all tests
./run_tests.sh

# Run specific tests
pytest tests/test_clusters.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
./run_integration_tests.sh
```

## Response Models

All API responses use Pydantic models defined in `models.py`:
- `ClusterResponse`: Cluster with metadata
- `ConversationResponse`: Conversation summary
- `ConversationDetailResponse`: Full conversation
- `StatsResponse`: Statistical overview
- `SearchResponse`: Search results

## Error Handling

Standard HTTP status codes:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `503 Service Unavailable`: Explorer not initialized

## Performance

- Pagination on all list endpoints
- Efficient SQLModel queries
- Response caching headers
- Async request handling

## Production Deployment

For production use:
1. Use PostgreSQL instead of SQLite
2. Configure proper logging
3. Add authentication if needed
4. Use a production ASGI server (uvicorn with workers)
5. Set up monitoring and alerting

Example production command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```
