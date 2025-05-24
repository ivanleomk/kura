# Kura Explorer Plan

## Overview

Build a web-based explorer for Kura checkpoint data with efficient database querying and modern UI.

## Architecture

### Backend (FastAPI + SQLModel)
- **Location**: `/kura/explorer/backend/`
- **Database**: SQLite (development) → PostgreSQL (production)
- **ORM**: SQLModel (already implemented)
- **Features**:
  - Paginated API endpoints
  - Efficient query optimization
  - Search functionality
  - Cluster hierarchy navigation

### Frontend (Vite + React + TypeScript + shadcn/ui)
- **Location**: `/kura/explorer/frontend/`
- **UI Library**: shadcn/ui with Tailwind CSS
- **State Management**: TanStack Query for server state
- **Routing**: React Router
- **Features**:
  - Cluster visualization (tree and graph views)
  - Conversation browser with search
  - Summary and message viewers
  - Metadata filtering

## API Endpoints

### Core Endpoints
```
GET  /api/stats                          # Overall statistics
GET  /api/clusters                       # List clusters (paginated)
GET  /api/clusters/:id                   # Cluster details
GET  /api/clusters/tree                  # Full hierarchy tree
GET  /api/conversations                  # List conversations (paginated)
GET  /api/conversations/:id              # Conversation details
GET  /api/search?q=...                   # Search across data
```

### Analysis Endpoints
```
GET  /api/clusters/:id/summary           # Aggregated summary of cluster
```

### Query Parameters
- `limit`: Page size (default: 50)
- `offset`: Pagination offset
- `parent_id`: Filter clusters by parent
- `level`: Filter clusters by level
- `cluster_id`: Filter conversations by cluster
- `sort`: Sort field and direction

## Frontend Components

### Layout
- `App.tsx` - Main app with routing
- `Layout.tsx` - Shared layout with navigation

### Pages
- `HomePage.tsx` - Dashboard with stats
- `ClustersPage.tsx` - Cluster explorer with map view
- `ConversationsPage.tsx` - Conversation browser
- `ClusterDetailPage.tsx` - Single cluster analysis
- `ConversationDetailPage.tsx` - Single conversation view
- `InsightsPage.tsx` - Cross-cluster patterns and trends
- `ComparePage.tsx` - Compare multiple clusters

### Core Components
- `ClusterTree.tsx` - Hierarchical cluster view
- `ClusterMap.tsx` - 2D cluster visualization with UMAP coordinates
- `ConversationList.tsx` - Paginated conversation table
- `MessageViewer.tsx` - Conversation messages display
- `SearchBar.tsx` - Global search component
- `StatsCards.tsx` - Statistics dashboard

### Analysis Components
- `ClusterSummaryPanel.tsx` - Aggregate view of cluster themes
- `MetadataDistribution.tsx` - Visualize metadata across clusters
- `LanguageAnalysis.tsx` - Language distribution and patterns
- `TopicEvolution.tsx` - How topics change over time
- `UserFrustrationMap.tsx` - Heatmap of frustration scores
- `CommonPatternsView.tsx` - Recurring conversation patterns
- `OutlierDetection.tsx` - Unusual conversations that don't fit

### UI Components (shadcn/ui)
- Card, Table, Dialog, Tabs
- Command (for search)
- ScrollArea (for long content)
- Separator, Badge, Button
- Skeleton (for loading states)

## Key Insights & Analysis Views

### 1. Cluster Overview Map
- 2D visualization using UMAP coordinates
- Bubble size = number of conversations
- Color intensity = average user frustration
- Click to zoom into cluster details
- Show connections between related clusters

### 2. Theme Extraction
- Common topics across all conversations
- Word clouds for each cluster
- Trending topics over time
- Comparing themes between meta-clusters

### 3. Conversation Patterns
- Common conversation flows (e.g., greeting → question → clarification → solution)
- Identify where conversations typically get stuck
- Success vs. failure patterns
- Average conversation length by cluster

### 4. User Insights
- Frustration hotspots (what topics frustrate users)
- Language distribution (what languages need better support)
- Request complexity analysis
- User intent classification

### 5. Outlier Analysis
- Conversations that don't fit any cluster well
- Extremely long or short conversations
- High frustration scores
- Unusual language combinations

### 6. Comparative Views
- Side-by-side cluster comparison
- Before/after analysis (if temporal data available)
- Cross-cluster metadata correlation
- Performance metrics by cluster

## Data Flow

1. **Initial Load**:
   - User runs `kura explore <checkpoint_dir>`
   - Backend loads checkpoint data into SQLite
   - Frontend connects to API

2. **Navigation**:
   - User browses clusters hierarchically
   - API returns paginated results
   - Frontend caches with TanStack Query

3. **Search**:
   - User searches across conversations/summaries
   - Backend performs indexed search
   - Results displayed with highlighting

## Implementation Steps

### Phase 1: Backend Setup
1. Create FastAPI app structure
2. Implement paginated endpoints
3. Add search functionality
4. Set up CORS and error handling

### Phase 2: Frontend Foundation
1. Initialize Vite + React + TypeScript
2. Install and configure shadcn/ui
3. Set up routing and layout
4. Create API client with TanStack Query

### Phase 3: Core Features
1. Build cluster tree view
2. Implement conversation browser
3. Add detail pages
4. Create search interface

### Phase 4: Enhancements
1. Add 2D cluster visualization
2. Implement filters and sorting
3. Add export functionality
4. Performance optimizations

## CLI Integration

```bash
# Start explorer with checkpoint directory
kura explore ./checkpoints

# This will:
# 1. Load data into SQLite (if needed)
# 2. Start FastAPI backend on port 8000
# 3. Start Vite dev server on port 5173
# 4. Open browser to http://localhost:5173
```

## Future Enhancements

1. **PostgreSQL Migration**:
   - Add connection string configuration
   - Implement migration scripts
   - Add connection pooling

2. **Advanced Features**:
   - Real-time updates
   - Collaborative annotations
   - Export to various formats
   - Conversation replay

3. **Visualizations**:
   - Time-series analysis
   - Cluster evolution
   - Embedding space exploration

## Technology Choices Rationale

- **FastAPI**: Fast, modern Python web framework with automatic OpenAPI docs
- **SQLModel**: Combines SQLAlchemy + Pydantic, already integrated
- **Vite**: Fast development experience with HMR
- **shadcn/ui**: Modern, accessible components that look professional
- **TanStack Query**: Powerful data fetching with caching
- **TypeScript**: Type safety across frontend

## Development Workflow

1. Backend development:
   ```bash
   cd kura/explorer/backend
   uvicorn main:app --reload
   ```

2. Frontend development:
   ```bash
   cd kura/explorer/frontend
   npm run dev
   ```

3. Full stack:
   ```bash
   kura explore ./checkpoints
   ```