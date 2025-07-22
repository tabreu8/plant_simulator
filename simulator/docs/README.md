# Production Line Simulator Documentation

This directory contains the complete documentation for the Production Line Simulator project.

## Complete Guide

**[Production Simulator Guide](PRODUCTION_SIMULATOR_GUIDE.md)** - Complete technical documentation covering:

- **Manufacturing Process**: 3-station production line (Material Prep → Assembly → Quality Inspection)
- **Machine States & Operation**: Detailed state management and operation phases  
- **MQTT Data Publishing**: Complete topic structure and data formats
- **Quality Control System**: Inspection process and quality metrics
- **Quick Start**: Docker and local development setup
- **Configuration**: Environment variables and machine settings
- **Troubleshooting**: Common issues and validation tools

## Additional Resources

- **[Deployment Guide](DEPLOYMENT.md)** - Docker deployment and production setup

## Documentation Philosophy

This consolidated guide provides everything needed to:
- Understand the manufacturing simulation
- Integrate with MQTT data streams  
- Deploy in production environments
- Troubleshoot and configure the system

The documentation is designed for industrial engineers, software developers, and system integrators working with manufacturing automation systems.
   - MQTT Broker: `localhost:1883`
   - WebSocket: `localhost:9001`

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the simulator:**
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER_HOST` | MQTT broker hostname | `localhost` |
| `MQTT_BROKER_PORT` | MQTT broker port | `1883` |
| `SIMULATION_SPEED` | Simulation speed multiplier | `1.0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PRODUCTION_LINE_NAME` | Name of the production line | `Assembly_Line_A` |
| `SHIFT_DURATION_HOURS` | Shift duration in hours | `8` |
| `CYCLE_TIME_SECONDS` | Base cycle time | `30` |

### Production Line Layout

The default configuration includes three machines:

1. **Material Preparation (MACHINE_001)**
   - Type: Preparation station
   - Sensors: Temperature, pressure, vibration, part presence
   - Actuators: Conveyor, pneumatic clamp, heating element
   - Cycle time: 25 seconds

2. **Assembly Station (MACHINE_002)**
   - Type: Assembly station
   - Sensors: Force, position, part presence, torque
   - Actuators: Robot arm, screwdriver, conveyor, pick-and-place
   - Cycle time: 35 seconds

3. **Quality Check (MACHINE_003)**
   - Type: Inspection station
   - Sensors: Camera, laser measurement, part presence, weight
   - Actuators: Conveyor, reject pusher, sorting gate
   - Cycle time: 20 seconds

## MQTT Topic Structure

```
production/{line_name}/
├── machines/{machine_id}/
│   ├── sensors/{sensor_type}      # Real-time sensor readings
│   └── actuators/{actuator_type}  # Actuator status updates
├── production_data                 # Overall production metrics
└── alarms/{severity}              # System alarms and alerts
```

### Example Topics

- `production/Assembly_Line_A/machines/MACHINE_001/sensors/temperature`
- `production/Assembly_Line_A/machines/MACHINE_002/actuators/robot_arm`
- `production/Assembly_Line_A/production_data`
- `production/Assembly_Line_A/alarms/high`

## Data Formats

### Sensor Data
```json
{
  "machine_id": "MACHINE_001",
  "sensor_type": "temperature",
  "value": 45.2,
  "timestamp": "2025-07-21T10:30:00",
  "unit": "°C"
}
```

### Production Data
```json
{
  "production_line_name": "Assembly_Line_A",
  "is_running": true,
  "current_of": {
    "of_number": "OF_20250721001",
    "part_type": "Widget_A",
    "progress_percent": 65.0
  },
  "alarm_active": false,
  "metrics": {
    "total_parts_produced": 150,
    "quality_rate": 0.98,
    "throughput_per_hour": 45.2,
    "oee_overall": 0.85
  }
}
```

## Architecture

```
src/
├── config/
│   └── settings.py           # Configuration management
├── core/
│   ├── mqtt_client.py        # MQTT communication
│   └── plant_simulator.py    # Main simulation orchestrator
└── models/
    ├── machine.py            # Individual machine simulation
    └── production_line.py    # Production line management
```

## Extending the Simulator

### Adding New Machines

1. **Update configuration** in `src/config/settings.py`:
   ```python
   {
       "id": "MACHINE_004",
       "name": "Packaging_Station",
       "type": "packaging",
       "cycle_time": 15,
       "failure_rate": 0.01,
       "sensors": ["weight", "barcode_scanner"],
       "actuators": ["packaging_unit", "label_printer"]
   }
   ```

2. **Extend sensor/actuator types** if needed in `src/models/machine.py`

### Adding New Sensor Types

1. **Define sensor** in `SensorType` enum
2. **Add baseline value** in `_initialize_sensor_baselines()`
3. **Implement generation logic** in `_generate_sensor_value()`
4. **Add unit mapping** in `_get_sensor_unit()`

### Custom Production Flows

Modify the `machine_sequence` in `ProductionLine` class to change the order of operations or implement parallel processing paths.

## Monitoring and Visualization

### MQTT Clients
- **MQTT Explorer**: Connect to `localhost:1883` to view all topics
- **Node-RED**: Create dashboards using the structured MQTT data
- **Grafana**: Use MQTT data source for time-series visualization

### Log Analysis
- Structured logging with configurable levels
- Machine-specific log namespaces
- Production event tracking

## Troubleshooting

### Common Issues

1. **MQTT Connection Failed**
   - Check if broker is running: `docker-compose ps`
   - Verify port accessibility: `telnet localhost 1883`

2. **Simulation Not Starting**
   - Check logs: `docker-compose logs plant-simulator`
   - Verify environment variables in `.env`

3. **Performance Issues**
   - Adjust `SIMULATION_SPEED` for slower hardware
   - Monitor Docker resource usage

### Development

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Test MQTT connectivity
mosquitto_pub -h localhost -t test/topic -m "Hello World"
mosquitto_sub -h localhost -t "production/+/+/+"
```

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate type hints and docstrings
3. Test with different simulation speeds
4. Ensure MQTT topic compatibility
5. Update documentation for new features

## License

This project is designed for educational and simulation purposes. Adapt as needed for your specific industrial automation requirements.
