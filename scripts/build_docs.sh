#!/bin/bash
# Script to build and serve the documentation

# Ensure mkdocstrings is installed
python3 -m pip install mkdocs-material mkdocstrings mkdocstrings-python

# Build the documentation
echo "Building documentation..."
python3 -m mkdocs build

# Serve the documentation (optional)
echo "To serve the documentation locally, run:"
echo "python3 -m mkdocs serve"