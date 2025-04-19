#!/usr/bin/env python3
"""
Audio Processing Benchmark Script

This script measures the performance of various audio processing operations
using the MCP audio fixtures. It generates benchmark reports that can be
used to track performance over time.
"""

import os
import sys
import time
import json
import base64
import statistics
import argparse
from pathlib import Path
from datetime import datetime
from glob import glob

import requests
import numpy as np
import soundfile as sf
from tqdm import tqdm

# Adjust path to import MCP server modules for direct testing
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_audio_server.analysis.chord_detection import BasicChordDetector
from mcp_audio_server.analysis.key_detection import BasicKeyDetector
from mcp_audio_server.analysis.tempo_tracking import BasicTempoDetector

# Constants
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
AUDIO_DIR = FIXTURES_DIR / "audio"
BENCHMARKS_DIR = Path(__file__).parent
RESULTS_DIR = BENCHMARKS_DIR / "results"
SERVER_URL = "http://localhost:8000"  # Default server URL

# Test categories
TEST_CATEGORIES = {
    'sample_rate': [f for f in glob(f"{AUDIO_DIR}/440hz_sr_*.wav")],
    'duration': [f for f in glob(f"{AUDIO_DIR}/440hz_duration_*.wav")],
    'format': [
        f"{AUDIO_DIR}/440hz_sine.wav",
        f"{AUDIO_DIR}/440hz_sine.flac",
        f"{AUDIO_DIR}/440hz_sine.ogg",
        f"{AUDIO_DIR}/440hz_mp3_320k.mp3",
    ],
    'complexity': [
        f"{AUDIO_DIR}/440hz_sine.wav",        # Simple
        f"{AUDIO_DIR}/sweep_100hz_to_1000hz.wav",  # Moderate
        f"{AUDIO_DIR}/white_noise.wav",       # Complex
    ],
    'channels': [
        f"{AUDIO_DIR}/440hz_sine.wav",        # Mono
        f"{AUDIO_DIR}/stereo_440_880hz.wav",  # Stereo
        f"{AUDIO_DIR}/surround_5_1.wav",      # 5.1
    ],
}


def get_test_audio(filepath):
    """Load test audio file as base64."""
    with open(filepath, "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")


def load_audio(filepath):
    """Load audio file as numpy array using soundfile."""
    try:
        audio, sr = sf.read(filepath)
        return audio, sr
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None, None


