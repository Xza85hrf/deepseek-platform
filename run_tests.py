#!/usr/bin/env python3
import pytest
import coverage

if __name__ == "__main__":
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests with pytest
    result = pytest.main(['tests', '-v', '--ignore=tests/test_agents.py'])
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    cov.report(show_missing=True)
    
    # Exit with appropriate status code
    exit(0 if result == 0 else 1)
