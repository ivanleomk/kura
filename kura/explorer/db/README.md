# Kura Explorer Database

Database models and data loading logic for the Kura Explorer.

## Overview

This module handles the persistence layer for Kura Explorer, providing SQLModel ORM models and utilities for loading checkpoint data into a SQLite database.

## Components

### Models (`models.py`)

Defines the database schema using SQLModel:

- **KuraConversation**: Stores conversation data with messages and metadata
- **KuraCluster**: Represents clusters with hierarchical relationships
- **KuraSummary**: Links conversations to clusters with extracted properties
- **KuraConversationCluster**: Many-to-many relationship table

### Loader (`loader.py`)

The `KuraExplorer` class handles:

- Loading checkpoint files (JSON/JSONL format)
- Creating and populating the database
- Providing query methods for the API
- Managing database sessions and transactions

## Database Schema

### Tables

```sql
-- Conversations table
CREATE TABLE kura_conversation (
    id TEXT PRIMARY KEY,
    created_at DATETIME,
    messages JSON,
    metadata JSON
);

-- Clusters table  
CREATE TABLE kura_cluster (
    id INTEGER PRIMARY KEY,
    name TEXT,
    umap_x FLOAT,
    umap_y FLOAT,
    parent_cluster_id INTEGER,
    FOREIGN KEY (parent_cluster_id) REFERENCES kura_cluster(id)
);

-- Summaries table
CREATE TABLE kura_summary (
    id TEXT PRIMARY KEY,
    created_at DATETIME,
    conversation_id TEXT,
    task TEXT,
    cluster_id INTEGER,
    language TEXT,
    is_frustration BOOLEAN,
    metadata JSON,
    FOREIGN KEY (conversation_id) REFERENCES kura_conversation(id),
    FOREIGN KEY (cluster_id) REFERENCES kura_cluster(id)
);

-- Many-to-many relationship
CREATE TABLE kura_conversation_cluster (
    conversation_id TEXT,
    cluster_id INTEGER,
    PRIMARY KEY (conversation_id, cluster_id),
    FOREIGN KEY (conversation_id) REFERENCES kura_conversation(id),
    FOREIGN KEY (cluster_id) REFERENCES kura_cluster(id)
);
```

### Indexes

- Primary keys on all id fields
- Foreign key indexes for relationships
- Composite index on conversation_cluster table

## Usage

### Initializing the Explorer

```python
from kura.explorer.db.loader import KuraExplorer

# Initialize with checkpoint directory
explorer = KuraExplorer(checkpoint_dir="/path/to/checkpoints")

# Access the database engine
engine = explorer.engine
```

### Loading Data

The explorer automatically loads data from checkpoint files:

1. **conversations.json**: Raw conversation data
2. **summaries.jsonl**: Conversation summaries with tasks
3. **clusters.jsonl**: Base cluster information
4. **meta_clusters.jsonl**: Hierarchical cluster relationships
5. **dimensionality.jsonl**: UMAP coordinates for visualization

### Querying Data

```python
from sqlmodel import Session, select

# Get all clusters
with Session(explorer.engine) as session:
    clusters = session.exec(select(KuraCluster)).all()

# Get conversations for a cluster
with Session(explorer.engine) as session:
    cluster = session.get(KuraCluster, cluster_id)
    conversations = cluster.conversations

# Search conversations
with Session(explorer.engine) as session:
    results = session.exec(
        select(KuraConversation)
        .where(KuraConversation.messages.like(f"%{query}%"))
    ).all()
```

## Data Flow

1. **Checkpoint Loading**: Files are read from the checkpoint directory
2. **Data Parsing**: JSON/JSONL files are parsed into Python objects
3. **Database Creation**: Tables are created if they don't exist
4. **Data Insertion**: Objects are converted to ORM models and inserted
5. **Relationship Building**: Foreign keys and many-to-many relationships are established

## Error Handling

The loader includes error handling for:

- Missing checkpoint files
- Invalid JSON data
- Database connection issues
- Duplicate key violations
- Missing foreign key references

## Performance Optimization

### Bulk Loading

Data is loaded using bulk operations for efficiency:

```python
session.bulk_insert_mappings(KuraConversation, conversation_data)
```

### Transaction Management

All loads happen within a single transaction for consistency:

```python
with Session(engine) as session:
    # Load all data
    session.commit()  # Or rollback on error
```

### Memory Management

Large checkpoint files are processed in chunks to avoid memory issues.

## Extending the Models

To add new fields:

1. Update the SQLModel class definition
2. Add a migration script (if preserving existing data)
3. Update the loader to populate new fields
4. Update API response models as needed

Example:

```python
class KuraConversation(SQLModel, table=True):
    # Existing fields...
    
    # Add new field
    sentiment_score: Optional[float] = None
```

## Testing

The database module includes comprehensive tests:

- Model validation
- Relationship integrity
- Query performance
- Data loading accuracy

Run tests:

```bash
cd ../backend
uv run pytest tests/test_database_integrity.py -v
```

## Troubleshooting

### Common Issues

1. **"Table already exists"**: Database already initialized, delete SQLite file to reset
2. **"Foreign key constraint failed"**: Check that parent records exist
3. **"No such table"**: Ensure KuraExplorer is initialized before queries
4. **Memory errors**: Reduce batch size for large datasets

### Debug Queries

Enable SQL logging:

```python
import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

## Migration Guide

### From SQLite to PostgreSQL

1. Update DATABASE_URL environment variable
2. Install PostgreSQL driver: `pip install psycopg2`
3. Update connection string in KuraExplorer
4. Run data migration script

### Schema Changes

For backwards compatibility:

1. Add new fields as nullable
2. Provide default values
3. Update existing records in a migration
4. Make fields required in next version

## Best Practices

1. **Always use context managers** for database sessions
2. **Validate data** before inserting into database
3. **Use transactions** for multi-table operations
4. **Index frequently queried fields**
5. **Monitor query performance** in production