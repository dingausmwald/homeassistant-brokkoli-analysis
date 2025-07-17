"""Green pixels processor for counting green pixels in images."""

from typing import Dict, Any
import cv2
import numpy as np

from .base import BaseProcessor


class GreenPixelsProcessor(BaseProcessor):
    """Processor for counting green pixels in images."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # HSV color ranges for green detection
        self.lower_green = np.array([35, 40, 40])
        self.upper_green = np.array([85, 255, 255])
        
        # Minimum green threshold (can be configured)
        self.min_green_threshold = config.get('min_green_threshold', 50)
    
    def process(self, image: np.ndarray, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process image and count green pixels.
        
        Args:
            image: Input image in RGB format
            metadata: Image metadata
            
        Returns:
            Dictionary with green pixel counts
        """
        if not self.is_enabled():
            return {}
        
        try:
            # Convert RGB to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Create mask for green pixels
            green_mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
            
            # Count green pixels
            green_pixels = cv2.countNonZero(green_mask)
            total_pixels = image.shape[0] * image.shape[1]
            green_percentage = (green_pixels / total_pixels) * 100
            
            results = {
                'green_pixels': green_pixels,
                'total_pixels': total_pixels,
                'green_percentage': round(green_percentage, 2)
            }
            
            # Process quadrants if enabled
            if self.quadrants:
                quadrant_results = self._process_quadrants_green(image)
                results.update(quadrant_results)
            
            self.logger.debug(f"Green pixels: {green_pixels} ({green_percentage:.2f}%)")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing green pixels: {e}")
            return {}
    
    def _process_quadrants_green(self, image: np.ndarray) -> Dict[str, Any]:
        """Process green pixels for each quadrant.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with quadrant results
        """
        quadrants = self._process_quadrants(image)
        quadrant_results = {}
        
        for quad_name, quad_image in quadrants.items():
            # Convert to HSV
            hsv = cv2.cvtColor(quad_image, cv2.COLOR_RGB2HSV)
            
            # Create mask for green pixels
            green_mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
            
            # Count green pixels
            green_pixels = cv2.countNonZero(green_mask)
            total_pixels = quad_image.shape[0] * quad_image.shape[1]
            green_percentage = (green_pixels / total_pixels) * 100
            
            quadrant_results[f'{quad_name}_green_pixels'] = green_pixels
            quadrant_results[f'{quad_name}_green_percentage'] = round(green_percentage, 2)
        
        return quadrant_results
    
    def get_sensor_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get MQTT sensor configurations for Home Assistant discovery.
        
        Returns:
            Dictionary with sensor configurations
        """
        source_name = self.name.lower().replace(' ', '_')
        device_name = f"brokkoli_analysis_{source_name}"
        
        configs = {}
        
        # Main green pixels sensor
        configs[f'{device_name}_green_pixels'] = {
            'name': f'{self.name} Green Pixels',
            'unique_id': f'{device_name}_green_pixels',
            'state_topic': f'homeassistant/sensor/{device_name}_green_pixels/state',
            'unit_of_measurement': 'pixels',
            'icon': 'mdi:leaf',
            'device': {
                'identifiers': [device_name],
                'name': f'Brokkoli Analysis {self.name}',
                'model': 'Green Pixels Counter',
                'manufacturer': 'Brokkoli Analysis'
            }
        }
        
        # Green percentage sensor
        configs[f'{device_name}_green_percentage'] = {
            'name': f'{self.name} Green Percentage',
            'unique_id': f'{device_name}_green_percentage',
            'state_topic': f'homeassistant/sensor/{device_name}_green_percentage/state',
            'unit_of_measurement': '%',
            'icon': 'mdi:percent',
            'device': {
                'identifiers': [device_name],
                'name': f'Brokkoli Analysis {self.name}',
                'model': 'Green Pixels Counter',
                'manufacturer': 'Brokkoli Analysis'
            }
        }
        
        # Quadrant sensors if enabled
        if self.quadrants:
            quadrant_names = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            for quad_name in quadrant_names:
                # Green pixels for quadrant
                configs[f'{device_name}_{quad_name}_green_pixels'] = {
                    'name': f'{self.name} {quad_name.replace("_", " ").title()} Green Pixels',
                    'unique_id': f'{device_name}_{quad_name}_green_pixels',
                    'state_topic': f'homeassistant/sensor/{device_name}_{quad_name}_green_pixels/state',
                    'unit_of_measurement': 'pixels',
                    'icon': 'mdi:leaf',
                    'device': {
                        'identifiers': [device_name],
                        'name': f'Brokkoli Analysis {self.name}',
                        'model': 'Green Pixels Counter',
                        'manufacturer': 'Brokkoli Analysis'
                    }
                }
                
                # Green percentage for quadrant
                configs[f'{device_name}_{quad_name}_green_percentage'] = {
                    'name': f'{self.name} {quad_name.replace("_", " ").title()} Green Percentage',
                    'unique_id': f'{device_name}_{quad_name}_green_percentage',
                    'state_topic': f'homeassistant/sensor/{device_name}_{quad_name}_green_percentage/state',
                    'unit_of_measurement': '%',
                    'icon': 'mdi:percent',
                    'device': {
                        'identifiers': [device_name],
                        'name': f'Brokkoli Analysis {self.name}',
                        'model': 'Green Pixels Counter',
                        'manufacturer': 'Brokkoli Analysis'
                    }
                }
        
        return configs 