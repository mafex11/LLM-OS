# Testing Framework - Quick Reference Card

## Run Tests

### Windows
```cmd
tests\automated\quick_test.bat
```

### Python
```cmd
python tests\automated\run_tests.py
```

## Output Files

All saved to `tests/automated/results/`:

| File | Content |
|------|---------|
| `test_run_*.log` | Detailed execution log |
| `test_report_*.txt` | Human-readable report |
| `test_results_*.json` | Machine-readable data |

## Test Categories (25 tests)

1. **Basic Tools** (3) - Launch, Done, Wait
2. **Navigation** (2) - Switch, Scroll
3. **Input Tools** (4) - Type, Click, Shortcut, Key, Clipboard
4. **System Tools** (3) - System, Shell, Human
5. **Reasoning** (3) - Multi-step, Context, Recovery
6. **Conversation** (3) - Greeting, Clarify, Memory
7. **Error Handling** (3) - Invalid, Edge cases, Complex

## Scoring

| Component | Points |
|-----------|--------|
| Completion | 30 |
| Valid output | 30 |
| Expected behavior | 40 |
| **Total** | **100** |

## Grading Scale

| Grade | Score | Status |
|-------|-------|--------|
| A+/A/A- | 90-100 | Excellent ✓ |
| B+/B/B- | 80-89 | Good ✓ |
| C+/C/C- | 70-79 | Pass ✓ |
| D | 60-69 | Poor ✗ |
| F | 0-59 | Fail ✗ |

## Status Symbols

- ✓ = Passed
- ✗ = Failed
- ⚠ = Error
- ⊘ = Skipped

## Common Issues

| Problem | Solution |
|---------|----------|
| Won't start | Check `.env` API keys |
| All fail | Activate venv first |
| Low scores | Review agent config |
| Timeout | Increase `max_steps` |

## Quick Tips

✅ **DO:**
- Run with venv activated
- Close other apps
- Check results folder
- Review logs for errors

❌ **DON'T:**
- Interrupt tests
- Interact during run
- Run without API keys
- Ignore error messages

## Results Location

```
tests/automated/results/
  ├── test_run_20250108_153000.log
  ├── test_report_20250108_153000.txt
  └── test_results_20250108_153000.json
```

## Example Output

```
Overall Score: 85.3/100 (B)
Passed: 22/25 (88%)
Failed: 2/25 (8%)
Errors: 1/25 (4%)

Best Category: Input Tools (A-, 91.2/100)
Worst Category: Error Handling (C, 73.3/100)
```

## Add New Test

```python
# In test_cases.py
self._run_test(
    "Test Name",
    "Category",
    lambda: self.agent.invoke("query"),
    expected_keywords=["word1", "word2"]
)
```

## Support Files

- `README.md` - Full documentation
- `TESTING_GUIDE.md` - Complete guide
- `EXAMPLE_REPORT.md` - Sample output
- `benchmark.py` - Performance tests

## Time Estimates

| Test Suite | Duration |
|------------|----------|
| Full run | 5-10 min |
| Per test | 10-30 sec |
| Report gen | < 1 sec |

## Required Setup

1. Virtual environment activated
2. Dependencies installed
3. `.env` with API keys
4. Windows OS (for full tests)

---

**Need help?** Check `TESTING_GUIDE.md` for details.

