"""Test enhanced features: malfunction simulation, inspection status, and data organization."""

import asyncio
import unittest
from datetime import datetime, timedelta
from src.models.machine import Machine, MachineState, OperationPhase, ProductionPart
from src.models.production_line import ProductionLine, ProductionOrder


class TestMalfunctionSimulation(unittest.TestCase):
    """Test malfunction simulation features."""
    
    def setUp(self):
        """Set up test machine with high failure rate."""
        self.machine_config = {
            "id": "TEST_MALFUNCTION_001",
            "name": "Test_Malfunction_Machine",
            "type": "preparation",
            "cycle_time": 10,
            "failure_rate": 1.0,  # 100% chance for testing
            "sensors": ["temperature", "pressure"],
            "actuators": ["conveyor", "heating_element"]
        }
        self.machine = Machine(self.machine_config, simulation_speed=50)
    
    def test_malfunction_state_exists(self):
        """Test that MALFUNCTION state is available."""
        self.assertIn(MachineState.MALFUNCTION, list(MachineState))
        self.assertEqual(MachineState.MALFUNCTION.value, "malfunction")
    
    def test_malfunction_tracking_attributes(self):
        """Test that malfunction tracking attributes are present."""
        self.assertTrue(hasattr(self.machine, 'malfunction_start_time'))
        self.assertTrue(hasattr(self.machine, 'malfunction_duration'))
        self.assertIsNone(self.machine.malfunction_start_time)
        self.assertEqual(self.machine.malfunction_duration, 0.0)
    
    def test_malfunction_simulation(self):
        """Test malfunction occurs and is tracked properly."""
        async def _test():
            await self.machine.start()
            
            # Create test part
            part = ProductionPart("TEST_PART_001", "TestWidget", datetime.now())
            
            # Process part (should trigger malfunction due to 100% failure rate)
            initial_time = datetime.now()
            await self.machine.process_part(part)
            processing_time = (datetime.now() - initial_time).total_seconds()
            
            # Verify malfunction was handled (processing should take longer)
            self.assertGreater(processing_time, 0.5)  # Should take some time for malfunction
            
            # Check that machine is back to normal state after processing
            self.assertEqual(self.machine.state, MachineState.IDLE)
            
            # Part should still pass (malfunction doesn't fail the part)
            self.assertEqual(part.quality_status, "pass")
        
        run_async_test(_test())
    
    def test_malfunction_data_in_status(self):
        """Test malfunction information in machine status."""
        # Simulate malfunction state
        self.machine.state = MachineState.MALFUNCTION
        self.machine.malfunction_start_time = datetime.now()
        self.machine.malfunction_duration = 120.0  # 2 minutes
        
        status = self.machine.get_status()
        production_data = status["machine_production_data"]
        
        # Should include malfunction information
        self.assertIn("malfunction_duration_remaining", production_data)
        self.assertIn("malfunction_elapsed", production_data)
        self.assertIsInstance(production_data["malfunction_duration_remaining"], (int, float))
        self.assertIsInstance(production_data["malfunction_elapsed"], (int, float))