def time_operation(func, *args, **kwargs):
    """Measure execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, (end_time - start_time) * 1000  # time in ms


def benchmark_local(audio_files, iterations=3):
    """Benchmark local audio processing operations."""
    results = {}
    
    # Initialize audio analysis objects
    chord_detector = BasicChordDetector()
    key_detector = BasicKeyDetector()
    tempo_detector = BasicTempoDetector()
    
    for filepath in tqdm(audio_files, desc="Benchmarking local processing"):
        file_id = os.path.basename(filepath)
        audio, sr = load_audio(filepath)
        
        if audio is None:
            continue
            
        file_results = {
            "file": file_id,
            "sample_rate": sr,
            "channels": 1 if len(audio.shape) == 1 else audio.shape[1],
            "duration": len(audio) / sr,
            "operations": {}
        }
        
        # Benchmark chord detection
        chord_times = []
        for _ in range(iterations):
            _, exec_time = time_operation(chord_detector.detect, audio, sr)
            chord_times.append(exec_time)
        
        # Benchmark key detection
        key_times = []
        for _ in range(iterations):
            _, exec_time = time_operation(key_detector.detect, audio, sr)
            key_times.append(exec_time)
        
        # Benchmark tempo detection
        tempo_times = []
        for _ in range(iterations):
            _, exec_time = time_operation(tempo_detector.detect, audio, sr)
            tempo_times.append(exec_time)
        
        file_results["operations"] = {
            "chord_detection": {
                "mean": statistics.mean(chord_times),
                "median": statistics.median(chord_times),
                "min": min(chord_times),
                "max": max(chord_times),
                "stdev": statistics.stdev(chord_times) if len(chord_times) > 1 else 0
            },
            "key_detection": {
                "mean": statistics.mean(key_times),
                "median": statistics.median(key_times),
                "min": min(key_times),
                "max": max(key_times),
                "stdev": statistics.stdev(key_times) if len(key_times) > 1 else 0
            },
            "tempo_detection": {
                "mean": statistics.mean(tempo_times),
                "median": statistics.median(tempo_times),
                "min": min(tempo_times),
                "max": max(tempo_times),
                "stdev": statistics.stdev(tempo_times) if len(tempo_times) > 1 else 0
            }
        }
        
        results[file_id] = file_results
    
    return results


def benchmark_api(audio_files, server_url, iterations=3):
    """Benchmark API calls to the server."""
    results = {}
    
    for filepath in tqdm(audio_files, desc="Benchmarking API calls"):
        file_id = os.path.basename(filepath)
        
        try:
            audio_data = get_test_audio(filepath)
        except Exception as e:
            print(f"Error preparing {filepath}: {e}")
            continue
        
        file_format = os.path.splitext(filepath)[1][1:]  # Get extension without dot
        if file_format == "mp3":
            format_name = "mp3"
        else:
            format_name = file_format
        
        file_results = {
            "file": file_id,
            "operations": {}
        }
        
        # Benchmark chord analysis endpoint
        chord_times = []
        for _ in range(iterations):
            request_data = {
                "audio_data": audio_data,
                "format": format_name,
                "options": {"model": "basic"}
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{server_url}/analyze_chords", 
                    json=request_data,
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    chord_times.append((end_time - start_time) * 1000)
                else:
                    print(f"Error analyzing chords for {file_id}: {response.text}")
            except Exception as e:
                print(f"Exception during chord analysis for {file_id}: {e}")
        
        # Benchmark key analysis endpoint
        key_times = []
        for _ in range(iterations):
            request_data = {
                "audio_data": audio_data,
                "format": format_name,
                "options": {"model": "basic"}
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{server_url}/analyze_key", 
                    json=request_data,
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    key_times.append((end_time - start_time) * 1000)
                else:
                    print(f"Error analyzing key for {file_id}: {response.text}")
            except Exception as e:
                print(f"Exception during key analysis for {file_id}: {e}")
        
        # Benchmark tempo analysis endpoint
        tempo_times = []
        for _ in range(iterations):
            request_data = {
                "audio_data": audio_data,
                "format": format_name,
                "options": {"model": "basic"}
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{server_url}/analyze_tempo", 
                    json=request_data,
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    tempo_times.append((end_time - start_time) * 1000)
                else:
                    print(f"Error analyzing tempo for {file_id}: {response.text}")
            except Exception as e:
                print(f"Exception during tempo analysis for {file_id}: {e}")
        
        # Calculate statistics if we have valid measurements
        if chord_times:
            file_results["operations"]["chord_analysis"] = {
                "mean": statistics.mean(chord_times),
                "median": statistics.median(chord_times),
                "min": min(chord_times),
                "max": max(chord_times),
                "stdev": statistics.stdev(chord_times) if len(chord_times) > 1 else 0
            }
        
        if key_times:
            file_results["operations"]["key_analysis"] = {
                "mean": statistics.mean(key_times),
                "median": statistics.median(key_times),
                "min": min(key_times),
                "max": max(key_times),
                "stdev": statistics.stdev(key_times) if len(key_times) > 1 else 0
            }
        
        if tempo_times:
            file_results["operations"]["tempo_analysis"] = {
                "mean": statistics.mean(tempo_times),
                "median": statistics.median(tempo_times),
                "min": min(tempo_times),
                "max": max(tempo_times),
                "stdev": statistics.stdev(tempo_times) if len(tempo_times) > 1 else 0
            }
        
        results[file_id] = file_results
    
    return results


def generate_report(local_results, api_results=None, save=True):
    """Generate a benchmark report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": timestamp,
        "local_processing": local_results,
    }
    
    if api_results:
        report["api_processing"] = api_results
    
    if save:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        output_file = RESULTS_DIR / f"benchmark_report_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {output_file}")
    
    return report


