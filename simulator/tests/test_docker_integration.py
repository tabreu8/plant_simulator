"""Integration tests using Docker containers to test the complete system."""

import asyncio
import docker
import json
import pytest
import subprocess
import time
import threading
from datetime import datetime
from typing import List, Dict, Any

import paho.mqtt.client as mqtt


class DockerMQTTIntegrationTest:
    """Integration test that launches MQTT broker with Docker and validates the system."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.mqtt_container = None
        self.plant_container = None
        self.mqtt_messages: List[Dict[str, Any]] = []
        self.mqtt_client = None
        self.mqtt_connected = False
        
    def setup_containers(self):
        """Set up Docker containers for testing."""
        print("Setting up Docker containers...")
        
        # Stop and remove existing containers if they exist
        self.cleanup_containers()
        
        # Create network
        try:
            network = self.docker_client.networks.create("test-plant-network", driver="bridge")
        except docker.errors.APIError:
            # Network might already exist
            network = self.docker_client.networks.get("test-plant-network")
        
        # Start MQTT broker
        print("Starting MQTT broker...")
        self.mqtt_container = self.docker_client.containers.run(
            "eclipse-mosquitto:2.0",
            name="test-mqtt-broker",
            ports={'1883/tcp': 1883},
            network="test-plant-network",
            detach=True,
            remove=True,
            command=["mosquitto", "-c", "/mosquitto-no-auth.conf"]
        )
        
        # Wait for MQTT broker to be ready
        self._wait_for_mqtt_broker()
        
        # Build plant simulator image
        print("Building plant simulator image...")
        subprocess.run([
            "docker", "build", "-t", "test-plant-simulator", "."
        ], cwd="/Users/tiago/Documents/Coding&Stuff/Manufacturing/plant_simulator", check=True)
        
        # Start plant simulator
        print("Starting plant simulator...")
        self.plant_container = self.docker_client.containers.run(
            "test-plant-simulator",
            name="test-plant-simulator",
            network="test-plant-network",
            environment={
                "MQTT_BROKER_HOST": "test-mqtt-broker",
                "MQTT_BROKER_PORT": "1883",
                "SIMULATION_SPEED": "2.0",  # Faster for testing
                "LOG_LEVEL": "DEBUG"
            },
            detach=True,
            remove=True
        )
        
        # Wait for plant simulator to connect
        time.sleep(5)
        
        print("Containers started successfully!")
    
    def _wait_for_mqtt_broker(self, timeout=30):
        """Wait for MQTT broker to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to connect to check if broker is ready
                test_client = mqtt.Client()
                test_client.connect("localhost", 1883, 5)
                test_client.disconnect()
                return
            except Exception:
                time.sleep(1)
        
        raise Exception("MQTT broker failed to start within timeout")
    
    def setup_mqtt_subscriber(self):
        """Set up MQTT client to collect messages."""
        print("Setting up MQTT subscriber...")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.mqtt_connected = True
                print("MQTT subscriber connected")
                # Subscribe to all production topics
                client.subscribe("production/#")
            else:
                print(f"MQTT subscriber connection failed: {rc}")
        
        def on_message(client, userdata, msg):
            message_data = {
                "topic": msg.topic,
                "payload": msg.payload.decode(),
                "timestamp": datetime.now().isoformat()
            }
            self.mqtt_messages.append(message_data)
            print(f"Received: {msg.topic} -> {msg.payload.decode()}")
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
        # Connect to MQTT broker
        self.mqtt_client.connect("localhost", 1883, 60)
        
        # Start the MQTT loop in a separate thread
        mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not self.mqtt_connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not self.mqtt_connected:
            raise Exception("Failed to connect MQTT subscriber")
    
    def cleanup_containers(self):
        """Clean up Docker containers."""
        print("Cleaning up containers...")
        
        # Stop containers
        for container_name in ["test-plant-simulator", "test-mqtt-broker"]:
            try:
                container = self.docker_client.containers.get(container_name)
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass
        
        # Remove network
        try:
            network = self.docker_client.networks.get("test-plant-network")
            network.remove()
        except docker.errors.NotFound:
            pass
        
        if self.mqtt_client:
            self.mqtt_client.disconnect()
    
    def test_plc_data_format(self):
        """Test that MQTT data follows PLC format specifications."""
        print("Testing PLC data format...")
        
        # Wait for some messages to arrive
        time.sleep(10)
        
        # Verify we received messages
        assert len(self.mqtt_messages) > 0, "No MQTT messages received"
        
        # Check sensor data format
        sensor_messages = [msg for msg in self.mqtt_messages 
                          if any(sensor in msg["topic"] for sensor in 
                               ["temperature", "pressure", "force", "part_present"])]
        
        assert len(sensor_messages) > 0, "No sensor messages received"
        
        # Test topic structure (should be production/line/machine/sensor)
        for msg in sensor_messages:
            topic_parts = msg["topic"].split("/")
            assert len(topic_parts) == 4, f"Invalid topic structure: {msg['topic']}"
            assert topic_parts[0] == "production", f"Topic should start with 'production': {msg['topic']}"
            assert "sensors" not in msg["topic"], f"Topic should not contain 'sensors': {msg['topic']}"
            assert "actuators" not in msg["topic"], f"Topic should not contain 'actuators': {msg['topic']}"
        
        # Test boolean conversion (part_present should be 0 or 1)
        part_present_messages = [msg for msg in self.mqtt_messages 
                                if "part_present" in msg["topic"]]
        
        assert len(part_present_messages) > 0, "No part_present messages received"
        
        for msg in part_present_messages:
            payload = msg["payload"]
            assert payload in ["0", "1"], f"Boolean should be 0 or 1, got: {payload}"
            assert payload != "true" and payload != "false", f"Boolean should not be true/false: {payload}"
        
        # Test numeric data format
        temperature_messages = [msg for msg in self.mqtt_messages 
                               if "temperature" in msg["topic"]]
        
        for msg in temperature_messages:
            payload = msg["payload"]
            try:
                float(payload)  # Should be convertible to float
            except ValueError:
                assert False, f"Temperature should be numeric: {payload}"
            
            # Should not be JSON
            assert not payload.startswith("{"), f"Payload should not be JSON: {payload}"
        
        print("✅ PLC data format test passed!")
    
    def test_actuator_status_format(self):
        """Test actuator status format (should be 0/1 not text)."""
        print("Testing actuator status format...")
        
        # Wait for actuator messages
        time.sleep(5)
        
        actuator_messages = [msg for msg in self.mqtt_messages 
                            if any(actuator in msg["topic"] for actuator in 
                                 ["conveyor", "robot_arm", "heating_element"])]
        
        assert len(actuator_messages) > 0, "No actuator messages received"
        
        for msg in actuator_messages:
            payload = msg["payload"]
            assert payload in ["0", "1"], f"Actuator status should be 0 or 1, got: {payload}"
            assert payload not in ["active", "ready", "error", "maintenance"], \
                f"Actuator status should not be text: {payload}"
        
        print("✅ Actuator status format test passed!")
    
    def test_data_continuity(self):
        """Test that data is published continuously."""
        print("Testing data continuity...")
        
        initial_count = len(self.mqtt_messages)
        time.sleep(8)  # Wait for more messages
        final_count = len(self.mqtt_messages)
        
        new_messages = final_count - initial_count
        assert new_messages > 10, f"Expected continuous data flow, got {new_messages} new messages"
        
        print(f"✅ Data continuity test passed! Received {new_messages} new messages")
    
    def test_machine_coverage(self):
        """Test that all machines are publishing data."""
        print("Testing machine coverage...")
        
        # Wait for sufficient data
        time.sleep(8)
        
        # Check for multiple machines
        machine_topics = set()
        for msg in self.mqtt_messages:
            topic_parts = msg["topic"].split("/")
            if len(topic_parts) >= 3 and topic_parts[0] == "production":
                machine_topics.add(topic_parts[2])  # machine ID
        
        assert len(machine_topics) >= 3, f"Expected at least 3 machines, found: {machine_topics}"
        print(f"✅ Machine coverage test passed! Found machines: {machine_topics}")
    
    def test_sensor_variety(self):
        """Test that various sensor types are being published."""
        print("Testing sensor variety...")
        
        expected_sensors = {"temperature", "pressure", "part_present", "force", "weight"}
        found_sensors = set()
        
        for msg in self.mqtt_messages:
            topic_parts = msg["topic"].split("/")
            if len(topic_parts) == 4:  # production/line/machine/sensor
                sensor_type = topic_parts[3]
                found_sensors.add(sensor_type)
        
        missing_sensors = expected_sensors - found_sensors
        assert len(missing_sensors) == 0, f"Missing sensor types: {missing_sensors}"
        
        print(f"✅ Sensor variety test passed! Found sensors: {found_sensors}")
    
    def run_all_tests(self):
        """Run all integration tests."""
        try:
            print("🚀 Starting Docker MQTT Integration Tests...")
            
            # Setup
            self.setup_containers()
            self.setup_mqtt_subscriber()
            
            # Run tests
            self.test_plc_data_format()
            self.test_actuator_status_format()
            self.test_data_continuity()
            self.test_machine_coverage()
            self.test_sensor_variety()
            
            print("🎉 All integration tests passed!")
            
            # Show some sample data
            print("\n📊 Sample MQTT messages received:")
            for i, msg in enumerate(self.mqtt_messages[:10]):
                print(f"  {i+1}. {msg['topic']} -> {msg['payload']}")
            
            print(f"\nTotal messages received: {len(self.mqtt_messages)}")
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            # Show container logs for debugging
            if self.plant_container:
                print("\n🔍 Plant simulator logs:")
                print(self.plant_container.logs().decode())
            raise
        finally:
            self.cleanup_containers()


def test_docker_mqtt_integration():
    """Main test function for pytest."""
    test_runner = DockerMQTTIntegrationTest()
    test_runner.run_all_tests()


if __name__ == "__main__":
    # Run the integration test directly
    test_runner = DockerMQTTIntegrationTest()
    test_runner.run_all_tests()
