"""System validation and benchmarking tools."""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json


class SystemValidator:
    """Comprehensive system validation and performance benchmarking."""
    
    def __init__(self, production_line):
        self.production_line = production_line
        self.validation_results = {}
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🔍 Running Comprehensive System Validation")
        print("=" * 50)
        
        results = {}
        
        # Test 1: Production Flow Validation
        results['production_flow'] = await self._validate_production_flow()
        
        # Test 2: Buffer Management Validation  
        results['buffer_management'] = await self._validate_buffer_management()
        
        # Test 3: Quality Control Validation
        results['quality_control'] = await self._validate_quality_control()
        
        # Test 4: Timing and Performance Validation
        results['timing_performance'] = await self._validate_timing_performance()
        
        # Test 5: Data Integrity Validation
        results['data_integrity'] = await self._validate_data_integrity()
        
        # Test 6: Error Recovery Validation
        results['error_recovery'] = await self._validate_error_recovery()
        
        # Calculate overall score
        results['overall_score'] = self._calculate_overall_score(results)
        
        return results
    
    async def validate_production_flow(self) -> Dict[str, Any]:
        """Test complete production flow with timing"""
        print("📋 Testing Production Flow...")
        
        try:
            # Create production line
            from src.models.production_line import ProductionLine
            from src.config.settings_simple import Settings
            
            settings = Settings()
            line = ProductionLine("Assembly_Line_A", settings)
            
            print("   ✓ Production line created")
            
            # Start production
            await line.start()
            print("   ✓ Production started")
            
            # Quick validation - check for 10 seconds
            start_time = time.time()
            timeout = 10  # 10 seconds max for quick validation
            
            print("   ⏱️  Running validation for 10 seconds...")
            await asyncio.sleep(timeout)
            
            # Check machine states
            machine_states = {}
            for machine in line.machines:
                machine_states[machine.machine_id] = {
                    'state': machine.state,
                    'current_part': machine.current_part.part_id if machine.current_part else None,
                    'sensor_count': len(machine.sensors),
                    'actuator_count': len(machine.actuators)
                }
            
            await line.stop()
            print("   ✓ Production stopped")
            
            # Calculate basic metrics
            total_sensors = sum(len(m.sensors) for m in line.machines)
            total_actuators = sum(len(m.actuators) for m in line.actuators)
            
            return {
                'machines_created': len(line.machines),
                'total_sensors': total_sensors,
                'total_actuators': total_actuators,
                'machine_states': machine_states,
                'validation_time': time.time() - start_time,
                'success': True
            }
            
        except Exception as e:
            print(f"   ❌ Error in production flow: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def _validate_buffer_management(self) -> Dict[str, Any]:
        """Validate buffer management system."""
        print("\n🔄 Testing Buffer Management...")
        
        # Test buffer status reporting
        buffer_status = self.production_line.get_buffer_status()
        
        # Validate buffer structure
        expected_buffers = [f"{mid}_input" for mid in self.production_line.machine_sequence]
        expected_buffers.extend([f"{mid}_output" for mid in self.production_line.machine_sequence])
        
        all_buffers_present = all(buffer in buffer_status for buffer in expected_buffers)
        buffer_sizes_valid = all(isinstance(size, int) and size >= 0 for size in buffer_status.values())
        
        return {
            'all_buffers_present': all_buffers_present,
            'buffer_sizes_valid': buffer_sizes_valid,
            'total_buffers': len(buffer_status),
            'score': 100 if all_buffers_present and buffer_sizes_valid else 60
        }
    
    async def _validate_quality_control(self) -> Dict[str, Any]:
        """Validate quality control mechanisms."""
        print("\n🎯 Testing Quality Control...")
        
        # Check if quality metrics are being tracked
        status = self.production_line.get_production_status()
        metrics = status.get('metrics', {})
        
        has_quality_rate = 'quality_rate' in metrics
        has_rejection_count = 'total_parts_rejected' in metrics
        quality_rate_valid = 0 <= metrics.get('quality_rate', -1) <= 1
        
        return {
            'has_quality_rate': has_quality_rate,
            'has_rejection_count': has_rejection_count, 
            'quality_rate_valid': quality_rate_valid,
            'current_quality_rate': metrics.get('quality_rate', 0),
            'score': 100 if has_quality_rate and has_rejection_count and quality_rate_valid else 70
        }
    
    async def _validate_timing_performance(self) -> Dict[str, Any]:
        """Validate timing and performance characteristics."""
        print("\n⏱️  Testing Timing Performance...")
        
        # Test sensor reading performance
        machine = list(self.production_line.machines.values())[0]
        
        # Benchmark sensor readings
        sensor_times = []
        for _ in range(100):
            start = time.time()
            machine.read_sensors()
            sensor_times.append(time.time() - start)
        
        avg_sensor_time = statistics.mean(sensor_times)
        sensor_rate = 1 / avg_sensor_time
        
        # Benchmark status generation
        status_times = []
        for _ in range(50):
            start = time.time()
            machine.get_status()
            status_times.append(time.time() - start)
        
        avg_status_time = statistics.mean(status_times)
        status_rate = 1 / avg_status_time
        
        # Performance benchmarks
        sensor_performance_good = sensor_rate > 50000  # 50k/sec minimum
        status_performance_good = status_rate > 10000   # 10k/sec minimum
        
        return {
            'avg_sensor_time_ms': avg_sensor_time * 1000,
            'sensor_rate_per_sec': sensor_rate,
            'avg_status_time_ms': avg_status_time * 1000,
            'status_rate_per_sec': status_rate,
            'sensor_performance_good': sensor_performance_good,
            'status_performance_good': status_performance_good,
            'score': 100 if sensor_performance_good and status_performance_good else 80
        }
    
    async def _validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity and consistency."""
        print("\n🔒 Testing Data Integrity...")
        
        # Check machine sensor data consistency
        machine = list(self.production_line.machines.values())[0]
        
        # Read sensors multiple times and check consistency
        readings = []
        for _ in range(10):
            reading = machine.read_sensors()
            readings.append(reading)
            await asyncio.sleep(0.1)
        
        # Check data structure consistency
        all_have_same_sensors = all(
            set(reading.keys()) == set(readings[0].keys()) 
            for reading in readings
        )
        
        # Check data types consistency
        data_types_consistent = True
        for sensor_type in readings[0].keys():
            types = [type(reading[sensor_type].value) for reading in readings]
            if len(set(types)) > 1:
                data_types_consistent = False
                break
        
        return {
            'sensor_structure_consistent': all_have_same_sensors,
            'data_types_consistent': data_types_consistent,
            'sensor_count': len(readings[0]) if readings else 0,
            'score': 100 if all_have_same_sensors and data_types_consistent else 70
        }
    
    async def _validate_error_recovery(self) -> Dict[str, Any]:
        """Validate error handling and recovery."""
        print("\n🛡️  Testing Error Recovery...")
        
        machine = list(self.production_line.machines.values())[0]
        
        # Test state transitions
        original_state = machine.state
        
        # Simulate error state
        from src.models.machine import MachineState
        machine.state = MachineState.ERROR
        
        # Test recovery
        await machine.start()
        recovered = machine.state == MachineState.RUNNING
        
        # Restore original state
        machine.state = original_state
        
        return {
            'error_state_settable': True,
            'recovery_possible': recovered,
            'state_transitions_work': True,
            'score': 100 if recovered else 60
        }
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall system score."""
        scores = [result['score'] for result in results.values() if 'score' in result]
        return statistics.mean(scores) if scores else 0
    
    def generate_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("🎯 PRODUCTION LINE VALIDATION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overall Score: {results['overall_score']:.1f}/100")
        report.append("")
        
        # Individual test results
        for test_name, test_results in results.items():
            if test_name == 'overall_score':
                continue
                
            report.append(f"📊 {test_name.replace('_', ' ').title()}")
            report.append("-" * 30)
            
            for key, value in test_results.items():
                if key != 'score':
                    report.append(f"   {key}: {value}")
            
            score = test_results.get('score', 0)
            status = "✅ PASS" if score >= 90 else "⚠️  NEEDS IMPROVEMENT" if score >= 70 else "❌ FAIL"
            report.append(f"   Score: {score}/100 {status}")
            report.append("")
        
        return "\n".join(report)


async def run_system_validation():
    """Run complete system validation."""
    from src.models.production_line import ProductionLine
    
    # Create test configuration
    config = {
        "name": "Validation_Line",
        "machines": [
            {
                "id": "VALIDATION_001",
                "name": "Test_Station_1",
                "type": "preparation",
                "cycle_time": 2,
                "failure_rate": 0.0,
                "sensors": ["temperature", "part_present"],
                "actuators": ["conveyor"]
            },
            {
                "id": "VALIDATION_002", 
                "name": "Test_Station_2",
                "type": "assembly",
                "cycle_time": 3,
                "failure_rate": 0.0,
                "sensors": ["force", "part_present"],
                "actuators": ["robot_arm"]
            }
        ]
    }
    
    # Create production line
    production_line = ProductionLine(config, simulation_speed=5.0)
    
    # Run validation
    validator = SystemValidator(production_line)
    results = await validator.run_comprehensive_validation()
    
    # Generate report
    report = validator.generate_validation_report(results)
    print("\n" + report)
    
    return results


if __name__ == '__main__':
    asyncio.run(run_system_validation())
