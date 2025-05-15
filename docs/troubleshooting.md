# Troubleshooting and Best Practices

This guide helps you solve common issues when working with Kura and provides best practices for effective usage.

## Common Issues

### Installation Problems

#### UMAP Installation Fails

**Problem**: Installing Kura fails with errors related to UMAP.

**Solution**: UMAP has specific dependencies and works best with Python 3.9:

```bash
# Create a Python 3.9 environment
conda create -n kura-env python=3.9
conda activate kura-env

# Install Kura
pip install kura
```

#### API Key Issues

**Problem**: Getting errors about invalid or missing API keys.

**Solution**: Ensure your API keys are correctly set:

```bash
# For Google Gemini (default model)
export GOOGLE_API_KEY=your_google_api_key

# If using OpenAI
export OPENAI_API_KEY=your_openai_api_key
```

On Windows, use `set` instead of `export`.

### Processing Errors

#### Not Enough Conversations

**Problem**: Clustering results are poor or don't make sense.

**Solution**: Kura works best with at least 100 conversations. With fewer, the clusters may not be meaningful:

```python
# Ensure you have enough data
if len(conversations) < 100:
    print("Warning: For meaningful clusters, provide at least 100 conversations")
```

#### Rate Limiting

**Problem**: Getting rate limit errors from API providers.

**Solution**: Adjust concurrency limits and implement retries:

```python
# Configure summarization model with lower concurrency
summary_model = SummaryModel(
    concurrent_requests={
        "default": 20,  # Lower from default of 50
        "openai": 50,   # Lower from default of 100
    }
)
```

#### Memory Issues

**Problem**: Running out of memory with large datasets.

**Solution**: Process data in batches and manage checkpoints:

```python
# Process in batches of 1000
batch_size = 1000
for i in range(0, len(conversations), batch_size):
    batch = conversations[i:i+batch_size]
    kura = Kura(checkpoint_dir=f"./checkpoints_batch_{i//batch_size}")
    asyncio.run(kura.cluster_conversations(batch))
```

### Visualization Issues

#### Web Server Won't Start

**Problem**: The `kura start-app` command fails.

**Solution**: 
1. Ensure the checkpoint directory exists and contains all required files
2. Check if port 8000 is available, or specify a different port
3. Make sure you have run the clustering process first

#### Poor Visualization Results

**Problem**: Clusters overlap too much or are hard to interpret.

**Solution**: Try different dimensionality reduction parameters:

```python
from kura.dimensionality import HDBUMAP

# Try different UMAP parameters
dimensionality_model = HDBUMAP(
    n_neighbors=30,  # Increase for more global structure (default: 15)
    min_dist=0.25,   # Increase for more spread (default: 0.1)
    n_components=2   # Keep at 2 for visualization
)

kura = Kura(dimensionality_reduction=dimensionality_model)
```

## Best Practices

### Data Preparation

1. **Quality Over Quantity**: For better results, prioritize conversation quality over sheer volume
2. **Diverse Dataset**: Include a diverse range of conversation topics and styles
3. **Clean Data**: Remove any corrupted or incomplete conversations

### Model Selection

1. **Model Compatibility**: Ensure embedding and summarization models work well together
2. **API Costs**: Consider API usage costs when selecting models
3. **Experimentation**: Try different models to find the best for your specific data

```python
# Example of trying different embedding models
from kura.embedding import OpenAIEmbeddingModel

# Try different embedding models
embedding_models = [
    OpenAIEmbeddingModel(model="text-embedding-3-small"),
    OpenAIEmbeddingModel(model="text-embedding-3-large")
]

for i, model in enumerate(embedding_models):
    kura = Kura(
        embedding_model=model,
        checkpoint_dir=f"./checkpoints_model_{i}"
    )
    asyncio.run(kura.cluster_conversations(conversations))
```

### Performance Optimization

1. **Checkpoint Management**: Use checkpoints to avoid reprocessing
2. **Concurrency Settings**: Adjust concurrency based on your API rate limits
3. **Metadata Extraction**: Only extract metadata that's necessary for your analysis

### Cluster Interpretation

1. **Start High-Level**: Begin by examining top-level clusters
2. **Drill Down**: Explore subclusters to understand finer distinctions
3. **Use Metadata**: Leverage metadata to identify patterns within clusters

### Workflow Integration

1. **Regular Processing**: Set up regular processing of new conversations
2. **Compare Results**: Compare clusters over time to identify trends
3. **Share Results**: Use the web interface to share insights with your team

## Advanced Troubleshooting

If you encounter issues not covered here:

1. Check the logs for detailed error messages
2. Examine the checkpoint files to understand the state of processing
3. Try running with a small sample of conversations to isolate the issue
4. Use Python's debugger to trace through the processing steps

## Getting Help

If you continue to experience issues:

1. File an issue on the [GitHub repository](https://github.com/567-labs/kura/issues)
2. Include detailed information about your environment and the specific error
3. If possible, provide a minimal reproducible example