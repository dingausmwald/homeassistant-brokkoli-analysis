"""Coordinator for managing sources and processors."""

import logging
import time
import threading
from typing import Dict, List, Any
import schedule

from sources import BaseSource, FolderSource
from processors import BaseProcessor, GreenPixelsProcessor
from mqtt_client import MQTTClient

logger = logging.getLogger(__name__)


class BrokkoliCoordinator:
    """Coordinates image sources and processors."""
    
    def __init__(self, config: dict, mqtt_client: MQTTClient):
        """Initialize coordinator.
        
        Args:
            config: Configuration dictionary
            mqtt_client: MQTT client instance
        """
        self.config = config
        self.mqtt_client = mqtt_client
        self.sources: Dict[str, BaseSource] = {}
        self.processors: Dict[str, BaseProcessor] = {}
        self.running = False
        self.scheduler_thread = None
        
        # Initialize sources and processors
        self._initialize_sources()
        self._initialize_processors()
        
    def _initialize_sources(self):
        """Initialize image sources from configuration."""
        sources_config = self.config.get('sources', [])
        
        for source_config in sources_config:
            name = source_config['name']
            source_type = source_config['type']
            
            try:
                if source_type == 'folder':
                    source = FolderSource(name, source_config)
                    self.sources[name] = source
                    logger.info(f"Initialized folder source: {name}")
                else:
                    logger.warning(f"Unknown source type: {source_type}")
                    
            except Exception as e:
                logger.error(f"Error initializing source {name}: {e}")
    
    def _initialize_processors(self):
        """Initialize image processors from configuration."""
        processors_config = self.config.get('processors', [])
        
        for processor_config in processors_config:
            name = processor_config['name']
            processor_type = processor_config['type']
            
            try:
                if processor_type == 'green_pixels':
                    processor = GreenPixelsProcessor(name, processor_config)
                    self.processors[name] = processor
                    logger.info(f"Initialized green pixels processor: {name}")
                else:
                    logger.warning(f"Unknown processor type: {processor_type}")
                    
            except Exception as e:
                logger.error(f"Error initializing processor {name}: {e}")
    
    def start(self):
        """Start the coordinator."""
        logger.info("Starting Brokkoli Coordinator")
        self.running = True
        
        # Start all sources
        for source in self.sources.values():
            try:
                source.start()
            except Exception as e:
                logger.error(f"Error starting source {source.name}: {e}")
        
        # Publish MQTT discovery
        self._publish_discovery()
        
        # Start availability publishing
        self.mqtt_client.publish_availability(True)
        
        # Schedule periodic processing
        self._schedule_processing()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Coordinator started successfully")
    
    def stop(self):
        """Stop the coordinator."""
        logger.info("Stopping Brokkoli Coordinator")
        self.running = False
        
        # Stop all sources
        for source in self.sources.values():
            try:
                source.stop()
            except Exception as e:
                logger.error(f"Error stopping source {source.name}: {e}")
        
        # Publish offline availability
        self.mqtt_client.publish_availability(False)
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Coordinator stopped")
    
    def _publish_discovery(self):
        """Publish MQTT discovery messages for all sensors."""
        logger.info("Publishing MQTT discovery messages")
        
        all_sensor_configs = {}
        
        # Collect sensor configurations from all processors
        for processor in self.processors.values():
            if processor.enabled:
                try:
                    sensor_configs = processor.get_sensor_configs()
                    all_sensor_configs.update(sensor_configs)
                except Exception as e:
                    logger.error(f"Error getting sensor configs from {processor.name}: {e}")
        
        # Publish discovery messages
        if all_sensor_configs:
            self.mqtt_client.publish_discovery(all_sensor_configs)
            logger.info(f"Published discovery for {len(all_sensor_configs)} sensors")
        else:
            logger.warning("No sensor configurations found")
    
    def _schedule_processing(self):
        """Schedule periodic image processing."""
        # Clear any existing schedules
        schedule.clear()
        
        # Schedule processing for each source
        for source_name, source in self.sources.items():
            if source.enabled:
                interval = source.config.get('update_interval', 30)
                schedule.every(interval).seconds.do(
                    self._process_source, source_name
                )
                logger.info(f"Scheduled processing for {source_name} every {interval} seconds")
        
        # Also schedule immediate processing on startup
        schedule.every(5).seconds.do(self._process_all_sources).tag('startup')
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
    
    def _process_all_sources(self):
        """Process all sources once (for startup)."""
        logger.info("Processing all sources (startup)")
        
        for source_name in self.sources.keys():
            self._process_source(source_name)
        
        # Remove startup schedule after first run
        schedule.clear('startup')
    
    def _process_source(self, source_name: str):
        """Process a specific source.
        
        Args:
            source_name: Name of the source to process
        """
        source = self.sources.get(source_name)
        if not source or not source.enabled:
            return
        
        try:
            # Check if there's a new image
            if not source.has_new_image():
                logger.debug(f"No new image for source: {source_name}")
                return
            
            # Get the latest image
            image = source.get_latest_image()
            if image is None:
                logger.debug(f"No image available for source: {source_name}")
                return
            
            logger.info(f"Processing new image from source: {source_name}")
            
            # Process image with all enabled processors
            for processor in self.processors.values():
                if processor.enabled:
                    try:
                        self._process_image_with_processor(image, processor, source_name)
                    except Exception as e:
                        logger.error(f"Error processing image with {processor.name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing source {source_name}: {e}")
    
    def _process_image_with_processor(self, image, processor: BaseProcessor, source_name: str):
        """Process an image with a specific processor.
        
        Args:
            image: Image to process
            processor: Processor to use
            source_name: Name of the source
        """
        # Process the image
        results = processor.process_image(image)
        
        if 'error' in results:
            logger.error(f"Processor {processor.name} returned error: {results['error']}")
            return
        
        # Publish results to MQTT
        self._publish_results(results, processor, source_name)
    
    def _publish_results(self, results: Dict[str, Any], processor: BaseProcessor, source_name: str):
        """Publish processing results to MQTT.
        
        Args:
            results: Processing results
            processor: Processor that generated the results
            source_name: Name of the source
        """
        try:
            if processor.quadrants:
                # Publish results for each quadrant
                for quadrant, quadrant_results in results.items():
                    if isinstance(quadrant_results, dict) and 'green_percentage' in quadrant_results:
                        topic = f"brokkoli/{processor.name}/{quadrant}"
                        value = quadrant_results['green_percentage']
                        self.mqtt_client.publish_state(topic, value)
                        logger.debug(f"Published {quadrant}: {value}%")
            else:
                # Publish single result
                if 'green_percentage' in results:
                    topic = f"brokkoli/{processor.name}"
                    value = results['green_percentage']
                    self.mqtt_client.publish_state(topic, value)
                    logger.debug(f"Published {processor.name}: {value}%")
                    
        except Exception as e:
            logger.error(f"Error publishing results: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "running": self.running,
            "sources": {name: source.enabled for name, source in self.sources.items()},
            "processors": {name: processor.enabled for name, processor in self.processors.items()},
            "mqtt_connected": self.mqtt_client.is_connected()
        } 