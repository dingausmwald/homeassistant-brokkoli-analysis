"""Base class for image processors."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class for image processors."""
    
    def __init__(self, name: str, config: dict):
        """Initialize the processor.
        
        Args:
            name: Name of the processor
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.quadrants = config.get("quadrants", False)
        
    @abstractmethod
    def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Process an image and return results.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with processing results
        """
        pass
        
    def get_sensor_topics(self) -> Dict[str, str]:
        """Get MQTT topics for sensors created by this processor.
        
        Returns:
            Dictionary mapping sensor names to MQTT topics
        """
        topics = {}
        
        if self.quadrants:
            # Create topics for each quadrant
            for quadrant in ["top_left", "top_right", "bottom_left", "bottom_right"]:
                topics[f"{self.name}_{quadrant}"] = f"brokkoli/{self.name}/{quadrant}"
        else:
            # Single topic for whole image
            topics[self.name] = f"brokkoli/{self.name}"
            
        return topics
        
    def split_into_quadrants(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Split image into four quadrants.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with quadrant images
        """
        height, width = image.shape[:2]
        mid_h, mid_w = height // 2, width // 2
        
        return {
            "top_left": image[:mid_h, :mid_w],
            "top_right": image[:mid_h, mid_w:],
            "bottom_left": image[mid_h:, :mid_w],
            "bottom_right": image[mid_h:, mid_w:]
        }
        
    def __str__(self):
        return f"{self.__class__.__name__}({self.name})" 