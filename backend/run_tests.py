"""
Test Runner Script

Run all tests with coverage reporting.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py unit         # Run only unit tests
    python run_tests.py integration  # Run only integration tests
    python run_tests.py --coverage   # Run with coverage report
"""

import sys
import subprocess
from pathlib import Path


def run_tests(test_type='all', coverage=False):
    """Run tests with pytest."""
    
    cmd = ['pytest']
    
    # Add coverage if requested
    if coverage or '--coverage' in sys.argv:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term-missing'])
    
    # Add verbosity
    cmd.append('-v')
    
    # Filter by test type
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type != 'all':
        # Specific test file or path
        cmd.append(test_type)
    else:
        # Run all tests
        cmd.append('tests/')
    
    # Run pytest
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode


if __name__ == '__main__':
    # Parse arguments
    test_type = 'all'
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        test_type = sys.argv[1]
    
    # Run tests
    exit_code = run_tests(test_type, '--coverage' in sys.argv)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)
