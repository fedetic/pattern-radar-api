#!/usr/bin/env python3
"""
Test runner for the pattern-radar-api test suite.

This script runs all tests to ensure the OHLC chart functionality works correctly
across all timeframes and doesn't regress.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit-only        # Run only unit tests
    python run_tests.py --integration-only # Run only integration tests
    python run_tests.py --verbose          # Run with verbose output
"""

import sys
import subprocess
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Run pattern-radar-api tests")
    parser.add_argument("--unit-only", action="store_true", 
                       help="Run only unit tests (CoinGecko client tests)")
    parser.add_argument("--integration-only", action="store_true",
                       help="Run only integration tests (API endpoint tests)")
    parser.add_argument("--market-cap-only", action="store_true",
                       help="Run only market cap tests")
    parser.add_argument("--chart-only", action="store_true",
                       help="Run only chart interaction tests")
    parser.add_argument("--pattern-reset-only", action="store_true",
                       help="Run only pattern reset tests")
    parser.add_argument("--pattern-viz-only", action="store_true",
                       help="Run only pattern visualization tests")
    parser.add_argument("--volume-chart-only", action="store_true",
                       help="Run only volume chart integration tests")
    parser.add_argument("--pattern-duration-only", action="store_true",
                       help="Run only pattern duration marker tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Run tests with verbose output")
    
    args = parser.parse_args()
    
    # Change to the project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest not found. Install it with: pip install pytest")
        return 1
    
    # Build pytest command
    pytest_args = []
    
    if args.unit_only:
        pytest_args.append("tests/test_coingecko_client.py")
    elif args.integration_only:
        pytest_args.append("tests/test_api_endpoints.py")
    elif args.market_cap_only:
        pytest_args.append("tests/test_market_cap.py")
    elif args.chart_only:
        pytest_args.append("tests/test_chart_interactions.py")
    elif args.pattern_reset_only:
        pytest_args.append("tests/test_pattern_reset.py")
    elif args.pattern_viz_only:
        pytest_args.append("tests/test_pattern_visualization.py")
    elif args.volume_chart_only:
        pytest_args.append("tests/test_volume_chart_integration.py")
    elif args.pattern_duration_only:
        pytest_args.append("tests/test_pattern_duration_markers.py")
    else:
        pytest_args.append("tests/")
    
    if args.verbose:
        pytest_args.append("-v")
    
    # Add coverage and other useful flags
    pytest_args.extend([
        "--tb=short",  # Shorter traceback format
        "-x",          # Stop on first failure
    ])
    
    print("Running pattern-radar-api tests...")
    print(f"Command: pytest {' '.join(pytest_args)}")
    print("-" * 50)
    
    # Run the tests
    try:
        result = subprocess.run([sys.executable, "-m", "pytest"] + pytest_args, 
                              capture_output=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())