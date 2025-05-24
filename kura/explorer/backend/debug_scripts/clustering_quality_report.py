"""Generate a clustering quality report."""

import json
from pathlib import Path
from collections import defaultdict

# Read checkpoint files
checkpoint_dir = Path("/Users/jasonliu/dev/kura/tutorial_checkpoints")

# Read all cluster types
all_clusters = {}

# Read base clusters
with open(checkpoint_dir / "clusters.jsonl", "r") as f:
    for line in f:
        cluster = json.loads(line)
        all_clusters[cluster["id"]] = cluster

# Read meta clusters
with open(checkpoint_dir / "meta_clusters.jsonl", "r") as f:
    for line in f:
        cluster = json.loads(line)
        all_clusters[cluster["id"]] = cluster

# Read summaries
summaries = {}
with open(checkpoint_dir / "summaries.jsonl", "r") as f:
    for line in f:
        summary = json.loads(line)
        summaries[summary["chat_id"]] = summary

print("CLUSTERING QUALITY REPORT")
print("=" * 80)
print(f"\nTotal clusters analyzed: {len(all_clusters)}")
print(f"Total conversations: {len(summaries)}")

# Key finding 1: Task diversity
print("\n1. TASK DIVERSITY PROBLEM")
print("-" * 40)
print("Most clusters have 100% task diversity, meaning every conversation")
print("in the cluster has a completely different task. This indicates")
print("the clustering is too broad and not capturing meaningful similarity.")

high_diversity_count = 0
for cluster_id, cluster in all_clusters.items():
    chat_ids = cluster.get("chat_ids", [])
    if len(chat_ids) < 3:
        continue

    tasks = set()
    for chat_id in chat_ids:
        if chat_id in summaries:
            task = summaries[chat_id].get("task")
            if task:
                tasks.add(task)

    if len(tasks) == len(chat_ids):
        high_diversity_count += 1

print(
    f"\nClusters with 100% task diversity: {high_diversity_count} out of {len(all_clusters)}"
)

# Key finding 2: Generic cluster names
print("\n2. GENERIC CLUSTER NAMES")
print("-" * 40)
print("Cluster names are too generic and repetitive:")

# Count word frequency
word_freq = defaultdict(int)
for cluster in all_clusters.values():
    words = cluster["name"].lower().split()
    for word in words:
        if len(word) > 3:
            word_freq[word] += 1

print("\nMost common words in cluster names:")
for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  - '{word}': appears in {count} clusters")

# Key finding 3: Example of poor clustering
print("\n3. EXAMPLE OF POOR CLUSTERING")
print("-" * 40)
print("Cluster: 'Assist with data analysis and debugging in APIs'")
print("This cluster contains:")

cluster_id = "a2b1f7456294467497d292b55def0b27"
if cluster_id in all_clusters:
    cluster = all_clusters[cluster_id]
    topics = []

    for chat_id in cluster.get("chat_ids", [])[:10]:
        if chat_id in summaries:
            task = summaries[chat_id].get("task", "Unknown")
            # Extract the main topic from task
            if "YouTube" in task:
                topics.append("YouTube video scripts")
            elif "white paper" in task:
                topics.append("White paper writing")
            elif "visualization" in task:
                topics.append("Data visualization")
            elif "blog" in task:
                topics.append("Blog writing")
            elif "Django" in task:
                topics.append("Django REST API")
            elif "Flutter" in task:
                topics.append("Flutter development")
            elif "Spark" in task:
                topics.append("Spark/Kafka streaming")
            elif "Spring Boot" in task:
                topics.append("Spring Boot development")
            elif "SEO" in task:
                topics.append("SEO optimization")
            else:
                topics.append("Other technical assistance")

    print("\nTopics found in this cluster:")
    for i, topic in enumerate(set(topics), 1):
        print(f"  {i}. {topic}")

# Key finding 4: Recommendations
print("\n4. RECOMMENDATIONS")
print("-" * 40)
print("The current clustering has several issues:")
print("1. Clusters are too broad and capture only high-level similarity")
print("2. Many unrelated technical topics are grouped together")
print("3. The embedding/clustering process needs refinement")
print("\nTo improve clustering quality:")
print("1. Increase the number of clusters for more granular grouping")
print("2. Use domain-specific embeddings that better capture technical differences")
print("3. Consider hierarchical clustering with better-defined levels")
print("4. Add post-processing to split overly broad clusters")

# Summary statistics
print("\n5. CLUSTERING STATISTICS")
print("-" * 40)

# Cluster size distribution
size_dist = defaultdict(int)
for cluster in all_clusters.values():
    size = len(cluster.get("chat_ids", []))
    if size > 0:
        size_dist[size] += 1

print("\nCluster sizes:")
total_convs_in_clusters = 0
for size in sorted(size_dist.keys()):
    count = size_dist[size]
    total_convs_in_clusters += size * count
    print(f"  - {count} clusters with {size} conversations each")

print(f"\nTotal conversations in clusters: {total_convs_in_clusters}")
print(
    f"Average conversations per cluster: {total_convs_in_clusters / len(all_clusters):.1f}"
)
