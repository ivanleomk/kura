"""Test the API setup."""

import os

os.environ["KURA_CHECKPOINT_DIR"] = "/Users/jasonliu/dev/kura/tutorial_checkpoints"

from kura.explorer.api import KuraExplorer

# Test loading the explorer
print("Testing KuraExplorer...")
explorer = KuraExplorer("/Users/jasonliu/dev/kura/tutorial_checkpoints")

# Get stats
stats = explorer.get_stats()
print(f"\nStats: {stats}")

# Get some clusters
clusters = explorer.db.query("SELECT * FROM clusters LIMIT 5")
print(f"\nSample clusters: {len(clusters)} found")
for cluster in clusters:
    print(f"  - {cluster['name']}: {cluster['description'][:50]}...")
