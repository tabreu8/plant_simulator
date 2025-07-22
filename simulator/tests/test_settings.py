"""Tests for configuration settings."""

import os
import unittest
from unittest.mock import patch

from src.config.settings_simple import Settings, MQTTSettings, ProductionLineSettings


class TestSettings(unittest.TestCase):
    """Test cases for Settings classes."""
    
    def test_mqtt_settings_defaults(self):
        """Test MQTT settings default values."""
        mqtt_settings = MQTTSettings()
        
        self.assertEqual(mqtt_settings.host, "localhost")
        self.assertEqual(mqtt_settings.port, 1883)
        self.assertIsNone(mqtt_settings.username)
        self.assertIsNone(mqtt_settings.password)
        self.assertEqual(mqtt_settings.keepalive, 60)
        self.assertEqual(mqtt_settings.qos, 1)
        self.assertFalse(mqtt_settings.retain)
    
    def test_mqtt_settings_environment_variables(self):
        """Test MQTT settings with environment variables."""
        env_vars = {
            "MQTT_BROKER_HOST": "test-broker.com",
            "MQTT_BROKER_PORT": "8883",
            "MQTT_USERNAME": "test_user",
            "MQTT_PASSWORD": "test_pass"
        }
        
        with patch.dict(os.environ, env_vars):
            mqtt_settings = MQTTSettings()
            
            self.assertEqual(mqtt_settings.host, "test-broker.com")
            self.assertEqual(mqtt_settings.port, 8883)
            self.assertEqual(mqtt_settings.username, "test_user")
            self.assertEqual(mqtt_settings.password, "test_pass")
    
    def test_production_line_settings_defaults(self):
        """Test production line settings default values."""
        pl_settings = ProductionLineSettings()
        
        self.assertEqual(pl_settings.name, "Assembly_Line_A")
        self.assertEqual(pl_settings.shift_duration_hours, 8)
        self.assertEqual(pl_settings.cycle_time_seconds, 30)
        self.assertEqual(len(pl_settings.machines), 3)
        
        # Check machine configurations
        machine_ids = [machine["id"] for machine in pl_settings.machines]
        expected_ids = ["MACHINE_001", "MACHINE_002", "MACHINE_003"]
        self.assertEqual(machine_ids, expected_ids)
        
        # Check first machine configuration
        machine_1 = pl_settings.machines[0]
        self.assertEqual(machine_1["name"], "Material_Prep")
        self.assertEqual(machine_1["type"], "preparation")
        self.assertEqual(machine_1["cycle_time"], 25)
        self.assertEqual(machine_1["failure_rate"], 0.02)
        self.assertIn("temperature", machine_1["sensors"])
        self.assertIn("conveyor", machine_1["actuators"])
    
    def test_production_line_settings_environment_variables(self):
        """Test production line settings with environment variables."""
        env_vars = {
            "PRODUCTION_LINE_NAME": "Test_Line_B",
            "SHIFT_DURATION_HOURS": "12",
            "CYCLE_TIME_SECONDS": "45"
        }
        
        with patch.dict(os.environ, env_vars):
            pl_settings = ProductionLineSettings()
            
            self.assertEqual(pl_settings.name, "Test_Line_B")
            self.assertEqual(pl_settings.shift_duration_hours, 12)
            self.assertEqual(pl_settings.cycle_time_seconds, 45)
    
    def test_main_settings_defaults(self):
        """Test main settings default values."""
        settings = Settings()
        
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.simulation_speed, 1.0)
        self.assertIsInstance(settings.mqtt, MQTTSettings)
        self.assertIsInstance(settings.production_line, ProductionLineSettings)
    
    def test_main_settings_environment_variables(self):
        """Test main settings with environment variables."""
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "SIMULATION_SPEED": "2.5"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            self.assertEqual(settings.log_level, "DEBUG")
            self.assertEqual(settings.simulation_speed, 2.5)
    
    def test_machine_configuration_structure(self):
        """Test machine configuration structure."""
        pl_settings = ProductionLineSettings()
        
        for machine in pl_settings.machines:
            # Required fields
            required_fields = ["id", "name", "type", "cycle_time", "failure_rate", "sensors", "actuators"]
            for field in required_fields:
                self.assertIn(field, machine)
            
            # Field types
            self.assertIsInstance(machine["id"], str)
            self.assertIsInstance(machine["name"], str)
            self.assertIsInstance(machine["type"], str)
            self.assertIsInstance(machine["cycle_time"], (int, float))
            self.assertIsInstance(machine["failure_rate"], (int, float))
            self.assertIsInstance(machine["sensors"], list)
            self.assertIsInstance(machine["actuators"], list)
            
            # Constraints
            self.assertGreater(machine["cycle_time"], 0)
            self.assertGreaterEqual(machine["failure_rate"], 0)
            self.assertLessEqual(machine["failure_rate"], 1)
            self.assertGreater(len(machine["sensors"]), 0)
            self.assertGreater(len(machine["actuators"]), 0)
    
    def test_settings_integration(self):
        """Test integration of all settings components."""
        settings = Settings()
        
        # Test that all components are properly initialized
        self.assertIsNotNone(settings.mqtt)
        self.assertIsNotNone(settings.production_line)
        
        # Test that sub-settings can be accessed
        self.assertEqual(settings.mqtt.port, 1883)
        self.assertEqual(settings.production_line.name, "Assembly_Line_A")
        
        # Test that changes to sub-settings don't affect defaults
        settings.mqtt.host = "custom-broker"
        new_settings = Settings()
        self.assertEqual(new_settings.mqtt.host, "localhost")


if __name__ == "__main__":
    unittest.main()
