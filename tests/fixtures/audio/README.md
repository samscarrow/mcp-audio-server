# MCP Audio Server Test Fixtures

This directory contains various audio test fixtures used for testing the MCP Audio Server's processing capabilities.

## File Categories

### Test Tones
- Pure sine waves at different frequencies (100Hz, 440Hz, 1000Hz, 10000Hz)
- Available in various formats (WAV, FLAC, OGG)
- Different bit depths (16-bit, 24-bit, 32-bit, Float)

### Frequency Sweeps
- Logarithmic sweeps across different frequency ranges
- Ascending and descending sweeps
- Useful for testing frequency response and processing

### Sample Rate Tests
- Same tone (440Hz) at different sample rates
- 8kHz, 16kHz, 22.05kHz, 44.1kHz, 48kHz, 96kHz

### Multi-channel Tests
- Stereo files with different frequencies per channel
- 5.1 surround sound test files

### MP3 Encoding Tests
- MP3 files at various bit rates (64k, 128k, 192k, 320k)

### Duration Tests
- Very short files (100ms)
- Standard length files (3s)
- Long files (10s, 30s)

### Special Test Cases
- Silence
- DC offset
- High amplitude (near clipping)
- Clipped audio

## Usage

These files are used by the MCP Audio Server's test suite to verify:
- Format compatibility
- Sample rate conversion
- Channel handling
- Duration limits
- Edge case handling

## Generation

All files were generated using the `generate_mcp_audio.py` script in the parent directory. 
To regenerate these files, run:

```bash
python tests/fixtures/generate_mcp_audio.py
```
