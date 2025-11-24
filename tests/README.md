# Windows-Use Agent - Testing Suite

This directory contains all testing resources for the Windows-Use Agent project.

## Directory Structure

```
tests/
├── conftest.py                # Shared pytest fixtures and configuration
├── pytest.ini                 # Pytest settings
├── requirements-test.txt      # Test dependencies
├── run_all_tests.py          # Main test runner
├── run_quick_tests.bat       # Quick smoke tests (Windows)
├── TESTING_GUIDE.md          # Complete testing guide (NEW!)
├── README.md                 # This file
│
├── unit/                     # Unit tests for individual components ⭐ ENHANCED
│   ├── tools/               # Agent tool tests (NEW!)
│   │   ├── test_tools_basic.py         # Done, Wait, Launch, Switch
│   │   ├── test_tools_input.py         # Click, Type, Key, Shortcut, Clipboard
│   │   ├── test_tools_navigation.py    # Scroll, Drag, Move, Resize
│   │   ├── test_tools_system.py        # System, Shell, Human, Scrape
│   │   └── test_tools_tracking.py      # Activity, Timeline, Schedule
│   │
│   ├── tracking/            # Activity tracking tests (NEW!)
│   │   ├── test_tracking_service.py    # ActivityTracker
│   │   ├── test_tracking_storage.py    # ActivityStorage
│   │   └── test_tracking_analyzer.py   # ActivityAnalyzer
│   │
│   ├── tree/                # UI tree parsing tests
│   │   └── test_tree_service.py        # Tree service (ENHANCED)
│   │
│   ├── desktop/             # Desktop service tests
│   │   └── test_desktop_service.py     # Desktop operations (ENHANCED)
│   │
│   └── agent/               # Agent core tests
│       └── test_agent_service.py       # Agent execution
│
├── integration/             # Integration tests (NEW!)
│   └── test_tool_execution.py          # End-to-end tool flow
│
└── automated/              # Automated integration testing
    ├── results/           # Test results and reports
    ├── run_tests.py       # Main test runner
    ├── test_cases.py      # Test definitions
    ├── test_logger.py     # Logging system
    ├── benchmark.py       # Performance benchmarks
    ├── quick_test.bat     # Windows quick start
    ├── README.md          # Detailed documentation
    ├── TESTING_GUIDE.md   # Complete testing guide
    ├── EXAMPLE_REPORT.md  # Sample test reports
    └── QUICK_REFERENCE.md # Quick reference card
```

## Quick Start

### Run All Tests (NEW!)

```cmd
# Run all tests with the main test runner
python tests/run_all_tests.py

# Run quick smoke tests (Windows)
tests\run_quick_tests.bat

# Run only unit tests
python tests/run_all_tests.py --type unit

# Run with coverage report
python tests/run_all_tests.py --coverage
```

### Run Unit Tests

```cmd
# Run all unit tests
pytest tests/unit/ -v

# Run specific test category
pytest tests/unit/tools/ -v          # All tool tests
pytest tests/unit/tracking/ -v       # Tracking tests
pytest tests/unit/desktop/ -v        # Desktop tests

# Run specific test file
pytest tests/unit/tools/test_tools_basic.py -v
```

### Run Automated Tests

```cmd
# Option 1: Batch script (easiest)
cd tests\automated
quick_test.bat

# Option 2: Python direct
venv\Scripts\activate
python tests\automated\run_tests.py
```

## Test Types

### 1. Unit Tests (ENHANCED) ⭐

**Location:** `tests/unit/`

**What it tests:**
- **Tools** (`tests/unit/tools/`): All 20+ agent tools
  - Basic tools (Done, Wait, Launch, Switch)
  - Input tools (Click, Type, Key, Shortcut, Clipboard)
  - Navigation tools (Scroll, Drag, Move, Resize)
  - System tools (System, Shell, Human, Scrape)
  - Tracking tools (Activity, Timeline, Schedule)
- **Tracking** (`tests/unit/tracking/`): Activity tracking components
  - ActivityTracker, ActivityStorage, ActivityAnalyzer
- **Desktop** (`tests/unit/desktop/`): Desktop service operations
- **Tree** (`tests/unit/tree/`): UI element parsing
- **Agent** (`tests/unit/agent/`): Core agent functionality

**Features:**
- Fast execution (< 1 second per test)
- Isolated testing with mocks
- 100+ test cases covering all tools
- Comprehensive edge case coverage

**Framework:** pytest with fixtures

