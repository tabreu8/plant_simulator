'use client'

import React, { useEffect, useState } from 'react'
import Navigation from '../components/Navigation'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import StatusBadge from '../components/StatusBadge'

// TypeScript interfaces
interface SensorData {
  value: string
  unit?: string
  quality?: string
  timestamp?: string
}

interface ActuatorData {
  status: string
  power?: string
  timestamp?: string
}

interface ChartDataPoint {
  timestamp: string
  formattedTime: string
  [key: string]: string | number
}

interface ChartSeries {
  id: string
  name: string
  color: string
  type: 'sensor' | 'actuator'
  dataKey: string
}

interface MachineData {
  id: string
  name: string
  state: string
  phase: string
  currentPart: string | null
  sensors: Record<string, SensorData>
  actuators: Record<string, ActuatorData>
  lastUpdate: string
}

interface MachineData {
  id: string
  name: string
  state: string
  phase: string
  currentPart: string | null
  sensors: Record<string, SensorData>
  actuators: Record<string, ActuatorData>
  lastUpdate: string
}

export default function SensorMonitorPage() {
  const [selectedMachine, setSelectedMachine] = useState<string>('MACHINE_001')
  const [machineData, setMachineData] = useState<Record<string, MachineData>>({})
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting...')
  
  // Chart state management
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [selectedSeries, setSelectedSeries] = useState<ChartSeries[]>([])
  const [availableSeries, setAvailableSeries] = useState<ChartSeries[]>([])
  const [showChart, setShowChart] = useState<boolean>(true)
  const MAX_DATA_POINTS = 100

  // MQTT Configuration
  const mqttHost = process.env.NEXT_PUBLIC_MQTT_HOST || 'localhost'
  const mqttPort = parseInt(process.env.NEXT_PUBLIC_MQTT_PORT || '9001')
  const productionLine = process.env.NEXT_PUBLIC_PRODUCTION_LINE || 'Assembly_Line_A'

  const machineNames: Record<string, string> = {
    'MACHINE_001': 'Material Preparation Station',
    'MACHINE_002': 'Assembly Station',
    'MACHINE_003': 'Quality Inspection Station'
  }

  // Function to update chart data with new sensor/actuator values
  const updateChartData = (machineId: string, fieldName: string, value: string, timestamp: string) => {
    if (machineId !== selectedMachine) return

    const numericValue = parseFloat(value)
    if (isNaN(numericValue)) return

    setChartData(prev => {
      const newData = [...prev]
      const timeKey = new Date(timestamp).toLocaleTimeString()
      
      // Find existing data point for this timestamp or create new one
      let dataPoint = newData.find(point => point.timestamp === timestamp)
      if (!dataPoint) {
        dataPoint = {
          timestamp,
          formattedTime: timeKey
        }
        newData.push(dataPoint)
      }
      
      // Add the new value
      dataPoint[fieldName] = numericValue
      
      // Keep only last 100 data points
      if (newData.length > MAX_DATA_POINTS) {
        newData.splice(0, newData.length - MAX_DATA_POINTS)
      }
      
      return newData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    })
  }

  // Function to update available series when machine data changes
  useEffect(() => {
    const currentMachine = machineData[selectedMachine]
    if (!currentMachine) return

    const series: ChartSeries[] = []
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0']
    let colorIndex = 0

    // Add sensor series
    Object.entries(currentMachine.sensors).forEach(([sensorName, sensorData]) => {
      const numericValue = parseFloat(sensorData.value)
      if (!isNaN(numericValue)) {
        series.push({
          id: `sensor_${sensorName}`,
          name: `${sensorName.replace(/_/g, ' ')} ${sensorData.unit ? `(${sensorData.unit})` : ''}`,
          color: colors[colorIndex % colors.length],
          type: 'sensor',
          dataKey: `sensor_${sensorName}`
        })
        colorIndex++
      }
    })

    // Add actuator power series
    Object.entries(currentMachine.actuators).forEach(([actuatorName, actuatorData]) => {
      if (actuatorData.power) {
        const numericValue = parseFloat(actuatorData.power)
        if (!isNaN(numericValue)) {
          series.push({
            id: `actuator_${actuatorName}_power`,
            name: `${actuatorName.replace(/_/g, ' ')} Power (W)`,
            color: colors[colorIndex % colors.length],
            type: 'actuator',
            dataKey: `actuator_${actuatorName}_power`
          })
          colorIndex++
        }
      }
    })

    setAvailableSeries(series)
    
    // Auto-select first few series if none selected
    if (selectedSeries.length === 0 && series.length > 0) {
      setSelectedSeries(series.slice(0, Math.min(3, series.length)))
    }
  }, [machineData, selectedMachine])

  // Reset chart data when machine changes
  useEffect(() => {
    setChartData([])
    setSelectedSeries([])
  }, [selectedMachine])

  useEffect(() => {
    const connectToMQTT = async () => {
      try {
        const PahoMQTT = await import('paho-mqtt')
        const client = new PahoMQTT.Client(mqttHost, mqttPort, 'sensor-monitor-' + Math.random().toString(16).substr(2, 8))

        const connectOptions = {
          onSuccess: () => {
            console.log('Connected to MQTT broker for sensor monitoring')
            setConnectionStatus('Connected - Monitoring Sensors')
            
            // Subscribe to all machine topics
            const topicPattern = `production/${productionLine}/machines/+/+`
            client.subscribe(topicPattern)
            console.log(`Subscribed to: ${topicPattern}`)
          },
          onFailure: (error: any) => {
            console.error('MQTT connection failed:', error)
            setConnectionStatus('Connection Failed')
          }
        }

        client.onMessageArrived = (message: any) => {
          const topic = message.destinationName
          const payload = message.payloadString
          const timestamp = new Date().toISOString()
          
          // Parse topic: production/Assembly_Line_A/machines/MACHINE_001/field_name
          const topicParts = topic.split('/')
          if (topicParts.length >= 5) {
            const machineId = topicParts[3]
            const fieldName = topicParts[4]
            
            setMachineData(prev => {
              const updated = { ...prev }
              
              // Initialize machine if not exists
              if (!updated[machineId]) {
                updated[machineId] = {
                  id: machineId,
                  name: machineNames[machineId] || machineId,
                  state: 'unknown',
                  phase: 'unknown',
                  currentPart: null,
                  sensors: {},
                  actuators: {},
                  lastUpdate: timestamp
                }
              }
              
              const machine = updated[machineId]
              machine.lastUpdate = timestamp
              
              // Parse different data types
              if (fieldName.startsWith('sensor_')) {
                const sensorName = fieldName.replace('sensor_', '')
                
                // Check if this is a unit or quality field
                if (fieldName.endsWith('_unit')) {
                  const baseName = sensorName.replace('_unit', '')
                  if (!machine.sensors[baseName]) {
                    machine.sensors[baseName] = { value: '', timestamp }
                  }
                  machine.sensors[baseName].unit = payload
                  machine.sensors[baseName].timestamp = timestamp
                } else if (fieldName.endsWith('_quality')) {
                  const baseName = sensorName.replace('_quality', '')
                  if (!machine.sensors[baseName]) {
                    machine.sensors[baseName] = { value: '', timestamp }
                  }
                  machine.sensors[baseName].quality = payload
                  machine.sensors[baseName].timestamp = timestamp
                } else {
                  // This is the main sensor value - only create entry if it doesn't end with _unit or _quality
                  if (!sensorName.endsWith('_unit') && !sensorName.endsWith('_quality')) {
                    if (!machine.sensors[sensorName]) {
                      machine.sensors[sensorName] = { value: '', timestamp }
                    }
                    machine.sensors[sensorName].value = payload
                    machine.sensors[sensorName].timestamp = timestamp
                    
                    // Update chart data
                    updateChartData(machineId, `sensor_${sensorName}`, payload, timestamp)
                  }
                }
              } else if (fieldName.startsWith('actuator_')) {
                const actuatorName = fieldName.replace('actuator_', '')
                
                // Check if this is a power field
                if (fieldName.endsWith('_power')) {
                  const baseName = actuatorName.replace('_power', '')
                  if (!machine.actuators[baseName]) {
                    machine.actuators[baseName] = { status: '', timestamp }
                  }
                  machine.actuators[baseName].power = payload
                  machine.actuators[baseName].timestamp = timestamp
                  
                  // Update chart data for power values
                  updateChartData(machineId, `actuator_${baseName}_power`, payload, timestamp)
                } else {
                  // This is the main actuator status - only create entry if it doesn't end with _power
                  if (!actuatorName.endsWith('_power')) {
                    if (!machine.actuators[actuatorName]) {
                      machine.actuators[actuatorName] = { status: '', timestamp }
                    }
                    machine.actuators[actuatorName].status = payload
                    machine.actuators[actuatorName].timestamp = timestamp
                  }
                }
              } else if (fieldName.startsWith('production_')) {
                // Handle production data
                switch (fieldName) {
                  case 'production_machine_state':
                    machine.state = payload
                    break
                  case 'production_operation_phase':
                    machine.phase = payload
                    break
                  case 'production_current_part_id':
                    machine.currentPart = payload === '(null)' ? null : payload
                    break
                }
              }
              
              return updated
            })
          }
        }

        client.onConnectionLost = (responseObject: any) => {
          console.log('Connection lost:', responseObject.errorMessage)
          setConnectionStatus('Connection Lost - Reconnecting...')
        }

        client.connect(connectOptions)

      } catch (error) {
        console.error('Failed to load MQTT client:', error)
        setConnectionStatus(`Error: ${error}`)
      }
    }

    connectToMQTT()
  }, [mqttHost, mqttPort, productionLine])

  const currentMachine = machineData[selectedMachine]

  const getSensorIcon = (sensorName: string): string => {
    if (sensorName.includes('temperature')) return '🌡️'
    if (sensorName.includes('pressure')) return '🔧'
    if (sensorName.includes('force')) return '💪'
    if (sensorName.includes('position')) return '📍'
    if (sensorName.includes('vibration')) return '〰️'
    if (sensorName.includes('camera')) return '📷'
    if (sensorName.includes('weight')) return '⚖️'
    if (sensorName.includes('part_present')) return '📦'
    return '📊'
  }

  const getActuatorIcon = (actuatorName: string): string => {
    if (actuatorName.includes('conveyor')) return '🔄'
    if (actuatorName.includes('robot') || actuatorName.includes('arm')) return '🤖'
    if (actuatorName.includes('clamp')) return '🗜️'
    if (actuatorName.includes('heating')) return '🔥'
    if (actuatorName.includes('pusher')) return '👉'
    if (actuatorName.includes('gate')) return '🚪'
    if (actuatorName.includes('screwdriver')) return '🔩'
    return '⚙️'
  }

  const getSensorQualityColor = (quality?: string): string => {
    switch (quality?.toLowerCase()) {
      case 'good': return 'text-green-600 bg-green-100'
      case 'poor': return 'text-yellow-600 bg-yellow-100'
      case 'bad': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getActuatorStatusColor = (status: string): string => {
    if (status.includes('running') || status.includes('active') || status.includes('on')) {
      return 'text-green-600 bg-green-100'
    }
    if (status.includes('stopped') || status.includes('off') || status.includes('idle')) {
      return 'text-gray-600 bg-gray-100'
    }
    if (status.includes('error') || status.includes('fault')) {
      return 'text-red-600 bg-red-100'
    }
    return 'text-blue-600 bg-blue-100'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Navigation */}
      <Navigation 
        connectionStatus={connectionStatus}
        lastUpdate={machineData[selectedMachine]?.lastUpdate}
      />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">

        {/* Machine Selection */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-4 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Select Machine</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(machineNames).map(([machineId, machineName]) => (
              <button
                key={machineId}
                onClick={() => setSelectedMachine(machineId)}
                className={`p-4 rounded-xl border-2 transition-all duration-300 group ${
                  selectedMachine === machineId
                    ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-lg scale-105'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:shadow-md hover:scale-102'
                }`}
              >
                <div className="text-base font-semibold mb-1">{machineId}</div>
                <div className="text-sm opacity-75 mb-2">{machineName}</div>
                {machineData[machineId] && (
                  <div className="mt-2">
                    <StatusBadge 
                      status={machineData[machineId].state}
                      variant="default"
                      animated={machineData[machineId].state === 'running'}
                    />
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Real-time Data Chart */}
        {currentMachine && showChart && (
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-semibold text-gray-800">
                Real-time Data Chart
              </h2>
              <button
                onClick={() => setShowChart(!showChart)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors duration-200 flex items-center space-x-2"
              >
                <span>📊</span>
                <span>Hide Chart</span>
              </button>
            </div>

            {/* Series Selection */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Select data series to display:
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {availableSeries.map((series) => (
                  <label 
                    key={series.id} 
                    className="flex items-center space-x-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors duration-200 border border-gray-200"
                  >
                    <input
                      type="checkbox"
                      checked={selectedSeries.some(s => s.id === series.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedSeries([...selectedSeries, series])
                        } else {
                          setSelectedSeries(selectedSeries.filter(s => s.id !== series.id))
                        }
                      }}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                    />
                    <div 
                      className="w-4 h-4 rounded-full border-2 border-white shadow-sm" 
                      style={{ backgroundColor: series.color }}
                    ></div>
                    <span className="text-sm text-gray-700 flex-1 font-medium" title={series.name}>
                      {series.name}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Chart Container */}
            <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-4">
              <div className="h-80">
                {chartData.length > 0 && selectedSeries.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart 
                      data={chartData}
                      margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.6} />
                      <XAxis 
                        dataKey="formattedTime" 
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        interval="preserveStartEnd"
                        axisLine={{ stroke: '#d1d5db' }}
                        tickLine={{ stroke: '#d1d5db' }}
                      />
                      <YAxis 
                        tick={{ fontSize: 11, fill: '#6b7280' }}
                        axisLine={{ stroke: '#d1d5db' }}
                        tickLine={{ stroke: '#d1d5db' }}
                      />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                          fontSize: '12px'
                        }}
                        labelStyle={{ color: '#374151', fontWeight: '600' }}
                        labelFormatter={(label) => `Time: ${label}`}
                        formatter={(value, name) => [
                          typeof value === 'number' ? value.toFixed(2) : value,
                          name
                        ]}
                        animationDuration={0}
                      />
                      <Legend 
                        wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                      />
                      {selectedSeries.map((series) => (
                        <Line
                          key={series.id}
                          type="monotone"
                          dataKey={series.dataKey}
                          stroke={series.color}
                          strokeWidth={2.5}
                          dot={{ r: 3, strokeWidth: 0, fill: series.color }}
                          activeDot={{ r: 5, strokeWidth: 0, fill: series.color }}
                          name={series.name}
                          connectNulls={true}
                          isAnimationActive={false}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500">
                    <div className="text-4xl mb-4">📊</div>
                    <div className="text-lg font-medium mb-2">
                      {selectedSeries.length === 0 
                        ? "Select data series to display" 
                        : "Waiting for data..."}
                    </div>
                    <div className="text-sm">
                      {selectedSeries.length === 0 
                        ? "Choose one or more sensors or actuators above to see their data on the chart" 
                        : "Data will appear here once the selected sensors start reporting"}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Chart Info Bar */}
              <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-200">
                <div className="text-xs text-gray-500">
                  Showing last {Math.min(chartData.length, MAX_DATA_POINTS)} data points
                </div>
                {selectedSeries.length > 0 && (
                  <div className="text-xs text-gray-500">
                    {selectedSeries.length} series selected
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Show/Hide Chart Button when chart is hidden */}
        {currentMachine && !showChart && (
          <div className="bg-white rounded-lg shadow-md p-3 mb-4 text-center">
            <button
              onClick={() => setShowChart(true)}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Show Real-time Chart
            </button>
          </div>
        )}

        {/* Machine Details */}
        {currentMachine && (
          <>
            {/* Machine Status */}
            <div className="bg-white rounded-lg shadow-md p-4 mb-4">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">
                {currentMachine.name} Status
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600 mb-1">Machine State</div>
                  <div className={`font-semibold ${
                    currentMachine.state === 'running' ? 'text-green-600' :
                    currentMachine.state === 'idle' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {currentMachine.state.toUpperCase()}
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600 mb-1">Current Phase</div>
                  <div className="font-semibold text-gray-800">{currentMachine.phase}</div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600 mb-1">Current Part</div>
                  <div className="font-semibold text-gray-800 text-sm">
                    {currentMachine.currentPart || 'No Part'}
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600 mb-1">Last Update</div>
                  <div className="font-semibold text-gray-800 text-sm">
                    {new Date(currentMachine.lastUpdate).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Sensors */}
            <div className="bg-white rounded-lg shadow-md p-4 mb-4">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Sensors</h2>
              
              {Object.keys(currentMachine.sensors).length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No sensor data available for this machine
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(currentMachine.sensors).map(([sensorName, sensorData]) => {
                    const isActive = sensorData.quality === 'good' || parseFloat(sensorData.value) > 0
                    return (
                      <div 
                        key={sensorName} 
                        className="group relative bg-gradient-to-br from-white via-gray-50/50 to-gray-100/30 border-2 border-gray-200 rounded-2xl p-5 hover:shadow-xl hover:scale-[1.02] transition-all duration-300 hover:border-gray-400"
                      >
                        {/* Active indicator dot */}
                        {isActive && (
                          <div className="absolute top-3 right-3 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                        )}
                        
                        {/* Header with sensor name and icon */}
                        <div className="flex items-center mb-4">
                          <div className={`flex items-center justify-center w-12 h-12 rounded-xl mr-4 transition-all duration-300 ${
                            isActive ? 'bg-blue-500 text-white shadow-md' : 'bg-blue-100 text-blue-600'
                          }`}>
                            <span className="text-xl">{getSensorIcon(sensorName)}</span>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-800 capitalize text-sm leading-tight">
                              {sensorName.replace(/_/g, ' ')}
                            </h4>
                            <div className="text-xs text-gray-500 mt-0.5">Sensor</div>
                          </div>
                        </div>
                        
                        {/* Value and Status */}
                        <div className="flex items-end justify-between mb-4">
                          <div className="flex-1">
                            <div className="text-3xl font-bold text-gray-900 leading-none">
                              {sensorData.value}
                              {sensorData.unit && (
                                <span className="text-lg text-gray-600 ml-1 font-medium">{sensorData.unit}</span>
                              )}
                            </div>
                          </div>
                          
                          {/* Enhanced Status indicator */}
                          <div className={`flex items-center px-3 py-1.5 rounded-full text-xs font-bold shadow-sm border-2 transition-all duration-200 ${
                            sensorData.quality === 'good' ? 'bg-green-50 text-green-700 border-green-200' :
                            sensorData.quality === 'poor' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                            sensorData.quality === 'bad' ? 'bg-red-50 text-red-700 border-red-200' :
                            'bg-gray-50 text-gray-600 border-gray-200'
                          }`}>
                            {sensorData.quality === 'good' && '✓ '}
                            {sensorData.quality === 'poor' && '⚠ '}
                            {sensorData.quality === 'bad' && '✗ '}
                            {sensorData.quality || 'N/A'}
                          </div>
                        </div>
                        
                        {/* Timestamp with enhanced styling */}
                        {sensorData.timestamp && (
                          <div className="flex items-center text-xs text-gray-500 bg-gray-100/80 rounded-lg px-3 py-2">
                            <span className="mr-1">🕒</span>
                            <span>Updated: {new Date(sensorData.timestamp).toLocaleTimeString()}</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Actuators */}
            <div className="bg-white rounded-lg shadow-md p-4 mb-4">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Actuators</h2>
              
              {Object.keys(currentMachine.actuators).length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No actuator data available for this machine
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(currentMachine.actuators).map(([actuatorName, actuatorData]) => {
                    const isActive = actuatorData.status.includes('running') || actuatorData.status.includes('active') || actuatorData.status.includes('on')
                    const isError = actuatorData.status.includes('error') || actuatorData.status.includes('fault')
                    return (
                      <div 
                        key={actuatorName} 
                        className={`group relative bg-gradient-to-br from-white via-gray-50/50 to-gray-100/30 border-2 rounded-2xl p-5 hover:shadow-xl hover:scale-[1.02] transition-all duration-300 hover:border-gray-400 ${
                          isError ? 'border-red-200' : 'border-gray-200'
                        }`}
                      >
                        {/* Active/Error indicator dot */}
                        {(isActive || isError) && (
                          <div className={`absolute top-3 right-3 w-3 h-3 rounded-full animate-pulse ${
                            isActive ? 'bg-green-400' : 'bg-red-400'
                          }`}></div>
                        )}
                        
                        {/* Header */}
                        <div className="flex items-center mb-4">
                          <div className={`flex items-center justify-center w-12 h-12 rounded-xl mr-4 transition-all duration-300 ${
                            isActive ? 'bg-green-500 text-white shadow-md' : 
                            isError ? 'bg-red-500 text-white shadow-md' : 'bg-green-100 text-green-600'
                          }`}>
                            <span className="text-xl">{getActuatorIcon(actuatorName)}</span>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-800 capitalize text-sm leading-tight">
                              {actuatorName.replace(/_/g, ' ')}
                            </h4>
                            <div className="text-xs text-gray-500 mt-0.5">Actuator</div>
                          </div>
                        </div>
                        
                        {/* Status with enhanced styling */}
                        <div className="mb-4">
                          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold shadow-sm border-2 transition-all duration-200 ${
                            isActive ? 'bg-green-50 text-green-700 border-green-200' :
                            actuatorData.status.includes('stopped') || actuatorData.status.includes('off') || actuatorData.status.includes('idle') ? 'bg-gray-50 text-gray-600 border-gray-200' :
                            isError ? 'bg-red-50 text-red-700 border-red-200' :
                            'bg-blue-50 text-blue-600 border-blue-200'
                          }`}>
                            {isActive && '▶ '}
                            {actuatorData.status.includes('stopped') && '⏸ '}
                            {isError && '⚠ '}
                            {actuatorData.status}
                          </div>
                        </div>
                        
                        {/* Power reading with enhanced styling */}
                        {actuatorData.power && (
                          <div className="mb-4">
                            <div className="flex items-center justify-between bg-gradient-to-r from-gray-100 to-gray-200/50 rounded-xl px-4 py-3">
                              <div className="flex items-center">
                                <span className="text-yellow-600 mr-2">⚡</span>
                                <span className="text-sm font-medium text-gray-700">Power</span>
                              </div>
                              <span className="text-lg font-bold text-gray-900">{actuatorData.power}W</span>
                            </div>
                          </div>
                        )}
                        
                        {/* Timestamp with enhanced styling */}
                        {actuatorData.timestamp && (
                          <div className="flex items-center text-xs text-gray-500 bg-gray-100/80 rounded-lg px-3 py-2">
                            <span className="mr-1">🕒</span>
                            <span>{new Date(actuatorData.timestamp).toLocaleTimeString()}</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </>
        )}

        {!currentMachine && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-gray-500 text-lg">
              Select a machine to view its sensor and actuator data
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
