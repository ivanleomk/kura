"""Analyze the clustering quality from checkpoint files."""

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

# Read summaries
summaries = {}
with open(checkpoint_dir / "summaries.jsonl", "r") as f:
    for line in f:
        summary = json.loads(line)
        summaries[summary["chat_id"]] = summary

# Analyze the problematic cluster
cluster_id = "a2b1f7456294467497d292b55def0b27"
if cluster_id in clusters:
    cluster = clusters[cluster_id]
    print(f"Cluster: {cluster['name']}")
    print(f"Description: {cluster['description']}")
    print(f"Number of conversations: {len(cluster['chat_ids'])}")
    
    # Check conversation topics
    print("\nConversations in this cluster:")
    for i, chat_id in enumerate(cluster['chat_ids'][:10]):
        if chat_id in summaries:
            summary = summaries[chat_id]
            print(f"\n{i+1}. {chat_id}")
            print(f"   Request: {summary.get('request', 'N/A')}")
            print(f"   Task: {summary.get('task', 'N/A')}")
            
    # Analyze what these conversations have in common
    print("\n\nAnalyzing commonalities:")
    tasks = []
    languages_used = defaultdict(int)
    
    for chat_id in cluster['chat_ids']:
        if chat_id in summaries:
            summary = summaries[chat_id]
            if summary.get('task'):
                tasks.append(summary['task'])
            if summary.get('languages'):
                for lang in summary['languages']:
                    languages_used[lang] += 1
    
    print(f"Unique tasks: {len(set(tasks))}")
    print(f"Language distribution: {dict(languages_used)}")
    
    # Check embeddings (if available)
    print("\n\nThis cluster appears to group conversations that are about:")
    print("- Data analysis (pandas, visualization)")
    print("- API development (Django, Spring Boot, REST)")
    print("- Content creation (blog posts, video scripts)")
    print("- Technical debugging")
    print("\nThe clustering seems too broad and groups unrelated technical assistance requests together.")