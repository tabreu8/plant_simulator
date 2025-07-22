# Machine Monitor - Production Line UI

A Next.js React application that provides real-time monitoring of the production line simulator via MQTT.

## Features

- **Real-time MQTT Connection**: Connects to the production line simulator via WebSocket MQTT
- **Machine State Monitoring**: Displays the current state of MACHINE_001 (Material Preparation)
- **Connection Status**: Shows MQTT broker connection status
- **Responsive Design**: Built with Tailwind CSS for modern styling
- **TypeScript**: Fully typed for better development experience

## Prerequisites

1. **Production Line Simulator**: Must be running with MQTT broker
2. **Node.js**: Version 18+ required
3. **WebSocket Support**: MQTT broker must have WebSocket enabled on port 9001

## Quick Start

### 1. Install Dependencies
```bash
cd UI/machine-monitor
npm install
```

### 2. Start the Production Line Simulator
```bash
# In the simulator directory
cd ../../simulator
docker-compose -f docker/docker-compose.yml up --build
```

This starts:
- MQTT Broker on port 1883 (standard MQTT) and 9001 (WebSocket)
- Production Line Simulator publishing real-time data

### 3. Start the UI Development Server
```bash
# In the UI directory
npm run dev
```

### 4. Open in Browser
Navigate to [http://localhost:3000](http://localhost:3000)

## MQTT Configuration

The application connects to:
- **Broker URL**: `ws://localhost:9001`
- **Topic**: `production/Assembly_Line_A/machines/MACHINE_001/production_machine_state`
- **Connection**: WebSocket over MQTT

## Expected Machine States

The machine can be in one of these states:
- **idle**: Machine ready but not processing (yellow)
- **running**: Actively processing parts (green)
- **malfunction**: Temporary fault state (red)
- **maintenance**: Scheduled or corrective maintenance (blue)
- **error**: Critical fault requiring intervention (dark red)

## Development

### Project Structure
```
machine-monitor/
├── src/
│   └── app/
│       ├── page.tsx          # Main monitoring page
│       ├── layout.tsx         # App layout
│       └── globals.css        # Global styles
├── package.json               # Dependencies and scripts
└── tailwind.config.ts         # Tailwind configuration
```

### Available Scripts
- `npm run dev`: Start development server with Turbopack
- `npm run build`: Build for production
- `npm run start`: Start production server
- `npm run lint`: Run ESLint

## Troubleshooting

### Connection Issues
1. **MQTT Broker Not Running**: Ensure Docker containers are up
2. **WebSocket Port Blocked**: Check if port 9001 is accessible
3. **CORS Issues**: Next.js dev server should handle this automatically

### No Data Received
1. **Simulator Not Publishing**: Check simulator logs
2. **Wrong Topic**: Verify the MQTT topic matches exactly
3. **Network Issues**: Ensure localhost connectivity

### Debug Information
The UI includes a debug panel showing:
- Connection status
- Current machine state
- Last update timestamp

## Next Steps

This is a basic implementation that monitors a single topic. Future enhancements could include:
- Multiple machine monitoring
- Historical data visualization
- Sensor data charts
- Production metrics dashboard
- Alarm management
- Mobile responsiveness improvements

## Technical Details

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **MQTT Client**: mqtt.js library
- **Real-time Updates**: WebSocket connection to MQTT broker
