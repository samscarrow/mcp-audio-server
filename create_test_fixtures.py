#!/usr/bin/env python3
"""
Script to create all test fixtures for the MCP Audio Server.
This creates basic audio test files and calls additional specialized fixture generators.
Also handles platform-independent generation of audio test files.
"""

import os
import numpy as np
import soundfile as sf
import subprocess
from pathlib import Path

# Base frequencies for notes (A4 = 440Hz standard tuning)
NOTE_FREQUENCIES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
}

# Chord structures (semitones from root)
CHORD_TYPES = {
    'major': [0, 4, 7],        # Root, major third, perfect fifth
    'minor': [0, 3, 7],        # Root, minor third, perfect fifth
    'dom7': [0, 4, 7, 10]      # Root, major third, perfect fifth, minor seventh
}

SAMPLE_RATE = 44100  # Standard sample rate (Hz)
BASE_DIR = Path("tests/fixtures")


def generate_sine_wave(freq, duration, sample_rate=SAMPLE_RATE, amplitude=0.2):
    """Generate a sine wave at the given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t)


def generate_chord(root, chord_type, duration=2.0):
    """Generate a chord from root note and chord type."""
    root_freq = NOTE_FREQUENCIES[root]
    chord = np.zeros(int(SAMPLE_RATE * duration))
    
    for semitone in CHORD_TYPES[chord_type]:
        freq = root_freq * (2 ** (semitone / 12))
        chord += generate_sine_wave(freq, duration)
    
    # Normalize
    return chord / np.max(np.abs(chord))


def generate_click_track(tempo, duration=2.0):
    """Generate a metronome click track."""
    beat_interval = 60.0 / tempo  # seconds between beats
    samples = np.zeros(int(SAMPLE_RATE * duration))
    
    # Add clicks at regular intervals
    for beat_time in np.arange(0, duration, beat_interval):
        beat_pos = int(beat_time * SAMPLE_RATE)
        click_len = min(int(0.01 * SAMPLE_RATE), len(samples) - beat_pos)
        
        # Generate a short click
        t = np.linspace(0, 0.01, click_len, endpoint=False)
        click = 0.8 * np.sin(2 * np.pi * 1000 * t) * np.exp(-10 * t)
        
        if beat_pos + click_len <= len(samples):
            samples[beat_pos:beat_pos + click_len] = click
    
    return samples


def create_test_files():
    """Create basic test audio files."""
    # Ensure directories exist
    for subdir in ['chords', 'tempo', 'key', 'edge_cases', 'errors']:
        os.makedirs(BASE_DIR / subdir, exist_ok=True)
    
    # 1. Simple chord samples
    print("Creating chord samples...")
    for root in ['C', 'F', 'G', 'D']:
        for chord_type in ['major', 'minor', 'dom7']:
            chord = generate_chord(root, chord_type)
            filename = f"{root}_{chord_type}.wav"
            sf.write(str(BASE_DIR / 'chords' / filename), chord, SAMPLE_RATE)
            print(f"  Created {filename}")
    
    # 2. Tempo samples
    print("\nCreating tempo samples...")
    for tempo in [60, 90, 120, 150]:
        # Pure click track
        click_track = generate_click_track(tempo)
        filename = f"{tempo}bpm_click.wav"
        sf.write(str(BASE_DIR / 'tempo' / filename), click_track, SAMPLE_RATE)
        
        # Click track with chord
        c_major = generate_chord('C', 'major')
        combined = 0.7 * c_major + 0.3 * click_track
        combined = combined / np.max(np.abs(combined))
        filename = f"{tempo}bpm_with_chord.wav"
        sf.write(str(BASE_DIR / 'tempo' / filename), combined, SAMPLE_RATE)
        print(f"  Created tempo files at {tempo} BPM")
    
    # 3. Key examples (simple triads)
    print("\nCreating key examples...")
    for key in ['C', 'G', 'D', 'A', 'F']:
        for chord_type in ['major', 'minor']:
            chord = generate_chord(key, chord_type)
            filename = f"{key}_{chord_type}_key.wav"
            sf.write(str(BASE_DIR / 'key' / filename), chord, SAMPLE_RATE)
            print(f"  Created {filename}")
    
    # 4. Edge cases
    print("\nCreating edge cases...")
    # Silent audio
    silent = np.zeros(int(SAMPLE_RATE * 2.0))
    sf.write(str(BASE_DIR / 'edge_cases' / 'silent.wav'), silent, SAMPLE_RATE)
    
    # Very short audio (100ms)
    short = generate_chord('C', 'major', 0.1)
    sf.write(str(BASE_DIR / 'edge_cases' / 'very_short.wav'), short, SAMPLE_RATE)
    
    # Very long audio
    long = np.concatenate([generate_chord('C', 'major'), 
                         generate_chord('F', 'major'),
                         generate_chord('G', 'major'), 
                         generate_chord('C', 'major')])
    sf.write(str(BASE_DIR / 'edge_cases' / 'long_progression.wav'), long, SAMPLE_RATE)
    
    # Low sample rate
    low_sr = 8000
    t = np.linspace(0, 2.0, int(low_sr * 2.0), endpoint=False)
    low_quality = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(str(BASE_DIR / 'edge_cases' / 'low_sample_rate.wav'), low_quality, low_sr)
    print("  Created edge case files")
    
    # 5. Error cases
    print("\nCreating error test cases...")
    # Corrupt WAV (just header)
    with open(str(BASE_DIR / 'errors' / 'corrupt.wav'), 'wb') as f:
        f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data')
    
    # Non-audio with WAV extension
    with open(str(BASE_DIR / 'errors' / 'not_audio.wav'), 'w') as f:
        f.write("This is not an audio file, just text with WAV extension.")
    print("  Created error test files")

    print("\nAll basic test audio files created successfully!")


def generate_mcp_audio_fixtures():
    """Generate specialized MCP audio fixtures by calling the dedicated script."""
    print("\nGenerating MCP audio fixtures...")
    try:
        script_path = Path("tests/fixtures/generate_mcp_audio.py")
        subprocess.run(["python", str(script_path)], check=True)
        print("MCP audio fixtures created successfully!")
    except subprocess.SubprocessError as e:
        print(f"Error generating MCP audio fixtures: {e}")


if __name__ == "__main__":
    create_test_files()
    generate_mcp_audio_fixtures()
