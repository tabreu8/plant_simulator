"""MQTT client for publishing production line data."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, MQTTMessage

from src.config.settings_simple import Settings


class MQTTClient:
    """Async MQTT client for production line data communication."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.client: Optional[Client] = None
        self.connected = False
        
        # Topic structure
        self.base_topic = f"production/{settings.production_line.name}"
        
    async def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client()
            
            # Set authentication if provided
            if self.settings.mqtt.username and self.settings.mqtt.password:
                self.client.username_pw_set(
                    self.settings.mqtt.username,
                    self.settings.mqtt.password
                )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            self.logger.info(f"Connecting to MQTT broker at {self.settings.mqtt.host}:{self.settings.mqtt.port}")
            self.client.connect(
                self.settings.mqtt.host,
                self.settings.mqtt.port,
                self.settings.mqtt.keepalive
            )
            
            # Start network loop
            self.client.loop_start()
            
            # Wait for connection
            retry_count = 0
            while not self.connected and retry_count < 10:
                await asyncio.sleep(0.5)
                retry_count += 1
            
            if not self.connected:
                raise Exception("Failed to connect to MQTT broker")
                
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from MQTT broker")

    async def publish_production_data(self, data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """Publish production line data to MQTT topic."""
        if not self.connected:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        topic = f"{self.base_topic}/production_data"
        
        payload = {
            **data,
            "timestamp": timestamp.isoformat()
        }
        
        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=self.settings.mqtt.qos,
                retain=self.settings.mqtt.retain
            )
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"Failed to publish production data: {result.rc}")
            else:
                self.logger.debug(f"Published production data: {topic} -> {payload}")
                
        except Exception as e:
            self.logger.error(f"Error publishing production data: {e}")
    
    async def publish_machine_status(self, machine_id: str, status_data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """Publish machine status as individual raw values to separate topics."""
        if not self.connected or not self.client:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Debug: Log what we received
        self.logger.debug(f"Publishing machine status for {machine_id}")
        self.logger.debug(f"Status data keys: {list(status_data.keys())}")
        
        # Flatten the nested structure for MQTT topics
        flattened_data = {}
        
        # Handle machine_production_data
        if "machine_production_data" in status_data:
            self.logger.debug(f"Found machine_production_data with keys: {list(status_data['machine_production_data'].keys())}")
            for key, value in status_data["machine_production_data"].items():
                flattened_data[f"production_{key}"] = value
        else:
            self.logger.warning(f"No machine_production_data found in status_data for {machine_id}")
        
        # Handle sensor_actuator_data
        if "sensor_actuator_data" in status_data:
            # Sensors
            if "sensors" in status_data["sensor_actuator_data"]:
                for sensor_type, sensor_info in status_data["sensor_actuator_data"]["sensors"].items():
                    flattened_data[f"sensor_{sensor_type}"] = sensor_info["value"]
                    flattened_data[f"sensor_{sensor_type}_unit"] = sensor_info["unit"]
                    flattened_data[f"sensor_{sensor_type}_quality"] = sensor_info["quality"]
            
            # Actuators
            if "actuators" in status_data["sensor_actuator_data"]:
                for actuator_type, actuator_info in status_data["sensor_actuator_data"]["actuators"].items():
                    flattened_data[f"actuator_{actuator_type}"] = actuator_info["status"]
                    flattened_data[f"actuator_{actuator_type}_power"] = actuator_info["power_consumption"]
        
        self.logger.debug(f"Flattened data keys: {list(flattened_data.keys())}")
        
        # Publish each flattened field as a separate topic with raw value
        for field_name, value in flattened_data.items():
            topic = f"{self.base_topic}/machines/{machine_id}/{field_name}"
            
            # Convert to simple string value
            if isinstance(value, bool):
                payload = "1" if value else "0"
            elif value is None:
                payload = ""
            elif isinstance(value, dict):
                payload = json.dumps(value)
            elif isinstance(value, list):
                payload = json.dumps(value)
            else:
                payload = str(value)
            
            try:
                result = self.client.publish(
                    topic,
                    payload,
                    qos=self.settings.mqtt.qos,
                    retain=self.settings.mqtt.retain
                )
                
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    self.logger.error(f"Failed to publish machine status field: {result.rc}")
                else:
                    self.logger.debug(f"Published: {topic} -> {payload}")
                    
            except Exception as e:
                self.logger.error(f"Error publishing machine status field {field_name}: {e}")
        
        # Log summary with correct path to machine state
        machine_state = status_data.get("machine_production_data", {}).get("machine_state", "UNKNOWN")
        current_part = status_data.get("machine_production_data", {}).get("current_part_id", "None")
        self.logger.info(f"Published machine status: {machine_id} -> State: {machine_state}, Part: {current_part}")
    
    def _format_message(self, data: Dict[str, Any]) -> str:
        """Format message data, converting booleans to PLC format."""
        def convert_value(value):
            if isinstance(value, bool):
                return "1" if value else "0"
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(v) for v in value]
            else:
                return value
        
        converted_data = convert_value(data)
        return json.dumps(converted_data)
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback."""
        if rc == 0:
            self.connected = True
            self.logger.info("Successfully connected to MQTT broker")
            
            # Subscribe to command topics
            command_topic = f"{self.base_topic}/commands/+"
            client.subscribe(command_topic)
            self.logger.info(f"Subscribed to command topic: {command_topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection: {rc}")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg: MQTTMessage):
        """MQTT message callback for commands."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            self.logger.info(f"Received command: {topic} -> {payload}")
            
            # Handle commands here (e.g., start/stop production, change parameters)
            # This can be extended based on requirements
            
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """Get the unit for a sensor type."""
        units = {
            "temperature": "°C",
            "pressure": "bar",
            "vibration": "mm/s",
            "force": "N",
            "torque": "Nm",
            "weight": "kg",
            "position": "mm",
            "part_present": "bool",
            "camera": "pixels",
            "laser_measurement": "mm"
        }
        return units.get(sensor_type, "unit")
