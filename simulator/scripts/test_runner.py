#!/usr/bin/env python3
"""
Comprehensive test runner for the production line simulator.
Runs all tests and provides detailed reporting.
"""

import sys
import os
import unittest
import asyncio
import time
from io import StringIO

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_all_tests():
    """Run all test suites and return results."""
    print("🧪 Production Line Simulator - Test Suite")
    print("=" * 60)
    
    # Capture test output
    test_output = StringIO()
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Test modules to run
    test_modules = [
        'tests.test_settings',
        'tests.test_machine',
        'tests.test_production_line',
        'tests.test_enhanced_features',  # New enhanced features tests
        'tests.test_mqtt_client',
        'tests.test_plant_simulator'
    ]
    
    # Results tracking
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_time = 0
    
    for module in test_modules:
        print(f"\n📋 Running tests for {module}")
        print("-" * 40)
        
        try:
            # Load test suite
            suite = loader.loadTestsFromName(module)
            
            # Run tests
            start_time = time.time()
            runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
            result = runner.run(suite)
            end_time = time.time()
            
            module_time = end_time - start_time
            total_time += module_time
            
            # Update counters
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
            # Print results for this module
            status = "✅ PASSED" if (len(result.failures) == 0 and len(result.errors) == 0) else "❌ FAILED"
            print(f"{status} - {result.testsRun} tests in {module_time:.2f}s")
            
            if result.failures:
                print(f"   Failures: {len(result.failures)}")
            if result.errors:
                print(f"   Errors: {len(result.errors)}")
                
        except Exception as e:
            print(f"❌ ERROR loading {module}: {e}")
            total_errors += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Total Time: {total_time:.2f}s")
    
    if total_failures == 0 and total_errors == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        return False


