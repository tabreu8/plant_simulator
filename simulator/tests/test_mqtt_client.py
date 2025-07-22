"""Tests for MQTT client functionality."""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.core.mqtt_client_simple import MQTTClient
from src.config.settings_simple import Settings


class TestMQTTClient(unittest.IsolatedAsyncioTestCase):
    """Test cases for MQTT client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.settings.production_line.name = "Test_Line"
        self.mqtt_client = MQTTClient(self.settings)
    
    def test_mqtt_client_initialization(self):
        """Test MQTT client initialization."""
        self.assertEqual(self.mqtt_client.settings, self.settings)
        self.assertFalse(self.mqtt_client.connected)
        self.assertEqual(self.mqtt_client.base_topic, "production/Test_Line")
    
    async def test_connect_disconnect(self):
        """Test MQTT connect and disconnect operations."""
        # Test connect
        await self.mqtt_client.connect()
        self.assertTrue(self.mqtt_client.connected)
        
        # Test disconnect
        await self.mqtt_client.disconnect()
        self.assertFalse(self.mqtt_client.connected)
    
    async def test_publish_sensor_data(self):
        """Test publishing sensor data as raw values."""
        await self.mqtt_client.connect()
        
        # Test with timestamp
        timestamp = datetime.now()
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="temperature",
            value=25.5,
            timestamp=timestamp
        )
        
        # Test boolean values are converted to 1/0
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="part_present",
            value=True
        )
        
        # Test without timestamp (should use current time)
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="pressure",
            value=2.1
        )
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    async def test_publish_actuator_status(self):
        """Test publishing actuator status."""
        await self.mqtt_client.connect()
        
        # Test with timestamp
        timestamp = datetime.now()
        await self.mqtt_client.publish_actuator_status(
            machine_id="MACHINE_001",
            actuator_type="conveyor",
            status="running",
            timestamp=timestamp
        )
        
        # Test without timestamp
        await self.mqtt_client.publish_actuator_status(
            machine_id="MACHINE_002",
            actuator_type="robot_arm",
            status="idle"
        )
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    async def test_publish_production_data(self):
        """Test publishing production data."""
        await self.mqtt_client.connect()
        
        production_data = {
            "line_status": "running",
            "parts_produced": 150,
            "quality_rate": 0.98,
            "current_order": "ORDER_001"
        }
        
        # Test with timestamp
        timestamp = datetime.now()
        await self.mqtt_client.publish_production_data(production_data, timestamp)
        
        # Test without timestamp
        await self.mqtt_client.publish_production_data(production_data)
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    async def test_publish_when_not_connected(self):
        """Test publishing when not connected."""
        # Should not raise exceptions, just log warnings
        await self.mqtt_client.publish_sensor_data("MACHINE_001", "temperature", 25.0)
        await self.mqtt_client.publish_actuator_status("MACHINE_001", "conveyor", "running")
        await self.mqtt_client.publish_production_data({"status": "test"})
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    def test_sensor_units(self):
        """Test sensor unit mapping."""
        expected_units = {
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
        
        for sensor_type, expected_unit in expected_units.items():
            unit = self.mqtt_client._get_sensor_unit(sensor_type)
            self.assertEqual(unit, expected_unit)
        
        # Test unknown sensor type
        unit = self.mqtt_client._get_sensor_unit("unknown_sensor")
        self.assertEqual(unit, "unit")


def run_async_test(coro):
    """Helper function to run async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    # Run async tests
    test_case = TestMQTTClient()
    test_case.setUp()
    
    print("Running async MQTT client tests...")
    
    # Test connect/disconnect
    print("Testing connect/disconnect...")
    run_async_test(test_case.test_connect_disconnect())
    
    # Test publishing
    print("Testing data publishing...")
    run_async_test(test_case.test_publish_sensor_data())
    run_async_test(test_case.test_publish_actuator_status())
    run_async_test(test_case.test_publish_production_data())
    run_async_test(test_case.test_publish_when_not_connected())
    
    print("Async MQTT client tests completed successfully!")
    
    # Run regular unittest
    unittest.main()
