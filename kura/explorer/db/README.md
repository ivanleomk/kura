# Kura Explorer Database

Database models and checkpoint loading for Kura Explorer.

## Overview

This module handles:
- SQLModel database schema definition
- Loading Kura checkpoint files into a database
- Efficient querying of conversation and cluster data

## Architecture

```
db/
├── models.py    # SQLModel database models
└── loader.py    # Checkpoint data loading logic
```

## Database Schema

### Core Tables

#### Conversation
- `id`: Unique identifier
- `summary_id`: Link to summary
- `created_at`: Creation timestamp
- `message_count`: Number of messages
- `metadata`: JSON field for custom data

#### Summary
- `id`: Unique identifier
- `conversation_id`: Link to conversation
- `content`: Summary text
- `task`: Extracted task description
- `language`: Primary language
- `frustration_score`: User frustration level (1-5)

#### Message
- `id`: Unique identifier
- `conversation_id`: Link to conversation
- `role`: Message author (user/assistant)
- `content`: Message text
- `created_at`: Message timestamp

#### Cluster
- `id`: Unique identifier
- `name`: Cluster label
- `description`: Detailed description
- `level`: Hierarchy level (0=root)
- `parent_id`: Parent cluster reference
- `x_coord`: UMAP X coordinate
- `y_coord`: UMAP Y coordinate

#### ClusterSummary
- Links summaries to clusters (many-to-many)

## Data Loading

The loader reads Kura checkpoint files:
- `conversations.json`: Raw conversation data
- `summaries.jsonl`: Generated summaries
- `clusters.jsonl`: Base clusters
- `meta_clusters.jsonl`: Hierarchical clusters
- `dimensionality.jsonl`: 2D projections

### Loading Process

```python
from kura.explorer.db.loader import CheckpointLoader

# Load checkpoint data
loader = CheckpointLoader(checkpoint_dir="./checkpoints")
loader.load_all()

# Or load specific components
loader.load_conversations()
loader.load_summaries()
loader.load_clusters()
```

## Querying Data

### Using SQLModel

```python
from sqlmodel import Session, select
from kura.explorer.db.models import Cluster, Summary

# Get all root clusters
with Session(engine) as session:
    statement = select(Cluster).where(Cluster.level == 0)
    root_clusters = session.exec(statement).all()

# Get summaries for a cluster
with Session(engine) as session:
    cluster = session.get(Cluster, cluster_id)
    summaries = [cs.summary for cs in cluster.cluster_summaries]
```

### Efficient Queries

- Use pagination for large result sets
- Join related tables in single queries
- Index frequently queried fields
- Use JSON operators for metadata queries

## Database Configuration

### SQLite (Development)
Default database location: `./kura_explorer.db`

### PostgreSQL (Production)
Set `DATABASE_URL` environment variable:
```bash
DATABASE_URL=postgresql://user:password@localhost/kura_explorer
```

## Migrations

Currently, the database is recreated on each load. For production:
1. Use Alembic for migrations
2. Version the schema
3. Handle backwards compatibility

## Troubleshooting

### Common Issues

1. **"Database is locked"** (SQLite)
   - Close other connections
   - Use WAL mode for concurrent access

2. **Slow queries**
   - Add indexes on foreign keys
   - Use query optimization
   - Consider PostgreSQL for large datasets

3. **Memory issues**
   - Load data in batches
   - Use streaming for large files
   - Implement pagination

### Performance Tips

- Batch insert operations
- Use async database drivers
- Cache frequently accessed data
- Optimize JSON queries