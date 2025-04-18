"""Plugin registry for audio analysis algorithms."""

import importlib
import inspect
import pkgutil
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

class AnalysisRegistry:
    """Registry for audio analysis plugins."""
    
    def __init__(self):
        self._detectors = {}
        
    def register(self, name: str, detector: Any) -> None:
        """Register a detector implementation."""
        if name in self._detectors:
            raise ValueError(f"Detector with name '{name}' already registered")
        self._detectors[name] = detector
        
    def get(self, name: str) -> Any:
        """Get a registered detector by name."""
        if name not in self._detectors:
            raise KeyError(f"No detector registered with name '{name}'")
        return self._detectors[name]
    
    def list_detectors(self) -> List[str]:
        """List all registered detector names."""
        return list(self._detectors.keys())
    
    def autodiscover(self, package_name: str = "mcp_audio_server.analysis") -> None:
        """Auto-discover and register all detectors in the package."""
        package = importlib.import_module(package_name)
        
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if not is_pkg:
                module = importlib.import_module(name)
                # Register any compatible classes
                for attr_name in dir(module):
                    if attr_name.startswith('_'):
                        continue
                    
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and hasattr(attr, '_detector_name'):
                        detector_name = getattr(attr, '_detector_name')
                        self.register(detector_name, attr())


def register_detector(name: str) -> Callable:
    """Decorator to register a detector class with the registry."""
    def decorator(cls: Type) -> Type:
        setattr(cls, '_detector_name', name)
        return cls
    return decorator
