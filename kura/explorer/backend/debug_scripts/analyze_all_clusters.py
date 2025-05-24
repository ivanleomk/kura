"""Analyze all clusters to assess clustering quality."""

import json
from pathlib import Path
from collections import defaultdict

# Read checkpoint files
checkpoint_dir = Path("/Users/jasonliu/dev/kura/tutorial_checkpoints")

# Read clusters
clusters = {}
with open(checkpoint_dir / "clusters.jsonl", "r") as f:
    for line in f:
        cluster = json.loads(line)
        clusters[cluster["id"]] = cluster

# Read meta clusters
meta_clusters = {}
with open(checkpoint_dir / "meta_clusters.jsonl", "r") as f:
    for line in f:
        cluster = json.loads(line)
        meta_clusters[cluster["id"]] = cluster

# Read summaries
summaries = {}
with open(checkpoint_dir / "summaries.jsonl", "r") as f:
    for line in f:
        summary = json.loads(line)
        summaries[summary["chat_id"]] = summary

# Combine all clusters
all_clusters = {**clusters, **meta_clusters}

print(f"Total clusters: {len(clusters)}")
print(f"Total meta clusters: {len(meta_clusters)}")
print(f"Total summaries: {len(summaries)}")

# Analyze each cluster
print("\n" + "="*80)
print("CLUSTER ANALYSIS")
print("="*80)

# Sort clusters by number of conversations
sorted_clusters = sorted(all_clusters.items(), key=lambda x: len(x[1].get('chat_ids', [])), reverse=True)

for cluster_id, cluster in sorted_clusters[:20]:  # Top 20 clusters
    chat_ids = cluster.get('chat_ids', [])
    if len(chat_ids) == 0:
        continue
        
    print(f"\n{'='*80}")
    print(f"Cluster: {cluster['name']}")
    print(f"ID: {cluster_id}")
    print(f"Description: {cluster['description'][:200]}...")
    print(f"Number of conversations: {len(chat_ids)}")
    
    # Analyze diversity of topics
    tasks = []
    requests = []
    languages_used = defaultdict(int)
    
    for chat_id in chat_ids:
        if chat_id in summaries:
            summary = summaries[chat_id]
            if summary.get('task'):
                tasks.append(summary['task'])
            if summary.get('request'):
                requests.append(summary['request'])
            if summary.get('languages'):
                for lang in summary['languages']:
                    languages_used[lang] += 1
    
    # Calculate diversity metrics
    unique_tasks = len(set(tasks))
    task_diversity = unique_tasks / len(tasks) if tasks else 0
    
    print(f"\nDiversity metrics:")
    print(f"  - Unique tasks: {unique_tasks} out of {len(tasks)} ({task_diversity:.2%} diversity)")
    print(f"  - Languages: {dict(languages_used)}")
    
    # Sample conversations
    print(f"\nSample conversations (first 5):")
    for i, chat_id in enumerate(chat_ids[:5]):
        if chat_id in summaries:
            summary = summaries[chat_id]
            print(f"\n  {i+1}. Task: {summary.get('task', 'N/A')}")
            print(f"     Request: {summary.get('request', 'N/A')[:100]}...")

# Analyze overall clustering quality
print("\n" + "="*80)
print("OVERALL CLUSTERING QUALITY ANALYSIS")
print("="*80)

# Count clusters by size
size_distribution = defaultdict(int)
for cluster in all_clusters.values():
    size = len(cluster.get('chat_ids', []))
    if size > 0:
        size_distribution[size] += 1

print("\nCluster size distribution:")
for size in sorted(size_distribution.keys()):
    print(f"  - {size} conversations: {size_distribution[size]} clusters")

# Find clusters with high diversity (potential over-clustering)
high_diversity_clusters = []
for cluster_id, cluster in all_clusters.items():
    chat_ids = cluster.get('chat_ids', [])
    if len(chat_ids) < 3:  # Skip small clusters
        continue
        
    tasks = []
    for chat_id in chat_ids:
        if chat_id in summaries:
            task = summaries[chat_id].get('task')
            if task:
                tasks.append(task)
    
    if tasks:
        unique_tasks = len(set(tasks))
        diversity = unique_tasks / len(tasks)
        if diversity > 0.8:  # High diversity threshold
            high_diversity_clusters.append((cluster_id, cluster['name'], len(chat_ids), diversity))

print(f"\nClusters with high topic diversity (potential over-clustering):")
for cluster_id, name, size, diversity in sorted(high_diversity_clusters, key=lambda x: x[3], reverse=True)[:10]:
    print(f"  - {name}: {size} conversations, {diversity:.2%} task diversity")

# Find common patterns in cluster names
cluster_name_words = defaultdict(int)
for cluster in all_clusters.values():
    words = cluster['name'].lower().split()
    for word in words:
        if len(word) > 3:  # Skip short words
            cluster_name_words[word] += 1

print(f"\nMost common words in cluster names:")
for word, count in sorted(cluster_name_words.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  - {word}: {count} clusters")