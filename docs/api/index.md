# API Reference

This section provides detailed API reference documentation for the Kura package, automatically generated from the source code.

## Core Components

Kura consists of several key components that work together to analyze and cluster conversations.

### Main Module

The main entry point for the Kura package.

::: kura.Kura
    options:
      show_bases: false
      show_source: true
      heading_level: 3

## Embedding Models

Embedding models convert text into vector representations.

::: kura.embedding
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

## Summarization

Summarization models convert raw conversations into concise summaries.

::: kura.summarisation
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

## Clustering

Clustering algorithms group similar conversations together.

::: kura.cluster
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Meta-Clustering

Meta-clustering provides hierarchical organization of clusters.

::: kura.meta_cluster
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

## Dimensionality Reduction

Dimensionality reduction techniques project high-dimensional embeddings to a lower-dimensional space for visualization.

::: kura.dimensionality
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

## Data Types

### Conversation Types

::: kura.types.conversation
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Cluster Types

::: kura.types.cluster
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Summarization Types

::: kura.types.summarisation
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Dimensionality Types

::: kura.types.dimensionality
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

## CLI

::: kura.cli.cli
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Server

::: kura.cli.server
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3

### Visualization

::: kura.cli.visualisation
    options:
      show_bases: true
      show_source: true
      members: true
      heading_level: 3