# Example Test Report

This is an example of what the test reports look like.

## Console Output During Test Run

```
================================================================================
WINDOWS-USE AGENT - AUTOMATED TEST SUITE
================================================================================

Initializing test environment...
Agent initialized successfully
Starting agent test cases...

================================================================================
STARTING COMPREHENSIVE AGENT TESTING
================================================================================

--- TESTING BASIC TOOLS ---

================================================================================
STARTING TEST: Launch Tool - Open Notepad [Basic Tools]
================================================================================
✓ Launch Tool - Open Notepad: PASS (1.23s) - Score: 95.0/100
================================================================================

================================================================================
STARTING TEST: Done Tool - Simple Response [Basic Tools]
================================================================================
✓ Done Tool - Simple Response: PASS (0.87s) - Score: 90.0/100
================================================================================

--- TESTING NAVIGATION TOOLS ---

================================================================================
STARTING TEST: Switch Tool - Switch to Notepad [Navigation]
================================================================================
✓ Switch Tool - Switch to Notepad: PASS (0.65s) - Score: 88.5/100
================================================================================

[... more tests ...]

================================================================================
Test report generated: tests/automated/results/test_report_20250108_153000.txt
JSON results saved: tests/automated/results/test_results_20250108_153000.json
Test log saved: tests/automated/results/test_run_20250108_153000.log
================================================================================
```

## Text Report Output

```
====================================================================================================
WINDOWS-USE AGENT - COMPREHENSIVE TEST REPORT
Generated: 2025-01-08 15:30:00
====================================================================================================

OVERALL SUMMARY
----------------------------------------------------------------------------------------------------
Total Tests:    25
Passed:         22 (88.0%)
Failed:         2 (8.0%)
Errors:         1 (4.0%)
Skipped:        0 (0.0%)
Overall Score:  85.3/100 (B)

CATEGORY BREAKDOWN
====================================================================================================

Category: Basic Tools
----------------------------------------------------------------------------------------------------
Tests:          3
Passed:         3 (100.0%)
Failed:         0 (0.0%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  92.5/100 (A)

Individual Tests:
  ✓ Launch Tool - Open Notepad                        95.0/100 (1.23s)
  ✓ Done Tool - Simple Response                       90.0/100 (0.87s)
  ✓ Wait Tool - Delay Execution                       92.5/100 (2.15s)

====================================================================================================

Category: Navigation
----------------------------------------------------------------------------------------------------
Tests:          2
Passed:         2 (100.0%)
Failed:         0 (0.0%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  87.3/100 (B+)

Individual Tests:
  ✓ Switch Tool - Switch to Notepad                   88.5/100 (0.65s)
  ✓ Scroll Tool - Scroll Down                         86.0/100 (0.92s)

====================================================================================================

Category: Input Tools
----------------------------------------------------------------------------------------------------
Tests:          4
Passed:         4 (100.0%)
Failed:         0 (0.0%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  91.2/100 (A-)

Individual Tests:
  ✓ Type Tool - Type Text                             94.0/100 (1.15s)
  ✓ Shortcut Tool - Select All                        90.0/100 (0.58s)
  ✓ Key Tool - Press Delete                           88.5/100 (0.45s)
  ✓ Clipboard Tool - Copy to Clipboard                92.5/100 (0.72s)

====================================================================================================

Category: System Tools
----------------------------------------------------------------------------------------------------
Tests:          3
Passed:         3 (100.0%)
Failed:         0 (0.0%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  88.7/100 (B+)

Individual Tests:
  ✓ System Tool - Get CPU Info                        92.0/100 (1.45s)
  ✓ Shell Tool - Run PowerShell Command               87.5/100 (1.12s)
  ✓ Human Tool - Ask Question                         86.5/100 (0.95s)

====================================================================================================

Category: Reasoning
----------------------------------------------------------------------------------------------------
Tests:          3
Passed:         2 (66.7%)
Failed:         1 (33.3%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  78.3/100 (C+)

Individual Tests:
  ✓ Multi-Step Task - Open and Type                   85.0/100 (2.34s)
  ✓ Context Understanding - Follow-up                 88.0/100 (1.12s)
  ✗ Error Recovery - Invalid Request                  62.0/100 (1.56s)

====================================================================================================

Category: Conversation
----------------------------------------------------------------------------------------------------
Tests:          3
Passed:         3 (100.0%)
Failed:         0 (0.0%)
Errors:         0 (0.0%)
Skipped:        0 (0.0%)
Average Score:  90.7/100 (A-)

Individual Tests:
  ✓ Greeting Response                                 92.0/100 (0.78s)
  ✓ Clarification Request                             91.5/100 (0.92s)
  ✓ Clear Conversation                                88.5/100 (0.65s)

====================================================================================================

Category: Error Handling
----------------------------------------------------------------------------------------------------
Tests:          3
Passed:         2 (66.7%)
Failed:         0 (0.0%)
Errors:         1 (33.3%)
Skipped:        0 (0.0%)
Average Score:  73.3/100 (C)

Individual Tests:
  ✓ Empty Input Handling                              70.0/100 (0.45s)
  ✓ Invalid Action Handling                           80.0/100 (1.23s)
  ⚠ Complex Query Handling                             0.0/100 (0.15s)
     Error: Maximum recursion depth exceeded

====================================================================================================

GRADING SCALE
----------------------------------------------------------------------------------------------------
A+ : 97-100  (Excellent)
A  : 93-96   (Excellent)
A- : 90-92   (Very Good)
B+ : 87-89   (Good)
B  : 83-86   (Good)
B- : 80-82   (Above Average)
C+ : 77-79   (Average)
C  : 73-76   (Average)
C- : 70-72   (Below Average)
D  : 60-69   (Poor)
F  : 0-59    (Failing)

====================================================================================================
```

## JSON Output

```json
{
  "timestamp": "20250108_153000",
  "summary": {
    "total": 25,
    "passed": 22,
    "failed": 2,
    "errors": 1,
    "skipped": 0,
    "overall_score": 85.3,
    "grade": "B"
  },
  "categories": {
    "Basic Tools": {
      "stats": {
        "total": 3,
        "passed": 3,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total_score": 277.5
      },
      "average_score": 92.5,
      "grade": "A"
    },
    "Navigation": {
      "stats": {
        "total": 2,
        "passed": 2,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total_score": 174.5
      },
      "average_score": 87.25,
      "grade": "B+"
    }
  },
  "results": [
    {
      "test_name": "Launch Tool - Open Notepad",
      "category": "Basic Tools",
      "status": "PASS",
      "duration": 1.23,
      "error_message": "",
      "expected": "",
      "actual": "I've opened Notepad for you.",
      "score": 95.0
    }
  ]
}
```

## Key Metrics

- **Overall Score**: 85.3/100 (B)
- **Pass Rate**: 88%
- **Categories Graded**:
  - Basic Tools: A (92.5/100)
  - Navigation: B+ (87.3/100)
  - Input Tools: A- (91.2/100)
  - System Tools: B+ (88.7/100)
  - Reasoning: C+ (78.3/100)
  - Conversation: A- (90.7/100)
  - Error Handling: C (73.3/100)

## Insights

**Strengths:**
- Excellent basic tool execution
- Strong input handling
- Good conversation flow
- Reliable system operations

**Areas for Improvement:**
- Error recovery in reasoning tasks
- Complex query handling
- Edge case management