def generate_summary(report):
    """Generate a summary of the benchmark results."""
    local_results = report["local_processing"]
    api_results = report.get("api_processing", {})
    
    # Summarize by category
    summary = {
        "categories": {}
    }
    
    for category, files in TEST_CATEGORIES.items():
        cat_summary = {"local": {}, "api": {}}
        
        # Average times for local processing
        for operation in ["chord_detection", "key_detection", "tempo_detection"]:
            times = []
            for filepath in files:
                file_id = os.path.basename(filepath)
                if file_id in local_results and "operations" in local_results[file_id]:
                    if operation in local_results[file_id]["operations"]:
                        times.append(local_results[file_id]["operations"][operation]["mean"])
            
            if times:
                cat_summary["local"][operation] = {
                    "mean": statistics.mean(times),
                    "median": statistics.median(times),
                    "min": min(times),
                    "max": max(times)
                }
        
        # Average times for API processing
        if api_results:
            for operation in ["chord_analysis", "key_analysis", "tempo_analysis"]:
                times = []
                for filepath in files:
                    file_id = os.path.basename(filepath)
                    if file_id in api_results and "operations" in api_results[file_id]:
                        if operation in api_results[file_id]["operations"]:
                            times.append(api_results[file_id]["operations"][operation]["mean"])
                
                if times:
                    cat_summary["api"][operation] = {
                        "mean": statistics.mean(times),
                        "median": statistics.median(times),
                        "min": min(times),
                        "max": max(times)
                    }
        
        summary["categories"][category] = cat_summary
    
    return summary


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run audio processing benchmarks")
    parser.add_argument("--local", action="store_true", help="Run local processing benchmarks")
    parser.add_argument("--api", action="store_true", help="Run API benchmarks")
    parser.add_argument("--server", default=SERVER_URL, help=f"Server URL (default: {SERVER_URL})")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations per test (default: 3)")
    parser.add_argument("--category", choices=list(TEST_CATEGORIES.keys()), help="Only benchmark a specific category")
    return parser.parse_args()


def main():
    """Main function to run benchmarks."""
    args = parse_args()
    
    # Default to local benchmarks if nothing specified
    if not args.local and not args.api:
        args.local = True
    
    # Select files to benchmark
    if args.category:
        audio_files = TEST_CATEGORIES[args.category]
    else:
        # Use a unique set of all files
        audio_files = set()
        for files in TEST_CATEGORIES.values():
            audio_files.update(files)
        audio_files = list(audio_files)
    
    # Run benchmarks
    local_results = {}
    api_results = {}
    
    if args.local:
        print(f"Running local benchmarks ({args.iterations} iterations per test)...")
        local_results = benchmark_local(audio_files, iterations=args.iterations)
    
    if args.api:
        print(f"Running API benchmarks against {args.server} ({args.iterations} iterations per test)...")
        api_results = benchmark_api(audio_files, args.server, iterations=args.iterations)
    
    # Generate and save report
    report = generate_report(local_results, api_results if args.api else None)
    
    # Generate summary
    summary = generate_summary(report)
    
    # Print summary
    print("\nBenchmark Summary:")
    for category, results in summary["categories"].items():
        print(f"\n{category.upper()}:")
        
        if results["local"]:
            print("  Local Processing:")
            for op, stats in results["local"].items():
                print(f"    {op}: {stats['mean']:.2f}ms (min: {stats['min']:.2f}ms, max: {stats['max']:.2f}ms)")
        
        if results["api"]:
            print("  API Processing:")
            for op, stats in results["api"].items():
                print(f"    {op}: {stats['mean']:.2f}ms (min: {stats['min']:.2f}ms, max: {stats['max']:.2f}ms)")
    
    # Save summary
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = RESULTS_DIR / f"benchmark_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to {summary_file}")


if __name__ == "__main__":
    main()
