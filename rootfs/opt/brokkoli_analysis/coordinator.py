"""Main coordinator for image processing and MQTT publishing."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import threading

from sources import BaseSource, FolderSource
from processors import BaseProcessor, GreenPixelsProcessor
from mqtt_client import MQTTClient

logger = logging.getLogger(__name__)


class ProcessingCoordinator:
    """Main coordinator for image processing and MQTT publishing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the coordinator.
        
        Args:
            config: Full configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.mqtt_client = MQTTClient(config['mqtt'])
        self.sources: List[BaseSource] = []
        self.processors: List[BaseProcessor] = []
        
        # Runtime state
        self.running = False
        self.processing_thread: Optional[threading.Thread] = None
        
        # Initialize sources and processors
        self._init_sources()
        self._init_processors()
    
    def _init_sources(self) -> None:
        """Initialize image sources from configuration."""
        for source_config in self.config.get('sources', []):
            source_type = source_config.get('type', 'folder')
            source_name = source_config.get('name', 'Unknown')
            
            if source_type == 'folder':
                source = FolderSource(source_name, source_config)
                self.sources.append(source)
                self.logger.info(f"Initialized folder source: {source_name}")
            else:
                self.logger.warning(f"Unknown source type: {source_type}")
    
    def _init_processors(self) -> None:
        """Initialize image processors from configuration."""
        for processor_config in self.config.get('processors', []):
            processor_type = processor_config.get('type', 'green_pixels')
            processor_name = processor_config.get('name', 'Unknown')
            
            if processor_type == 'green_pixels':
                processor = GreenPixelsProcessor(processor_name, processor_config)
                self.processors.append(processor)
                self.logger.info(f"Initialized green pixels processor: {processor_name}")
            else:
                self.logger.warning(f"Unknown processor type: {processor_type}")
    
    def start(self) -> bool:
        """Start the coordinator.
        
        Returns:
            True if startup successful, False otherwise
        """
        self.logger.info("Starting Brokkoli Analysis Coordinator...")
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            self.logger.error("Failed to connect to MQTT broker")
            return False
        
        # Start all sources
        for source in self.sources:
            try:
                source.start()
                if not source.is_available():
                    self.logger.warning(f"Source {source.name} is not available")
            except Exception as e:
                self.logger.error(f"Error starting source {source.name}: {e}")
        
        # Register sensors with Home Assistant
        self._register_sensors()
        
        # Start processing thread
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        self.logger.info("Coordinator started successfully")
        return True
    
    def stop(self) -> None:
        """Stop the coordinator."""
        self.logger.info("Stopping Brokkoli Analysis Coordinator...")
        
        # Stop processing
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        # Stop all sources
        for source in self.sources:
            try:
                source.stop()
            except Exception as e:
                self.logger.error(f"Error stopping source {source.name}: {e}")
        
        # Disconnect from MQTT
        self.mqtt_client.disconnect()
        
        self.logger.info("Coordinator stopped")
    
    def _register_sensors(self) -> None:
        """Register all sensors with Home Assistant via MQTT discovery."""
        self.logger.info("Registering sensors with Home Assistant...")
        
        for source in self.sources:
            for processor in self.processors:
                if not processor.is_enabled():
                    continue
                
                # Get sensor configurations for this source-processor combination
                sensor_configs = processor.get_sensor_configs()
                
                # Update sensor configs with source-specific information
                source_name = source.name.lower().replace(' ', '_')
                
                for sensor_id, config in sensor_configs.items():
                    # Update sensor ID to include source
                    updated_sensor_id = sensor_id.replace('brokkoli_analysis_', f'brokkoli_analysis_{source_name}_')
                    
                    # Update config with source-specific information
                    updated_config = config.copy()
                    updated_config['unique_id'] = updated_sensor_id
                    updated_config['state_topic'] = config['state_topic'].replace(
                        'brokkoli_analysis_', f'brokkoli_analysis_{source_name}_'
                    )
                    
                    # Update device information
                    if 'device' in updated_config:
                        device_info = updated_config['device'].copy()
                        device_info['identifiers'] = [f'brokkoli_analysis_{source_name}']
                        device_info['name'] = f'Brokkoli Analysis {source.name}'
                        updated_config['device'] = device_info
                    
                    # Register sensor
                    if self.mqtt_client.register_sensor(updated_sensor_id, updated_config):
                        self.logger.info(f"Registered sensor: {updated_sensor_id}")
                    else:
                        self.logger.error(f"Failed to register sensor: {updated_sensor_id}")
    
    def _processing_loop(self) -> None:
        """Main processing loop."""
        self.logger.info("Starting processing loop...")
        
        while self.running:
            try:
                # Process each source
                for source in self.sources:
                    if not source.is_available():
                        continue
                    
                    # Get latest frame
                    frame = source.get_latest_frame()
                    if frame is None:
                        continue
                    
                    # Get metadata
                    metadata = source.get_metadata()
                    
                    # Process frame with all enabled processors
                    for processor in self.processors:
                        if not processor.is_enabled():
                            continue
                        
                        try:
                            # Process the image
                            results = processor.process(frame, metadata)
                            
                            if results:
                                # Publish results to MQTT
                                self._publish_results(source, processor, results)
                        
                        except Exception as e:
                            self.logger.error(f"Error processing with {processor.name}: {e}")
                
                # Sleep before next iteration
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                time.sleep(5)
        
        self.logger.info("Processing loop stopped")
    
    def _publish_results(self, source: BaseSource, processor: BaseProcessor, results: Dict[str, Any]) -> None:
        """Publish processing results to MQTT.
        
        Args:
            source: Source that provided the image
            processor: Processor that generated the results
            results: Processing results
        """
        source_name = source.name.lower().replace(' ', '_')
        
        # Build sensor data for publishing
        sensor_data = {}
        
        for key, value in results.items():
            # Build sensor ID
            sensor_id = f'brokkoli_analysis_{source_name}_{key}'
            sensor_data[sensor_id] = value
        
        # Publish sensor data
        if sensor_data:
            if self.mqtt_client.publish_sensor_data(sensor_data):
                self.logger.debug(f"Published results for {source.name} - {processor.name}")
            else:
                self.logger.error(f"Failed to publish results for {source.name} - {processor.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'running': self.running,
            'mqtt_connected': self.mqtt_client.is_connected(),
            'sources': [
                {
                    'name': source.name,
                    'type': source.__class__.__name__,
                    'available': source.is_available()
                }
                for source in self.sources
            ],
            'processors': [
                {
                    'name': processor.name,
                    'type': processor.__class__.__name__,
                    'enabled': processor.is_enabled()
                }
                for processor in self.processors
            ]
        } 