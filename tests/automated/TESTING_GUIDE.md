# Windows-Use Agent Testing Framework - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Structure](#test-structure)
4. [Understanding Results](#understanding-results)
5. [Customizing Tests](#customizing-tests)
6. [Best Practices](#best-practices)

## Overview

The automated testing framework provides comprehensive testing for the Windows-Use Agent with:
- **25+ test cases** covering all tools and capabilities
- **7 test categories** for organized evaluation
- **Automatic scoring** (0-100 scale)
- **Letter grades** (A+ to F)
- **Detailed reports** in text and JSON formats
- **Performance tracking** and benchmarking

## Quick Start

### 1. Run Tests (Windows)

**Option A: Batch Script**
```cmd
cd tests\automated
quick_test.bat
```

**Option B: Python Direct**
```cmd
# Activate venv
venv\Scripts\activate

# Run tests
python tests\automated\run_tests.py
```

### 2. View Results

Results are saved in `tests/automated/results/`:
- `test_run_TIMESTAMP.log` - Detailed execution log
- `test_report_TIMESTAMP.txt` - Human-readable report
- `test_results_TIMESTAMP.json` - Machine-readable data

### 3. Review Report

Open the `.txt` file to see:
- Overall pass/fail statistics
- Category breakdowns with grades
- Individual test scores
- Execution times

## Test Structure

### Categories

1. **Basic Tools** (3 tests)
   - Launch Tool
   - Done Tool
   - Wait Tool

2. **Navigation** (2 tests)
   - Switch Tool
   - Scroll Tool

3. **Input Tools** (4 tests)
   - Type Tool
   - Click Tool
   - Shortcut Tool
   - Key Tool
   - Clipboard Tool

4. **System Tools** (3 tests)
   - System Tool
   - Shell Tool
   - Human Tool

5. **Reasoning** (3 tests)
   - Multi-step tasks
   - Context understanding
   - Error recovery

6. **Conversation** (3 tests)
   - Greetings
   - Clarifications
   - Memory

7. **Error Handling** (3 tests)
   - Invalid inputs
   - Edge cases
   - Complex queries

### Scoring System

Each test is scored 0-100 based on:
- **30 points**: Test completes without crashes
- **30 points**: Valid response generated
- **40 points**: Expected keywords/behaviors present

### Grading Scale

| Grade | Score | Quality |
|-------|-------|---------|
| A+    | 97-100| Excellent |
| A     | 93-96 | Excellent |
| A-    | 90-92 | Very Good |
| B+    | 87-89 | Good |
| B     | 83-86 | Good |
| B-    | 80-82 | Above Average |
| C+    | 77-79 | Average |
| C     | 73-76 | Average |
| C-    | 70-72 | Below Average |
| D     | 60-69 | Poor |
| F     | 0-59  | Failing |

## Understanding Results

### Example Output

```
Category: Basic Tools
Tests:          3
Passed:         3 (100.0%)
Failed:         0 (0.0%)
Average Score:  92.5/100 (A)

Individual Tests:
  ✓ Launch Tool - Open Notepad      95.0/100 (1.23s)
  ✓ Done Tool - Simple Response      90.0/100 (0.87s)
  ✓ Wait Tool - Delay Execution      92.5/100 (2.15s)
```

**Symbols:**
- ✓ = Passed (score ≥ 70)
- ✗ = Failed (score < 70)
- ⚠ = Error (exception thrown)
- ⊘ = Skipped

### Interpreting Scores

**90-100 (A range)**: Excellent performance
- Agent executes correctly
- All expected behaviors present
- Fast execution

**80-89 (B range)**: Good performance
- Agent works correctly
- Most expected behaviors present
- Acceptable speed

**70-79 (C range)**: Acceptable performance
- Agent completes task
- Some expected behaviors missing
- May be slow

**Below 70**: Needs attention
- Agent may fail or error
- Missing expected behaviors
- Review logs for issues

## Customizing Tests

### Adding New Tests

Edit `tests/automated/test_cases.py`:

```python
def test_my_category(self):
    """Test my new category"""
    self.logger.log_info("\n--- TESTING MY CATEGORY ---\n")
    
    self._run_test(
        "My Test Name",
        "My Category",
        lambda: self.agent.invoke("my test query"),
        expected_keywords=["expected", "words"]
    )
```

### Modifying Scoring

Edit `test_cases.py`, method `_score_result()`:

```python
def _score_result(self, result, expected_keywords=None) -> float:
    score = 0.0
    
    # Customize scoring logic here
    if result:
        score += 40  # Higher weight for completion
    
    # Check keywords
    if expected_keywords:
        matches = sum(1 for k in expected_keywords 
                     if k.lower() in result.content.lower())
        score += (matches / len(expected_keywords)) * 60
    
    return min(score, 100)
```

### Changing Test Parameters

Edit `run_tests.py`:

```python
agent = Agent(
    llm=llm,
    max_steps=20,      # More steps for complex tests
    enable_tts=False,  # Keep disabled for speed
    enable_conversation=True
)
```

## Best Practices

### Before Running Tests

1. **Close unnecessary apps** - Reduces interference
2. **Check environment** - Ensure `.env` has API keys
3. **Free up resources** - Tests work better with available RAM/CPU
4. **Disable TTS** - Keeps tests fast (already default)

### During Test Runs

1. **Don't interact** - Let tests run uninterrupted
2. **Monitor console** - Watch for unexpected errors
3. **Check resources** - Ensure system isn't overloaded
4. **Be patient** - Full suite takes 5-10 minutes

### After Test Runs

1. **Review reports** - Check all three output files
2. **Analyze failures** - Look at error messages
3. **Compare runs** - Track improvements over time
4. **Update tests** - Add cases for found bugs

### Troubleshooting

**Tests fail to start:**
- Check Python environment activated
- Verify all dependencies installed
- Ensure `.env` file exists with keys

**Low scores across board:**
- Review agent configuration
- Check system performance
- Verify API keys are valid

**Specific test failures:**
- Check test logs for details
- Review expected keywords
- Test manually to verify

**Timeouts:**
- Increase `max_steps` in agent config
- Check system resources
- Simplify test queries

## Advanced Usage

### Running Specific Categories

Modify `run_tests.py`:

```python
# Only run basic tools
agent_tests.test_basic_tools()
```

### Performance Benchmarking

```python
from tests.automated.benchmark import PerformanceBenchmark

benchmark = PerformanceBenchmark(agent)
benchmark.run_benchmarks()
```

### Custom Reporters

Create custom analysis by parsing JSON:

```python
import json

with open('test_results_TIMESTAMP.json') as f:
    results = json.load(f)
    
# Custom analysis
for test in results['results']:
    if test['score'] < 70:
        print(f"Failed: {test['test_name']}")
```

### CI/CD Integration

GitHub Actions example:

```yaml
name: Test Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      run: |
        python tests/automated/run_tests.py
    
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: tests/automated/results/
```

## Files Reference

| File | Purpose |
|------|---------|
| `run_tests.py` | Main test runner |
| `test_cases.py` | Test definitions |
| `test_logger.py` | Logging and reporting |
| `benchmark.py` | Performance testing |
| `quick_test.bat` | Windows batch script |
| `README.md` | Documentation |
| `EXAMPLE_REPORT.md` | Sample output |

## Support

For issues or questions:
1. Check logs in `results/` folder
2. Review example reports
3. Verify environment setup
4. Check agent configuration

## Version History

- v1.0 (2025-01-08): Initial testing framework
  - 25+ comprehensive tests
  - 7 test categories
  - Automatic scoring and grading
  - Multiple report formats

