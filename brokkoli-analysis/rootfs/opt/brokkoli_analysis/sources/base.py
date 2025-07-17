"""Base class for image sources."""

import logging
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Base class for image sources (folder, stream, etc.)."""
    
    def __init__(self, name: str, config: dict):
        """Initialize the source.
        
        Args:
            name: Name of the source
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        
    @abstractmethod
    def get_latest_image(self) -> Optional[np.ndarray]:
        """Get the latest image from the source.
        
        Returns:
            Latest image as numpy array or None if no image available
        """
        pass
        
    @abstractmethod
    def has_new_image(self) -> bool:
        """Check if there's a new image available.
        
        Returns:
            True if new image is available, False otherwise
        """
        pass
        
    @abstractmethod
    def start(self):
        """Start the source (monitoring, connection, etc.)."""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the source and cleanup resources."""
        pass
        
    def __str__(self):
        return f"{self.__class__.__name__}({self.name})" 