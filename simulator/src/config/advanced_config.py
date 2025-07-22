# Advanced Production Line Configuration
# This file extends the basic configuration with more realistic industrial parameters

ADVANCED_PRODUCTION_LINES = {
    "High_Volume_Assembly": {
        "name": "High_Volume_Assembly",
        "target_throughput": 120,  # parts per hour
        "machines": [
            {
                "id": "MACHINE_001",
                "name": "Material_Preparation",
                "type": "preparation", 
                "cycle_time": 18,
                "failure_rate": 0.02,
                "sensors": ["temperature", "pressure", "vibration", "part_present", "material_level"],
                "actuators": ["conveyor", "pneumatic_clamp", "heating_element", "material_feeder"],
                "buffer_capacity": 3,
                "power_consumption": {"idle": 75, "running": 450, "error": 25}
            },
            {
                "id": "MACHINE_002", 
                "name": "Precision_Assembly",
                "type": "assembly",
                "cycle_time": 25,
                "failure_rate": 0.015,
                "sensors": ["force", "torque", "position", "part_present", "tool_wear"],
                "actuators": ["robot_arm", "screwdriver", "conveyor", "pick_and_place", "vision_system"],
                "buffer_capacity": 2,
                "power_consumption": {"idle": 125, "running": 850, "error": 50}
            },
            {
                "id": "MACHINE_003",
                "name": "Multi_Point_Inspection", 
                "type": "inspection",
                "cycle_time": 15,
                "failure_rate": 0.01,
                "sensors": ["pressure", "current", "flow_rate", "part_present", "laser_measurement", "weight"],
                "actuators": ["test_fixture", "reject_pusher", "conveyor", "sorting_gate", "leak_tester"],
                "buffer_capacity": 4,
                "power_consumption": {"idle": 100, "running": 350, "error": 30}
            }
        ],
        "quality_targets": {
            "overall_yield": 0.955,
            "first_pass_yield": 0.98,
            "rework_rate": 0.02
        },
        "maintenance_schedule": {
            "preventive_hours": 168,  # Weekly
            "predictive_monitoring": True,
            "oee_target": 0.85
        }
    },
    
    "Flexible_Manufacturing_Cell": {
        "name": "Flexible_Manufacturing_Cell",
        "target_throughput": 80,  # parts per hour
        "machines": [
            {
                "id": "CELL_001",
                "name": "Multi_Purpose_Workstation",
                "type": "flexible",
                "cycle_time": 35,
                "failure_rate": 0.025,
                "sensors": ["temperature", "pressure", "force", "position", "part_present", "tool_id"],
                "actuators": ["6_axis_robot", "tool_changer", "conveyor", "rotary_table", "clamping_system"],
                "buffer_capacity": 6,
                "power_consumption": {"idle": 200, "running": 1200, "error": 75}
            },
            {
                "id": "CELL_002",
                "name": "Automated_Quality_Station", 
                "type": "inspection",
                "cycle_time": 22,
                "failure_rate": 0.008,
                "sensors": ["3d_scanner", "pressure", "electrical_test", "part_present", "barcode_reader"],
                "actuators": ["test_fixture", "probe_system", "conveyor", "reject_bin", "pass_bin"],
                "buffer_capacity": 3,
                "power_consumption": {"idle": 150, "running": 500, "error": 40}
            }
        ],
        "quality_targets": {
            "overall_yield": 0.97,
            "first_pass_yield": 0.985,
            "rework_rate": 0.01
        },
        "maintenance_schedule": {
            "preventive_hours": 336,  # Bi-weekly
            "predictive_monitoring": True, 
            "oee_target": 0.88
        }
    }
}

# Sensor Ranges and Behaviors (Industrial Grade)
SENSOR_SPECIFICATIONS = {
    "temperature": {
        "range": {"min": -40, "max": 150},
        "accuracy": 0.1,
        "resolution": 0.01,
        "response_time": 0.5,
        "drift_rate": 0.02  # per hour
    },
    "pressure": {
        "range": {"min": 0, "max": 10},
        "accuracy": 0.05,
        "resolution": 0.001,
        "response_time": 0.1,
        "drift_rate": 0.01
    },
    "force": {
        "range": {"min": 0, "max": 5000},
        "accuracy": 0.5,
        "resolution": 0.1,
        "response_time": 0.05,
        "drift_rate": 0.1
    },
    "position": {
        "range": {"min": 0, "max": 1000},
        "accuracy": 0.01,
        "resolution": 0.001,
        "response_time": 0.02,
        "drift_rate": 0.005
    },
    "vibration": {
        "range": {"min": 0, "max": 50},
        "accuracy": 0.1,
        "resolution": 0.01,
        "response_time": 0.1,
        "drift_rate": 0.05
    }
}

# Advanced Part Types with Specifications
PART_SPECIFICATIONS = {
    "Automotive_Component_A": {
        "material": "Aluminum_6061",
        "weight_target": 1.45,
        "weight_tolerance": 0.05,
        "dimensions": {"length": 125.0, "width": 85.0, "height": 32.0},
        "tolerance": 0.1,
        "surface_finish": "Ra_1.6",
        "processing_temps": {"prep": 85, "assembly": 23, "test": 23},
        "cycle_times": {"prep": 22, "assembly": 28, "inspect": 18}
    },
    "Electronics_Housing_B": {
        "material": "ABS_Plastic",
        "weight_target": 0.85,
        "weight_tolerance": 0.02,
        "dimensions": {"length": 95.0, "width": 65.0, "height": 18.0},
        "tolerance": 0.05,
        "surface_finish": "Smooth",
        "processing_temps": {"prep": 45, "assembly": 21, "test": 21},
        "cycle_times": {"prep": 15, "assembly": 32, "inspect": 12}
    }
}

# Failure Mode Analysis 
FAILURE_MODES = {
    "sensor_drift": {"probability": 0.008, "recovery_time": 300, "impact": "quality"},
    "actuator_jam": {"probability": 0.005, "recovery_time": 600, "impact": "availability"},
    "power_fluctuation": {"probability": 0.003, "recovery_time": 120, "impact": "performance"},
    "tool_wear": {"probability": 0.015, "recovery_time": 1800, "impact": "quality"},
    "communication_loss": {"probability": 0.002, "recovery_time": 180, "impact": "availability"},
    "air_pressure_drop": {"probability": 0.01, "recovery_time": 240, "impact": "performance"}
}

# Advanced MQTT Topics for Industry 4.0 Integration
MQTT_TOPIC_EXTENSIONS = {
    "energy_monitoring": "production/{line_name}/energy/{machine_id}",
    "predictive_maintenance": "production/{line_name}/maintenance/{machine_id}/predictions", 
    "quality_analytics": "production/{line_name}/quality/analytics",
    "oee_realtime": "production/{line_name}/oee/{timeframe}",
    "alarm_analytics": "production/{line_name}/alarms/trends",
    "environmental": "production/{line_name}/environment/{zone_id}",
    "traceability": "production/{line_name}/traceability/{part_id}",
    "process_optimization": "production/{line_name}/optimization/recommendations"
}
