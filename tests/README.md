# Windows-Use Agent - Testing Suite

This directory contains all testing resources for the Windows-Use Agent project.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── agent/              # Agent-specific tests
│   ├── desktop/            # Desktop service tests
│   └── tree/               # Tree parsing tests
│
├── automated/              # Automated integration testing ⭐ NEW
│   ├── results/           # Test results and reports
│   ├── run_tests.py       # Main test runner
│   ├── test_cases.py      # Test definitions
│   ├── test_logger.py     # Logging system
│   ├── benchmark.py       # Performance benchmarks
│   ├── quick_test.bat     # Windows quick start
│   ├── README.md          # Detailed documentation
│   ├── TESTING_GUIDE.md   # Complete testing guide
│   ├── EXAMPLE_REPORT.md  # Sample test reports
│   └── QUICK_REFERENCE.md # Quick reference card
│
└── README.md              # This file
```

## Quick Start

### Run Automated Tests

```cmd
# Option 1: Batch script (easiest)
cd tests\automated
quick_test.bat

# Option 2: Python direct
venv\Scripts\activate
python tests\automated\run_tests.py
```

### Run Unit Tests

```cmd
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/agent/test_agent_service.py
```

## Test Types

### 1. Automated Integration Tests (NEW) ⭐

**Location:** `tests/automated/`

**What it tests:**
- All 15+ agent tools
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

### 2. Unit Tests

**Location:** `tests/unit/`

**What it tests:**
- Individual functions
- Component isolation
- Edge cases
- Input validation

**Framework:** pytest

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

### Automated Tests Cover:

**Tools (15+):**
- ✓ Launch Tool
- ✓ Click Tool
- ✓ Type Tool
- ✓ Switch Tool
- ✓ Scroll Tool
- ✓ Drag Tool
- ✓ Move Tool
- ✓ Shortcut Tool
- ✓ Key Tool
- ✓ Wait Tool
- ✓ Clipboard Tool
- ✓ Shell Tool
- ✓ System Tool
- ✓ Human Tool
- ✓ Done Tool

**Capabilities:**
- ✓ Multi-step reasoning
- ✓ Context understanding
- ✓ Error recovery
- ✓ Conversation flow
- ✓ Memory management
- ✓ Edge case handling

### Unit Tests Cover:

- Agent service initialization
- Tool registry
- Desktop state management
- Tree parsing utilities
- Prompt generation

## Adding Tests

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

### Add Unit Test

Create in `unit/` with pytest:

```python
def test_my_function():
    result = my_function(input)
    assert result == expected
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

---

**Quick Start:** Run `tests\automated\quick_test.bat` to see it in action!