class TestInspectionFeatures(unittest.TestCase):
    """Test inspection machine OK/NOK status features."""
    
    def setUp(self):
        """Set up inspection machine."""
        self.machine_config = {
            "id": "TEST_INSPECTION_001",
            "name": "Test_Inspection_Machine",
            "type": "inspection",
            "cycle_time": 15,
            "failure_rate": 0.0,  # No malfunctions for this test
            "sensors": ["camera", "laser_measurement"],
            "actuators": ["conveyor", "reject_pusher", "sorting_gate"]
        }
        self.machine = Machine(self.machine_config, simulation_speed=50)
    
    def test_inspection_result_generation(self):
        """Test that inspection generates OK/NOK results."""
        async def _test():
            await self.machine.start()
            
            # Process multiple parts to get both results
            results = []
            for i in range(10):
                part = ProductionPart(f"TEST_PART_{i:03d}", "TestWidget", datetime.now())
                await self.machine.process_part(part)
                
                # Check if inspection result was recorded
                if "inspection_result" in self.machine.sensor_data:
                    result = self.machine.sensor_data["inspection_result"].value
                    results.append(result)
                    self.assertIn(result, ["ok", "nok"])
                    
                    # Verify part quality matches inspection result
                    if result == "nok":
                        self.assertEqual(part.quality_status, "reject")
                    else:
                        self.assertEqual(part.quality_status, "pass")
            
            # Should have some results
            self.assertGreater(len(results), 0)
            # With random 5% rejection rate, we might get some NOK results
            self.assertTrue(any(r == "ok" for r in results))
        
        run_async_test(_test())
    
    def test_inspection_status_in_machine_data(self):
        """Test inspection status appears in machine status data."""
        # Simulate inspection result
        from src.models.machine import SensorReading
        inspection_reading = SensorReading(
            sensor_type="inspection_result",
            value="nok",
            timestamp=datetime.now(),
            unit="status",
            quality="good"
        )
        self.machine.sensor_data["inspection_result"] = inspection_reading
        
        # Test machine status directly first
        status = self.machine.get_status()
        production_data = status["machine_production_data"]
        
        # For machine status, inspection_status is not included, only in production line data
        # Let's test the production line method instead
        line_config = {
            "name": "test_line",
            "machines": [self.machine_config]
        }
        line = ProductionLine(line_config)
        
        # Manually add the sensor data to the production line's machine
        line.machines["TEST_INSPECTION_001"].sensor_data["inspection_result"] = inspection_reading
        
        machine_data = line.get_machine_status_data()
        production_data = machine_data["TEST_INSPECTION_001"]["machine_production_data"]
        
        self.assertEqual(production_data["inspection_status"], "nok")


class TestDataOrganization(unittest.TestCase):
    """Test new data organization with sensor_actuator_data and machine_production_data."""
    
    def setUp(self):
        """Set up test machine."""
        self.machine_config = {
            "id": "TEST_DATA_001",
            "name": "Test_Data_Machine",
            "type": "preparation",
            "cycle_time": 10,
            "failure_rate": 0.0,
            "sensors": ["temperature", "pressure", "vibration"],
            "actuators": ["conveyor", "heating_element"]
        }
        self.machine = Machine(self.machine_config, simulation_speed=10)
    
    def test_machine_status_structure(self):
        """Test new machine status data structure."""
        async def _test():
            await self.machine.start()
            
            status = self.machine.get_status()
            
            # Check top-level structure
            self.assertIn("machine_production_data", status)
            self.assertIn("sensor_actuator_data", status)
            
            # Check machine production data
            production_data = status["machine_production_data"]
            required_fields = ["id", "name", "type", "state", "operation_phase", 
                              "current_part", "parts_processed", "total_runtime_hours", 
                              "last_maintenance"]
            for field in required_fields:
                self.assertIn(field, production_data)
            
            # Check sensor actuator data
            sensor_actuator_data = status["sensor_actuator_data"]
            self.assertIn("sensors", sensor_actuator_data)
            self.assertIn("actuators", sensor_actuator_data)
            self.assertIsInstance(sensor_actuator_data["sensors"], dict)
            self.assertIsInstance(sensor_actuator_data["actuators"], dict)
        
        run_async_test(_test())
    
    def test_production_line_machine_status_structure(self):
        """Test production line machine status data organization."""
        line_config = {
            "name": "test_line",
            "machines": [self.machine_config]
        }
        line = ProductionLine(line_config)
        
        machine_data = line.get_machine_status_data()
        
        # Check structure for each machine
        for machine_id, data in machine_data.items():
            self.assertIn("machine_production_data", data)
            self.assertIn("sensor_actuator_data", data)
            
            # Check production data fields
            production_data = data["machine_production_data"]
            required_fields = ["machine_state", "operation_phase", "machine_type", 
                              "machine_name", "parts_processed_today", "total_runtime_hours"]
            for field in required_fields:
                self.assertIn(field, production_data)
            
            # Check sensor actuator data
            sensor_actuator_data = data["sensor_actuator_data"]
            self.assertIn("sensors", sensor_actuator_data)
            self.assertIn("actuators", sensor_actuator_data)
    
    def test_oee_removal(self):
        """Test that OEE calculations have been removed."""
        status = self.machine.get_status()
        
        # OEE should not be present in any part of the status
        self.assertNotIn("oee", status)
        self.assertNotIn("oee", status["machine_production_data"])
        self.assertNotIn("oee", status["sensor_actuator_data"])


