"""MQTT client for Home Assistant integration."""

import json
import logging
import time
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client for Home Assistant integration with discovery."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT client.
        
        Args:
            config: MQTT configuration
        """
        self.config = config
        self.host = config['host']
        self.port = config['port']
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.discovery_prefix = config.get('discovery_prefix', 'homeassistant')
        
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
        # Store registered sensors
        self.registered_sensors: Dict[str, Dict[str, Any]] = {}
    
    def connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if self.connected:
                self.logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
                return True
            else:
                self.logger.error("Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from MQTT broker")
    
    def register_sensor(self, sensor_id: str, config: Dict[str, Any]) -> bool:
        """Register a sensor with Home Assistant discovery.
        
        Args:
            sensor_id: Unique sensor identifier
            config: Sensor configuration for HA discovery
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to MQTT broker")
            return False
        
        try:
            # Build discovery topic
            discovery_topic = f"{self.discovery_prefix}/sensor/{sensor_id}/config"
            
            # Publish discovery message
            payload = json.dumps(config)
            result = self.client.publish(discovery_topic, payload, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.registered_sensors[sensor_id] = config
                self.logger.info(f"Registered sensor: {sensor_id}")
                return True
            else:
                self.logger.error(f"Failed to register sensor {sensor_id}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering sensor {sensor_id}: {e}")
            return False
    
    def publish_sensor_state(self, sensor_id: str, state: Any) -> bool:
        """Publish sensor state.
        
        Args:
            sensor_id: Sensor identifier
            state: State value to publish
            
        Returns:
            True if publish successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to MQTT broker")
            return False
        
        if sensor_id not in self.registered_sensors:
            self.logger.error(f"Sensor {sensor_id} not registered")
            return False
        
        try:
            # Get state topic from sensor config
            config = self.registered_sensors[sensor_id]
            state_topic = config.get('state_topic')
            
            if not state_topic:
                self.logger.error(f"No state topic for sensor {sensor_id}")
                return False
            
            # Publish state
            result = self.client.publish(state_topic, str(state))
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published state for {sensor_id}: {state}")
                return True
            else:
                self.logger.error(f"Failed to publish state for {sensor_id}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing state for {sensor_id}: {e}")
            return False
    
    def publish_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """Publish multiple sensor states.
        
        Args:
            sensor_data: Dictionary with sensor_id -> state mapping
            
        Returns:
            True if all publishes successful, False otherwise
        """
        success = True
        
        for sensor_id, state in sensor_data.items():
            if not self.publish_sensor_state(sensor_id, state):
                success = False
        
        return success
    
    def unregister_sensor(self, sensor_id: str) -> bool:
        """Unregister a sensor from Home Assistant.
        
        Args:
            sensor_id: Sensor identifier
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self.connected:
            self.logger.error("Not connected to MQTT broker")
            return False
        
        try:
            # Build discovery topic
            discovery_topic = f"{self.discovery_prefix}/sensor/{sensor_id}/config"
            
            # Publish empty payload to remove sensor
            result = self.client.publish(discovery_topic, "", retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                if sensor_id in self.registered_sensors:
                    del self.registered_sensors[sensor_id]
                self.logger.info(f"Unregistered sensor: {sensor_id}")
                return True
            else:
                self.logger.error(f"Failed to unregister sensor {sensor_id}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unregistering sensor {sensor_id}: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            self.logger.info("MQTT client connected")
        else:
            self.logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"MQTT client disconnected unexpectedly: {rc}")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Callback for MQTT message."""
        self.logger.debug(f"Received message: {msg.topic} - {msg.payload.decode()}")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected 