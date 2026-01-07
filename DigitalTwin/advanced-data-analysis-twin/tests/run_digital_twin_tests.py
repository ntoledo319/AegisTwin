#!/usr/bin/env python3
"""
Test runner for Digital Twin tests.

This script runs all the tests for the Digital Twin components.
"""

import os
import sys
import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    """
    Run all Digital Twin tests.
    """
    # Create test directories if they don't exist
    os.makedirs("tests/data/memories/episodic", exist_ok=True)
    os.makedirs("tests/data/memories/semantic", exist_ok=True)
    os.makedirs("tests/data/memories/procedural", exist_ok=True)
    os.makedirs("tests/data/memories/index", exist_ok=True)
    
    # Run tests
    args = [
        "-xvs",  # Verbose output, stop on first failure
        "tests/digital_twin",  # Test directory
    ]
    
    # Add any command line arguments
    args.extend(sys.argv[1:])
    
    # Run pytest
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main())