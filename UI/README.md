# User Interface (UI)

This directory contains the user interface components for the Production Line Manufacturing System.

## Overview

The UI provides real-time monitoring and control capabilities for the production line simulator, including:

- **Real-time Dashboard**: Live production metrics and machine status
- **Machine Monitoring**: Individual machine states, sensors, and actuators
- **Production Management**: Order tracking, quality metrics, and throughput
- **Alarm Management**: Real-time alerts and notifications
- **Historical Data**: Trends, reports, and analytics

## Planned Components

### Web Interface
- React/Vue.js dashboard for production monitoring
- Real-time MQTT data visualization
- Interactive machine status displays
- Production analytics and reporting

### Desktop Application  
- Cross-platform desktop app for operators
- HMI-style interface for production control
- Offline capability with data synchronization
- Advanced diagnostics and troubleshooting tools

### Mobile Interface
- Mobile-responsive web app
- Push notifications for critical alarms
- Quick status overview for managers
- Remote monitoring capabilities

## Integration with Simulator

The UI connects to the production line simulator via:

- **MQTT Topics**: Real-time data subscription from `production/Assembly_Line_A/#`
- **WebSocket Connection**: For real-time updates and bidirectional communication
- **REST API**: For configuration and historical data (future enhancement)

## MQTT Data Sources

The UI will consume data from these simulator topics:

### Machine Status
```
production/Assembly_Line_A/machines/MACHINE_001/production_machine_state
production/Assembly_Line_A/machines/MACHINE_001/production_current_part_id
production/Assembly_Line_A/machines/MACHINE_001/production_parts_processed_today
```

### Sensor Data
```
production/Assembly_Line_A/machines/MACHINE_001/sensor_temperature
production/Assembly_Line_A/machines/MACHINE_002/sensor_force
production/Assembly_Line_A/machines/MACHINE_003/sensor_camera
```

### Production Metrics
```
production/Assembly_Line_A/production_data  # JSON with overall metrics
```

## Development Setup

*Setup instructions will be added when UI components are implemented*

```bash
cd UI/
# npm install (for web interface)
# pip install -r requirements.txt (for desktop app)
```

## Future Enhancements

- Multi-line support for complex manufacturing facilities
- Advanced analytics with machine learning insights
- Integration with ERP/MES systems
- Custom dashboard configuration
- Role-based access control
- Data export and reporting tools
