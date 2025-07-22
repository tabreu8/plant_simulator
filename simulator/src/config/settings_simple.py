"""Configuration settings for the production line simulator."""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MQTTSettings:
    """MQTT broker configuration."""
    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    qos: int = 1
    retain: bool = False
    
    def __post_init__(self):
        # Load from environment variables
        self.host = os.getenv("MQTT_BROKER_HOST", self.host)
        self.port = int(os.getenv("MQTT_BROKER_PORT", self.port))
        self.username = os.getenv("MQTT_USERNAME", self.username)
        self.password = os.getenv("MQTT_PASSWORD", self.password)


@dataclass
class ProductionLineSettings:
    """Production line configuration."""
    name: str = "Assembly_Line_A"
    shift_duration_hours: int = 8
    cycle_time_seconds: int = 30
    
    # Machine configuration
    machines: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "id": "MACHINE_001",
            "name": "Material_Prep",
            "type": "preparation",
            "cycle_time": 25,
            "failure_rate": 0.02,
            "sensors": ["temperature", "pressure", "vibration", "part_present"],
            "actuators": ["conveyor", "pneumatic_clamp", "heating_element"]
        },
        {
            "id": "MACHINE_002", 
            "name": "Assembly_Station",
            "type": "assembly",
            "cycle_time": 35,
            "failure_rate": 0.015,
            "sensors": ["force", "position", "part_present", "torque"],
            "actuators": ["robot_arm", "screwdriver", "conveyor", "pick_and_place"]
        },
        {
            "id": "MACHINE_003",
            "name": "Quality_Check",
            "type": "inspection",
            "cycle_time": 20,
            "failure_rate": 0.01,
            "sensors": ["camera", "laser_measurement", "part_present", "weight"],
            "actuators": ["conveyor", "reject_pusher", "sorting_gate"]
        }
    ])
    
    def __post_init__(self):
        # Load from environment variables
        self.name = os.getenv("PRODUCTION_LINE_NAME", self.name)
        self.shift_duration_hours = int(os.getenv("SHIFT_DURATION_HOURS", self.shift_duration_hours))
        self.cycle_time_seconds = int(os.getenv("CYCLE_TIME_SECONDS", self.cycle_time_seconds))


@dataclass
class Settings:
    """Main application settings."""
    
    # General settings
    log_level: str = "INFO"
    simulation_speed: float = 1.0
    
    # Component settings
    mqtt: MQTTSettings = field(default_factory=MQTTSettings)
    production_line: ProductionLineSettings = field(default_factory=ProductionLineSettings)
    
    def __post_init__(self):
        # Load from environment variables
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.simulation_speed = float(os.getenv("SIMULATION_SPEED", self.simulation_speed))
        
        # Initialize sub-settings
        self.mqtt = MQTTSettings()
        self.production_line = ProductionLineSettings()
