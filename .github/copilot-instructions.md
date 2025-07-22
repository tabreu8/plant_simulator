<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Production Line Simulator - Copilot Instructions

This is a Python-based production line simulator that models industrial manufacturing processes with realistic sensor data, actuator control, and MQTT communication.

## Project Context

- **Domain**: Industrial automation and manufacturing simulation
- **Architecture**: Modular design with clear separation of concerns
- **Communication**: MQTT-based data publishing for IoT integration
- **Deployment**: Docker containerized for easy deployment

## Key Components

1. **Machine Models**: Individual machine simulation with sensors and actuators
2. **Production Line**: Orchestrates multiple machines in a manufacturing flow
3. **MQTT Client**: Publishes real-time data to message broker
4. **Plant Simulator**: Main orchestrator that manages the entire simulation

## Code Guidelines

- Use type hints consistently throughout the codebase
- Follow async/await patterns for concurrent operations
- Implement proper error handling and logging
- Use dataclasses for data structures
- Follow the existing naming conventions (snake_case)
- Add docstrings to all public methods and classes

## Simulation Concepts

- **Realistic Data**: Generate sensor values that reflect actual manufacturing conditions
- **State Management**: Track machine states (idle, running, error, maintenance)
- **Production Flow**: Model realistic part flow through multiple processing stations
- **Quality Control**: Include quality checks and rejection scenarios
- **Performance Metrics**: Calculate OEE (Overall Equipment Effectiveness), throughput, quality rates

## MQTT Topic Structure

```
production/{line_name}/
├── machines/{machine_id}/
│   ├── sensors/{sensor_type}
│   └── actuators/{actuator_type}
├── production_data
└── alarms/{severity}
```

## Configuration

- Use Pydantic settings for configuration management
- Support environment variables for Docker deployment
- Make the system easily configurable for different production layouts
- Allow simulation speed adjustment for testing/demo purposes

## Extension Points

The system is designed to be easily extensible:
- Add new machine types by extending the Machine class
- Modify production flows by updating machine sequences
- Add new sensor/actuator types through configuration
- Implement custom quality control logic
- Add new MQTT topics for additional data streams

When making changes, ensure backward compatibility and maintain the modular structure.
