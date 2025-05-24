# Kura Explorer Backend Tests

This directory contains comprehensive tests for the Kura Explorer FastAPI backend application.

## Test Structure

The test suite is organized into the following files:

- **`conftest.py`** - Test configuration and shared fixtures
- **`test_main.py`** - Tests for main app endpoints (health, stats) and configuration
- **`test_clusters.py`** - Tests for clusters router endpoints
- **`test_conversations.py`** - Tests for conversations router endpoints
- **`test_search.py`** - Tests for search router endpoints
- **`test_runner.py`** - Custom test runner script with various options

## Prerequisites

Before running tests, ensure you have the testing dependencies installed:

```bash
# Install test dependencies
uv add --group dev pytest pytest-asyncio httpx pytest-mock pytest-cov

# Or install all optional dependencies
uv sync --all-extras
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term-missing

# Stop on first failure
uv run pytest -x
```

### Integration Tests (NEW)

**Cluster-Conversation Mapping Tests** - These tests use real checkpoint data to verify that clusters are properly mapped to conversations:

```bash
# Run all integration tests
./run_integration_tests.sh

# Run specific integration test categories
python tests/test_runner.py cluster-mapping
python tests/test_runner.py database

# Run individual integration test files
uv run pytest tests/test_integration_clusters.py -v -s
uv run pytest tests/test_database_integrity.py -v -s
```

**What Integration Tests Verify:**
- Database schema and table creation
- Conversation records created from summary data
- Cluster-conversation link integrity
- SQLModel ORM relationships working
- API endpoints returning real conversation data
- No orphaned records or broken links
- Accurate conversation counts across API and database

### Using the Custom Test Runner

The `test_runner.py` script provides convenient commands for different testing scenarios:

```bash
# Run all tests
python tests/test_runner.py all

# Run tests for specific router
python tests/test_runner.py router clusters
python tests/test_runner.py router conversations
python tests/test_runner.py router search

# Run tests matching a pattern
python tests/test_runner.py pattern "test_get_clusters"
python tests/test_runner.py pattern "TestHealth"

# Generate coverage report
python tests/test_runner.py coverage
```

### Running Specific Test Categories

```bash
# Run tests for a specific file
uv run pytest tests/test_clusters.py

# Run a specific test class
uv run pytest tests/test_clusters.py::TestGetClusters

# Run a specific test method
uv run pytest tests/test_clusters.py::TestGetClusters::test_get_clusters_success

# Run tests matching a keyword
uv run pytest -k "clusters and success"
```

## Test Categories

### 1. Main App Tests (`test_main.py`)
- Health check endpoint
- Statistics endpoint
- CORS configuration
- App metadata and configuration
- Error handling

### 2. Clusters Tests (`test_clusters.py`)
- GET `/api/clusters` - List clusters with pagination and filtering
- GET `/api/clusters/tree` - Cluster hierarchy tree
- GET `/api/clusters/{id}` - Individual cluster details
- GET `/api/clusters/{id}/summary` - Cluster aggregated summary
- Response model validation
- Dependency injection testing

### 3. Conversations Tests (`test_conversations.py`)
- GET `/api/conversations` - List conversations with filtering
- GET `/api/conversations/{id}` - Individual conversation details
- Pagination logic
- Filtering by language, frustration, cluster
- Response model validation

### 4. Search Tests (`test_search.py`)
- GET `/api/search` - Search across conversations
- Query validation (minimum length, required parameter)
- Result limiting and pagination
- Response structure validation
- Error handling

### 5. Integration Tests (NEW)

#### Database Integrity Tests (`test_database_integrity.py`)
- Database schema validation
- Table structure verification
- Data loading from checkpoint files
- Conversation-summary ID matching
- Cluster-conversation link validation
- ORM relationship testing

#### Cluster Mapping Tests (`test_integration_clusters.py`)
- Real cluster-conversation mapping verification
- API endpoint integration with real data
- Cluster tree structure validation
- Data integrity across all tables
- Search functionality integration
- API consistency checks

**Key Features:**
- Uses real checkpoint data from `tutorial_checkpoints/`
- Verifies 190 conversations, 29 clusters, 380 links
- Tests actual database relationships and API responses
- Validates data integrity and prevents regressions

## Test Fixtures

The test suite uses several fixtures defined in `conftest.py`:

### `mock_explorer`
A comprehensive mock of the `KuraExplorer` class with sample data including:
- Sample clusters with hierarchical relationships
- Sample conversations with metadata
- Sample summaries with languages, tasks, and frustration scores
- Mock search functionality

