#!/usr/bin/env python3
"""
Generate test audio fixtures with known musical properties.
This script creates WAV files with specific chords, tempos, and keys for testing.
"""

import numpy as np
import soundfile as sf
import os
from pathlib import Path

# Base frequencies for notes (A4 = 440Hz standard tuning)
NOTE_FREQUENCIES = {
    'C': 261.63,
    'C#': 277.18,
    'D': 293.66,
    'D#': 311.13,
    'E': 329.63,
    'F': 349.23,
    'F#': 369.99,
    'G': 392.00,
    'G#': 415.30,
    'A': 440.00,
    'A#': 466.16,
    'B': 493.88,
}

# Common chord structures (semitones from root)
CHORD_TYPES = {
    'major': [0, 4, 7],          # Root, major third, perfect fifth
    'minor': [0, 3, 7],          # Root, minor third, perfect fifth
    'diminished': [0, 3, 6],     # Root, minor third, diminished fifth
    'augmented': [0, 4, 8],      # Root, major third, augmented fifth
    'major7': [0, 4, 7, 11],     # Root, major third, perfect fifth, major seventh
    'minor7': [0, 3, 7, 10],     # Root, minor third, perfect fifth, minor seventh
    'dominant7': [0, 4, 7, 10],  # Root, major third, perfect fifth, minor seventh
}

SAMPLE_RATE = 44100  # Standard sample rate in Hz
DURATION = 3.0       # Duration of each sample in seconds


def get_note_frequency(note, octave=4):
    """Get the frequency of a note in a specific octave."""
    base_freq = NOTE_FREQUENCIES[note]
    if octave < 4:
        return base_freq / (2 ** (4 - octave))
    elif octave > 4:
        return base_freq * (2 ** (octave - 4))
    return base_freq


