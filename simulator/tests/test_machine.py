"""Tests for machine models."""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.models.machine import (
    Machine, MachineState, SensorReading, ActuatorStatus, 
    ProductionPart, SensorType, ActuatorType
)


class TestMachine(unittest.IsolatedAsyncioTestCase):
    """Test cases for Machine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.machine_config = {
            "id": "TEST_MACHINE_001",
            "name": "Test_Machine",
            "type": "test",
            "cycle_time": 10,
            "failure_rate": 0.1,
            "sensors": ["temperature", "pressure", "part_present"],
            "actuators": ["conveyor", "pneumatic_clamp"]
        }
        self.machine = Machine(self.machine_config, simulation_speed=10.0)
    
    def test_machine_initialization(self):
        """Test machine initialization."""
        self.assertEqual(self.machine.id, "TEST_MACHINE_001")
        self.assertEqual(self.machine.name, "Test_Machine")
        self.assertEqual(self.machine.type, "test")
        self.assertEqual(self.machine.cycle_time, 10)
        self.assertEqual(self.machine.failure_rate, 0.1)
        self.assertEqual(self.machine.simulation_speed, 10.0)
        self.assertEqual(self.machine.state, MachineState.STOPPED)
        self.assertEqual(self.machine.parts_processed, 0)
        self.assertIsNotNone(self.machine.sensor_baselines)
    
    def test_sensor_baselines_initialization(self):
        """Test sensor baseline values are properly initialized."""
        expected_sensors = ["temperature", "pressure", "vibration", "force", 
                          "position", "part_present", "torque", "weight", 
                          "camera", "laser_measurement"]
        
        for sensor in expected_sensors:
            self.assertIn(sensor, self.machine.sensor_baselines)
            self.assertIsInstance(self.machine.sensor_baselines[sensor], (int, float, bool))
    
    async def test_machine_start_stop(self):
        """Test machine start and stop operations."""
        # Test start
        await self.machine.start()
        self.assertEqual(self.machine.state, MachineState.IDLE)
        self.assertEqual(len(self.machine.actuator_data), 2)  # conveyor, pneumatic_clamp
        
        for actuator_type in self.machine.actuators:
            self.assertIn(actuator_type, self.machine.actuator_data)
            actuator_status = self.machine.actuator_data[actuator_type]
            # Accept any valid actuator state since different types have different initial states
            self.assertIsInstance(actuator_status.status, str)
            self.assertGreaterEqual(actuator_status.power_consumption, 0)
        
        # Test stop
        await self.machine.stop()
        self.assertEqual(self.machine.state, MachineState.STOPPED)
        
        for actuator_type in self.machine.actuators:
            actuator_status = self.machine.actuator_data[actuator_type]
            self.assertEqual(actuator_status.status, "stopped")
            self.assertEqual(actuator_status.power_consumption, 0.0)
    
    def test_sensor_reading(self):
        """Test sensor reading functionality."""
        sensor_data = self.machine.read_sensors()
        
        # Check that all configured sensors are read
        for sensor_type in self.machine.sensors:
            self.assertIn(sensor_type, sensor_data)
            reading = sensor_data[sensor_type]
            self.assertIsInstance(reading, SensorReading)
            self.assertEqual(reading.sensor_type, sensor_type)
            self.assertIsNotNone(reading.value)
            self.assertIsInstance(reading.timestamp, datetime)
            self.assertIn(reading.quality, ["good", "poor", "bad"])
    
    def test_sensor_value_generation(self):
        """Test realistic sensor value generation."""
        # Test part_present sensor
        self.machine.current_part = None
        value = self.machine._generate_sensor_value("part_present")
        self.assertFalse(value)
        
        # Create a mock part
        part = ProductionPart("TEST_001", "TestPart", datetime.now())
        self.machine.current_part = part
        value = self.machine._generate_sensor_value("part_present")
        self.assertTrue(value)
        
        # Test numeric sensors
        temp_value = self.machine._generate_sensor_value("temperature")
        self.assertIsInstance(temp_value, (int, float))
        
        pressure_value = self.machine._generate_sensor_value("pressure")
        self.assertIsInstance(pressure_value, (int, float))
    
    def test_sensor_quality_determination(self):
        """Test sensor quality determination logic."""
        # Test normal state
        self.machine.state = MachineState.IDLE
        quality = self.machine._determine_sensor_quality("temperature", 25.0)
        self.assertIn(quality, ["good", "poor"])
        
        # Test error state
        self.machine.state = MachineState.ERROR
        quality = self.machine._determine_sensor_quality("temperature", 25.0)
        self.assertIn(quality, ["poor", "bad"])
    
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
            unit = self.machine._get_sensor_unit(sensor_type)
            self.assertEqual(unit, expected_unit)
        
        # Test unknown sensor type
        unit = self.machine._get_sensor_unit("unknown_sensor")
        self.assertEqual(unit, "unit")
    
    async def test_part_processing(self):
        """Test part processing through machine."""
        # Start machine first
        await self.machine.start()
        
        # Create a test part
        part = ProductionPart("TEST_PART_001", "TestWidget", datetime.now())
        
        # Process the part
        processed_part = await self.machine.process_part(part)
        
        # Verify processing results
        self.assertEqual(processed_part.part_id, "TEST_PART_001")
        self.assertEqual(processed_part.current_station, "TEST_MACHINE_001")
        self.assertIn(processed_part.quality_status, ["pass", "fail"])
        self.assertEqual(len(processed_part.processing_history), 1)
        
        # Verify machine state after processing
        self.assertEqual(self.machine.state, MachineState.IDLE)
        self.assertIsNone(self.machine.current_part)
        self.assertEqual(self.machine.parts_processed, 1)
        
        # Verify processing history
        history = processed_part.processing_history[0]
        self.assertEqual(history["machine_id"], "TEST_MACHINE_001")
        self.assertEqual(history["machine_name"], "Test_Machine")
        self.assertIsInstance(history["processing_time"], (int, float))
        self.assertIn(history["quality_status"], ["pass", "fail"])
    
    async def test_part_processing_machine_not_ready(self):
        """Test part processing when machine is not ready."""
        part = ProductionPart("TEST_PART_002", "TestWidget", datetime.now())
        
        # Try to process part when machine is stopped
        with self.assertRaises(ValueError):
            await self.machine.process_part(part)
    
    def test_machine_status(self):
        """Test machine status reporting."""
        status = self.machine.get_status()
        
        # Check new data structure
        self.assertIn("machine_production_data", status)
        self.assertIn("sensor_actuator_data", status)
        
        # Test machine production data fields
        production_data = status["machine_production_data"]
        required_production_fields = ["id", "name", "type", "state", "operation_phase", 
                                    "current_part", "parts_processed", "total_runtime_hours", 
                                    "last_maintenance"]
        
        for field in required_production_fields:
            self.assertIn(field, production_data)
        
        # Test sensor actuator data structure
        sensor_actuator_data = status["sensor_actuator_data"]
        self.assertIn("sensors", sensor_actuator_data)
        self.assertIn("actuators", sensor_actuator_data)
        
        # Test data types
        self.assertIsInstance(production_data["parts_processed"], int)
        self.assertIsInstance(production_data["total_runtime_hours"], (int, float))
        self.assertIsInstance(sensor_actuator_data["sensors"], dict)
        self.assertIsInstance(sensor_actuator_data["actuators"], dict)
    
    def test_enums(self):
        """Test enum definitions."""
        # Test MachineState enum
        states = [MachineState.STOPPED, MachineState.RUNNING, MachineState.MAINTENANCE, 
                 MachineState.ERROR, MachineState.IDLE]
        for state in states:
            self.assertIsInstance(state.value, str)
        
        # Test SensorType enum
        sensor_types = [SensorType.TEMPERATURE, SensorType.PRESSURE, SensorType.VIBRATION]
        for sensor_type in sensor_types:
            self.assertIsInstance(sensor_type.value, str)
        
        # Test ActuatorType enum
        actuator_types = [ActuatorType.CONVEYOR, ActuatorType.PNEUMATIC_CLAMP, ActuatorType.HEATING_ELEMENT]
        for actuator_type in actuator_types:
            self.assertIsInstance(actuator_type.value, str)
    
    def test_dataclasses(self):
        """Test dataclass structures."""
        # Test SensorReading
        reading = SensorReading("temperature", 25.0, datetime.now(), "°C")
        self.assertEqual(reading.sensor_type, "temperature")
        self.assertEqual(reading.value, 25.0)
        self.assertEqual(reading.unit, "°C")
        self.assertEqual(reading.quality, "good")  # default value
        
        # Test ActuatorStatus
        status = ActuatorStatus("conveyor", "running", datetime.now(), 150.0)
        self.assertEqual(status.actuator_type, "conveyor")
        self.assertEqual(status.status, "running")
        self.assertEqual(status.power_consumption, 150.0)
        
        # Test ProductionPart
        part = ProductionPart("PART_001", "Widget", datetime.now())
        self.assertEqual(part.part_id, "PART_001")
        self.assertEqual(part.part_type, "Widget")
        self.assertIsNone(part.current_station)
        self.assertEqual(part.quality_status, "unknown")
        self.assertEqual(len(part.processing_history), 0)


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
    test_case = TestMachine()
    test_case.setUp()
    
    print("Running async tests...")
    
    # Test machine start/stop
    print("Testing machine start/stop...")
    run_async_test(test_case.test_machine_start_stop())
    
    # Test part processing
    print("Testing part processing...")
    run_async_test(test_case.test_part_processing())
    
    # Test error handling
    print("Testing error handling...")
    run_async_test(test_case.test_part_processing_machine_not_ready())
    
    print("Async tests completed successfully!")
    
    # Run regular unittest
    unittest.main()
