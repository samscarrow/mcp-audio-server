"""Tempo tracking module."""

import logging
from typing import Dict, Optional, Tuple

import numpy as np

from mcp_audio_server.analysis import register_detector

logger = logging.getLogger(__name__)


@register_detector("basic_tempo")
class BasicTempoDetector:
    """Basic tempo detection implementation."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
    def detect_tempo(self, waveform: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Detect tempo in audio waveform.
        
        Args:
            waveform: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            Dictionary with tempo in BPM and confidence
        """
        try:
            import librosa
        except ImportError:
            logger.error("librosa required for tempo detection")
            return {"tempo": 0.0, "confidence": 0.0}
        
        logger.info(f"Analyzing tempo in audio (sr={sr})")
        
        # Extract onset envelope from audio
        onset_env = librosa.onset.onset_strength(y=waveform, sr=sr)
        
        # Perform tempo estimation
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
        
        # In a real implementation, we would also compute a confidence
        # For now, we'll use a placeholder
        confidence = 0.8
        
        return {
            "tempo": float(tempo),
            "confidence": confidence
        }


@register_detector("advanced_tempo")
class AdvancedTempoDetector:
    """Advanced tempo detection with beat tracking."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
    def detect_tempo(self, waveform: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Advanced tempo detection with beat tracking.
        
        Args:
            waveform: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            Dictionary with tempo in BPM, confidence, and optional beat positions
        """
        try:
            import librosa
        except ImportError:
            logger.error("librosa required for tempo detection")
            return {"tempo": 0.0, "confidence": 0.0}
        
        # Extract onset envelope
        onset_env = librosa.onset.onset_strength(y=waveform, sr=sr)
        
        # Dynamic tempo estimation
        ac_tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, aggregate=None)
        
        # Get the tempo estimate
        tempo = float(np.median(ac_tempo))
        
        # Calculate tempo stability (as a proxy for confidence)
        tempo_std = float(np.std(ac_tempo))
        confidence = max(0.0, min(1.0, 1.0 - (tempo_std / tempo)))
        
        result = {
            "tempo": tempo,
            "confidence": confidence
        }
        
        # Include beat positions if requested
        if self.config.get("return_beats", False):
            _, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            beat_times = librosa.frames_to_time(beats, sr=sr)
            result["beat_positions"] = beat_times.tolist()
        
        return result
