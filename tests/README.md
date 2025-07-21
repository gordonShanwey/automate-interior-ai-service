# Testing Guide

This directory contains comprehensive tests for the Interior AI Service.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── unit/                    # Unit tests for individual components
│   ├── test_config.py       # Configuration tests
│   ├── test_health.py       # Health endpoint tests
│   ├── test_main.py         # Main application tests
│   ├── test_models.py       # Data model tests
│   └── test_webhooks.py     # Webhook endpoint tests
├── integration/             # Integration tests
│   └── test_health_integration.py
├── e2e/                     # End-to-end tests (future)
└── README.md               # This file
```

## Running Tests

### Quick Test Runner

Use the convenient test runner script:

```bash
# Run unit tests (default)
./run_tests.sh

# Run unit tests without coverage
./run_tests.sh quick

# Run integration tests
./run_tests.sh integration

# Run all tests
./run_tests.sh all

# Run tests with coverage report
./run_tests.sh coverage
```

### Direct Pytest Commands

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests only
uv run pytest tests/integration/

# Run specific test file
uv run pytest tests/unit/test_health.py

# Run specific test function
uv run pytest tests/unit/test_health.py::TestHealthEndpoints::test_health_check_basic

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run tests without coverage
uv run pytest --no-cov
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Fast execution
- High coverage of business logic

### Integration Tests (`tests/integration/`)
- Test interactions between components
- Test API endpoints with mocked external services
- Verify data flow between layers
- Test error handling and edge cases

### End-to-End Tests (`tests/e2e/`)
- Test complete workflows
- Use real external services (in test environment)
- Verify system behavior from user perspective
- Slower execution, comprehensive validation

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `app`: FastAPI application instance
- `client`: TestClient for making HTTP requests
- `async_client`: AsyncClient for async HTTP requests
- `mock_settings`: Mock configuration settings
- `mock_google_cloud_auth`: Mock Google Cloud authentication
- `mock_genai_client`: Mock Google GenAI client
- `mock_pubsub_client`: Mock Pub/Sub client
- `sample_client_data`: Sample client form data
- `sample_pubsub_message`: Sample Pub/Sub message

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_workflow():
    pass

@pytest.mark.e2e
def test_end_to_end_workflow():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

Run specific test categories:

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run tests excluding slow ones
uv run pytest -m "not slow"
```

## Coverage

The project aims for 80% test coverage. Coverage reports are generated automatically:

- HTML report: `htmlcov/index.html`
- Terminal report: Shows missing lines
- XML report: `coverage.xml` (for CI/CD)

## Writing Tests

### Guidelines

1. **Test Structure**: Use descriptive test class and function names
2. **Arrange-Act-Assert**: Structure tests with clear sections
3. **Mock External Dependencies**: Don't rely on external services in unit tests
4. **Test Edge Cases**: Include error conditions and boundary values
5. **Use Fixtures**: Reuse common test data and mocks

### Example

```python
class TestExample:
    def test_successful_operation(self, client: TestClient):
        """Test successful operation with valid input."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        response = client.post("/api/endpoint", json=test_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_error_handling(self, client: TestClient):
        """Test error handling with invalid input."""
        # Arrange
        invalid_data = {}
        
        # Act
        response = client.post("/api/endpoint", json=invalid_data)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
```

## Continuous Integration

Tests are automatically run in CI/CD pipeline:

- All tests must pass
- Coverage must be >= 80%
- No linting errors
- No security vulnerabilities

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `uv sync --dev`
2. **Mock Issues**: Check that mocks are properly configured in fixtures
3. **Async Tests**: Use `pytest-asyncio` for async test functions
4. **Coverage Issues**: Ensure all code paths are tested

### Debug Mode

Run tests with verbose output for debugging:

```bash
uv run pytest -v -s --tb=long
```

## Future Enhancements

- [ ] Add performance tests
- [ ] Add load testing
- [ ] Add security tests
- [ ] Add API contract tests
- [ ] Add visual regression tests (if UI is added) 