#!/usr/bin/env python3
"""Main entry point for Brokkoli Analysis addon."""

import json
import logging
import signal
import sys
import time
from pathlib import Path

from mqtt_client import MQTTClient
from coordinator import BrokkoliCoordinator


def setup_logging(log_level: str = "info"):
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (debug, info, warning, error)
    """
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    
    level = level_map.get(log_level.lower(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config() -> dict:
    """Load configuration from options.json.
    
    Returns:
        Configuration dictionary
    """
    config_path = Path("/data/options.json")
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info("Configuration loaded successfully")
        logger.debug(f"Config: {config}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


def validate_config(config: dict) -> bool:
    """Validate configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['mqtt', 'sources', 'processors']
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required configuration field: {field}")
            return False
    
    # Validate MQTT config
    mqtt_config = config['mqtt']
    mqtt_required = ['host', 'port']
    
    for field in mqtt_required:
        if field not in mqtt_config:
            logger.error(f"Missing required MQTT configuration field: {field}")
            return False
    
    # Validate sources
    sources = config['sources']
    if not isinstance(sources, list) or len(sources) == 0:
        logger.error("At least one source must be configured")
        return False
    
    for source in sources:
        if 'name' not in source or 'type' not in source:
            logger.error("Source must have 'name' and 'type' fields")
            return False
        
        if source['type'] == 'folder' and 'path' not in source:
            logger.error("Folder source must have 'path' field")
            return False
    
    # Validate processors
    processors = config['processors']
    if not isinstance(processors, list) or len(processors) == 0:
        logger.error("At least one processor must be configured")
        return False
    
    for processor in processors:
        if 'name' not in processor or 'type' not in processor:
            logger.error("Processor must have 'name' and 'type' fields")
            return False
    
    return True


class BrokkoliAnalysisApp:
    """Main application class."""
    
    def __init__(self):
        self.config = None
        self.mqtt_client = None
        self.coordinator = None
        self.running = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def run(self):
        """Run the application."""
        logger.info("Starting Brokkoli Analysis Addon")
        
        # Load and validate configuration
        self.config = load_config()
        if not validate_config(self.config):
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Initialize MQTT client
        mqtt_config = self.config['mqtt']
        self.mqtt_client = MQTTClient(mqtt_config)
        
        # Connect to MQTT broker
        if not self.mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            sys.exit(1)
        
        # Initialize coordinator
        self.coordinator = BrokkoliCoordinator(self.config, self.mqtt_client)
        
        # Start coordinator
        self.coordinator.start()
        
        # Main loop
        self.running = True
        logger.info("Brokkoli Analysis Addon started successfully")
        
        try:
            while self.running:
                time.sleep(1)
                
                # Check MQTT connection
                if not self.mqtt_client.is_connected():
                    logger.warning("MQTT connection lost, attempting to reconnect...")
                    if not self.mqtt_client.connect():
                        logger.error("Failed to reconnect to MQTT broker")
                        time.sleep(5)  # Wait before next attempt
                        continue
                    
                    # Republish discovery after reconnection
                    self.coordinator._publish_discovery()
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application."""
        if not self.running:
            return
            
        logger.info("Shutting down Brokkoli Analysis Addon")
        self.running = False
        
        # Stop coordinator
        if self.coordinator:
            self.coordinator.stop()
        
        # Disconnect MQTT client
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        logger.info("Shutdown complete")


def main():
    """Main function."""
    # Set up logging (will be overridden by config later)
    setup_logging()
    
    global logger
    logger = logging.getLogger(__name__)
    
    try:
        # Create and run application
        app = BrokkoliAnalysisApp()
        
        # Update logging level from config if available
        if hasattr(app, 'config') and app.config:
            log_level = app.config.get('log_level', 'info')
            setup_logging(log_level)
        
        app.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 