"""Key detection module."""

import logging
from typing import Dict, Optional, Tuple

import numpy as np

from mcp_audio_server.analysis import register_detector

logger = logging.getLogger(__name__)


@register_detector("basic_key")
class BasicKeyDetector:
    """Basic musical key detection implementation."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
    def detect_key(self, waveform: np.ndarray, sr: int) -> Dict[str, any]:
        """
        Detect musical key of audio waveform.
        
        Args:
            waveform: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            Dictionary with key name and confidence
        """
        try:
            import librosa
        except ImportError:
            logger.error("librosa required for key detection")
            return {"key": "", "confidence": 0.0}
        
        logger.info(f"Analyzing key in audio (sr={sr})")
        
        # Extract chroma features
        chroma = librosa.feature.chroma_cqt(y=waveform, sr=sr)
        
        # Average chroma features over time
        chroma_avg = np.mean(chroma, axis=1)
        
        # Define key profiles for major and minor keys
        # These are simplified Krumhansl-Kessler profiles
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        # Calculate correlation with each possible key
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        minor_key_names = [f"{k}m" for k in key_names]
        
        max_corr = -1
        detected_key = ""
        
        # Check correlation with major keys
        for i in range(12):
            # Rotate the profile to match each key
            rotated_profile = np.roll(major_profile, i)
            corr = np.corrcoef(rotated_profile, chroma_avg)[0, 1]
            
            if corr > max_corr:
                max_corr = corr
                detected_key = key_names[i]
        
        # Check correlation with minor keys
        for i in range(12):
            # Rotate the profile to match each key
            rotated_profile = np.roll(minor_profile, i)
            corr = np.corrcoef(rotated_profile, chroma_avg)[0, 1]
            
            if corr > max_corr:
                max_corr = corr
                detected_key = minor_key_names[i]
        
        # Convert correlation coefficient to confidence (range 0-1)
        # Adjust the range from [-1, 1] to [0, 1]
        confidence = (max_corr + 1) / 2
        
        return {
            "key": detected_key,
            "confidence": float(confidence)
        }


@register_detector("advanced_key")
class AdvancedKeyDetector:
    """Advanced key detection with more sophisticated profiles."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.enable_segment_analysis = self.config.get("enable_segment_analysis", False)
        
    def detect_key(self, waveform: np.ndarray, sr: int) -> Dict[str, any]:
        """
        Advanced key detection implementation.
        
        Args:
            waveform: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            Dictionary with key name, confidence, and optional segment analysis
        """
        basic_detector = BasicKeyDetector(self.config)
        result = basic_detector.detect_key(waveform, sr)
        
        # If segment analysis is enabled, also analyze the key by segments
        if self.enable_segment_analysis and len(waveform) > sr * 10:  # Only for tracks > 10 seconds
            try:
                import librosa
                
                # Split audio into segments
                segment_length = sr * 10  # 10-second segments
                num_segments = len(waveform) // segment_length
                
                segment_keys = []
                
                for i in range(num_segments):
                    start = i * segment_length
                    end = (i + 1) * segment_length
                    segment = waveform[start:end]
                    
                    # Detect key in this segment
                    segment_result = basic_detector.detect_key(segment, sr)
                    segment_keys.append({
                        "start_time": i * 10,  # in seconds
                        "end_time": (i + 1) * 10,
                        "key": segment_result["key"],
                        "confidence": segment_result["confidence"]
                    })
                
                # Add segment analysis to the result
                result["segments"] = segment_keys
                
            except Exception as e:
                logger.error(f"Error in segment analysis: {e}")
        
        return result
