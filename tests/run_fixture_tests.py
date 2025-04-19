#!/usr/bin/env python3
"""
Utility script to run tests with MCP audio fixtures.
This script helps with running tests against the audio fixtures we've created.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import random

# Directories
REPO_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
AUDIO_DIR = FIXTURES_DIR / "audio"
CHORD_DIR = FIXTURES_DIR / "chords"
TEMPO_DIR = FIXTURES_DIR / "tempo"
KEY_DIR = FIXTURES_DIR / "key"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run MCP audio fixture tests")
    
    parser.add_argument(
        "--test-type",
        choices=["all", "format", "tempo", "key", "chord", "edge", "error", "specific"],
        default="all",
        help="Type of test to run",
    )
    
    parser.add_argument(
        "--format",
        choices=["wav", "flac", "ogg", "mp3", "all"],
        default="all",
        help="Audio format to test with (when test-type is 'format')",
    )
    
    parser.add_argument(
        "--specific-file",
        help="Specific file to test (when test-type is 'specific')",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Increase verbosity",
    )
    
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate test fixtures before running tests",
    )
    
    parser.add_argument(
        "--random",
        action="store_true",
        help="Test with random subset of fixtures",
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of random samples to test (when --random is used)",
    )
    
    return parser.parse_args()


def generate_fixtures():
    """Generate test fixtures."""
    print("Generating test fixtures...")
    subprocess.run(
        [sys.executable, REPO_ROOT / "create_test_fixtures.py"],
        check=True,
    )
    print("Fixtures generated.")


def get_test_command(args):
    """Build the pytest command based on command line arguments."""
    cmd = ["pytest", "-v"]
    
    # Use mock implementations for stable testing
    os.environ["USE_MOCK_IMPLEMENTATIONS"] = "1"
    
    if args.test_type == "all":
        cmd.append("tests/test_audio_fixtures.py")
    elif args.test_type == "format":
        if args.format == "all":
            cmd.append("tests/test_audio_fixtures.py::test_chord_detection_wav")
            cmd.append("tests/test_audio_fixtures.py::test_chord_detection_flac")
            cmd.append("tests/test_audio_fixtures.py::test_chord_detection_ogg")
            cmd.append("tests/test_audio_fixtures.py::test_chord_detection_mp3")
        else:
            cmd.append(f"tests/test_audio_fixtures.py::test_chord_detection_{args.format}")
    elif args.test_type == "tempo":
        cmd.append("tests/test_audio_fixtures.py::test_tempo_detection")
    elif args.test_type == "key":
        cmd.append("tests/test_audio_fixtures.py::test_key_detection")
    elif args.test_type == "chord":
        cmd.append("tests/test_audio_fixtures.py::test_chord_detection_wav")
    elif args.test_type == "edge":
        cmd.append("tests/test_audio_fixtures.py::test_edge_cases")
    elif args.test_type == "error":
        cmd.append("tests/test_audio_fixtures.py::test_error_cases")
    elif args.test_type == "specific" and args.specific_file:
        # For specific file testing, we'll create a temporary test file
        create_specific_test(args.specific_file)
        cmd.append("tests/test_specific_fixture.py")
    
    if args.verbose:
        cmd.append("-v")
    
    return cmd


def get_random_fixtures(directory, num_samples=5, pattern="*.wav"):
    """Get a random subset of fixtures."""
    import glob
    files = glob.glob(str(directory / pattern))
    return random.sample(files, min(num_samples, len(files)))


def create_specific_test(specific_file):
    """Create a temporary test file for testing a specific fixture."""
    test_file_content = f"""
import os
import pytest
import base64
from fastapi.testclient import TestClient

from mcp_audio_server.main import app

client = TestClient(app)

def get_test_audio():
    \"\"\"Load specific test audio file as base64.\"\"\"
    with open("{specific_file}", "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")

def test_specific_file():
    \"\"\"Test a specific audio file.\"\"\"
    audio_data = get_test_audio()
    file_ext = os.path.splitext("{specific_file}")[1][1:]
    
    request_data = {{
        "audio_data": audio_data,
        "format": file_ext,
        "options": {{"model": "basic"}},
        "analyzers": ["chords", "tempo", "key"]
    }}
    
    response = client.post("/analyze", json=request_data)
    print(f"\\nResponse status code: {{response.status_code}}")
    print(f"Response headers: {{response.headers}}")
    result = response.json()
    print(f"Response: {{result}}")
    
    if response.status_code == 200:
        assert "schema_version" in result
        if "chords" in result:
            print(f"Chords detected: {{result['chords']}}")
        if "tempo" in result:
            print(f"Tempo detected: {{result['tempo']}}")
        if "key" in result:
            print(f"Key detected: {{result['key']}}")
    else:
        print(f"Error: {{result}}")
"""
    
    with open("tests/test_specific_fixture.py", "w") as f:
        f.write(test_file_content)
    
    print(f"Created test file for testing {specific_file}")


def main():
    """Main function."""
    args = parse_args()
    
    if args.generate:
        generate_fixtures()
    
    if args.random:
        # Test with random fixtures instead of running the standard tests
        print(f"Testing with {args.sample_size} random fixtures...")
        fixtures = get_random_fixtures(AUDIO_DIR, args.sample_size)
        
        for fixture in fixtures:
            print(f"\nTesting with {fixture}...")
            args.test_type = "specific"
            args.specific_file = fixture
            cmd = get_test_command(args)
            subprocess.run(cmd, check=True)
    else:
        # Run the standard tests
        cmd = get_test_command(args)
        result = subprocess.run(cmd)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
