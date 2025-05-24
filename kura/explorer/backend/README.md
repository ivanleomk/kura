# Kura Explorer Backend

FastAPI backend service for the Kura Explorer application.

## Overview

The backend provides a RESTful API for accessing and analyzing Kura checkpoint data. It loads checkpoint files into a SQLite database and exposes endpoints for querying clusters, conversations, and performing searches.

## Architecture

### Key Components

- **FastAPI Application** (`main.py`): Core application setup with CORS, middleware, and dependency injection
- **Routers** (`/routers`): API endpoint implementations organized by domain
  - `clusters.py`: Cluster-related endpoints
  - `conversations.py`: Conversation browsing and details
  - `search.py`: Full-text search functionality
- **Models** (`models.py`): Pydantic response models for API consistency
- **Database** (`../db`): SQLModel ORM models and data loading logic

### API Endpoints

#### Clusters
- `GET /api/clusters` - List all clusters with pagination
- `GET /api/clusters/tree` - Hierarchical cluster tree structure
- `GET /api/clusters/{id}` - Individual cluster details
- `GET /api/clusters/{id}/summary` - Aggregated cluster summary

#### Conversations
- `GET /api/conversations` - Browse conversations with filters
- `GET /api/conversations/{id}` - Individual conversation details

#### Search
- `GET /api/search` - Full-text search across conversations

#### System
- `GET /health` - Health check endpoint
- `GET /api/stats` - System statistics and overview

## Setup

### Installation

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -r requirements.txt
```

### Environment Variables

- `KURA_CHECKPOINT_DIR`: Path to checkpoint files directory (required)
- `DATABASE_URL`: SQLite database path (optional, defaults to in-memory)

### Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8001

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI app configuration
├── models.py            # Response models
├── routers/            # API endpoints
│   ├── clusters.py
│   ├── conversations.py
│   └── search.py
├── tests/              # Test suite
│   ├── conftest.py     # Test fixtures
│   ├── test_*.py       # Test files
│   └── README.md       # Testing documentation
├── debug_scripts/      # Analysis tools
└── requirements.txt    # Dependencies
```

### Adding New Endpoints

1. Create a new router in `/routers` directory
2. Define Pydantic models in `models.py`
3. Register the router in `main.py`
4. Add corresponding tests in `/tests`

### Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `404`: Resource not found
- `422`: Validation error
- `503`: Service unavailable (explorer not initialized)

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_clusters.py
```

### Integration Tests

```bash
# Run integration tests with real data
./run_integration_tests.sh

# Test cluster-conversation mappings
python tests/test_runner.py cluster-mapping
```

See `/tests/README.md` for comprehensive testing documentation.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### OpenAPI Schema

Generate the OpenAPI schema:

```bash
python extract_openapi.py > openapi.json
```

## Performance Considerations

- Database queries use indexes on cluster_id and conversation_id
- Pagination is implemented to handle large datasets
- Search uses SQL LIKE queries (consider full-text search for production)
- In-memory caching for frequently accessed data

## Debugging

### Debug Scripts

The `/debug_scripts` directory contains tools for analyzing data quality:

- `analyze_all_clusters.py`: Comprehensive cluster analysis
- `clustering_quality_report.py`: Quality metrics and issues
- `test_cluster_debug.py`: Test specific cluster relationships

### Common Issues

1. **Empty API responses**: Check that checkpoint files exist and contain valid data
2. **Slow queries**: Consider adding database indexes or using PostgreSQL
3. **Memory usage**: Large datasets may require pagination tuning

## Production Deployment

### Recommendations

1. **Database**: Use PostgreSQL instead of SQLite
   ```python
   DATABASE_URL = "postgresql://user:pass@localhost/kura"
   ```

2. **Process Manager**: Use Gunicorn with Uvicorn workers
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Monitoring**: Add application metrics and logging
4. **Security**: Enable authentication and rate limiting

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Contributing

1. Write tests for new features
2. Ensure all tests pass
3. Update API documentation
4. Follow existing code patterns