### `client`
A FastAPI `TestClient` instance with the mocked explorer injected.

### `async_client`
An async HTTP client for testing async endpoints.

### `sample_cluster_data` & `sample_conversation_data`
Sample data structures for testing response formats.

## Testing Patterns

### Mocking Database Sessions
Many tests mock SQLModel database sessions:

```python
with patch('routers.clusters.Session') as mock_session:
    mock_session_instance = Mock()
    mock_session.return_value.__enter__.return_value = mock_session_instance
    mock_session_instance.exec.return_value.all.return_value = sample_data
```

### Testing Error Conditions
Each router is tested for error conditions:
- Explorer not initialized (503 errors)
- Resource not found (404 errors)
- Validation errors (422 errors)
- Invalid parameters

### Response Model Validation
Tests verify response structure and data types:
- Required fields are present
- Optional fields have correct types when present
- Nested objects have proper structure
- Arrays contain expected item types

## Coverage Goals

The test suite aims for high coverage across:
- **Line Coverage**: >90% of code lines executed
- **Branch Coverage**: >85% of conditional branches tested
- **Function Coverage**: 100% of public functions tested

View coverage reports:
```bash
# Generate HTML coverage report
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal coverage report
uv run pytest --cov=. --cov-report=term-missing
```

## Best Practices

### Writing New Tests
1. **Use descriptive test names**: `test_get_clusters_with_pagination_success`
2. **Test one thing per test**: Focus on a single behavior
3. **Use appropriate fixtures**: Reuse mock data where possible
4. **Test error conditions**: Don't just test the happy path
5. **Verify mock calls**: Ensure the right methods are called with correct parameters

### Test Organization
1. **Group related tests in classes**: `TestGetClusters`, `TestHealthEndpoint`
2. **Use clear docstrings**: Explain what the test verifies
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Clean up after tests**: Use fixtures for setup/teardown

### Mocking Guidelines
1. **Mock external dependencies**: Database, file system, network calls
2. **Use specific mocks**: Mock exactly what you need
3. **Verify mock interactions**: Assert that mocks were called correctly
4. **Reset mocks between tests**: Use fresh mocks for each test

## Debugging Tests

### Running Failed Tests Only
```bash
# Re-run only failed tests
uv run pytest --lf

# Run failed tests first, then all others
uv run pytest --ff
```

### Debugging with Print Statements
```bash
# Show print statements and logs
uv run pytest -s

# Show more detailed output
uv run pytest -vv
```

### Using the Debugger
```bash
# Drop into debugger on failures
uv run pytest --pdb

# Drop into debugger on first failure
uv run pytest --pdb -x
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
- name: Run tests
  run: |
    uv run pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Performance Considerations

- Tests use mocked dependencies for speed
- Database operations are mocked to avoid I/O
- Parallel test execution is supported with `pytest-xdist`
- Test isolation prevents side effects between tests

## Troubleshooting

### Common Issues

**Import Errors**: Ensure `PYTHONPATH` includes the project root
```bash
export PYTHONPATH=/path/to/kura:$PYTHONPATH
```

**Mock Not Found**: Check that the patch path matches the actual import path in the code being tested

**Fixture Not Found**: Ensure fixtures are defined in `conftest.py` or imported properly

**Coverage Too Low**: Add tests for untested code paths, especially error conditions

### Environment Variables
Set these for testing:
- `KURA_CHECKPOINT_DIR=/tmp/test_checkpoints`
- `TESTING=true` (if used by the application)

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests cover both success and failure cases
3. Update this README if adding new test categories
4. Verify all tests pass before submitting PR
5. Aim to maintain or improve coverage percentage

## Running Integration Tests

### Prerequisites for Integration Tests
- Tutorial checkpoint data at `/Users/jasonliu/dev/kura/tutorial_checkpoints/`
- Files required: `summaries.jsonl`, `clusters.jsonl`, `meta_clusters.jsonl`, `dimensionality.jsonl`

### Integration Test Execution
```bash
# Complete integration test suite
./run_integration_tests.sh

# Quick verification of cluster-conversation mappings
python tests/test_runner.py cluster-mapping

# Database integrity only
python tests/test_runner.py database
```

### Integration Test Results
After running integration tests, check:
- `INTEGRATION_TEST_RESULTS.md` - Detailed results and analysis
- Console output for real-time verification
- Database state summary at end of test run

Example successful output:
```
✅ Found 190 conversations in database
✅ Found 380 cluster-conversation links
✅ Cluster-conversation relationships working!
```