**Usage:**
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests (NEW) ⭐

**Location:** `tests/integration/`

**What it tests:**
- Complete tool execution flow (agent → registry → tool → desktop)
- Multi-step operations
- Error handling across components
- Tool interaction with real services

**Features:**
- End-to-end workflow validation
- Real component integration
- Error propagation testing

**Usage:**
```bash
pytest tests/integration/ -v
```

### 3. Automated Integration Tests

**Location:** `tests/automated/`

**What it tests:**
- All 15+ agent tools with real LLM
- Reasoning capabilities
- Conversation flow
- Error handling
- Multi-step tasks
- System integration

**Features:**
- 25+ comprehensive test cases
- Automatic scoring (0-100)
- Letter grades (A+ to F)
- Detailed reports (TXT + JSON)
- Performance tracking
- Category breakdowns

**Output:**
- Test logs
- Graded reports
- JSON results
- Performance data

**Usage:**
See `automated/README.md` for complete guide.

## Test Results

### Automated Test Reports

Results saved to `tests/automated/results/`:

```
results/
├── test_run_TIMESTAMP.log       # Detailed execution log
├── test_report_TIMESTAMP.txt    # Human-readable report
└── test_results_TIMESTAMP.json  # Machine-readable data
```

### Example Report Summary

```
Overall Score: 85.3/100 (B)
Total Tests: 25
Passed: 22 (88%)
Failed: 2 (8%)
Errors: 1 (4%)

Category Grades:
- Basic Tools: A (92.5/100)
- Navigation: B+ (87.3/100)
- Input Tools: A- (91.2/100)
- System Tools: B+ (88.7/100)
- Reasoning: C+ (78.3/100)
- Conversation: A- (90.7/100)
- Error Handling: C (73.3/100)
```

## Documentation

| File | Purpose |
|------|---------|
| `automated/README.md` | Full automated testing docs |
| `automated/TESTING_GUIDE.md` | Complete guide with examples |
| `automated/EXAMPLE_REPORT.md` | Sample test output |
| `automated/QUICK_REFERENCE.md` | Quick reference card |

## Test Coverage

### Comprehensive Coverage (NEW!) ⭐

**All Tools (20+):** Unit + Integration Tests
- ✓ Launch Tool - App launching
- ✓ Switch Tool - App switching
- ✓ Done Tool - Task completion
- ✓ Wait Tool - Delays
- ✓ Click Tool - Mouse clicks
- ✓ Type Tool - Keyboard input
- ✓ Key Tool - Individual keys
- ✓ Shortcut Tool - Key combinations
- ✓ Clipboard Tool - Copy/paste
- ✓ Scroll Tool - Scrolling
- ✓ Drag Tool - Drag and drop
- ✓ Move Tool - Cursor movement
- ✓ Resize Tool - Window management
- ✓ System Tool - System information
- ✓ Shell Tool - PowerShell commands
- ✓ Human Tool - User interaction
- ✓ Scrape Tool - Web scraping
- ✓ Activity Tool - Activity tracking queries
- ✓ Timeline Tool - Timeline analysis
- ✓ Schedule Tool - Task scheduling

**Tracking Module:**
- ✓ ActivityTracker - Activity monitoring
- ✓ ActivityStorage - Data persistence
- ✓ ActivityAnalyzer - AI analysis

**Desktop Module:**
- ✓ App listing and switching
- ✓ Window management
- ✓ Command execution
- ✓ UI element detection
- ✓ State management

**Tree Module:**
- ✓ UI element parsing
- ✓ Interactive element detection
- ✓ Scrollable element identification
- ✓ Coordinate calculation

**Agent Core:**
- ✓ Agent service initialization
- ✓ Tool registry
- ✓ Reasoning and planning
- ✓ Error handling
- ✓ Multi-step execution

**Capabilities:**
- ✓ Complete tool execution flow
- ✓ Multi-step reasoning
- ✓ Context understanding
- ✓ Error recovery
- ✓ Conversation flow
- ✓ Memory management
- ✓ Edge case handling

## Adding Tests

### Add Unit Test (NEW!)

Create test file in appropriate `unit/` subdirectory:

```python
"""
Tests for MyNewTool.
"""

import pytest
from unittest.mock import MagicMock, patch
from windows_use.agent.tools.service import my_new_tool


class TestMyNewTool:
    """Tests for MyNewTool."""
    
    @patch('windows_use.agent.tools.service.pg')
    def test_my_new_tool_basic(self, mock_pg):
        """Test basic functionality."""
        result = my_new_tool(param="value")
        
        assert result is not None
        assert "expected" in result.lower()
    
    def test_my_new_tool_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            my_new_tool(param=None)
```

