"""Green pixels processor for counting green pixels in images."""

import logging
from typing import Dict, Any
import numpy as np
import cv2

from .base import BaseProcessor

logger = logging.getLogger(__name__)


class GreenPixelsProcessor(BaseProcessor):
    """Processor for counting green pixels in images."""
    
    def __init__(self, name: str, config: dict):
        """Initialize green pixels processor.
        
        Args:
            name: Name of the processor
            config: Configuration dictionary
        """
        super().__init__(name, config)
        
        # HSV color range for green detection
        # Default values for green hue range
        self.lower_green = np.array([40, 40, 40])   # Lower HSV threshold
        self.upper_green = np.array([80, 255, 255]) # Upper HSV threshold
        
        # Allow custom thresholds from config
        if 'lower_green' in config:
            self.lower_green = np.array(config['lower_green'])
        if 'upper_green' in config:
            self.upper_green = np.array(config['upper_green'])
            
        logger.info(f"Green pixels processor initialized with thresholds: "
                   f"lower={self.lower_green}, upper={self.upper_green}")
    
    def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Process image to count green pixels.
        
        Args:
            image: Input image as numpy array (RGB format)
            
        Returns:
            Dictionary with green pixel counts and percentages
        """
        try:
            if self.quadrants:
                return self._process_quadrants(image)
            else:
                return self._process_whole_image(image)
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {"error": str(e)}
    
    def _process_whole_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Process the whole image for green pixels.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with results
        """
        green_count, total_pixels, percentage = self._count_green_pixels(image)
        
        return {
            "green_pixels": green_count,
            "total_pixels": total_pixels,
            "green_percentage": percentage
        }
    
    def _process_quadrants(self, image: np.ndarray) -> Dict[str, Any]:
        """Process image quadrants for green pixels.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with results for each quadrant
        """
        quadrants = self.split_into_quadrants(image)
        results = {}
        
        for quadrant_name, quadrant_image in quadrants.items():
            green_count, total_pixels, percentage = self._count_green_pixels(quadrant_image)
            
            results[quadrant_name] = {
                "green_pixels": green_count,
                "total_pixels": total_pixels,
                "green_percentage": percentage
            }
            
        return results
    
    def _count_green_pixels(self, image: np.ndarray) -> tuple[int, int, float]:
        """Count green pixels in an image.
        
        Args:
            image: Input image in RGB format
            
        Returns:
            Tuple of (green_pixel_count, total_pixels, percentage)
        """
        # Convert RGB to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Create mask for green pixels
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
        
        # Count green pixels
        green_pixels = cv2.countNonZero(mask)
        total_pixels = image.shape[0] * image.shape[1]
        
        # Calculate percentage
        percentage = (green_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        logger.debug(f"Green pixels: {green_pixels}/{total_pixels} ({percentage:.2f}%)")
        
        return green_pixels, total_pixels, percentage
    
    def get_sensor_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get MQTT sensor configurations for Home Assistant discovery.
        
        Returns:
            Dictionary with sensor configurations
        """
        configs = {}
        
        if self.quadrants:
            # Create sensors for each quadrant
            for quadrant in ["top_left", "top_right", "bottom_left", "bottom_right"]:
                sensor_name = f"{self.name}_{quadrant}"
                configs[sensor_name] = {
                    "name": f"Green Pixels {quadrant.replace('_', ' ').title()}",
                    "state_topic": f"brokkoli/{self.name}/{quadrant}",
                    "unit_of_measurement": "%",
                    "device_class": "humidity",  # Closest match for percentage
                    "unique_id": f"brokkoli_{self.name}_{quadrant}",
                    "value_template": "{{ value | round(1) }}"
                }
        else:
            # Single sensor for whole image
            configs[self.name] = {
                "name": f"Green Pixels {self.name.replace('_', ' ').title()}",
                "state_topic": f"brokkoli/{self.name}",
                "unit_of_measurement": "%",
                "device_class": "humidity",  # Closest match for percentage
                "unique_id": f"brokkoli_{self.name}",
                "value_template": "{{ value | round(1) }}"
            }
            
        return configs 