#!/bin/bash
# Script to build and serve the documentation

# Ensure mkdocstrings and other required plugins are installed
python3 -m pip install mkdocs-material mkdocstrings-python mkdocs-rss-plugin

# Build the documentation
echo "Building documentation..."
python3 -m mkdocs build

# Serve the documentation (optional)
echo "To serve the documentation locally, run:"
echo "python3 -m mkdocs serve --dev-addr=127.0.0.1:8000"