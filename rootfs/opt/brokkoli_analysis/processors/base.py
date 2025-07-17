"""Base class for image processors."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class for all image processors."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the processor.
        
        Args:
            name: Human-readable name for the processor
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.quadrants = config.get('quadrants', False)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing processor: {name} (enabled: {self.enabled})")
    
    @abstractmethod
    def process(self, image: np.ndarray, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process an image and return results.
        
        Args:
            image: Input image as numpy array
            metadata: Metadata about the image
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    @abstractmethod
    def get_sensor_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get MQTT sensor configurations for Home Assistant discovery.
        
        Returns:
            Dictionary with sensor configurations
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if processor is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
    
    def _process_quadrants(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Split image into quadrants for processing.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with quadrant images
        """
        h, w = image.shape[:2]
        mid_h, mid_w = h // 2, w // 2
        
        return {
            'top_left': image[:mid_h, :mid_w],
            'top_right': image[:mid_h, mid_w:],
            'bottom_left': image[mid_h:, :mid_w],
            'bottom_right': image[mid_h:, mid_w:]
        } 