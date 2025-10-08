# Windows-Use Agent - Automated Testing Framework

This folder contains comprehensive automated tests for the Windows-Use Agent project.

## Overview

The testing framework provides:
- **Automated test execution** for all agent tools and capabilities
- **Detailed logging** of test runs
- **Scoring and grading** for each test category
- **Comprehensive reports** in text and JSON formats
- **Analysis** of agent performance across different categories

## Test Categories

### 1. Basic Tools
- Launch Tool (opening applications)
- Done Tool (completing tasks)
- Wait Tool (delays)

### 2. Navigation Tools
- Switch Tool (switching applications)
- Scroll Tool (scrolling content)
- Resize Tool (window management)

### 3. Input Tools
- Type Tool (typing text)
- Click Tool (clicking elements)
- Shortcut Tool (keyboard shortcuts)
- Key Tool (individual key presses)
- Clipboard Tool (copy/paste)

### 4. System Tools
- System Tool (system information)
- Shell Tool (PowerShell commands)
- Human Tool (user interaction)

### 5. Reasoning Capabilities
- Multi-step task execution
- Context understanding
- Error recovery
- Planning and strategy

### 6. Conversation Flow
- Greeting responses
- Clarification requests
- Memory and context
- Conversation management

### 7. Error Handling
- Invalid input handling
- Edge case management
- Complex query processing
- Error recovery

## Running Tests

### Basic Usage

```bash
# Activate virtual environment
venv\Scripts\activate

# Run all tests
python tests/automated/run_tests.py
```

### What Happens

1. **Initialization**: Sets up test environment and agent
2. **Test Execution**: Runs all test cases sequentially
3. **Logging**: Records all actions and results
4. **Analysis**: Scores each test (0-100)
5. **Report Generation**: Creates detailed reports

## Output Files

All test results are saved to `tests/automated/results/`:

### 1. Test Log (`test_run_YYYYMMDD_HHMMSS.log`)
Detailed log of test execution including:
- Test start/end markers
- Individual test results
- Errors and warnings
- Timing information

### 2. Test Report (`test_report_YYYYMMDD_HHMMSS.txt`)
Human-readable report with:
- Overall summary statistics
- Category breakdown with grades
- Individual test scores
- Pass/fail status

### 3. JSON Results (`test_results_YYYYMMDD_HHMMSS.json`)
Machine-readable results for:
- Integration with CI/CD
- Automated analysis
- Trend tracking

## Grading Scale

Tests are scored 0-100 and graded as follows:

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A+    | 97-100     | Excellent   |
| A     | 93-96      | Excellent   |
| A-    | 90-92      | Very Good   |
| B+    | 87-89      | Good        |
| B     | 83-86      | Good        |
| B-    | 80-82      | Above Average |
| C+    | 77-79      | Average     |
| C     | 73-76      | Average     |
| C-    | 70-72      | Below Average |
| D     | 60-69      | Poor        |
| F     | 0-59       | Failing     |

## Scoring Criteria

Each test is scored based on:
- **30 points**: Test completes without error
- **30 points**: Valid response/output generated
- **40 points**: Expected keywords/behaviors present

## Test Structure

### Test Logger (`test_logger.py`)
- Handles all logging operations
- Generates reports and analysis
- Calculates scores and grades

### Test Cases (`test_cases.py`)
- Contains all test definitions
- Organized by category
- Includes expected outcomes

### Test Runner (`run_tests.py`)
- Main entry point
- Initializes environment
- Executes all tests
- Generates final reports

## Adding New Tests

To add new tests:

1. Open `test_cases.py`
2. Add test method to appropriate category
3. Use `_run_test()` helper:

```python
self._run_test(
    "Test Name",
    "Category",
    lambda: self.agent.invoke("your query here"),
    expected_keywords=["keyword1", "keyword2"]
)
```

## Troubleshooting

### Common Issues

**Agent fails to initialize:**
- Check `.env` file for API keys
- Ensure all dependencies installed

**Tests timeout:**
- Increase `max_steps` in agent config
- Check system performance

**Low scores:**
- Review expected keywords
- Check agent responses in logs

## Example Report Output

```
==================================================================================
WINDOWS-USE AGENT - COMPREHENSIVE TEST REPORT
Generated: 2025-01-08 15:30:00
==================================================================================

OVERALL SUMMARY
----------------------------------------------------------------------------------
Total Tests:    25
Passed:         22 (88.0%)
Failed:         2 (8.0%)
Errors:         1 (4.0%)
Skipped:        0 (0.0%)
Overall Score:  85.3/100 (B)

CATEGORY BREAKDOWN
==================================================================================

Category: Basic Tools
----------------------------------------------------------------------------------
Tests:          3
Passed:         3 (100.0%)
Failed:         0 (0.0%)
Average Score:  92.5/100 (A)

Individual Tests:
  ✓ Launch Tool - Open Notepad                        95.0/100 (1.23s)
  ✓ Done Tool - Simple Response                       90.0/100 (0.87s)
  ✓ Wait Tool - Delay Execution                       92.5/100 (2.15s)
```

## Continuous Integration

To integrate with CI/CD:

1. Run tests on every commit
2. Parse JSON output for results
3. Fail build if overall score < 70
4. Track scores over time

Example GitHub Actions:
```yaml
- name: Run Tests
  run: python tests/automated/run_tests.py
  
- name: Check Results
  run: |
    score=$(jq '.summary.overall_score' tests/automated/results/test_results_*.json)
    if (( $(echo "$score < 70" | bc -l) )); then
      exit 1
    fi
```

## Notes

- Tests run with TTS disabled for speed
- `max_steps` set to 10 for faster execution
- Some tests may require specific applications
- Results vary based on system performance