class TestFullProductionFlow(unittest.TestCase):
    """Test complete production flow through multiple machines."""
    
    def setUp(self):
        """Set up a production line with three machines."""
        self.line_config = {
            "name": "Full_Test_Line",
            "machines": [
                {
                    "id": "PREP_001",
                    "name": "Material_Preparation",
                    "type": "preparation",
                    "cycle_time": 8,
                    "failure_rate": 0.0,  # No random failures for testing
                    "sensors": ["temperature", "pressure", "part_present"],
                    "actuators": ["conveyor", "heating_element", "pneumatic_clamp"]
                },
                {
                    "id": "ASSEMBLY_001", 
                    "name": "Assembly_Station",
                    "type": "assembly",
                    "cycle_time": 12,
                    "failure_rate": 0.0,
                    "sensors": ["force", "torque", "position"],
                    "actuators": ["robot_arm", "screwdriver", "conveyor"]
                },
                {
                    "id": "INSPECTION_001",
                    "name": "Quality_Inspection", 
                    "type": "inspection",
                    "cycle_time": 6,
                    "failure_rate": 0.0,
                    "sensors": ["camera", "laser_measurement"],
                    "actuators": ["conveyor", "reject_pusher", "sorting_gate"]
                }
            ]
        }
        self.production_line = ProductionLine(self.line_config, simulation_speed=20)
    
    def test_complete_production_flow(self):
        """Test a part flowing through the entire production line."""
        async def _test():
            # Start the production line
            await asyncio.gather(
                *[machine.start() for machine in self.production_line.machines.values()]
            )
            
            # Add a production order
            order = ProductionOrder("TEST_ORDER_001", "TestWidget", 1)
            await self.production_line.add_production_order(order)
            
            # Manually release a part and track its flow
            part = ProductionPart("TEST_ORDER_001_0001", "TestWidget", datetime.now())
            
            # Track flow through each machine
            flow_data = []
            
            # Stage 1: Material Preparation
            prep_machine = self.production_line.machines["PREP_001"]
            self.assertEqual(prep_machine.state, MachineState.IDLE)
            
            # Record initial sensor data
            prep_sensors_before = prep_machine.read_sensors()
            
            # Process part through preparation
            processed_part = await prep_machine.process_part(part)
            
            # Record data after processing
            prep_sensors_after = prep_machine.read_sensors()
            prep_status = prep_machine.get_status()
            
            flow_data.append({
                "stage": "preparation",
                "machine_id": "PREP_001",
                "sensors_before": prep_sensors_before,
                "sensors_after": prep_sensors_after,
                "machine_status": prep_status,
                "part_quality": processed_part.quality_status,
                "processing_history": processed_part.processing_history.copy()
            })
            
            # Stage 2: Assembly
            assembly_machine = self.production_line.machines["ASSEMBLY_001"]
            assembly_sensors_before = assembly_machine.read_sensors()
            
            processed_part = await assembly_machine.process_part(processed_part)
            
            assembly_sensors_after = assembly_machine.read_sensors()
            assembly_status = assembly_machine.get_status()
            
            flow_data.append({
                "stage": "assembly",
                "machine_id": "ASSEMBLY_001", 
                "sensors_before": assembly_sensors_before,
                "sensors_after": assembly_sensors_after,
                "machine_status": assembly_status,
                "part_quality": processed_part.quality_status,
                "processing_history": processed_part.processing_history.copy()
            })
            
            # Stage 3: Inspection
            inspection_machine = self.production_line.machines["INSPECTION_001"]
            inspection_sensors_before = inspection_machine.read_sensors()
            
            processed_part = await inspection_machine.process_part(processed_part)
            
            inspection_sensors_after = inspection_machine.read_sensors()
            inspection_status = inspection_machine.get_status()
            
            flow_data.append({
                "stage": "inspection",
                "machine_id": "INSPECTION_001",
                "sensors_before": inspection_sensors_before, 
                "sensors_after": inspection_sensors_after,
                "machine_status": inspection_status,
                "part_quality": processed_part.quality_status,
                "processing_history": processed_part.processing_history.copy(),
                "inspection_result": inspection_machine.sensor_data.get("inspection_result")
            })
            
            # Verify the complete flow
            self._verify_production_flow(flow_data, processed_part)
            
            # Stop machines
            await asyncio.gather(
                *[machine.stop() for machine in self.production_line.machines.values()]
            )
        
        run_async_test(_test())
    
    def _verify_production_flow(self, flow_data, final_part):
        """Verify the production flow data is correct."""
        # Should have processed through all 3 stages
        self.assertEqual(len(flow_data), 3)
        
        # Verify each stage
        prep_data = flow_data[0]
        assembly_data = flow_data[1] 
        inspection_data = flow_data[2]
        
        # Preparation stage verification
        self.assertEqual(prep_data["stage"], "preparation")
        self.assertEqual(prep_data["machine_id"], "PREP_001")
        self.assertIn("temperature", prep_data["sensors_after"])
        self.assertIn("pressure", prep_data["sensors_after"])
        self.assertIn("part_present", prep_data["sensors_after"])
        
        prep_status = prep_data["machine_status"]
        self.assertIn("machine_production_data", prep_status)
        self.assertIn("sensor_actuator_data", prep_status)
        
        # Assembly stage verification
        self.assertEqual(assembly_data["stage"], "assembly")
        self.assertEqual(assembly_data["machine_id"], "ASSEMBLY_001")
        self.assertIn("force", assembly_data["sensors_after"])
        self.assertIn("torque", assembly_data["sensors_after"])
        self.assertIn("position", assembly_data["sensors_after"])
        
        # Inspection stage verification
        self.assertEqual(inspection_data["stage"], "inspection")
        self.assertEqual(inspection_data["machine_id"], "INSPECTION_001")
        self.assertIn("camera", inspection_data["sensors_after"])
        self.assertIn("laser_measurement", inspection_data["sensors_after"])
        
        # Should have inspection result
        if inspection_data["inspection_result"]:
            result_value = inspection_data["inspection_result"].value
            self.assertIn(result_value, ["ok", "nok"])
        
        # Final part verification
        self.assertEqual(len(final_part.processing_history), 3)
        
        # Processing history should be in order
        machine_sequence = [record["machine_id"] for record in final_part.processing_history]
        expected_sequence = ["PREP_001", "ASSEMBLY_001", "INSPECTION_001"]
        self.assertEqual(machine_sequence, expected_sequence)
        
        # Each processing record should have required fields
        for record in final_part.processing_history:
            required_fields = ["machine_id", "machine_name", "start_time", 
                              "end_time", "processing_time", "quality_status"]
            for field in required_fields:
                self.assertIn(field, record)
            
            # Processing time should be reasonable
            self.assertGreater(record["processing_time"], 0)
            self.assertLess(record["processing_time"], 30)  # Should be under 30 seconds with fast simulation
    
    def test_buffer_flow_management(self):
        """Test part flow through station buffers."""
        async def _test():
            # Start machines
            await asyncio.gather(
                *[machine.start() for machine in self.production_line.machines.values()]
            )
            
            # Check initial buffer status
            buffer_status = self.production_line.get_buffer_status()
            expected_buffers = ["PREP_001_input", "PREP_001_output", 
                               "ASSEMBLY_001_input", "ASSEMBLY_001_output",
                               "INSPECTION_001_input", "INSPECTION_001_output"]
            
            for buffer_name in expected_buffers:
                self.assertIn(buffer_name, buffer_status)
                self.assertEqual(buffer_status[buffer_name], 0)
            
            # Add parts to first station buffer
            part1 = ProductionPart("TEST_PART_001", "TestWidget", datetime.now())
            part2 = ProductionPart("TEST_PART_002", "TestWidget", datetime.now())
            
            self.production_line.station_buffers["PREP_001_input"].extend([part1, part2])
            
            # Check buffer counts
            buffer_status = self.production_line.get_buffer_status()
            self.assertEqual(buffer_status["PREP_001_input"], 2)
            
            # Process one part manually through station queue processing
            await self.production_line._process_station_queues()
            
            # Should have moved one part from input to processing
            buffer_status = self.production_line.get_buffer_status()
            self.assertEqual(buffer_status["PREP_001_input"], 1)  # One remaining
            
            # Wait for processing to complete and move to output
            await asyncio.sleep(2)  # Give time for processing
            await self.production_line._manage_part_flow()
            
            # Stop machines
            await asyncio.gather(
                *[machine.stop() for machine in self.production_line.machines.values()]
            )
        
        run_async_test(_test())


# Helper function to run async tests
def run_async_test(coro):
    """Helper function to run async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMalfunctionSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestInspectionFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestDataOrganization))
    suite.addTests(loader.loadTestsFromTestCase(TestFullProductionFlow))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