### Add Integration Test

Create in `integration/`:

```python
def test_my_feature_integration(self, agent):
    """Test complete workflow."""
    result = agent.invoke("Test my feature")
    assert result.is_done or not result.error
```

### Add Automated Test

Edit `automated/test_cases.py`:

```python
def test_my_feature(self):
    self._run_test(
        "Test Name",
        "Category",
        lambda: self.agent.invoke("test query"),
        expected_keywords=["expected", "result"]
    )
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Automated Tests
  run: python tests/automated/run_tests.py

- name: Check Results
  run: |
    score=$(jq '.summary.overall_score' tests/automated/results/*.json)
    if (( $(echo "$score < 70" | bc -l) )); then
      exit 1
    fi
```

## Grading Scale

| Grade | Score Range | Quality |
|-------|-------------|---------|
| A+ | 97-100 | Excellent |
| A | 93-96 | Excellent |
| A- | 90-92 | Very Good |
| B+ | 87-89 | Good |
| B | 83-86 | Good |
| B- | 80-82 | Above Average |
| C+ | 77-79 | Average |
| C | 73-76 | Average |
| C- | 70-72 | Below Average |
| D | 60-69 | Poor |
| F | 0-59 | Failing |

## Best Practices

### Before Testing

1. Ensure `.env` has API keys
2. Activate virtual environment
3. Close unnecessary applications
4. Free up system resources

### During Testing

1. Don't interrupt test runs
2. Monitor console output
3. Check for unexpected errors
4. Let tests complete fully

### After Testing

1. Review all report files
2. Analyze failed tests
3. Track scores over time
4. Update tests as needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests won't start | Check venv activated, API keys set |
| All tests fail | Verify dependencies installed |
| Low scores | Review agent configuration |
| Timeouts | Increase max_steps in config |

## Support

For help with testing:

1. Check `automated/TESTING_GUIDE.md`
2. Review `automated/EXAMPLE_REPORT.md`
3. See `automated/QUICK_REFERENCE.md`
4. Check test logs in `results/`

## Contributing

When adding features:

1. Add automated tests for new tools
2. Update test cases for changes
3. Maintain test coverage
4. Document new test categories

## Version History

### v1.0 (Current)
- ✓ Automated integration testing
- ✓ 25+ comprehensive tests
- ✓ Automatic grading system
- ✓ Multiple report formats
- ✓ Performance benchmarking
- ✓ Unit test foundation

## New Testing Features (v2.0) ⭐

### What's New

1. **Comprehensive Unit Tests**
   - 100+ tests covering all 20+ tools
   - Tests for tracking, desktop, and tree modules
   - Fast execution with mocked dependencies

2. **Integration Tests**
   - End-to-end workflow validation
   - Tool execution flow testing
   - Error propagation testing

3. **Better Organization**
   - Clear test structure by category
   - Shared fixtures in `conftest.py`
   - Pytest configuration

4. **Enhanced Documentation**
   - Complete testing guide (`TESTING_GUIDE.md`)
   - Clear examples and templates
   - Troubleshooting section

5. **Test Runners**
   - Main test runner (`run_all_tests.py`)
   - Quick smoke tests (`run_quick_tests.bat`)
   - Flexible filtering options

### Getting Started

1. **Install test dependencies:**
   ```bash
   pip install -r tests/requirements-test.txt
   ```

2. **Run quick smoke tests:**
   ```bash
   tests\run_quick_tests.bat
   ```

3. **Run all tests:**
   ```bash
   python tests/run_all_tests.py
   ```

4. **View coverage:**
   ```bash
   python tests/run_all_tests.py --coverage
   ```

## Documentation

| File | Purpose |
|------|---------|
| `TESTING_GUIDE.md` | Complete testing guide with examples |
| `automated/README.md` | Automated testing documentation |
| `automated/TESTING_GUIDE.md` | Detailed automated test guide |
| `automated/EXAMPLE_REPORT.md` | Sample test output |
| `automated/QUICK_REFERENCE.md` | Quick reference card |

---

**Quick Start:** 
- Unit Tests: `pytest tests/unit/ -v`
- Integration Tests: `pytest tests/integration/ -v`
- Automated Tests: `tests\automated\quick_test.bat`
- Full Guide: See `tests/TESTING_GUIDE.md`

