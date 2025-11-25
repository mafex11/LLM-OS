"""
Main test runner for Windows-Use Agent.
Runs all tests with proper configuration and reporting.
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_tests(test_type="all", verbose=False, coverage=False, markers=None):
    """
    Run tests with pytest.
    
    Args:
        test_type: Type of tests to run ('all', 'unit', 'integration', 'tools', 'tracking')
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        markers: Additional pytest markers to filter tests
    """
    # Build pytest command
    cmd = ["pytest"]
    
    # Add test path based on type
    if test_type == "unit":
        cmd.append("tests/unit")
    elif test_type == "integration":
        cmd.append("tests/integration")
    elif test_type == "tools":
        cmd.extend(["-m", "tools"])
    elif test_type == "tracking":
        cmd.extend(["-m", "tracking"])
    elif test_type == "all":
        cmd.append("tests")
    else:
        print(f"Unknown test type: {test_type}")
        print("Valid types: all, unit, integration, tools, tracking")
        return 1
    
    # Add verbose flag
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=windows_use",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add custom markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Add common options
    cmd.extend([
        "--tb=short",
        "--disable-warnings"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 80)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    return result.returncode


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    cmd = ["pytest", test_path, "-v", "--tb=short"]
    
    print(f"Running test: {test_path}")
    print("=" * 80)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def list_tests():
    """List all available tests."""
    cmd = ["pytest", "--collect-only", "-q", "tests"]
    
    print("Available tests:")
    print("=" * 80)
    
    subprocess.run(cmd, cwd=Path(__file__).parent.parent)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests for Windows-Use Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python tests/run_all_tests.py
  
  # Run only unit tests
  python tests/run_all_tests.py --type unit
  
  # Run integration tests with coverage
  python tests/run_all_tests.py --type integration --coverage
  
  # Run specific test file
  python tests/run_all_tests.py --file tests/unit/tools/test_tools_basic.py
  
  # List all tests
  python tests/run_all_tests.py --list
  
  # Run tests matching marker
  python tests/run_all_tests.py --markers "tools and not slow"
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "tools", "tracking"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Run tests matching specific markers (e.g., 'unit and not slow')"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="Run a specific test file or test function"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tests"
    )
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        list_tests()
        return 0
    
    # Handle specific file
    if args.file:
        return run_specific_test(args.file)
    
    # Run tests
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        markers=args.markers
    )


if __name__ == "__main__":
    sys.exit(main())


