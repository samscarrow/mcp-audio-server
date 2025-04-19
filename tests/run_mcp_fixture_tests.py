#!/usr/bin/env python3
"""
Run tests with MCP audio fixtures.

This script runs the test suite against the MCP audio fixtures,
measuring code coverage and generating reports.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Default paths
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
AUDIO_DIR = FIXTURES_DIR / "audio"
COVERAGE_DIR = PROJECT_ROOT / "coverage"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run MCP audio fixture tests")
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--html", 
        action="store_true", 
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml", 
        action="store_true", 
        help="Generate XML coverage report for CI integration"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose test output"
    )
    parser.add_argument(
        "--test-file", "-f", 
        help="Specific test file to run (e.g., test_mcp_audio_fixtures.py)"
    )
    return parser.parse_args()


def check_fixtures():
    """Check if MCP audio fixtures exist, generate if not."""
    if not AUDIO_DIR.exists() or len(list(AUDIO_DIR.glob("*.wav"))) == 0:
        print("MCP audio fixtures not found or incomplete. Generating...")
        try:
            script_path = FIXTURES_DIR / "generate_mcp_audio.py"
            subprocess.run(["python", str(script_path)], check=True)
            print("MCP audio fixtures generated successfully!")
        except subprocess.SubprocessError as e:
            print(f"Error generating MCP audio fixtures: {e}")
            return False
    return True


def run_tests(args):
    """Run pytest with specified options."""
    if not check_fixtures():
        print("ERROR: Required audio fixtures are missing.")
        return 1
    
    # Build pytest command
    cmd = ["pytest"]
    
    # Add verbosity flag if requested
    if args.verbose:
        cmd.append("-v")
    
    # Add specific test file if provided
    if args.test_file:
        cmd.append(f"tests/{args.test_file}")
    else:
        # Otherwise, run all audio fixture tests
        cmd.append("tests/test_audio_fixtures.py")
        cmd.append("tests/test_mcp_audio_fixtures.py")
    
    # Add coverage args if requested
    if args.coverage:
        os.makedirs(COVERAGE_DIR, exist_ok=True)
        cmd = ["coverage", "run", "--source=mcp_audio_server"] + cmd
    
    # Run the tests
    result = subprocess.run(cmd)
    
    # Generate coverage reports if requested
    if args.coverage and result.returncode == 0:
        print("\nGenerating coverage report...")
        subprocess.run(["coverage", "report"])
        
        if args.html:
            subprocess.run([
                "coverage", "html", 
                f"--directory={COVERAGE_DIR}/html"
            ])
            print(f"HTML coverage report generated in {COVERAGE_DIR}/html")
        
        if args.xml:
            subprocess.run([
                "coverage", "xml", 
                f"-o={COVERAGE_DIR}/coverage.xml"
            ])
            print(f"XML coverage report generated: {COVERAGE_DIR}/coverage.xml")
    
    return result.returncode


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_tests(args))
