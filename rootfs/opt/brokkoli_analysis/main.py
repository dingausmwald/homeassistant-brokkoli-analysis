#!/usr/bin/env python3
"""Main entry point for Brokkoli Analysis Addon."""

import json
import logging
import os
import signal
import sys
from typing import Dict, Any

from coordinator import ProcessingCoordinator


def load_config() -> Dict[str, Any]:
    """Load configuration from Home Assistant addon options.
    
    Returns:
        Configuration dictionary
    """
    try:
        # Load configuration from addon options
        options_file = '/data/options.json'
        
        if os.path.exists(options_file):
            with open(options_file, 'r') as f:
                config = json.load(f)
        else:
            # Fallback to default configuration
            config = {
                'mqtt': {
                    'host': 'core-mosquitto',
                    'port': 1883,
                    'username': '',
                    'password': '',
                    'discovery_prefix': 'homeassistant'
                },
                'sources': [
                    {
                        'name': 'Camera Left',
                        'type': 'folder',
                        'path': '/share/brokkoli/camera_left',
                        'update_interval': 30
                    }
                ],
                'processors': [
                    {
                        'name': 'Green Pixels',
                        'type': 'green_pixels',
                        'enabled': True,
                        'quadrants': False
                    }
                ],
                'log_level': 'info'
            }
        
        return config
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def setup_logging(log_level: str = 'info') -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level
    """
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }
    
    log_level = level_map.get(log_level.lower(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('paho.mqtt.client').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logging.info(f"Received signal {signum}, shutting down...")
    global coordinator
    if coordinator:
        coordinator.stop()
    sys.exit(0)


def main():
    """Main entry point."""
    global coordinator
    coordinator = None
    
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging(config.get('log_level', 'info'))
        
        logger = logging.getLogger(__name__)
        logger.info("Starting Brokkoli Analysis Addon...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start coordinator
        coordinator = ProcessingCoordinator(config)
        
        if not coordinator.start():
            logger.error("Failed to start coordinator")
            sys.exit(1)
        
        logger.info("Brokkoli Analysis Addon started successfully")
        
        # Keep the main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    
    finally:
        if coordinator:
            coordinator.stop()


if __name__ == '__main__':
    main() 