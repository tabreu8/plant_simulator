# Production Line Dashboard UI

A modern React-based dashboard for real-time monitoring and visualization of the production line simulator.

## 🎯 Features

### 1. Overview Dashboard (`/`)
- **System Status**: Real-time connection monitoring
- **Machine Count**: Active machines display  
- **Primary Machine State**: Current status of main machine
- **Quick Actions**: Navigation to detailed views
- **Configuration Display**: MQTT and production settings

### 2. Production Line Visualization (`/production-line`)
- **Top-Down Layout**: Visual representation of the 3-machine production line
- **Machine Status**: Real-time state, phase, and current part display
- **Buffer Visualization**: Inter-machine buffer status with part tracking
- **Conveyor System**: Animated conveyor belts with material flow
- **Production Statistics**: Individual machine performance metrics

### 3. Sensor Monitor (`/sensors`)
- **Machine Selection**: Choose any machine for detailed monitoring
- **Sensor Data**: Real-time values with units and quality indicators
- **Actuator Status**: Current state and power consumption
- **Data Quality**: Visual quality indicators (good/poor/bad)
- **Historical Context**: Timestamps for all data points

## 🎨 UI Components

### Core Components
- **`Machine`**: Visual machine representation with status indicators
- **`Buffer`**: Inter-machine buffer with capacity visualization
- **`Conveyor`**: Animated conveyor belt system
- **`Navigation`**: App-wide navigation with active page highlighting

### Visual Design
- **Responsive Layout**: Mobile-friendly design
- **Color Coding**: Intuitive status colors (green=running, blue=idle, red=error)
- **Real-time Updates**: Live data refresh via MQTT WebSocket
- **Interactive Elements**: Hover effects and clickable navigation

## 🔧 Configuration

### Environment Variables
```bash
# MQTT Broker Configuration
NEXT_PUBLIC_MQTT_HOST=localhost
NEXT_PUBLIC_MQTT_PORT=9001  
NEXT_PUBLIC_MQTT_PROTOCOL=ws

# Production Configuration
NEXT_PUBLIC_PRODUCTION_LINE=Assembly_Line_A
NEXT_PUBLIC_MACHINE_ID=MACHINE_001
```

### Machine Layout Configuration
The production line visualization uses a fixed layout:

```typescript
const machinePositions = {
  'MACHINE_001': { x: 200, y: 200 },  // Material Preparation
  'MACHINE_002': { x: 500, y: 200 },  // Assembly Station  
  'MACHINE_003': { x: 800, y: 200 }   // Quality Inspection
}

const bufferPositions = {
  'BUFFER_001': { x: 350, y: 200 },   // Between Machine 1 & 2
  'BUFFER_002': { x: 650, y: 200 }    // Between Machine 2 & 3
}
```

## 🚀 Development

### Prerequisites
- Node.js 18+
- npm or yarn
- Running MQTT broker (via simulator Docker setup)

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access dashboard
open http://localhost:3000
```

### Docker Development
```bash
# Build and run complete system
docker-compose up --build

# UI will be available at http://localhost:3000
```

## 📊 Data Flow

### MQTT Integration
The UI connects to the MQTT broker via WebSocket and subscribes to:

```
production/{line_name}/machines/+/+
```

### Data Processing
- **Real-time Updates**: Direct MQTT message handling
- **State Management**: React useState for component state
- **Data Transformation**: Topic parsing and value processing
- **Error Handling**: Connection loss detection and retry

### Topic Mapping
```typescript
// Machine state
production/Assembly_Line_A/machines/MACHINE_001/production_machine_state

// Sensor data  
production/Assembly_Line_A/machines/MACHINE_001/sensor_temperature
production/Assembly_Line_A/machines/MACHINE_001/sensor_temperature_unit
production/Assembly_Line_A/machines/MACHINE_001/sensor_temperature_quality

// Actuator status
production/Assembly_Line_A/machines/MACHINE_001/actuator_conveyor
production/Assembly_Line_A/machines/MACHINE_001/actuator_conveyor_power
```

## 🎭 Visual States

### Machine States
- **Running**: Green background with pulse animation
- **Idle**: Blue background  
- **Malfunction**: Red background
- **Maintenance**: Yellow background
- **Unknown**: Gray background

### Sensor Quality
- **Good**: Green indicator
- **Poor**: Yellow indicator  
- **Bad**: Red indicator

### Buffer Status
- **Low**: Green indicator (< 30% full)
- **Medium**: Yellow indicator (30-70% full)
- **High**: Orange indicator (70-90% full)
- **Full**: Red indicator (> 90% full)

## 🔄 Real-time Features

### Auto-refresh
- **Connection Status**: Live MQTT connection monitoring
- **Machine Data**: Real-time state and sensor updates
- **Visual Feedback**: Immediate UI updates on data changes
- **Error Recovery**: Automatic reconnection on connection loss

### Performance
- **Efficient Updates**: Selective component re-rendering
- **Memory Management**: Proper cleanup on component unmount
- **Network Optimization**: Targeted MQTT subscriptions

## 🐛 Troubleshooting

### Common Issues

1. **MQTT Connection Failed**
   - Check if MQTT broker is running (`docker ps`)
   - Verify WebSocket port 9001 is accessible
   - Check browser console for detailed errors

2. **No Data Appearing**
   - Ensure production simulator is running and publishing data
   - Check MQTT topic subscriptions in browser console
   - Verify environment variables are correctly set

3. **UI Not Loading**
   - Check if Next.js dev server is running on port 3000
   - Verify all dependencies are installed (`npm install`)
   - Check for TypeScript compilation errors

### Debug Commands
```bash
# Check MQTT messages
docker exec mqtt_broker_global mosquitto_sub -h localhost -t "production/+/machines/+/+"

# View service logs
docker-compose logs -f ui-dashboard

# Check service status
docker-compose ps
```

## 🔮 Future Enhancements

### Planned Features
- **Charts & Graphs**: Historical data visualization
- **Alarm System**: Real-time alerts and notifications
- **Multi-line Support**: Monitor multiple production lines
- **Mobile App**: React Native mobile application
- **Data Export**: CSV/Excel export functionality
- **User Authentication**: Role-based access control

### Technical Improvements
- **WebSocket Reconnection**: Enhanced connection reliability
- **Offline Support**: Cached data during disconnections
- **Performance Monitoring**: Real-time performance metrics
- **Accessibility**: WCAG compliance improvements

## 📝 License

This UI is part of the Production Line Simulator project and follows the same MIT License.

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
