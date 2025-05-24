"""Test runner script for the Kura Explorer Backend."""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(
    test_path: str = "tests/",
    coverage: bool = True,
    verbose: bool = True,
    pattern: str = None,
    fail_fast: bool = False
):
    """Run tests with various options.
    
    Args:
        test_path: Path to test files (default: tests/)
        coverage: Whether to collect coverage data
        verbose: Whether to run in verbose mode
        pattern: Pattern to match test files/methods
        fail_fast: Whether to stop on first failure
    """
    cmd = ["uv", "run", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if fail_fast:
        cmd.append("-x")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if pattern:
        cmd.extend(["-k", pattern])
    
    cmd.append(test_path)
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def run_specific_router_tests(router_name: str):
    """Run tests for a specific router.
    
    Args:
        router_name: Name of the router (main, clusters, conversations, search)
    """
    test_file = f"tests/test_{router_name}.py"
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found!")
        return 1
    
    return run_tests(test_file, coverage=False, verbose=True)


def run_integration_tests():
    """Run integration tests that test multiple components together."""
    return run_tests("tests/", pattern="integration", verbose=True)


def run_cluster_mapping_tests():
    """Run integration tests for cluster-conversation mapping."""
    test_files = [
        "tests/test_integration_clusters.py",
        "tests/test_database_integrity.py"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"Test file {test_file} not found!")
            continue
        
        print(f"\n🔄 Running {test_file}...")
        result = run_tests(test_file, coverage=False, verbose=True)
        if result != 0:
            print(f"❌ {test_file} failed")
            return result
    
    return 0


def run_database_integrity_tests():
    """Run database integrity tests specifically."""
    return run_tests("tests/test_database_integrity.py", coverage=False, verbose=True)


def run_unit_tests():
    """Run only unit tests (exclude integration tests)."""
    return run_tests("tests/", pattern="not integration", verbose=True)


def check_test_coverage():
    """Run tests and generate detailed coverage report."""
    print("Running tests with coverage analysis...")
    result = run_tests(coverage=True, verbose=False)
    
    if result == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {result}")
    
    return result


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <command> [options]")
        print("\nCommands:")
        print("  all                  - Run all tests")
        print("  unit                 - Run unit tests only")
        print("  integration          - Run integration tests only") 
        print("  cluster-mapping      - Run cluster-conversation mapping tests")
        print("  database             - Run database integrity tests")
        print("  coverage             - Run tests with coverage report")
        print("  router <name>        - Run tests for specific router")
        print("  pattern <pattern>    - Run tests matching pattern")
        print("\nExamples:")
        print("  python test_runner.py all")
        print("  python test_runner.py cluster-mapping")
        print("  python test_runner.py database")
        print("  python test_runner.py router clusters")
        print("  python test_runner.py pattern 'test_get_clusters'")
        return 1
    
    command = sys.argv[1]
    
    if command == "all":
        return run_tests()
    elif command == "unit":
        return run_unit_tests()
    elif command == "integration":
        return run_integration_tests()
    elif command == "cluster-mapping":
        return run_cluster_mapping_tests()
    elif command == "database":
        return run_database_integrity_tests()
    elif command == "coverage":
        return check_test_coverage()
    elif command == "router" and len(sys.argv) > 2:
        router_name = sys.argv[2]
        return run_specific_router_tests(router_name)
    elif command == "pattern" and len(sys.argv) > 2:
        pattern = sys.argv[2]
        return run_tests(pattern=pattern)
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 