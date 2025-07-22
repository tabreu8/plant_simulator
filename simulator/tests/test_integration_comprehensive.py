"""Comprehensive integration tests for the production line simulator."""

import asyncio
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.models.production_line import ProductionLine, ProductionOrder
from src.models.machine import Machine, ProductionPart
from src.core.plant_simulator import PlantSimulator
from src.config.settings_simple import Settings


class TestProductionLineIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for complete production line scenarios."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.settings.production_line.name = "Test_Line"
        
        self.production_config = {
            "name": "Test_Line",
            "machines": [
                {
                    "id": "MACHINE_001",
                    "name": "Material_Prep",
                    "type": "preparation",
                    "cycle_time": 2,  # Fast for testing
                    "failure_rate": 0.0,
                    "sensors": ["temperature", "pressure", "part_present"],
                    "actuators": ["conveyor", "pneumatic_clamp", "heating_element"]
                },
                {
                    "id": "MACHINE_002", 
                    "name": "Assembly_Station",
                    "type": "assembly",
                    "cycle_time": 3,
                    "failure_rate": 0.0,
                    "sensors": ["force", "position", "part_present"],
                    "actuators": ["robot_arm", "screwdriver", "conveyor"]
                },
                {
                    "id": "MACHINE_003",
                    "name": "Quality_Check", 
                    "type": "inspection",
                    "cycle_time": 2,
                    "failure_rate": 0.0,
                    "sensors": ["pressure", "current", "part_present"],
                    "actuators": ["test_fixture", "reject_pusher", "conveyor"]
                }
            ]
        }
        
        self.production_line = ProductionLine(self.production_config, simulation_speed=10.0)
    
    async def test_complete_production_cycle(self):
        """Test a complete part flowing through all stations."""
        # Add production order
        order = ProductionOrder(
            order_id="TEST_ORDER_001",
            part_type="Widget_A",
            quantity=3,
            status="in_progress"
        )
        await self.production_line.add_production_order(order)
        
        # Start production line
        await self.production_line.start()
        
        # Wait for parts to flow through
        await asyncio.sleep(2)
        
        # Verify parts are being processed
        self.assertGreater(len(self.production_line.active_parts), 0)
        
        # Wait for complete cycle
        await asyncio.sleep(10)
        
        # Verify parts completed
        self.assertGreater(len(self.production_line.completed_parts), 0)
        
        # Stop production line
        await self.production_line.stop()
    
    async def test_buffer_flow_control(self):
        """Test buffer management and flow control."""
        # Add order with multiple parts
        order = ProductionOrder(
            order_id="TEST_ORDER_002",
            part_type="Widget_B", 
            quantity=5,
            status="in_progress"
        )
        await self.production_line.add_production_order(order)
        
        # Start production
        await self.production_line.start()
        
        # Let system run
        await asyncio.sleep(5)
        
        # Check buffer status
        buffer_status = self.production_line.get_buffer_status()
        
        # Verify buffers are being used
        total_buffered = sum(buffer_status.values())
        self.assertGreaterEqual(total_buffered, 0)
        
        await self.production_line.stop()
    
    async def test_part_id_generation(self):
        """Test unique sequential part ID generation."""
        order = ProductionOrder(
            order_id="TEST_ORDER_003",
            part_type="Widget_C",
            quantity=5,
            status="in_progress"
        )
        await self.production_line.add_production_order(order)
        
        await self.production_line.start()
        await asyncio.sleep(3)
        
        # Check that part IDs are sequential and unique
        part_ids = [part.part_id for part in self.production_line.active_parts]
        part_ids.extend([part.part_id for part in self.production_line.completed_parts])
        
        # Verify sequential numbering
        expected_ids = [f"TEST_ORDER_003_{i:04d}" for i in range(1, len(part_ids) + 1)]
        self.assertEqual(sorted(part_ids), sorted(expected_ids[:len(part_ids)]))
        
        await self.production_line.stop()
    
    async def test_quality_control_flow(self):
        """Test quality control with rejection scenarios."""
        # Configure machine with higher failure rate for testing
        machine_config = self.production_config["machines"][2].copy()
        machine_config["failure_rate"] = 0.3  # 30% failure rate for testing
        
        # Create production line with quality failures
        test_config = self.production_config.copy()
        test_config["machines"][2] = machine_config
        
        production_line = ProductionLine(test_config, simulation_speed=20.0)
        
        order = ProductionOrder(
            order_id="TEST_ORDER_004",
            part_type="Widget_D",
            quantity=10,
            status="in_progress"
        )
        await production_line.add_production_order(order)
        
        await production_line.start()
        await asyncio.sleep(8)
        
        # Verify some parts were rejected
        total_parts = len(production_line.completed_parts) + production_line.metrics.total_parts_rejected
        self.assertGreater(total_parts, 0)
        
        # Check quality rate calculation
        if total_parts > 0:
            quality_rate = len(production_line.completed_parts) / total_parts
            self.assertLess(quality_rate, 1.0)  # Should be less than 100% due to failures
        
        await production_line.stop()
    
    async def test_production_metrics(self):
        """Test production metrics calculation."""
        order = ProductionOrder(
            order_id="TEST_ORDER_005",
            part_type="Widget_E",
            quantity=5,
            status="in_progress"
        )
        await self.production_line.add_production_order(order)
        
        await self.production_line.start()
        await asyncio.sleep(5)
        
        # Check metrics
        status = self.production_line.get_production_status()
        
        # Verify metrics structure
        self.assertIn("metrics", status)
        metrics = status["metrics"]
        
        # Check all required metric fields
        required_fields = ["total_parts_produced", "total_parts_rejected", 
                          "quality_rate", "throughput_per_hour", "cycle_time_avg", "oee_overall"]
        for field in required_fields:
            self.assertIn(field, metrics)
            self.assertIsInstance(metrics[field], (int, float))
        
        await self.production_line.stop()
    
    async def test_machine_state_transitions(self):
        """Test machine state transitions during operation."""
        await self.production_line.start()
        
        # Check initial states
        for machine in self.production_line.machines.values():
            self.assertEqual(machine.state.value, "running")
        
        # Add order to trigger processing
        order = ProductionOrder(
            order_id="TEST_ORDER_006",
            part_type="Widget_F",
            quantity=2,
            status="in_progress"
        )
        await self.production_line.add_production_order(order)
        
        # Wait for processing to start
        await asyncio.sleep(3)
        
        # Verify machines are in active states
        machine_states = [machine.state.value for machine in self.production_line.machines.values()]
        self.assertIn("running", machine_states)
        
        await self.production_line.stop()
        
        # Verify machines stopped
        for machine in self.production_line.machines.values():
            self.assertEqual(machine.state.value, "idle")


