#!/usr/bin/env python3
"""
Generate MCP audio test fixtures with different formats and properties.
This script creates various audio files for testing the MCP audio server.
"""

import numpy as np
import soundfile as sf
import os
from pathlib import Path
import librosa
import subprocess

SAMPLE_RATE = 44100  # Standard sample rate in Hz
DURATION = 3.0       # Duration of each sample in seconds

def generate_sine_wave(frequency, duration, sample_rate=SAMPLE_RATE, amplitude=0.8):
    """Generate a pure sine wave at the given frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave

def generate_sweep(start_freq, end_freq, duration, sample_rate=SAMPLE_RATE, amplitude=0.8):
    """Generate a frequency sweep (chirp) from start_freq to end_freq."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Logarithmic sweep
    phase = 2 * np.pi * start_freq * duration / np.log(end_freq/start_freq) * (np.exp(t/duration * np.log(end_freq/start_freq)) - 1)
    sweep = amplitude * np.sin(phase)
    
    return sweep

def generate_white_noise(duration, sample_rate=SAMPLE_RATE, amplitude=0.3):
    """Generate white noise."""
    noise = amplitude * np.random.randn(int(sample_rate * duration))
    return noise

def create_mcp_audio_fixtures():
    """Create audio fixtures for MCP audio server testing."""
    base_dir = Path("~/dev/projects/mcp-audio-server/tests/fixtures/audio").expanduser()
    os.makedirs(base_dir, exist_ok=True)
    
    # Create fixtures in different formats
    formats = [
        {"ext": "wav", "format": "WAV", "subtype": "PCM_16"},
        {"ext": "wav", "format": "WAV", "subtype": "PCM_24"},
        {"ext": "wav", "format": "WAV", "subtype": "PCM_32"},
        {"ext": "wav", "format": "WAV", "subtype": "FLOAT"},
        {"ext": "flac", "format": "FLAC", "subtype": "PCM_16"},
        {"ext": "ogg", "format": "OGG", "subtype": "VORBIS"},
    ]
    
    # 1. Generate standard test tones
    for freq in [100, 440, 1000, 10000]:
        tone = generate_sine_wave(freq, DURATION)
        for fmt in formats:
            filename = f"{freq}hz_sine.{fmt['ext']}"
            sf.write(base_dir / filename, tone, SAMPLE_RATE, 
                     format=fmt['format'], subtype=fmt['subtype'])
            print(f"Created {filename}")
    
    # 2. Generate frequency sweeps
    sweep_pairs = [
        (100, 1000),    # Low to mid
        (1000, 10000),  # Mid to high
        (100, 10000),   # Full range
        (10000, 100)    # Descending
    ]
    
    for start, end in sweep_pairs:
        sweep = generate_sweep(start, end, DURATION)
        filename = f"sweep_{start}hz_to_{end}hz.wav"
        sf.write(base_dir / filename, sweep, SAMPLE_RATE)
        print(f"Created {filename}")
    
    # 3. Generate white noise
    noise = generate_white_noise(DURATION)
    sf.write(base_dir / "white_noise.wav", noise, SAMPLE_RATE)
    print("Created white_noise.wav")
    
    # 4. Generate different sample rates
    for sr in [8000, 16000, 22050, 44100, 48000, 96000]:
        # Resample a 440Hz tone to the target sample rate
        tone = generate_sine_wave(440, DURATION, sample_rate=sr)
        filename = f"440hz_sr_{sr}.wav"
        sf.write(base_dir / filename, tone, sr)
        print(f"Created {filename}")
    
    # 5. Generate multi-channel audio
    tone = generate_sine_wave(440, DURATION)
    
    # Stereo (2 channels)
    # Left channel: 440Hz, Right channel: 880Hz
    right_channel = generate_sine_wave(880, DURATION)
    stereo = np.vstack((tone, right_channel)).T
    sf.write(base_dir / "stereo_440_880hz.wav", stereo, SAMPLE_RATE)
    print("Created stereo_440_880hz.wav")
    
    # 5.1 surround (6 channels)
    ch1 = generate_sine_wave(100, DURATION, amplitude=0.5)
    ch2 = generate_sine_wave(200, DURATION, amplitude=0.5)
    ch3 = generate_sine_wave(300, DURATION, amplitude=0.5)
    ch4 = generate_sine_wave(400, DURATION, amplitude=0.5)
    ch5 = generate_sine_wave(500, DURATION, amplitude=0.5)
    ch6 = generate_sine_wave(50, DURATION, amplitude=0.5)  # LFE channel
    surround = np.vstack((ch1, ch2, ch3, ch4, ch5, ch6)).T
    sf.write(base_dir / "surround_5_1.wav", surround, SAMPLE_RATE)
    print("Created surround_5_1.wav")
    
    # 6. Generate MP3 files using FFmpeg
    try:
        # First create a WAV file, then convert to MP3
        tone = generate_sine_wave(440, DURATION)
        temp_wav = base_dir / "temp.wav"
        sf.write(temp_wav, tone, SAMPLE_RATE)
        
        # Convert to MP3 at different bitrates
        for bitrate in [64, 128, 192, 320]:
            mp3_file = base_dir / f"440hz_mp3_{bitrate}k.mp3"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(temp_wav), 
                "-b:a", f"{bitrate}k", str(mp3_file)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Created 440hz_mp3_{bitrate}k.mp3")
        
        # Clean up temp file
        os.remove(temp_wav)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Warning: FFmpeg not available, skipping MP3 generation")
    
    # 7. Generate short and long duration files
    durations = [0.1, 0.5, 10.0, 30.0]
    for dur in durations:
        tone = generate_sine_wave(440, dur)
        filename = f"440hz_duration_{dur}s.wav"
        sf.write(base_dir / filename, tone, SAMPLE_RATE)
        print(f"Created {filename}")
    
    # 8. Generate special test cases
    # Silence
    silence = np.zeros(int(SAMPLE_RATE * DURATION))
    sf.write(base_dir / "silence.wav", silence, SAMPLE_RATE)
    print("Created silence.wav")
    
    # DC offset (non-zero mean)
    dc_offset = generate_sine_wave(440, DURATION) + 0.5
    sf.write(base_dir / "dc_offset.wav", dc_offset, SAMPLE_RATE)
    print("Created dc_offset.wav")
    
    # Very high amplitude (near clipping)
    high_amp = generate_sine_wave(440, DURATION, amplitude=0.99)
    sf.write(base_dir / "high_amplitude.wav", high_amp, SAMPLE_RATE)
    print("Created high_amplitude.wav")
    
    # Clipped audio
    clipped = generate_sine_wave(440, DURATION, amplitude=1.5)
    clipped = np.clip(clipped, -1.0, 1.0)
    sf.write(base_dir / "clipped.wav", clipped, SAMPLE_RATE)
    print("Created clipped.wav")

if __name__ == "__main__":
    create_mcp_audio_fixtures()
    print("All MCP audio fixtures generated successfully!")
