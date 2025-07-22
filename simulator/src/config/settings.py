"""Configuration settings for the production line simulator."""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class MQTTSettings(BaseSettings):
    """MQTT broker configuration."""
    host: str = Field(default="localhost", env="MQTT_BROKER_HOST")
    port: int = Field(default=1883, env="MQTT_BROKER_PORT")
    username: Optional[str] = Field(default=None, env="MQTT_USERNAME")
    password: Optional[str] = Field(default=None, env="MQTT_PASSWORD")
    keepalive: int = Field(default=60)
    qos: int = Field(default=1)
    retain: bool = Field(default=False)


class ProductionLineSettings(BaseSettings):
    """Production line configuration."""
    name: str = Field(default="Assembly_Line_A", env="PRODUCTION_LINE_NAME")
    shift_duration_hours: int = Field(default=8, env="SHIFT_DURATION_HOURS")
    cycle_time_seconds: int = Field(default=30, env="CYCLE_TIME_SECONDS")
    
    # Machine configuration
    machines: List[Dict[str, Any]] = Field(default_factory=lambda: [
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


class Settings(PydanticBaseSettings):
    """Main application settings."""
    
    # General settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    simulation_speed: float = Field(default=1.0, env="SIMULATION_SPEED")
    
    # Component settings
    mqtt: MQTTSettings = Field(default_factory=MQTTSettings)
    production_line: ProductionLineSettings = Field(default_factory=ProductionLineSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