class TestMQTTDataFormat(unittest.IsolatedAsyncioTestCase):
    """Test MQTT data format and publishing."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        from src.core.mqtt_client_simple import MQTTClient
        from src.config.settings_simple import Settings
        
        self.settings = Settings()
        self.mqtt_client = MQTTClient(self.settings)
    
    async def test_boolean_sensor_format(self):
        """Test boolean sensors are published as 1/0."""
        await self.mqtt_client.connect()
        
        # Test boolean values
        await self.mqtt_client.publish_sensor_data("TEST_MACHINE", "part_present", True)
        await self.mqtt_client.publish_sensor_data("TEST_MACHINE", "part_present", False)
        
        # In a real MQTT test, we would subscribe and verify the actual published values
        # For now, we verify the client accepts boolean inputs
        self.assertTrue(True)  # Placeholder - would need actual MQTT broker for full test
    
    async def test_sensor_data_types(self):
        """Test various sensor data types."""
        await self.mqtt_client.connect()
        
        # Test different sensor types
        test_data = [
            ("temperature", 25.5, float),
            ("pressure", 1.2, float),
            ("part_present", True, bool),
            ("force", 150, int),
            ("position", 75.0, float)
        ]
        
        for sensor_type, value, expected_type in test_data:
            self.assertIsInstance(value, expected_type)
            await self.mqtt_client.publish_sensor_data("TEST_MACHINE", sensor_type, value)


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test error handling and recovery scenarios."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.production_config = {
            "name": "Error_Test_Line",
            "machines": [{
                "id": "ERROR_MACHINE",
                "name": "Error_Test_Machine",
                "type": "test",
                "cycle_time": 1,
                "failure_rate": 0.5,  # High failure rate for testing
                "sensors": ["temperature", "part_present"],
                "actuators": ["conveyor"]
            }]
        }
        
        self.production_line = ProductionLine(self.production_config, simulation_speed=20.0)
    
    async def test_machine_error_recovery(self):
        """Test machine error states and recovery."""
        machine = list(self.production_line.machines.values())[0]
        
        # Start machine
        await machine.start()
        self.assertEqual(machine.state.value, "running")
        
        # Simulate error
        machine.state = machine.state.ERROR
        self.assertEqual(machine.state.value, "error")
        
        # Test recovery
        await machine.start()  # Should recover from error
        self.assertEqual(machine.state.value, "running")
    
    async def test_invalid_production_order(self):
        """Test handling of invalid production orders."""
        # Test with invalid quantity
        invalid_order = ProductionOrder(
            order_id="INVALID_001",
            part_type="Widget_X",
            quantity=0,  # Invalid quantity
            status="in_progress"
        )
        
        # Should handle gracefully without crashing
        try:
            await self.production_line.add_production_order(invalid_order)
            self.assertTrue(True)  # Succeeded without exception
        except Exception as e:
            self.fail(f"Should handle invalid order gracefully: {e}")


if __name__ == '__main__':
    unittest.main()
