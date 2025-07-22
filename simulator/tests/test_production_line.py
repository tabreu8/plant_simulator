"""Tests for production line models."""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.models.production_line import (
    ProductionLine, ProductionOrder, ProductionMetrics
)
from src.models.machine import Machine, MachineState, ProductionPart


class TestProductionLine(unittest.IsolatedAsyncioTestCase):
    """Test cases for ProductionLine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.production_config = {
            "name": "Test_Line",
            "machines": [
                {
                    "id": "MACHINE_001",
                    "name": "Test_Machine_1",
                    "type": "preparation",
                    "cycle_time": 5,
                    "failure_rate": 0.0,  # No failures for testing
                    "sensors": ["temperature", "part_present"],
                    "actuators": ["conveyor"]
                },
                {
                    "id": "MACHINE_002",
                    "name": "Test_Machine_2",
                    "type": "assembly",
                    "cycle_time": 7,
                    "failure_rate": 0.0,
                    "sensors": ["force", "part_present"],
                    "actuators": ["robot_arm"]
                }
            ]
        }
        self.production_line = ProductionLine(self.production_config, simulation_speed=20.0)
    
    def test_production_line_initialization(self):
        """Test production line initialization."""
        self.assertEqual(self.production_line.name, "Test_Line")
        self.assertEqual(self.production_line.simulation_speed, 20.0)
        self.assertEqual(len(self.production_line.machines), 2)
        self.assertIn("MACHINE_001", self.production_line.machines)
        self.assertIn("MACHINE_002", self.production_line.machines)
        self.assertFalse(self.production_line.is_running)
        self.assertEqual(len(self.production_line.current_orders), 0)
        self.assertEqual(len(self.production_line.active_parts), 0)
        self.assertEqual(len(self.production_line.completed_parts), 0)
    
    def test_production_metrics_initialization(self):
        """Test production metrics initialization."""
        metrics = self.production_line.metrics
        self.assertIsInstance(metrics, ProductionMetrics)
        self.assertEqual(metrics.total_parts_produced, 0)
        self.assertEqual(metrics.total_parts_rejected, 0)
        self.assertEqual(metrics.cycle_time_avg, 0.0)
        self.assertEqual(metrics.throughput_per_hour, 0.0)
        self.assertEqual(metrics.quality_rate, 0.0)
        # Removed oee_overall since it's no longer part of metrics
    
    async def test_production_line_start_stop(self):
        """Test production line start and stop operations."""
        # Test that we can start the line
        start_task = asyncio.create_task(self.production_line.start())
        
        # Wait a moment for initialization
        await asyncio.sleep(0.1)
        
        self.assertTrue(self.production_line.is_running)
        self.assertIsNotNone(self.production_line.start_time)
        
        # Check that machines are started
        for machine in self.production_line.machines.values():
            self.assertEqual(machine.state, MachineState.IDLE)
        
        # Stop the line
        await self.production_line.stop()
        start_task.cancel()
        
        self.assertFalse(self.production_line.is_running)
        
        # Check that machines are stopped
        for machine in self.production_line.machines.values():
            self.assertEqual(machine.state, MachineState.STOPPED)
    
    def test_production_order_creation(self):
        """Test production order creation and properties."""
        order = ProductionOrder(
            order_id="TEST_ORDER_001",
            part_type="TestWidget",
            quantity=10,
            priority="high"
        )
        
        self.assertEqual(order.order_id, "TEST_ORDER_001")
        self.assertEqual(order.part_type, "TestWidget")
        self.assertEqual(order.quantity, 10)
        self.assertEqual(order.priority, "high")
        self.assertEqual(order.parts_completed, 0)
        self.assertEqual(order.status, "pending")
        self.assertIsInstance(order.created_at, datetime)
    
    async def test_add_production_order(self):
        """Test adding production orders."""
        order = ProductionOrder(
            order_id="TEST_ORDER_002",
            part_type="TestWidget",
            quantity=5
        )
        
        await self.production_line.add_production_order(order)
        
        self.assertEqual(len(self.production_line.current_orders), 1)
        self.assertEqual(self.production_line.current_orders[0].order_id, "TEST_ORDER_002")
        self.assertEqual(self.production_line.current_orders[0].status, "in_progress")
    
    def test_buffer_status(self):
        """Test buffer status monitoring."""
        buffer_status = self.production_line.get_buffer_status()
        
        # Should have buffers for both machines
        expected_buffers = ["MACHINE_001_input", "MACHINE_001_output", 
                           "MACHINE_002_input", "MACHINE_002_output"]
        
        for buffer_name in expected_buffers:
            self.assertIn(buffer_name, buffer_status)
            self.assertEqual(buffer_status[buffer_name], 0)  # Initially empty
    
    def test_production_status(self):
        """Test production status reporting."""
        status = self.production_line.get_production_status()
        
        required_fields = ["production_line", "is_running", "start_time", "machines",
                          "active_orders", "active_parts", "completed_parts", "metrics"]
        
        for field in required_fields:
            self.assertIn(field, status)
        
        self.assertEqual(status["production_line"], "Test_Line")
        self.assertFalse(status["is_running"])
        self.assertEqual(len(status["machines"]), 2)
        
        # Test metrics structure
        metrics = status["metrics"]
        metrics_fields = ["total_parts_produced", "total_parts_rejected", "quality_rate",
                         "throughput_per_hour", "cycle_time_avg"]
        
        for field in metrics_fields:
            self.assertIn(field, metrics)
            self.assertIsInstance(metrics[field], (int, float))
    
    def test_sensor_data_collection(self):
        """Test sensor data collection from all machines."""
        sensor_data = self.production_line.get_sensor_data()
        
        # Should have data for both machines
        self.assertEqual(len(sensor_data), 2)
        self.assertIn("MACHINE_001", sensor_data)
        self.assertIn("MACHINE_002", sensor_data)
        
        # Check machine 1 sensor data
        machine_1_data = sensor_data["MACHINE_001"]
        expected_sensors = ["temperature", "part_present"]
        for sensor in expected_sensors:
            self.assertIn(sensor, machine_1_data)
            sensor_info = machine_1_data[sensor]
            self.assertIn("value", sensor_info)
            self.assertIn("unit", sensor_info)
            self.assertIn("quality", sensor_info)
            self.assertIn("timestamp", sensor_info)
    
    def test_actuator_data_collection(self):
        """Test actuator data collection from all machines."""
        actuator_data = self.production_line.get_actuator_data()
        
        # Should have data for both machines
        self.assertEqual(len(actuator_data), 2)
        self.assertIn("MACHINE_001", actuator_data)
        self.assertIn("MACHINE_002", actuator_data)
        
        # Note: Actuator data will be empty until machines are started
        # This tests the structure, not the content
    
    async def test_complete_part(self):
        """Test part completion process."""
        # Add an order first
        order = ProductionOrder("TEST_ORDER_003", "TestWidget", 2)
        await self.production_line.add_production_order(order)
        
        # Create a part
        part = ProductionPart("TEST_ORDER_003_0001", "TestWidget", datetime.now())
        part.quality_status = "pass"
        self.production_line.active_parts.append(part)
        
        initial_active_parts = len(self.production_line.active_parts)
        initial_completed_parts = len(self.production_line.completed_parts)
        
        # Complete the part
        await self.production_line._complete_part(part)
        
        # Verify part was moved from active to completed
        self.assertEqual(len(self.production_line.active_parts), initial_active_parts - 1)
        self.assertEqual(len(self.production_line.completed_parts), initial_completed_parts + 1)
        self.assertIn(part, self.production_line.completed_parts)
        
        # Verify metrics were updated
        self.assertEqual(self.production_line.metrics.total_parts_produced, 1)
        self.assertEqual(self.production_line.metrics.total_parts_rejected, 0)
        
        # Verify order progress
        self.assertEqual(order.parts_completed, 1)
    
    async def test_complete_part_with_failure(self):
        """Test part completion with quality failure."""
        # Add an order first
        order = ProductionOrder("TEST_ORDER_004", "TestWidget", 2)
        await self.production_line.add_production_order(order)
        
        # Create a failed part
        part = ProductionPart("TEST_ORDER_004_0001", "TestWidget", datetime.now())
        part.quality_status = "fail"
        self.production_line.active_parts.append(part)
        
        # Complete the part
        await self.production_line._complete_part(part)
        
        # Verify metrics reflect the rejection
        self.assertEqual(self.production_line.metrics.total_parts_produced, 1)
        self.assertEqual(self.production_line.metrics.total_parts_rejected, 1)
    
    async def test_metrics_update(self):
        """Test metrics calculation and update."""
        # Set up some test data
        self.production_line.start_time = datetime.now() - timedelta(hours=1)
        self.production_line.metrics.total_parts_produced = 10
        self.production_line.metrics.total_parts_rejected = 1
        
        # Add a completed part with processing history
        part = ProductionPart("TEST_PART", "TestWidget", datetime.now() - timedelta(minutes=5))
        part.processing_history = [{
            "machine_id": "MACHINE_001",
            "end_time": datetime.now()
        }]
        self.production_line.completed_parts.append(part)
        
        # Update metrics
        await self.production_line._update_metrics()
        
        # Verify calculations
        self.assertGreater(self.production_line.metrics.throughput_per_hour, 0)
        self.assertAlmostEqual(self.production_line.metrics.quality_rate, 0.9, places=2)  # 9/10 good parts


class TestProductionOrder(unittest.TestCase):
    """Test cases for ProductionOrder dataclass."""
    
    def test_production_order_defaults(self):
        """Test production order default values."""
        order = ProductionOrder("ORDER_001", "Widget", 10)
        
        self.assertEqual(order.order_id, "ORDER_001")
        self.assertEqual(order.part_type, "Widget")
        self.assertEqual(order.quantity, 10)
        self.assertEqual(order.priority, "normal")
        self.assertEqual(order.parts_completed, 0)
        self.assertEqual(order.status, "pending")
        self.assertIsInstance(order.created_at, datetime)
        self.assertIsNone(order.due_date)


class TestProductionMetrics(unittest.TestCase):
    """Test cases for ProductionMetrics dataclass."""
    
    def test_production_metrics_defaults(self):
        """Test production metrics default values."""
        metrics = ProductionMetrics()
        
        self.assertEqual(metrics.total_parts_produced, 0)
        self.assertEqual(metrics.total_parts_rejected, 0)
        self.assertEqual(metrics.cycle_time_avg, 0.0)
        self.assertEqual(metrics.throughput_per_hour, 0.0)
        self.assertEqual(metrics.quality_rate, 0.0)
        # Removed oee_overall since it's no longer part of metrics
        self.assertIsInstance(metrics.total_downtime, timedelta)


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
    test_case = TestProductionLine()
    test_case.setUp()
    
    print("Running async production line tests...")
    
    # Test start/stop
    print("Testing production line start/stop...")
    run_async_test(test_case.test_production_line_start_stop())
    
    # Test order management
    print("Testing order management...")
    run_async_test(test_case.test_add_production_order())
    
    # Test part completion
    print("Testing part completion...")
    run_async_test(test_case.test_complete_part())
    run_async_test(test_case.test_complete_part_with_failure())
    
    # Test metrics
    print("Testing metrics update...")
    run_async_test(test_case.test_metrics_update())
    
    print("Async production line tests completed successfully!")
    
    # Run regular unittest
    unittest.main()
