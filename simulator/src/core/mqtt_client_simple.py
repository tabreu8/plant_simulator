"""Simple MQTT client simulation without external dependencies."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime


class MQTTClient:
    """Mock MQTT client for development/testing when paho-mqtt is not available."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.connected = False
        
        # Topic structure
        self.base_topic = f"production/{settings.production_line.name}"
        
    async def connect(self):
        """Simulate connection to MQTT broker."""
        try:
            self.logger.info(f"Simulating MQTT connection to {self.settings.mqtt.host}:{self.settings.mqtt.port}")
            
            # Simulate connection delay
            await asyncio.sleep(1)
            
            self.connected = True
            self.logger.info("Successfully connected to MQTT broker (simulated)")
                
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            raise
    
    async def disconnect(self):
        """Simulate disconnection from MQTT broker."""
        self.connected = False
        self.logger.info("Disconnected from MQTT broker (simulated)")
    
    async def publish_sensor_data(self, machine_id: str, sensor_type: str, value: Any, timestamp: Optional[datetime] = None):
        """Simulate publishing sensor data to MQTT topic."""
        if not self.connected:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        topic = f"{self.base_topic}/machines/{machine_id}/sensors/{sensor_type}"
        
        payload = {
            "machine_id": machine_id,
            "sensor_type": sensor_type,
            "value": value,
            "timestamp": timestamp.isoformat(),
            "unit": self._get_sensor_unit(sensor_type)
        }
        
        # Simulate publishing by logging
        self.logger.debug(f"[MQTT PUB] {topic} -> {json.dumps(payload)}")
    
    async def publish_actuator_status(self, machine_id: str, actuator_type: str, status: Any, timestamp: Optional[datetime] = None):
        """Simulate publishing actuator status to MQTT topic."""
        if not self.connected:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        topic = f"{self.base_topic}/machines/{machine_id}/actuators/{actuator_type}"
        
        payload = {
            "machine_id": machine_id,
            "actuator_type": actuator_type,
            "status": status,
            "timestamp": timestamp.isoformat()
        }
        
        # Simulate publishing by logging
        self.logger.debug(f"[MQTT PUB] {topic} -> {json.dumps(payload)}")
    
    async def publish_machine_status(self, machine_id: str, status_data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """Publish machine status as individual raw values to separate topics."""
        if not self.connected:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Publish each status field as a separate topic with raw value
        for field_name, value in status_data.items():
            topic = f"{self.base_topic}/machines/{machine_id}/{field_name}"
            
            # Convert to simple string value
            if isinstance(value, bool):
                payload = "1" if value else "0"
            elif value is None:
                payload = ""
            else:
                payload = str(value)
            
            # Simulate publishing by logging key fields only
            if field_name in ['machine_state', 'operation_phase', 'current_part_id', 'parts_processed_today']:
                self.logger.info(f"[MQTT PUB] {topic} -> {payload}")
        
        # Log summary
        self.logger.info(f"Published machine status: {machine_id} -> State: {status_data.get('machine_state', 'UNKNOWN')}, Part: {status_data.get('current_part_id', 'None')}")
    
    async def publish_production_data(self, data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """Publish production line data as individual raw values."""
        if not self.connected:
            self.logger.warning("MQTT client not connected, skipping publish")
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Publish each production field as a separate topic with raw value
        for field_name, value in data.items():
            topic = f"{self.base_topic}/{field_name}"
            
            # Convert to simple string value
            if isinstance(value, bool):
                payload = "1" if value else "0"
            elif value is None:
                payload = ""
            else:
                payload = str(value)
            
            # Log key production metrics
            if field_name in ['is_running', 'completed_parts', 'active_parts', 'line_status']:
                self.logger.info(f"[MQTT PUB] {topic} -> {payload}")
    
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
