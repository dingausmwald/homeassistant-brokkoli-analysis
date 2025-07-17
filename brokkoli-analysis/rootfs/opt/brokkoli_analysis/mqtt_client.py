"""MQTT client for Home Assistant discovery and state publishing."""

import json
import logging
import time
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for Home Assistant integration."""
    
    def __init__(self, config: dict):
        """Initialize MQTT client.
        
        Args:
            config: MQTT configuration dictionary
        """
        self.config = config
        self.client = None
        self.connected = False
        self.discovery_prefix = config.get('discovery_prefix', 'homeassistant')
        
        # Device information for Home Assistant
        self.device_info = {
            "identifiers": ["brokkoli_analysis"],
            "name": "Brokkoli Analysis",
            "manufacturer": "Custom",
            "model": "Image Analyzer",
            "sw_version": "1.0.0"
        }
        
        # Origin information
        self.origin_info = {
            "name": "Brokkoli Analysis Addon",
            "sw": "1.0.0",
            "url": "https://github.com/your-username/brokkoli-analysis-addon"
        }
        
    def connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set credentials if provided
            if self.config.get('username') and self.config.get('password'):
                self.client.username_pw_set(
                    self.config['username'], 
                    self.config['password']
                )
                
            # Connect to broker
            self.client.connect(
                self.config['host'], 
                self.config['port'], 
                60
            )
            
            # Start network loop
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
                
            if self.connected:
                logger.info("Connected to MQTT broker")
                return True
            else:
                logger.error("Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info("MQTT connection successful")
            
            # Subscribe to birth message to trigger discovery
            client.subscribe(f"{self.discovery_prefix}/status")
            
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection")
    
    def _on_message(self, client, userdata, msg):
        """Callback for MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            # Handle birth message
            if topic == f"{self.discovery_prefix}/status" and payload == "online":
                logger.info("Home Assistant birth message received, triggering discovery")
                # Note: Discovery will be triggered by the coordinator
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def publish_discovery(self, sensor_configs: Dict[str, Dict[str, Any]]):
        """Publish sensor discovery configurations.
        
        Args:
            sensor_configs: Dictionary of sensor configurations
        """
        if not self.connected:
            logger.error("MQTT not connected, cannot publish discovery")
            return
            
        for sensor_name, config in sensor_configs.items():
            try:
                # Add device and origin info
                discovery_payload = {
                    **config,
                    "device": self.device_info,
                    "origin": self.origin_info
                }
                
                # Discovery topic
                discovery_topic = f"{self.discovery_prefix}/sensor/brokkoli/{sensor_name}/config"
                
                # Publish discovery message with retain flag
                self.client.publish(
                    discovery_topic,
                    json.dumps(discovery_payload),
                    qos=1,
                    retain=True
                )
                
                logger.info(f"Published discovery for sensor: {sensor_name}")
                
            except Exception as e:
                logger.error(f"Error publishing discovery for {sensor_name}: {e}")
    
    def publish_state(self, topic: str, value: Any, retain: bool = False):
        """Publish state to MQTT topic.
        
        Args:
            topic: MQTT topic
            value: State value
            retain: Whether to retain the message
        """
        if not self.connected:
            logger.error("MQTT not connected, cannot publish state")
            return
            
        try:
            # Convert value to string
            if isinstance(value, (int, float)):
                payload = str(value)
            else:
                payload = json.dumps(value)
                
            self.client.publish(topic, payload, qos=0, retain=retain)
            logger.debug(f"Published state to {topic}: {payload}")
            
        except Exception as e:
            logger.error(f"Error publishing state to {topic}: {e}")
    
    def publish_availability(self, available: bool = True):
        """Publish availability status.
        
        Args:
            available: Whether the addon is available
        """
        availability_topic = "brokkoli/availability"
        status = "online" if available else "offline"
        
        self.publish_state(availability_topic, status, retain=True)
        logger.info(f"Published availability: {status}")
    
    def remove_discovery(self, sensor_name: str):
        """Remove sensor discovery (publish empty payload).
        
        Args:
            sensor_name: Name of the sensor to remove
        """
        if not self.connected:
            return
            
        discovery_topic = f"{self.discovery_prefix}/sensor/brokkoli/{sensor_name}/config"
        self.client.publish(discovery_topic, "", qos=1, retain=True)
        logger.info(f"Removed discovery for sensor: {sensor_name}")
    
    def is_connected(self) -> bool:
        """Check if MQTT client is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected 