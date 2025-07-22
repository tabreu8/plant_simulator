# Production Line Simulator - Complete Guide

## Overview
This is a complete 3-machine production line simulator that models realistic industrial manufacturing with sensor data, actuator control, and MQTT communication. The system simulates Material Preparation → Assembly → Quality Inspection workflow with real-time data publishing.

## Manufacturing Process

### Production Flow
```
Raw Material → Station 1 (Material Prep) → Station 2 (Assembly) → Station 3 (Quality Check) → Finished/Rejected Parts
```

#### Station 1: Material Preparation (MACHINE_001)
- **Function**: Raw material heating, cutting, surface preparation
- **Cycle Time**: 25 seconds
- **Sensors**: Temperature, Pressure, Vibration, Part Present
- **Actuators**: Conveyor, Pneumatic Clamp, Heating Element
- **Quality Gate**: Temperature validation (80-85°C), pressure verification (1.8-2.0 bar)

#### Station 2: Assembly (MACHINE_002)  
- **Function**: Component assembly, fastening, robotic operations
- **Cycle Time**: 35 seconds
- **Sensors**: Force, Position, Torque, Part Present
- **Actuators**: Robot Arm, Screwdriver, Conveyor, Pick & Place
- **Quality Gate**: Force limits (80-150N), torque validation (15-50Nm)

#### Station 3: Quality Inspection (MACHINE_003)
- **Function**: Final quality control, dimensional verification, OK/NOK decision
- **Cycle Time**: 20 seconds  
- **Sensors**: Camera, Laser Measurement, Weight, Part Present
- **Actuators**: Conveyor, Reject Pusher, Sorting Gate
- **Quality Gate**: Weight (1.2-1.8kg), dimensions (49-51mm), visual inspection

### Part Flow Management
- **Part ID Format**: `{OrderID}_{PartNumber:04d}` (e.g., `OF_20250721001_0001`)
- **Buffer Management**: 2-part capacity between stations
- **Flow Control**: FIFO processing with realistic blocking/starving
- **Quality Rate**: ~95% overall yield (realistic rejection rates)

## Machine States & Operation Phases

### Machine States
- **idle**: Ready to process, waiting for parts
- **running**: Actively processing parts through operation phases  
- **malfunction**: Temporary fault state (30-180 seconds recovery)
- **maintenance**: Scheduled or corrective maintenance mode
- **error**: Critical fault requiring operator intervention

### Operation Phases (when running)
1. **preparation**: Part loading, setup (20% of cycle)
2. **positioning**: Moving to working position (15% of cycle)
3. **processing**: Main operation execution (50% of cycle)
4. **quality_check**: In-process verification (10% of cycle)  
5. **completion**: Part unloading, cleanup (5% of cycle)

## MQTT Data Publishing

### Topic Structure
All data is published as **raw values** (not JSON) for PLC compatibility:
```
production/{line_name}/machines/{machine_id}/{data_type}
```

### Machine Status Data (All Machines Publish)
```bash
# Core Machine Information
production/Assembly_Line_A/machines/MACHINE_001/production_machine_state          # "idle", "running", "malfunction", "maintenance"
production/Assembly_Line_A/machines/MACHINE_001/production_operation_phase        # "idle", "preparation", "processing", etc.
production/Assembly_Line_A/machines/MACHINE_001/production_machine_type           # "preparation", "assembly", "inspection"
production/Assembly_Line_A/machines/MACHINE_001/production_machine_name           # "Material_Prep", "Assembly_Station", "Quality_Check"

# Current Part Processing (null when idle, part ID when processing)
production/Assembly_Line_A/machines/MACHINE_001/production_current_part_id        # "OF_20250721001_0001" or "(null)"
production/Assembly_Line_A/machines/MACHINE_001/production_current_part_type      # "Widget_A" or "(null)"
production/Assembly_Line_A/machines/MACHINE_001/production_current_part_quality   # "pass", "fail" or "(null)"

# Production Metrics
production/Assembly_Line_A/machines/MACHINE_001/production_parts_processed_today  # "12"
production/Assembly_Line_A/machines/MACHINE_001/production_cycle_time_target      # "25" (seconds)
production/Assembly_Line_A/machines/MACHINE_001/production_phase_duration_remaining # "12.3" (seconds)

# Buffer Status
production/Assembly_Line_A/machines/MACHINE_001/production_input_buffer_count     # "0", "1", "2"
production/Assembly_Line_A/machines/MACHINE_001/production_output_buffer_count    # "0", "1", "2"

# Maintenance Information
production/Assembly_Line_A/machines/MACHINE_001/production_total_runtime_hours    # "18.5"
production/Assembly_Line_A/machines/MACHINE_001/production_next_maintenance_due   # "2025-07-28 14:00"
```

### Sensor Data (Real-time, 1-2 Hz)
```bash
# Material Prep (MACHINE_001)
production/Assembly_Line_A/machines/MACHINE_001/sensor_temperature         # "85.2" (°C)
production/Assembly_Line_A/machines/MACHINE_001/sensor_pressure            # "1.8" (bar)
production/Assembly_Line_A/machines/MACHINE_001/sensor_vibration           # "0.3" (mm/s)
production/Assembly_Line_A/machines/MACHINE_001/sensor_part_present        # "1" or "0"

# Assembly Station (MACHINE_002)  
production/Assembly_Line_A/machines/MACHINE_002/sensor_force               # "120.5" (N)
production/Assembly_Line_A/machines/MACHINE_002/sensor_position            # "75.0" (mm)
production/Assembly_Line_A/machines/MACHINE_002/sensor_torque              # "15.2" (Nm)
production/Assembly_Line_A/machines/MACHINE_002/sensor_part_present        # "1" or "0"

# Quality Check (MACHINE_003)
production/Assembly_Line_A/machines/MACHINE_003/sensor_camera              # "1920" (pixels)
production/Assembly_Line_A/machines/MACHINE_003/sensor_laser_measurement   # "49.8" (mm)
production/Assembly_Line_A/machines/MACHINE_003/sensor_weight              # "1.45" (kg)
production/Assembly_Line_A/machines/MACHINE_003/sensor_part_present        # "1" or "0"
```

### Actuator Data (Event-driven on state changes)
```bash
# Material Prep (MACHINE_001)
production/Assembly_Line_A/machines/MACHINE_001/actuator_conveyor          # "stopped", "running", "running_slow"
production/Assembly_Line_A/machines/MACHINE_001/actuator_pneumatic_clamp   # "open", "closed", "closing"
production/Assembly_Line_A/machines/MACHINE_001/actuator_heating_element   # "off", "heating", "maintaining"

# Assembly Station (MACHINE_002)
production/Assembly_Line_A/machines/MACHINE_002/actuator_robot_arm         # "home", "moving_to_pickup", "assembling"
production/Assembly_Line_A/machines/MACHINE_002/actuator_screwdriver       # "idle", "engaging", "driving"
production/Assembly_Line_A/machines/MACHINE_002/actuator_pick_and_place    # "active", "moving", "gripping"

# Quality Check (MACHINE_003)
production/Assembly_Line_A/machines/MACHINE_003/actuator_reject_pusher     # "retracted", "extending", "extended"
production/Assembly_Line_A/machines/MACHINE_003/actuator_sorting_gate      # "pass", "reject", "idle"
```

### Production Line Data
```bash
# Overall line status and metrics published as JSON to:
production/Assembly_Line_A/production_data

# Contains: line status, shift info, current orders, active parts, quality metrics, alarms
```

## Key Performance Indicators

### Production Metrics
- **Throughput**: Parts per hour (calculated from completed parts)
- **Quality Rate**: Percentage of parts passing all quality checks  
- **Cycle Time**: Average time per part through entire line
- **OEE**: Overall Equipment Effectiveness (Availability × Performance × Quality)

### Machine Metrics  
- **State Distribution**: Time spent in each machine state
- **Parts Processed**: Daily/shift/total part counts
- **Malfunction Frequency**: Mean Time Between Failures (MTBF)
- **Buffer Efficiency**: Average buffer utilization between stations

## Quality Control System

### Inspection Process
- **OK/NOK Decision**: Clear pass/fail status for each part
- **Pass Rate**: 95% under normal conditions (industry realistic)
- **Quality Factors**: Processing time, sensor readings, machine condition
- **Rejection Handling**: Failed parts tracked and removed from flow

### Inspection Data
- **inspection_result**: "ok" or "nok"
- **dimensional_measurement**: Laser measurement (47-52mm range)
- **weight_measurement**: Mass verification (1.2-1.8kg tolerance)
- **visual_defects**: Camera inspection results

## Quick Start

### 1. Using Docker (Recommended)
```bash
cd docker/
docker-compose up --build
```
This starts:
- MQTT Broker (mosquitto) on port 1883
- Production Line Simulator publishing real-time data

### 2. Local Development
```bash
pip install -r requirements.txt
python main.py
```

### 3. View MQTT Data
```bash
# Subscribe to all machine status
mosquitto_sub -h localhost -t "production/Assembly_Line_A/machines/+/+" -v

# Monitor current parts being processed
mosquitto_sub -h localhost -t "production/Assembly_Line_A/machines/+/production_current_part_id" -v

# Watch sensor data
mosquitto_sub -h localhost -t "production/Assembly_Line_A/machines/+/sensor_+" -v
```

## Troubleshooting

### Common Issues
1. **No MQTT Data**: Check broker connection and container status
2. **Inconsistent Production**: Verify buffer status and machine states  
3. **Missing Current Part Info**: Normal when machines are idle (shows "(null)")
4. **Performance Issues**: Adjust simulation speed in configuration

### Validation
- **Test Suite**: Run `python3 scripts/test_runner.py` (62 comprehensive tests)
- **Docker Integration**: Automated MQTT format validation
- **Performance**: 87,000+ sensor readings/second capability

## Configuration

### Environment Variables
- `MQTT_BROKER_HOST`: MQTT broker hostname (default: localhost)
- `MQTT_BROKER_PORT`: MQTT broker port (default: 1883)
- `SIMULATION_SPEED`: Speed multiplier for testing (default: 1.0)
- `PRODUCTION_LINE_NAME`: Line identifier (default: Assembly_Line_A)

### Machine Configuration
Each machine type has configurable:
- Cycle times and phase durations
- Sensor ranges and failure rates
- Quality thresholds and rejection criteria
- Maintenance schedules and malfunction frequency

This simulator provides **industrial-grade data streams** suitable for developing HMI systems, SCADA integrations, and production monitoring applications in a realistic manufacturing environment.
