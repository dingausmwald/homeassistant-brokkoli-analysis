"""Base class for image and video sources."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Base class for all image/video sources."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the source.
        
        Args:
            name: Human-readable name for the source
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing source: {name}")
    
    @abstractmethod
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the source.
        
        Returns:
            numpy array representing the image or None if no frame available
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is available and ready.
        
        Returns:
            True if source is ready, False otherwise
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the source (if needed)."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the source and cleanup resources."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the current frame.
        
        Returns:
            Dictionary with metadata like timestamp, resolution, etc.
        """
        return {
            'source_name': self.name,
            'source_type': self.__class__.__name__
        } 