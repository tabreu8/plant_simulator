# Production Line Simulator - Deployment Guide

This guide explains how to deploy the Production Line Simulator using Docker Compose with an integrated MQTT broker.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- At least 512MB RAM available
- Ports 1883, 9001, and optionally 4000 available

## Quick Start

### 1. Basic Deployment

Deploy the simulator with MQTT broker:

```bash
docker-compose up -d
```

This will start:
- **Plant Simulator**: The main production line simulation
- **MQTT Broker**: Eclipse Mosquitto broker for data communication

### 2. With Monitoring (Optional)

Deploy with MQTT web interface for monitoring:

```bash
docker-compose --profile monitoring up -d
```

This additionally starts:
- **MQTT Explorer**: Web-based MQTT client at http://localhost:4000

### 3. Development Mode

For development with real-time logs:

```bash
docker-compose up
```

## Services Overview

### Plant Simulator
- **Container**: `plant_simulator`
- **Image**: Built from local Dockerfile
- **Purpose**: Simulates 3-machine production line with realistic sensor data
- **Dependencies**: Requires MQTT broker to be running

### MQTT Broker (Eclipse Mosquitto)
- **Container**: `mqtt_broker`
- **Image**: `eclipse-mosquitto:2.0`
- **Ports**:
  - `1883`: MQTT TCP protocol
  - `9001`: MQTT WebSocket protocol
- **Volumes**:
  - Configuration: `./mosquitto.conf`
  - Data persistence: `mqtt_data` volume
  - Logs: `mqtt_logs` volume

### MQTT Explorer (Optional)
- **Container**: `mqtt_explorer`
- **Image**: `smeagolworms4/mqtt-explorer`
- **Port**: `4000` (Web interface)
- **Purpose**: Monitor MQTT messages in real-time

## Configuration

### Environment Variables

You can customize the simulation by setting environment variables in `docker-compose.yml`:

```yaml
environment:
  - MQTT_BROKER_HOST=mqtt-broker     # MQTT broker hostname
  - MQTT_BROKER_PORT=1883           # MQTT broker port
  - MQTT_USERNAME=                  # MQTT username (optional)
  - MQTT_PASSWORD=                  # MQTT password (optional)
  - SIMULATION_SPEED=1.0            # Simulation speed multiplier
  - LOG_LEVEL=INFO                  # Logging level
```

### Mosquitto Configuration

The MQTT broker is configured via `mosquitto.conf`:

- **Anonymous access**: Enabled (for development)
- **Persistence**: Enabled with auto-save
- **WebSocket support**: Enabled on port 9001
- **Logging**: File and console logging
- **Connection limits**: 1000 max connections

For production, consider:
- Enabling authentication
- Setting up ACLs (Access Control Lists)
- Using SSL/TLS certificates

## MQTT Topic Structure

The simulator publishes data to structured topics:

```
production/TestPlant/
├── machines/
│   ├── MACHINE_001/
│   │   ├── sensors/temperature
│   │   ├── sensors/vibration
│   │   ├── sensors/pressure
│   │   └── actuators/motor_speed
│   ├── MACHINE_002/
│   │   └── ...
│   └── MACHINE_003/
│       └── ...
├── production_data
├── alarms/high
├── alarms/medium
└── alarms/low
```

## Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f plant-simulator
docker-compose logs -f mqtt-broker
```

### Restart Simulator Only
```bash
docker-compose restart plant-simulator
```

### Scale for Load Testing
```bash
# Run multiple simulator instances
docker-compose up -d --scale plant-simulator=3
```

### Check Service Health
```bash
docker-compose ps
```

### Update and Rebuild
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Data Persistence

- **MQTT Data**: Persisted in `mqtt_data` Docker volume
- **MQTT Logs**: Persisted in `mqtt_logs` Docker volume
- **Configuration**: Mounted from local files

To backup data:
```bash
docker run --rm -v plant_simulator_mqtt_data:/data -v $(pwd):/backup alpine tar czf /backup/mqtt_data_backup.tar.gz -C /data .
```

## Monitoring and Debugging

### Health Checks

Both services include health checks:
- **MQTT Broker**: Tests message publishing
- **Plant Simulator**: Tests MQTT connection

Check health status:
```bash
docker-compose ps
```

### MQTT Monitoring

1. **Web Interface**: http://localhost:4000 (if monitoring profile is enabled)
2. **Command Line Client**:
   ```bash
   # Subscribe to all topics
   docker exec mqtt_broker mosquitto_sub -h localhost -t "production/#" -v
   
   # Publish test message
   docker exec mqtt_broker mosquitto_pub -h localhost -t "test/topic" -m "test message"
   ```

### Performance Monitoring

Monitor container resources:
```bash
docker stats plant_simulator mqtt_broker
```

### Troubleshooting

1. **Connection Issues**:
   ```bash
   # Check if MQTT broker is accessible
   docker exec plant_simulator python -c "import socket; socket.create_connection(('mqtt-broker', 1883))"
   ```

2. **Service Dependencies**:
   ```bash
   # Ensure proper startup order
   docker-compose down && docker-compose up -d
   ```

3. **Log Analysis**:
   ```bash
   # Check for errors
   docker-compose logs plant-simulator | grep -i error
   docker-compose logs mqtt-broker | grep -i error
   ```

## Production Considerations

### Security
- Enable MQTT authentication
- Use SSL/TLS encryption
- Implement proper firewall rules
- Regular security updates

### Performance
- Monitor memory usage
- Adjust simulation speed based on hardware
- Consider load balancing for multiple instances
- Set up proper log rotation

### Backup
- Regular backup of MQTT data volumes
- Configuration file versioning
- Container image versioning

### Monitoring
- Set up external monitoring (Prometheus, Grafana)
- Implement alerting for service failures
- Monitor MQTT message rates and patterns

## Network Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  Plant          │    │  MQTT Broker    │
│  Simulator      │◄──►│  (Mosquitto)    │
│  :internal      │    │  :1883, :9001   │
└─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         └───────────────────────┘
                 Docker Network
                (plant-network)
```

All services communicate within the isolated `plant-network` Docker network, with only necessary ports exposed to the host.
