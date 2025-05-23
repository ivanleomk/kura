# Kura Explorer API Documentation

## Overview

The Kura Explorer API provides RESTful endpoints for exploring and analyzing conversation data from Kura checkpoints. It offers powerful filtering, sorting, and aggregation capabilities.

Base URL: `http://localhost:8001`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Core Endpoints

### Health Check

```http
GET /api/health
```

Check the API health status and initialization state.

**Response:**
```json
{
  "status": "healthy",
  "explorer_initialized": true,
  "checkpoint_dir": "./checkpoints"
}
```

### Statistics

```http
GET /api/stats
```

Get overall statistics about the checkpoint data.

**Response:**
```json
{
  "total_conversations": 500,
  "total_messages": 3500,
  "total_summaries": 500,
  "total_clusters": 29,
  "root_clusters": 10,
  "max_cluster_level": 2
}
```

## Clusters

### List Clusters

```http
GET /api/clusters
```

Get clusters with pagination, filtering, and sorting.

**Query Parameters:**
- `parent_id` (string, optional): Filter by parent cluster ID
- `level` (integer, optional): Filter by cluster level (0 = root)
- `limit` (integer, default: 50): Number of results per page
- `offset` (integer, default: 0): Pagination offset
- `sort_by` (string, default: "name"): Sort field ["name", "conversation_count", "frustration"]
- `sort_desc` (boolean, default: false): Sort in descending order
- `language` (string, optional): Filter by language
- `min_frustration` (float, optional): Minimum average frustration score (1-5)

**Response:**
```json
{
  "items": [
    {
      "id": "cluster_123",
      "name": "Technical Support",
      "description": "Users seeking help with technical issues",
      "level": 0,
      "parent_id": null,
      "x_coord": 12.5,
      "y_coord": -3.2,
      "conversation_count": 150,
      "child_count": 3,
      "avg_frustration": 3.2,
      "languages": ["english", "python", "javascript"]
    }
  ],
  "total": 29,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

### Get Cluster Tree

```http
GET /api/clusters/tree
```

Get the full cluster hierarchy as a tree structure.

**Response:**
```json
[
  {
    "id": "root_cluster_1",
    "name": "Technical Support",
    "description": "...",
    "level": 0,
    "conversation_count": 150,
    "avg_frustration": 3.2,
    "children": [
      {
        "id": "child_cluster_1",
        "name": "API Issues",
        "description": "...",
        "level": 1,
        "conversation_count": 50,
        "avg_frustration": 3.5,
        "children": []
      }
    ]
  }
]
```

### Get Cluster Details

```http
GET /api/clusters/{cluster_id}
```

Get detailed information about a specific cluster.

**Response includes:**
- Basic cluster information
- Average frustration score
- Language distribution
- Parent and children clusters
- Sample conversations
- Full hierarchy path

### Get Cluster Summary

```http
GET /api/clusters/{cluster_id}/summary
```

Get aggregated summary statistics for a cluster.

**Response:**
```json
{
  "cluster_id": "cluster_123",
  "cluster_name": "Technical Support",
  "total_conversations": 150,
  "language_distribution": {
    "english": 150,
    "python": 45,
    "javascript": 30
  },
  "frustration_distribution": {
    "1": 20,
    "2": 40,
    "3": 50,
    "4": 30,
    "5": 10
  },
  "top_tasks": [
    {"task": "Debug API errors", "count": 25},
    {"task": "Fix authentication issues", "count": 20}
  ],
  "sample_summaries": ["..."]
}
```

## Conversations

### List Conversations

```http
GET /api/conversations
```

Get conversations with pagination and filtering.

**Query Parameters:**
- `cluster_id` (string, optional): Filter by cluster ID
- `search` (string, optional): Search in summaries
- `limit` (integer, default: 50): Results per page
- `offset` (integer, default: 0): Pagination offset
- `language` (string, optional): Filter by language
- `min_frustration` (integer, optional): Minimum frustration score (1-5)
- `max_frustration` (integer, optional): Maximum frustration score (1-5)

### Get Conversation Details

```http
GET /api/conversations/{conversation_id}
```

Get detailed conversation with all messages.

**Response includes:**
- Conversation metadata
- Full message history
- Summary information
- Associated clusters

## Search

### Search Conversations

```http
GET /api/search
```

Full-text search across all conversations and summaries.

**Query Parameters:**
- `q` (string, required): Search query (minimum 2 characters)
- `limit` (integer, default: 50): Maximum results

**Response:**
```json
{
  "conversations": [...],
  "total_count": 25,
  "query": "authentication error"
}
```

## Insights & Analysis

### Language Statistics

```http
GET /api/insights/language-stats
```

Get language usage statistics across all conversations.

**Response:**
```json
[
  {
    "language": "english",
    "count": 500,
    "percentage": 100.0
  },
  {
    "language": "python",
    "count": 150,
    "percentage": 30.0
  }
]
```

### Frustration Heatmap

```http
GET /api/insights/frustration-map
```

Get user frustration scores by cluster for visualization.

**Query Parameters:**
- `min_conversations` (integer, default: 5): Minimum conversations in cluster

**Response:**
```json
[
  {
    "cluster_id": "cluster_123",
    "cluster_name": "Technical Support",
    "avg_frustration": 3.5,
    "conversation_count": 150,
    "x_coord": 12.5,
    "y_coord": -3.2
  }
]
```

### Metadata Distribution

```http
GET /api/insights/metadata-dist?key=model
```

Analyze the distribution of metadata values.

**Query Parameters:**
- `key` (string, required): Metadata key to analyze

### Common Themes

```http
GET /api/insights/themes
```

Extract common themes across clusters.

**Query Parameters:**
- `min_frequency` (integer, default: 3): Minimum frequency for theme

### Outlier Conversations

```http
GET /api/insights/outliers
```

Find conversations that don't fit typical patterns.

**Response categorizes outliers by:**
- High frustration (score = 5)
- Very short conversations (≤ 2 messages)
- Multilingual (≥ 3 languages)
- Assistant errors

### Common Patterns

```http
GET /api/insights/common-patterns
```

Identify common conversation patterns and statistics.

### Compare Clusters

```http
POST /api/insights/compare-clusters
```

Compare multiple clusters side by side.

**Request Body:**
```json
{
  "cluster_ids": ["cluster_1", "cluster_2", "cluster_3"]
}
```

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": "cluster_1",
      "cluster_name": "Technical Support",
      "conversation_count": 150,
      "avg_frustration": 3.2,
      "top_languages": [["english", 150], ["python", 45]],
      "top_tasks": [["Debug API", 25], ["Fix auth", 20]],
      "level": 0
    }
  ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameter value"
}
```

### 404 Not Found
```json
{
  "detail": "Cluster not found"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Explorer not initialized"
}
```

## Rate Limiting

Currently, there are no rate limits on the API.

## Pagination

Most list endpoints support pagination using:
- `limit`: Number of results per page (max: 200)
- `offset`: Number of results to skip

The response includes:
- `total`: Total number of results
- `has_more`: Whether more pages are available

## OpenAPI Specification

The full OpenAPI 3.1.0 specification is available at:
- JSON: `/openapi.json`
- Interactive docs: `/docs` (Swagger UI)
- ReDoc: `/redoc`