def run_async_integration_test():
    """Run a comprehensive integration test."""
    print("\n🔄 Running Integration Test")
    print("-" * 40)
    
    async def integration_test():
        """Complete integration test of the simulator."""
        try:
            from src.config.settings_simple import Settings
            from src.core.mqtt_client import MQTTClient
            from src.core.plant_simulator import PlantSimulator
            from src.models.production_line import ProductionOrder
            
            # Initialize with fast simulation speed
            settings = Settings()
            settings.simulation_speed = 100.0  # Very fast
            
            # Create components
            mqtt_client = MQTTClient(settings)
            await mqtt_client.connect()
            
            plant_simulator = PlantSimulator(settings, mqtt_client)
            
            # Start simulation
            print("   Starting plant simulator...")
            simulation_task = asyncio.create_task(plant_simulator.start())
            
            # Wait for initialization
            await asyncio.sleep(0.5)
            
            # Add a test order
            print("   Adding production order...")
            order = ProductionOrder(
                order_id="INTEGRATION_TEST_001",
                part_type="TestWidget",
                quantity=5,
                priority="high"
            )
            await plant_simulator.production_line.add_production_order(order)
            
            # Let simulation run
            print("   Running simulation for 3 seconds...")
            await asyncio.sleep(3.0)
            
            # Check results
            status = plant_simulator.production_line.get_production_status()
            print(f"   Parts produced: {status['metrics']['total_parts_produced']}")
            print(f"   Active parts: {status['active_parts']}")
            print(f"   Line status: {plant_simulator._get_line_status()}")
            
            # Stop simulation
            print("   Stopping simulator...")
            await plant_simulator.stop()
            simulation_task.cancel()
            
            await mqtt_client.disconnect()
            
            print("✅ Integration test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the async integration test
    return asyncio.run(integration_test())


def run_performance_test():
    """Run basic performance tests."""
    print("\n⚡ Running Performance Tests")
    print("-" * 40)
    
    try:
        from src.models.machine import Machine
        from src.models.production_line import ProductionLine
        
        # Test machine sensor reading performance
        machine_config = {
            "id": "PERF_TEST_001",
            "name": "Performance_Test_Machine",
            "type": "test",
            "cycle_time": 1,
            "failure_rate": 0,
            "sensors": ["temperature", "pressure", "vibration", "force", "position"],
            "actuators": ["conveyor"]
        }
        
        machine = Machine(machine_config, simulation_speed=1000.0)
        
        # Time sensor readings
        start_time = time.time()
        for _ in range(1000):
            machine.read_sensors()
        end_time = time.time()
        
        sensor_time = end_time - start_time
        print(f"   Sensor reading: 1000 readings in {sensor_time:.3f}s ({1000/sensor_time:.0f} readings/s)")
        
        # Test production line status generation
        production_config = {
            "name": "Performance_Test_Line",
            "machines": [machine_config]
        }
        
        production_line = ProductionLine(production_config, simulation_speed=1000.0)
        
        start_time = time.time()
        for _ in range(100):
            production_line.get_production_status()
        end_time = time.time()
        
        status_time = end_time - start_time
        print(f"   Status generation: 100 statuses in {status_time:.3f}s ({100/status_time:.0f} statuses/s)")
        
        print("✅ Performance tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def validate_configuration():
    """Validate configuration and dependencies."""
    print("\n🔧 Validating Configuration")
    print("-" * 40)
    
    issues = []
    
    try:
        # Test configuration loading
        from src.config.settings_simple import Settings
        settings = Settings()
        print("   ✅ Configuration loading")
        
        # Validate machine configurations
        for i, machine in enumerate(settings.production_line.machines):
            if not machine.get("id"):
                issues.append(f"Machine {i} missing ID")
            if not machine.get("sensors"):
                issues.append(f"Machine {machine.get('id', i)} has no sensors")
            if not machine.get("actuators"):
                issues.append(f"Machine {machine.get('id', i)} has no actuators")
        
        if not issues:
            print("   ✅ Machine configurations valid")
        
        # Test imports
        from src.models.machine import Machine
        from src.models.production_line import ProductionLine
        from src.core.mqtt_client_simple import MQTTClient
        from src.core.plant_simulator import PlantSimulator
        print("   ✅ All modules import successfully")
        
    except Exception as e:
        issues.append(f"Configuration validation error: {e}")
    
    if issues:
        print("   ❌ Configuration issues found:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print("   ✅ Configuration validation passed")
        return True


def run_docker_integration_test():
    """Run Docker integration test to validate complete system."""
    print("\n🐳 Docker Integration Test")
    print("-" * 40)
    
    try:
        # Import and run the Docker integration test
        from tests.test_docker_simple import test_docker_mqtt_integration
        return test_docker_mqtt_integration()
    except ImportError:
        print("❌ Docker integration test module not found")
        return False
    except Exception as e:
        print(f"❌ Docker integration test failed: {e}")
        return False


def main():
    """Main test runner function."""
    print("Starting comprehensive test suite...\n")
    
    # Track overall results
    all_passed = True
    
    # 1. Validate configuration
    config_ok = validate_configuration()
    all_passed = all_passed and config_ok
    
    # 2. Run unit tests
    unit_tests_ok = run_all_tests()
    all_passed = all_passed and unit_tests_ok
    
    # 3. Run async integration test
    integration_ok = run_async_integration_test()
    all_passed = all_passed and integration_ok
    
    # 4. Run Docker integration test
    docker_ok = run_docker_integration_test()
    all_passed = all_passed and docker_ok
    
    # 5. Run performance tests
    performance_ok = run_performance_test()
    all_passed = all_passed and performance_ok
    all_passed = all_passed and performance_ok
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED - SYSTEM READY!")
        print("\nThe production line simulator is working correctly and ready for use.")
        print("You can now run:")
        print("  python main.py        # Full simulation")
        print("  python demo.py        # Quick demo")
        exit_code = 0
    else:
        print("❌ SOME TESTS FAILED - ISSUES DETECTED")
        print("\nPlease review the test results above and fix any issues.")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
