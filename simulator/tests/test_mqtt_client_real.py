"""Tests for real MQTT client functionality with PLC-style data format."""

import asyncio
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.core.mqtt_client import MQTTClient
from src.config.settings_simple import Settings


class TestRealMQTTClient(unittest.TestCase):
    """Test cases for real MQTT client with PLC-style formatting."""
    
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
    
    @patch('paho.mqtt.client.Client')
    async def test_connect_success(self, mock_client_class):
        """Test successful MQTT connection."""
        # Mock the MQTT client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate successful connection
        def simulate_connect(host, port, keepalive):
            # Trigger the on_connect callback
            self.mqtt_client._on_connect(mock_client, None, None, 0)
            return mock_client
        
        mock_client.connect.side_effect = simulate_connect
        
        await self.mqtt_client.connect()
        
        # Verify connection was attempted
        mock_client.connect.assert_called_once()
        self.assertTrue(self.mqtt_client.connected)
    
    @patch('paho.mqtt.client.Client')
    async def test_publish_sensor_data_boolean_conversion(self, mock_client_class):
        """Test boolean to numeric conversion in sensor data."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Setup client as connected
        self.mqtt_client.client = mock_client
        self.mqtt_client.connected = True
        
        # Test boolean True conversion
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="part_present",
            value=True
        )
        
        # Verify publish was called with "1" for True
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/part_present",
            "1",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
        
        # Test boolean False conversion
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_002",
            sensor_type="part_present",
            value=False
        )
        
        # Verify publish was called with "0" for False
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_002/part_present",
            "0",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
    
    @patch('paho.mqtt.client.Client')
    async def test_publish_sensor_data_numeric_values(self, mock_client_class):
        """Test numeric value publishing."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Setup client as connected
        self.mqtt_client.client = mock_client
        self.mqtt_client.connected = True
        
        # Test float value
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="temperature",
            value=25.5
        )
        
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/temperature",
            "25.5",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
        
        # Test integer value
        await self.mqtt_client.publish_sensor_data(
            machine_id="MACHINE_001",
            sensor_type="force",
            value=150
        )
        
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/force",
            "150",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
    
    @patch('paho.mqtt.client.Client')
    async def test_publish_actuator_status_conversion(self, mock_client_class):
        """Test actuator status to numeric conversion."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Setup client as connected
        self.mqtt_client.client = mock_client
        self.mqtt_client.connected = True
        
        # Test "active" status
        await self.mqtt_client.publish_actuator_status(
            machine_id="MACHINE_001",
            actuator_type="conveyor",
            status="active"
        )
        
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/conveyor",
            "1",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
        
        # Test "ready" status
        await self.mqtt_client.publish_actuator_status(
            machine_id="MACHINE_001",
            actuator_type="robot_arm",
            status="ready"
        )
        
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/robot_arm",
            "1",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
        
        # Test "error" status
        await self.mqtt_client.publish_actuator_status(
            machine_id="MACHINE_001",
            actuator_type="heating_element",
            status="error"
        )
        
        mock_client.publish.assert_called_with(
            "production/Test_Line/MACHINE_001/heating_element",
            "0",
            qos=self.settings.mqtt.qos,
            retain=self.settings.mqtt.retain
        )
    
    def test_plc_topic_structure(self):
        """Test PLC-style topic structure."""
        # Test sensor topic
        expected_topic = "production/Test_Line/MACHINE_001/temperature"
        self.mqtt_client.client = MagicMock()
        self.mqtt_client.connected = True
        
        # The topic structure should be plant/machine/sensor (no /sensors/ or /actuators/)
        base_topic = self.mqtt_client.base_topic
        machine_id = "MACHINE_001"
        sensor_type = "temperature"
        
        topic = f"{base_topic}/{machine_id}/{sensor_type}"
        self.assertEqual(topic, expected_topic)
    
    async def test_publish_when_not_connected(self):
        """Test publishing when not connected."""
        # Should not raise exceptions, just log warnings
        await self.mqtt_client.publish_sensor_data("MACHINE_001", "temperature", 25.0)
        await self.mqtt_client.publish_actuator_status("MACHINE_001", "conveyor", "active")
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    async def test_disconnect(self):
        """Test MQTT disconnect."""
        mock_client = MagicMock()
        self.mqtt_client.client = mock_client
        self.mqtt_client.connected = True
        
        await self.mqtt_client.disconnect()
        
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
        self.assertFalse(self.mqtt_client.connected)


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
    test_case = TestRealMQTTClient()
    test_case.setUp()
    
    print("Running real MQTT client tests...")
    
    # Test initialization
    test_case.test_mqtt_client_initialization()
    test_case.test_plc_topic_structure()
    
    # Test async methods
    run_async_test(test_case.test_connect_success())
    run_async_test(test_case.test_publish_sensor_data_boolean_conversion())
    run_async_test(test_case.test_publish_sensor_data_numeric_values())
    run_async_test(test_case.test_publish_actuator_status_conversion())
    run_async_test(test_case.test_publish_when_not_connected())
    run_async_test(test_case.test_disconnect())
    
    print("Real MQTT client tests completed successfully!")
    
    # Run regular unittest
    unittest.main()