def generate_tone(frequency, duration, sample_rate=SAMPLE_RATE, amplitude=0.3):
    """Generate a pure sine wave tone at the given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone


def generate_chord(root_note, chord_type, duration=DURATION, sample_rate=SAMPLE_RATE):
    """Generate a chord based on the root note and chord type."""
    if root_note not in NOTE_FREQUENCIES:
        raise ValueError(f"Unknown note: {root_note}")
    if chord_type not in CHORD_TYPES:
        raise ValueError(f"Unknown chord type: {chord_type}")
    
    root_freq = NOTE_FREQUENCIES[root_note]
    chord = np.zeros(int(sample_rate * duration))
    
    # Add the frequencies for each note in the chord
    for semitone_offset in CHORD_TYPES[chord_type]:
        freq = root_freq * (2 ** (semitone_offset / 12))
        chord += generate_tone(freq, duration, sample_rate)
    
    # Normalize to prevent clipping
    chord = chord / np.max(np.abs(chord))
    return chord


def generate_chord_progression(chords, durations, sample_rate=SAMPLE_RATE):
    """Generate a chord progression with the given chords and durations."""
    progression = np.array([])
    
    for (root, chord_type), duration in zip(chords, durations):
        chord = generate_chord(root, chord_type, duration, sample_rate)
        progression = np.append(progression, chord)
    
    return progression


def generate_metronome(tempo, duration, sample_rate=SAMPLE_RATE):
    """Generate a metronome click track at the given tempo."""
    # Calculate number of samples per beat
    beat_duration = 60.0 / tempo  # in seconds
    samples_per_beat = int(sample_rate * beat_duration)
    total_samples = int(sample_rate * duration)
    
    # Create an empty array
    click_track = np.zeros(total_samples)
    
    # Add clicks at beat intervals
    for i in range(0, total_samples, samples_per_beat):
        # Click sound (short burst)
        click_duration = 0.01  # 10ms click
        click_samples = int(sample_rate * click_duration)
        
        # Ensure we don't go beyond the array bounds
        end_idx = min(i + click_samples, total_samples)
        
        # Generate short sine burst for click
        t = np.linspace(0, click_duration, end_idx - i, endpoint=False)
        click = 0.5 * np.sin(2 * np.pi * 1000 * t)
        
        # Apply envelope to avoid clicks
        envelope = np.exp(-5 * t / click_duration)
        click = click * envelope
        
        click_track[i:end_idx] = click
    
    return click_track


def create_test_files():
    """Create all test audio files."""
    base_dir = Path(__file__).parent
    
    # Ensure output directories exist
    dirs = ['chords', 'tempo', 'key', 'edge_cases', 'errors']
    for d in dirs:
        os.makedirs(base_dir / d, exist_ok=True)
    
    # 1. Generate chord samples
    chord_types = ['major', 'minor', 'major7', 'minor7', 'dominant7']
    for root in ['C', 'F', 'G', 'A']:
        for chord_type in chord_types:
            chord = generate_chord(root, chord_type)
            filename = f"{root}_{chord_type}.wav"
            sf.write(base_dir / 'chords' / filename, chord, SAMPLE_RATE)
            print(f"Created {filename}")
    
    # 2. Generate chord progressions
    progressions = [
        # C major progression (I-IV-V-I)
        ([('C', 'major'), ('F', 'major'), ('G', 'major'), ('C', 'major')], 
         [1.0, 1.0, 1.0, 1.0], 
         'C_major_progression.wav'),
        
        # A minor progression (i-iv-V-i)
        ([('A', 'minor'), ('D', 'minor'), ('E', 'major'), ('A', 'minor')], 
         [1.0, 1.0, 1.0, 1.0], 
         'A_minor_progression.wav'),
        
        # Jazz II-V-I in C
        ([('D', 'minor7'), ('G', 'dominant7'), ('C', 'major7')], 
         [1.0, 1.0, 2.0], 
         'jazz_251_progression.wav'),
    ]
    
    for chords, durations, filename in progressions:
        progression = generate_chord_progression(chords, durations)
        sf.write(base_dir / 'chords' / filename, progression, SAMPLE_RATE)
        print(f"Created {filename}")
    
    # 3. Generate tempo examples
    for tempo in [60, 90, 120, 180]:
        metronome = generate_metronome(tempo, DURATION)
        filename = f"{tempo}bpm_click.wav"
        sf.write(base_dir / 'tempo' / filename, metronome, SAMPLE_RATE)
        print(f"Created {filename}")
        
        # Also create a combined version with a chord
        chord = generate_chord('C', 'major', DURATION)
        combined = 0.7 * chord + 0.3 * metronome
        combined = combined / np.max(np.abs(combined))
        filename = f"{tempo}bpm_with_chord.wav"
        sf.write(base_dir / 'tempo' / filename, combined, SAMPLE_RATE)
        print(f"Created {filename}")
    
    # 4. Generate key examples (simple chord progressions in different keys)
    for key in ['C', 'G', 'D', 'A', 'E', 'F']:
        # Use circle of fifths to determine the IV and V chords
        circle_of_fifths = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
        idx = circle_of_fifths.index(key)
        fourth = circle_of_fifths[(idx - 1) % 12]  # IV chord is one step counter-clockwise
        fifth = circle_of_fifths[(idx + 1) % 12]   # V chord is one step clockwise
        
        # Create a I-IV-V-I progression
        progression = generate_chord_progression(
            [(key, 'major'), (fourth, 'major'), (fifth, 'major'), (key, 'major')],
            [1.0, 1.0, 1.0, 1.0]
        )
        filename = f"{key}_major_key.wav"
        sf.write(base_dir / 'key' / filename, progression, SAMPLE_RATE)
        print(f"Created {filename}")
    
    # 5. Generate edge cases
    # Silent audio
    silent = np.zeros(int(SAMPLE_RATE * DURATION))
    sf.write(base_dir / 'edge_cases' / 'silent.wav', silent, SAMPLE_RATE)
    print("Created silent.wav")
    
    # Very short audio (100ms)
    short_chord = generate_chord('C', 'major', 0.1)
    sf.write(base_dir / 'edge_cases' / 'very_short.wav', short_chord, SAMPLE_RATE)
    print("Created very_short.wav")
    
    # Very long audio (10s)
    long_progression = generate_chord_progression(
        [('C', 'major'), ('F', 'major'), ('G', 'major'), ('C', 'major')],
        [2.5, 2.5, 2.5, 2.5]
    )
    sf.write(base_dir / 'edge_cases' / 'very_long.wav', long_progression, SAMPLE_RATE)
    print("Created very_long.wav")
    
    # Low sample rate
    low_sr = 8000
    t = np.linspace(0, DURATION, int(low_sr * DURATION), endpoint=False)
    low_quality = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(base_dir / 'edge_cases' / 'low_sample_rate.wav', low_quality, low_sr)
    print("Created low_sample_rate.wav")
    
    # 6. Generate error test cases
    # Create a corrupt WAV file (just the header, no actual data)
    with open(base_dir / 'errors' / 'corrupt.wav', 'wb') as f:
        # Just write the RIFF header but no actual valid data
        f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data')
    print("Created corrupt.wav")
    
    # Non-audio file with WAV extension
    with open(base_dir / 'errors' / 'not_audio.wav', 'w') as f:
        f.write("This is not an audio file, just a text file with WAV extension.")
    print("Created not_audio.wav")


if __name__ == "__main__":
    create_test_files()
    print("All test audio files generated successfully!")
