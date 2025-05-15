# Contributing to Kura

Thank you for your interest in contributing to Kura! This document provides guidelines and information to help you contribute effectively.

## Setting Up the Development Environment

1. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install the package in development mode with dev dependencies:
```bash
uv pip install -e ".[dev]"
```

## Testing

Kura uses pytest for testing. The current test suite primarily focuses on the meta-clustering functionality.

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_meta_cluster.py

# Run a specific test
pytest tests/test_meta_cluster.py::test_cluster_label_exact_match
```

### Test Structure

Tests are located in the `tests/` directory. The current tests verify:

- **Exact match functionality**: Tests that `ClusterLabel` correctly validates when there's an exact match between input and candidate clusters.
- **Fuzzy matching**: Tests that similar but not identical strings can be matched using fuzzy matching with an appropriate threshold.
- **Validation errors**: Tests that the system properly rejects inputs that don't match any candidates.

### Writing New Tests

When adding new features or fixing bugs, please include appropriate tests. Follow these guidelines:

1. Create test files with the `test_` prefix
2. Write test functions with descriptive names and docstrings
3. Use pytest fixtures when appropriate
4. Use assertions to verify expected behavior

## Type Checking

Kura uses pyright for type checking:

```bash
pyright
```

## Documentation

To work on documentation:

1. Install documentation dependencies:
```bash
uv pip install -e ".[docs]"
```

2. Serve documentation locally:
```bash
mkdocs serve
```

## Code Style

- Follow PEP 8 guidelines for Python code
- Use type hints for all function parameters and return values
- Write docstrings for all public classes and functions

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## UI Development

If you're working on the UI:

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```