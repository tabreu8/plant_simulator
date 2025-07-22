"""Simple Docker integration test that validates MQTT data format without external dependencies."""

import subprocess
import time
import sys
import os


def test_docker_mqtt_integration():
    """Test the complete system using Docker containers and MQTT data validation."""
    print("🐳 Docker MQTT Integration Test")
    print("=" * 50)
    
    try:
        # Check if Docker is available
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not available or not running")
        return False
    
    try:
        # Get the docker directory path
        docker_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docker')
        
        # Check if containers are running
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, check=True, cwd=docker_dir)
        
        if 'plant_simulator' not in result.stdout or 'mqtt_broker' not in result.stdout:
            print("⚠️  Docker containers not running. Starting them...")
            subprocess.run(['docker-compose', 'up', '-d'], check=True, cwd=docker_dir)
            print("⏳ Waiting 15 seconds for containers to initialize...")
            time.sleep(15)
        else:
            print("✅ Docker containers are running")
        
        # Test MQTT broker connectivity
        print("\n📡 Testing MQTT broker connectivity...")
        result = subprocess.run([
            'docker', 'exec', 'mqtt_broker', 
            'mosquitto_pub', '-h', 'localhost', '-t', 'test', '-m', 'ping'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ MQTT broker is not responding")
            return False
        else:
            print("✅ MQTT broker is responding")
        
        # Collect MQTT data for analysis
        print("\n📊 Collecting MQTT data for 20 seconds...")
        messages = []
        
        try:
            proc = subprocess.Popen([
                'docker', 'exec', 'mqtt_broker', 
                'mosquitto_sub', '-h', 'localhost', '-t', 'production/#', '-v'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            start_time = time.time()
            while time.time() - start_time < 20:
                line = proc.stdout.readline()
                if line.strip():
                    messages.append(line.strip())
            
            proc.terminate()
            proc.wait()
            
        except Exception as e:
            print(f"❌ Error collecting MQTT data: {e}")
            return False
        
        if not messages:
            print("❌ No MQTT messages received - system may not be working")
            return False
        
        print(f"✅ Collected {len(messages)} MQTT messages")
        
        # Analyze message format
        return analyze_mqtt_data_format(messages)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker command failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False


def analyze_mqtt_data_format(messages):
    """Analyze MQTT messages to validate PLC-style format."""
    print("\n🔍 Analyzing MQTT data format...")
    
    # Categorize messages
    sensor_messages = []
    actuator_messages = []
    boolean_messages = []
    production_data_messages = []
    
    for msg in messages:
        if ' ' in msg:
            topic, payload = msg.split(' ', 1)
            
            # Check if it's production data (JSON is expected for this)
            if 'production_data' in topic:
                production_data_messages.append((topic, payload))
            else:
                # Regular sensor/actuator data
                topic_parts = topic.split('/')
                if len(topic_parts) == 4 and topic_parts[0] == 'production':
                    if any(sensor in topic for sensor in ['temperature', 'pressure', 'force', 'weight', 'camera', 'laser_measurement', 'vibration', 'position']):
                        sensor_messages.append((topic, payload))
                    elif any(actuator in topic for actuator in ['conveyor', 'robot_arm', 'heating_element', 'pneumatic_clamp', 'screwdriver', 'pick_and_place', 'reject_pusher', 'sorting_gate']):
                        actuator_messages.append((topic, payload))
                    
                    if 'part_present' in topic or any(actuator in topic for actuator in ['conveyor', 'robot_arm', 'heating_element']):
                        boolean_messages.append((topic, payload))
    
    # Test results
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Check we have sensor messages
    if sensor_messages:
        print("✅ Test 1: Sensor messages found")
        tests_passed += 1
    else:
        print("❌ Test 1: No sensor messages found")
    
    # Test 2: Check we have actuator messages  
    if actuator_messages:
        print("✅ Test 2: Actuator messages found")
        tests_passed += 1
    else:
        print("❌ Test 2: No actuator messages found")
    
    # Test 3: Check topic structure (no /sensors/ or /actuators/)
    old_format_count = sum(1 for msg in messages if '/sensors/' in msg or '/actuators/' in msg)
    if old_format_count == 0:
        print("✅ Test 3: Topic structure follows PLC format (no /sensors/ or /actuators/)")
        tests_passed += 1
    else:
        print(f"❌ Test 3: Found {old_format_count} messages with old format (/sensors/ or /actuators/)")
    
    # Test 4: Check boolean conversion (should be 0/1, not true/false)
    wrong_booleans = []
    for topic, payload in boolean_messages:
        if payload.lower() in ['true', 'false']:
            wrong_booleans.append((topic, payload))
    
    if not wrong_booleans:
        print("✅ Test 4: Boolean values correctly converted to 0/1")
        tests_passed += 1
    else:
        print(f"❌ Test 4: Found {len(wrong_booleans)} boolean values as true/false instead of 0/1")
    
    # Test 5: Check sensor values are numeric (not JSON)
    json_sensor_count = 0
    for topic, payload in sensor_messages:
        if payload.startswith('{') and payload.endswith('}'):
            json_sensor_count += 1
    
    if json_sensor_count == 0:
        print("✅ Test 5: Sensor values are raw numeric (not JSON)")
        tests_passed += 1
    else:
        print(f"❌ Test 5: Found {json_sensor_count} sensor values in JSON format")
    
    # Test 6: Check data continuity (should have recent messages)
    if len(messages) >= 30:  # Should have plenty of messages in 20 seconds
        print("✅ Test 6: Data continuity test passed (sufficient message volume)")
        tests_passed += 1
    else:
        print(f"❌ Test 6: Data continuity test failed (only {len(messages)} messages in 20 seconds)")
    
    # Show sample data
    print(f"\n📋 Sample PLC-style messages:")
    plc_samples = [msg for msg in messages if ' ' in msg and not msg.strip().endswith('}')][:8]
    for i, msg in enumerate(plc_samples, 1):
        print(f"   {i}. {msg}")
    
    # Results summary
    print(f"\n🎯 Format Tests: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All PLC format tests passed!")
        return True
    else:
        print("❌ Some PLC format tests failed")
        return False


if __name__ == "__main__":
    success = test_docker_mqtt_integration()
    if success:
        print("\n🎉 Docker integration test passed!")
        sys.exit(0)
    else:
        print("\n❌ Docker integration test failed!")
        sys.exit(1)
