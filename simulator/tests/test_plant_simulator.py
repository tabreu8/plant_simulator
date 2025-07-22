"""Tests for plant simulator functionality."""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.core.plant_simulator import PlantSimulator
from src.core.mqtt_client_simple import MQTTClient
from src.config.settings_simple import Settings


class TestPlantSimulator(unittest.TestCase):
    """Test cases for PlantSimulator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.settings.simulation_speed = 10.0  # Speed up for tests
        self.settings.production_line.name = "Test_Plant"
        
        # Create mock MQTT client
        self.mqtt_client = MQTTClient(self.settings)
        
        self.plant_simulator = PlantSimulator(self.settings, self.mqtt_client)
    
    def test_plant_simulator_initialization(self):
        """Test plant simulator initialization."""
        self.assertEqual(self.plant_simulator.settings, self.settings)
        self.assertEqual(self.plant_simulator.mqtt_client, self.mqtt_client)
        self.assertFalse(self.plant_simulator.is_running)
        self.assertIsNotNone(self.plant_simulator.production_line)
        self.assertEqual(self.plant_simulator.production_line.name, "Test_Plant")
    
    def test_shift_info_calculation(self):
        """Test shift information calculation."""
        # Test different times of day
        test_times = [
            (8, "Morning"),    # 8 AM
            (16, "Afternoon"), # 4 PM
            (23, "Night"),     # 11 PM
            (2, "Night")       # 2 AM
        ]
        
        for hour, expected_shift in test_times:
            with patch('src.core.plant_simulator.datetime') as mock_datetime:
                mock_now = datetime(2025, 7, 21, hour, 30, 0)
                mock_datetime.now.return_value = mock_now
                
                shift_info = self.plant_simulator._get_shift_info()
                
                self.assertEqual(shift_info["current_shift"], expected_shift)
                self.assertIn("shift_start", shift_info)
                self.assertIn("shift_end", shift_info)
                self.assertIn("time_remaining_minutes", shift_info)
                self.assertIn("shift_progress_percent", shift_info)
                
                self.assertIsInstance(shift_info["time_remaining_minutes"], (int, float))
                self.assertIsInstance(shift_info["shift_progress_percent"], (int, float))
                self.assertGreaterEqual(shift_info["shift_progress_percent"], 0)
                self.assertLessEqual(shift_info["shift_progress_percent"], 100)
    
    def test_current_of_info_no_orders(self):
        """Test current OF info when no orders are active."""
        of_info = self.plant_simulator._get_current_of()
        
        expected_fields = ["of_number", "part_type", "total_quantity", "completed_quantity",
                          "remaining_quantity", "progress_percent", "priority", "status", "due_date"]
        
        for field in expected_fields:
            self.assertIn(field, of_info)
        
        self.assertIsNone(of_info["of_number"])
        self.assertIsNone(of_info["part_type"])
        self.assertEqual(of_info["total_quantity"], 0)
        self.assertEqual(of_info["status"], "no_active_order")
    
    def test_current_of_info_with_orders(self):
        """Test current OF info with active orders."""
        async def async_test():
            from src.models.production_line import ProductionOrder
            
            # Add a test order
            order = ProductionOrder(
                order_id="TEST_OF_001",
                part_type="TestWidget",
                quantity=10,
                priority="high"
            )
            order.parts_completed = 3
            
            await self.plant_simulator.production_line.add_production_order(order)
            
            of_info = self.plant_simulator._get_current_of()
            
            self.assertEqual(of_info["of_number"], "TEST_OF_001")
            self.assertEqual(of_info["part_type"], "TestWidget")
            self.assertEqual(of_info["total_quantity"], 10)
            self.assertEqual(of_info["completed_quantity"], 3)
            self.assertEqual(of_info["remaining_quantity"], 7)
            self.assertEqual(of_info["progress_percent"], 30.0)
            self.assertEqual(of_info["priority"], "high")
            self.assertEqual(of_info["status"], "in_progress")
        
        run_async_test(async_test())
    
    def test_alarm_checking_no_alarms(self):
        """Test alarm checking when no alarms are active."""
        active_alarms = self.plant_simulator._check_active_alarms()
        self.assertFalse(active_alarms)
    
    def test_line_status_determination(self):
        """Test line status determination logic."""
        # Test when not running
        self.plant_simulator.production_line.is_running = False
        status = self.plant_simulator._get_line_status()
        self.assertEqual(status, "stopped")
        
        # Test when running but idle
        self.plant_simulator.production_line.is_running = True
        status = self.plant_simulator._get_line_status()
        self.assertEqual(status, "idle")
    
    def test_alarm_generation(self):
        """Test alarm generation based on conditions."""
        # Mock production status with various conditions
        mock_status = {
            "machines": {
                "MACHINE_001": {"state": "running"},
                "MACHINE_002": {"state": "error"}  # This should trigger an alarm
            },
            "metrics": {
                "quality_rate": 0.92,  # Below threshold, should trigger alarm
                "throughput_per_hour": 5.0     # Below threshold, should trigger alarm
            }
        }
        
        with patch.object(self.plant_simulator.production_line, 'get_production_status', return_value=mock_status):
            alarms = self.plant_simulator._generate_alarms()
            
            # Should have at least one alarm for the machine error
            self.assertGreater(len(alarms), 0)
            
            # Check for machine error alarm
            machine_error_alarms = [a for a in alarms if a["alarm_type"] == "machine_error"]
            self.assertGreater(len(machine_error_alarms), 0)
            
            error_alarm = machine_error_alarms[0]
            self.assertEqual(error_alarm["machine_id"], "MACHINE_002")
            self.assertEqual(error_alarm["severity"], "high")
            self.assertFalse(error_alarm["acknowledged"])
    
    def test_generate_random_order(self):
        """Test random order generation."""
        async def async_test():
            initial_orders = len(self.plant_simulator.production_line.current_orders)
            
            await self.plant_simulator._generate_random_order()
            
            # Should have one more order
            self.assertEqual(len(self.plant_simulator.production_line.current_orders), initial_orders + 1)
            
            # Check order properties
            new_order = self.plant_simulator.production_line.current_orders[-1]
            self.assertTrue(new_order.order_id.startswith("OF_"))
            self.assertIn(new_order.part_type, ["Widget_A", "Widget_B", "Component_X", "Assembly_Y"])
            self.assertIn(new_order.priority, ["low", "normal", "high"])
            self.assertGreaterEqual(new_order.quantity, 20)
            self.assertLessEqual(new_order.quantity, 100)
        
        run_async_test(async_test())
    
    def test_generate_initial_order(self):
        """Test initial order generation."""
        async def async_test():
            await self.plant_simulator._generate_initial_order()
            
            # Should have one order
            self.assertEqual(len(self.plant_simulator.production_line.current_orders), 1)
            
            order = self.plant_simulator.production_line.current_orders[0]
            self.assertTrue(order.order_id.endswith("001"))
            self.assertEqual(order.part_type, "Widget_A")
            self.assertEqual(order.quantity, 50)
            self.assertEqual(order.priority, "normal")
        
        run_async_test(async_test())


class TestPlantSimulatorIntegration(unittest.TestCase):
    """Integration tests for plant simulator."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.settings = Settings()
        self.settings.simulation_speed = 50.0  # Very fast for integration tests
        self.mqtt_client = MQTTClient(self.settings)
        self.plant_simulator = PlantSimulator(self.settings, self.mqtt_client)
    
    def test_short_simulation_run(self):
        """Test a short simulation run."""
        async def async_test():
            # Start simulation
            simulation_task = asyncio.create_task(self.plant_simulator.start())
            
            # Let it run for a short time
            await asyncio.sleep(2.0)  # 2 seconds real time = 100 seconds simulated time
            
            # Stop simulation
            await self.plant_simulator.stop()
            simulation_task.cancel()
            
            # Check that simulation ran
            self.assertFalse(self.plant_simulator.is_running)
            
            # Should have at least one order
            self.assertGreaterEqual(len(self.plant_simulator.production_line.current_orders), 1)
        
        run_async_test(async_test())


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
    test_case = TestPlantSimulator()
    test_case.setUp()
    
    print("Running async plant simulator tests...")
    
    # Test OF info with orders
    print("Testing OF info with orders...")
    run_async_test(test_case.test_current_of_info_with_orders())
    
    # Test order generation
    print("Testing order generation...")
    run_async_test(test_case.test_generate_random_order())
    run_async_test(test_case.test_generate_initial_order())
    
    # Integration test
    integration_test = TestPlantSimulatorIntegration()
    integration_test.setUp()
    print("Running integration test...")
    run_async_test(integration_test.test_short_simulation_run())
    
    print("Async plant simulator tests completed successfully!")
    
    # Run regular unittest
    unittest.main()
