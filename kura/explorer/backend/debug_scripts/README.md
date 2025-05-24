# Debug Scripts

This directory contains debug scripts for analyzing clustering quality and troubleshooting issues.

## Scripts

### test_cluster_debug.py
Tests cluster-conversation relationships for a specific cluster. Checks if conversations are properly linked through the database relationships.

### analyze_clustering.py
Analyzes a specific cluster to understand why unrelated conversations are grouped together.

### analyze_all_clusters.py
Comprehensive analysis of all clusters, showing:
- Cluster size distribution
- Task diversity metrics
- Common patterns in cluster names
- Sample conversations from each cluster

### clustering_quality_report.py
Generates a summary report on clustering quality issues, including:
- Task diversity problems (most clusters have 100% unique tasks)
- Generic cluster naming patterns
- Specific examples of poor clustering
- Recommendations for improvement

## Usage

Run any script from the backend directory:
```bash
cd /Users/jasonliu/dev/kura/kura/explorer/backend
python debug_scripts/analyze_all_clusters.py
```

## Key Findings

The analysis revealed that the clustering algorithm is grouping unrelated conversations together. Nearly all clusters have 100% task diversity, meaning every conversation in a cluster is about a different topic. This indicates the clustering is too broad and only capturing high-level similarity (e.g., "technical assistance") rather than meaningful topic groupings.

The issue is with the original Kura clustering process, not the Explorer implementation.