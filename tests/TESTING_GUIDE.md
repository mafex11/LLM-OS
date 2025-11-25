# Windows-Use Agent - Testing Guide

Complete guide to testing the Windows-Use Agent project.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Coverage](#coverage)
- [Troubleshooting](#troubleshooting)

## Overview

The test suite includes comprehensive tests for all tools and components:

- **Unit Tests**: Fast, isolated tests for individual functions and classes
- **Integration Tests**: Tests for complete workflows and tool execution
- **Automated Tests**: End-to-end tests with agent interaction

### Test Statistics

- **Total Test Files**: 15+
- **Test Coverage**: All 20+ agent tools
- **Test Categories**: Tools, Tracking, Desktop, Tree, Integration

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and pytest configuration
├── pytest.ini                  # Pytest settings
├── requirements-test.txt       # Test dependencies
├── run_all_tests.py           # Main test runner
├── run_quick_tests.bat        # Quick smoke tests (Windows)
├── TESTING_GUIDE.md           # This file
│
├── unit/                      # Unit tests (fast, isolated)
│   ├── tools/                # Agent tool tests
│   │   ├── test_tools_basic.py           # Done, Wait, Launch, Switch
│   │   ├── test_tools_input.py           # Click, Type, Key, Shortcut, Clipboard
│   │   ├── test_tools_navigation.py      # Scroll, Drag, Move, Resize
│   │   ├── test_tools_system.py          # System, Shell, Human, Scrape
│   │   └── test_tools_tracking.py        # Activity, Timeline, Schedule
│   │
│   ├── tracking/             # Activity tracking tests
│   │   ├── test_tracking_service.py      # ActivityTracker
│   │   ├── test_tracking_storage.py      # ActivityStorage
│   │   └── test_tracking_analyzer.py     # ActivityAnalyzer
│   │
│   ├── tree/                 # UI tree parsing tests
│   │   └── test_tree_service.py          # Tree service
│   │
│   ├── desktop/              # Desktop service tests
│   │   └── test_desktop_service.py       # Desktop operations
│   │
│   └── agent/                # Agent core tests
│       └── test_agent_service.py         # Agent execution
│
├── integration/              # Integration tests (slower)
│   └── test_tool_execution.py           # End-to-end tool flow
│
└── automated/               # Automated end-to-end tests
    ├── run_tests.py        # Automated test runner
    ├── test_cases.py       # Test definitions
    ├── test_logger.py      # Test logging
    └── README.md           # Automated testing docs
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest tests/

# Run quick smoke tests (Windows)
tests\run_quick_tests.bat
```

### Using the Test Runner

```bash
# Run all tests
python tests/run_all_tests.py

# Run only unit tests
python tests/run_all_tests.py --type unit

# Run integration tests
python tests/run_all_tests.py --type integration

# Run with coverage report
python tests/run_all_tests.py --coverage

# Run specific test file
python tests/run_all_tests.py --file tests/unit/tools/test_tools_basic.py

# List all available tests
python tests/run_all_tests.py --list
```

### Direct Pytest Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run specific test category
pytest tests/unit/tools/ -v

# Run tests matching marker
pytest -m "unit and not slow"

# Run with coverage
pytest tests/ --cov=windows_use --cov-report=html

# Run specific test function
pytest tests/unit/tools/test_tools_basic.py::TestDoneTool::test_done_tool_returns_answer -v
```

## Test Categories

### 1. Tool Tests (`tests/unit/tools/`)

Test all agent tools in isolation with mocked dependencies.

**Basic Tools**:
- `Done Tool`: Task completion
- `Wait Tool`: Delays
- `Launch Tool`: App launching
- `Switch Tool`: App switching

**Input Tools**:
- `Click Tool`: Mouse clicks
- `Type Tool`: Keyboard input
- `Key Tool`: Individual keys
- `Shortcut Tool`: Key combinations
- `Clipboard Tool`: Copy/paste

**Navigation Tools**:
- `Scroll Tool`: Scrolling
- `Drag Tool`: Drag and drop
- `Move Tool`: Cursor movement
- `Resize Tool`: Window management

**System Tools**:
- `System Tool`: System information
- `Shell Tool`: PowerShell commands
- `Human Tool`: User interaction
- `Scrape Tool`: Web scraping

**Tracking Tools**:
- `Activity Tool`: Activity queries
- `Timeline Tool`: Timeline analysis
- `Schedule Tool`: Task scheduling

**Run tool tests**:
```bash
pytest tests/unit/tools/ -v
```

### 2. Tracking Tests (`tests/unit/tracking/`)

Test activity tracking components.

**Components**:
- `ActivityTracker`: Activity monitoring
- `ActivityStorage`: Data persistence
- `ActivityAnalyzer`: AI analysis

**Run tracking tests**:
```bash
pytest tests/unit/tracking/ -v
```

### 3. Desktop Tests (`tests/unit/desktop/`)

Test desktop service operations.

**Features**:
- App listing and switching
- Window management
- Command execution
- UI element detection

**Run desktop tests**:
```bash
pytest tests/unit/desktop/ -v
```

### 4. Tree Tests (`tests/unit/tree/`)

Test UI tree parsing and element detection.

**Features**:
- Element traversal
- Interactive element detection
- Scrollable element identification
- Coordinate calculation

**Run tree tests**:
```bash
pytest tests/unit/tree/ -v
```

### 5. Integration Tests (`tests/integration/`)

Test complete workflows from agent to tool execution.

**Scenarios**:
- Tool execution flow
- Error handling
- Multi-step operations
- Registry operations

**Run integration tests**:
```bash
pytest tests/integration/ -v
```

### 6. Automated Tests (`tests/automated/`)

End-to-end tests with real agent interaction and grading.

**Features**:
- Real LLM interaction
- Comprehensive scenarios
- Automatic scoring
- Performance tracking

**Run automated tests**:
```bash
cd tests/automated
python run_tests.py
```

See `tests/automated/README.md` for detailed documentation.

## Writing Tests

### Test File Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Using Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_my_feature(mock_desktop, mock_llm):
    """Test using shared fixtures."""
    result = my_function(mock_desktop)
    assert result is not None
```

### Test Template

```python
"""
Tests for MyComponent.
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.my_module import MyComponent


class TestMyComponent:
    """Tests for MyComponent class."""
    
    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        return MyComponent()
    
    def test_basic_functionality(self, component):
        """Test basic feature."""
        result = component.do_something()
        assert result == expected_value
    
    @patch('windows_use.my_module.external_dependency')
    def test_with_mock(self, mock_dep, component):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        result = component.use_dependency()
        assert "mocked" in result
```

### Test Markers

Add markers to categorize tests:

```python
@pytest.mark.unit
def test_unit():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_integration():
    """Slower integration test."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Test that takes longer to run."""
    pass
```

Run tests by marker:
```bash
pytest -m "unit and not slow"
```

## Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest tests/ --cov=windows_use --cov-report=html --cov-report=term-missing

# View HTML report
# Open htmlcov/index.html in browser
```

### Coverage Goals

- **Overall**: >80%
- **Critical modules**: >90%
  - Agent tools
  - Desktop service
  - Tree service

### Check Coverage

```bash
# Summary in terminal
pytest --cov=windows_use --cov-report=term-missing

# Detailed HTML report
pytest --cov=windows_use --cov-report=html
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'windows_use'`

**Solution**:
```bash
# Ensure you're in project root
cd /path/to/Windows-Use

# Run tests from project root
pytest tests/
```

#### 2. Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'pytest'`

**Solution**:
```bash
# Install test dependencies
pip install -r tests/requirements-test.txt
```

#### 3. Tests Hanging

**Problem**: Tests hang indefinitely

**Solution**:
- Use pytest-timeout: `pytest --timeout=30`
- Check for infinite loops in code
- Verify mocks are set up correctly

#### 4. Failed Assertions

**Problem**: Tests fail with assertion errors

**Solution**:
- Run with verbose output: `pytest -vv`
- Check test logs: `tests/test_logs/pytest.log`
- Verify mock return values match expectations

#### 5. Windows-Specific Issues

**Problem**: Tests fail on Windows but not locally

**Solution**:
- Check path separators (use `Path` from `pathlib`)
- Verify Windows-specific dependencies are mocked
- Test with `run_quick_tests.bat`

### Debug Mode

Run tests with detailed output:

```bash
# Maximum verbosity
pytest -vv --tb=long --log-cli-level=DEBUG

# Stop on first failure
pytest -x

# Run specific test with debugging
pytest tests/unit/tools/test_tools_basic.py::TestDoneTool::test_done_tool_returns_answer -vv --tb=long
```

### Test Logs

Logs are saved to `tests/test_logs/pytest.log`:

```bash
# View recent test logs
tail -f tests/test_logs/pytest.log
```

## Best Practices

### 1. Test Isolation

Each test should be independent:
- Don't rely on test execution order
- Clean up resources after tests
- Use fixtures for setup/teardown

### 2. Mock External Dependencies

Always mock:
- Network calls
- File system operations
- UI automation calls
- External APIs

### 3. Test Names

Use descriptive test names:
```python
# Good
def test_click_tool_returns_error_for_out_of_bounds_coordinates():
    pass

# Bad
def test_click():
    pass
```

### 4. Assertions

Be specific with assertions:
```python
# Good
assert result == "Expected value"
assert "error" in result.lower()
assert len(items) == 3

# Bad
assert result
assert items
```

### 5. Test Documentation

Document test purpose:
```python
def test_feature():
    """
    Test that feature X correctly handles Y condition.
    
    This verifies:
    1. Proper input validation
    2. Correct error handling
    3. Expected return value
    """
    pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    
    - name: Run tests
      run: pytest tests/ --cov=windows_use --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For questions or issues:
1. Check this guide
2. Review existing tests for examples
3. Check test logs for errors
4. Open an issue on GitHub

---

**Last Updated**: November 2025


