'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Return Button */}
        <div className="mb-4">
          <Link 
            href="/" 
            className="inline-flex items-center space-x-2 px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 shadow-md"
          >
            <span>←</span>
            <span>Back to Main</span>
          </Link>
        </div>

        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Sensor & Actuator Monitor
              </h1>
              <p className="text-gray-600">
                Real-time monitoring of machine sensors and actuators
              </p>
            </div>
            
            <div className="text-right">
              <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                connectionStatus.includes('Connected') 
                  ? 'bg-green-100 text-green-800' 
                  : connectionStatus.includes('Error') || connectionStatus.includes('Failed')
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  connectionStatus.includes('Connected') ? 'bg-green-500' : 'bg-yellow-500'
                }`}></div>
                {connectionStatus}
              </div>
            </div>
          </div>
        </div>

        {/* Machine Selection */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Select Machine</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(machineNames).map(([machineId, machineName]) => (
              <button
                key={machineId}
                onClick={() => setSelectedMachine(machineId)}
                className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                  selectedMachine === machineId
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold">{machineId}</div>
                <div className="text-sm opacity-75">{machineName}</div>
                {machineData[machineId] && (
                  <div className="mt-2">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      machineData[machineId].state === 'running' ? 'bg-green-100 text-green-800' :
                      machineData[machineId].state === 'idle' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {machineData[machineId].state}
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Real-time Data Chart */}
        {currentMachine && showChart && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">
                Real-time Data Chart
              </h2>
              <button
                onClick={() => setShowChart(!showChart)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Hide Chart
              </button>
            </div>

            {/* Series Selection */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Select data series to display:
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {availableSeries.map((series) => (
                  <label key={series.id} className="flex items-center space-x-2 cursor-pointer">
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
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 truncate" title={series.name}>
                      {series.name}
                    </span>
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: series.color }}
                    ></div>
                  </label>
                ))}
              </div>
            </div>

            {/* Chart */}
            <div className="h-80">
              {chartData.length > 0 && selectedSeries.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart 
                    data={chartData}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="formattedTime" 
                      tick={{ fontSize: 12 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip 
                      labelFormatter={(label) => `Time: ${label}`}
                      formatter={(value, name) => [
                        typeof value === 'number' ? value.toFixed(2) : value,
                        name
                      ]}
                      animationDuration={0}
                    />
                    <Legend />
                    {selectedSeries.map((series) => (
                      <Line
                        key={series.id}
                        type="monotone"
                        dataKey={series.dataKey}
                        stroke={series.color}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                        name={series.name}
                        connectNulls={true}
                        isAnimationActive={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  {selectedSeries.length === 0 
                    ? "Select data series to display on the chart" 
                    : "Waiting for data..."}
                </div>
              )}
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Showing last {Math.min(chartData.length, MAX_DATA_POINTS)} data points
            </div>
          </div>
        )}

        {/* Show/Hide Chart Button when chart is hidden */}
        {currentMachine && !showChart && (
          <div className="bg-white rounded-lg shadow-md p-4 mb-6 text-center">
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
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                {currentMachine.name} Status
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Machine State</div>
                  <div className={`font-semibold ${
                    currentMachine.state === 'running' ? 'text-green-600' :
                    currentMachine.state === 'idle' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {currentMachine.state.toUpperCase()}
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Current Phase</div>
                  <div className="font-semibold text-gray-800">{currentMachine.phase}</div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Current Part</div>
                  <div className="font-semibold text-gray-800 text-sm">
                    {currentMachine.currentPart || 'No Part'}
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Last Update</div>
                  <div className="font-semibold text-gray-800 text-sm">
                    {new Date(currentMachine.lastUpdate).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Sensors */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Sensors</h2>
              
              {Object.keys(currentMachine.sensors).length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No sensor data available for this machine
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(currentMachine.sensors).map(([sensorName, sensorData]) => (
                    <div key={sensorName} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow duration-200">
                      {/* Header with sensor name and icon */}
                      <div className="flex items-center mb-3">
                        <span className="text-2xl mr-2">{getSensorIcon(sensorName)}</span>
                        <div className="font-medium text-gray-800 capitalize">
                          {sensorName.replace(/_/g, ' ')}
                        </div>
                      </div>
                      
                      {/* Value, Unit, and Status in a single line */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-2xl font-bold text-gray-900">
                          {sensorData.value}
                          {sensorData.unit && (
                            <span className="text-sm text-gray-600 ml-1">{sensorData.unit}</span>
                          )}
                        </div>
                        
                        {/* Status (Quality) indicator */}
                        <div className={`px-2 py-1 rounded text-xs font-medium ${getSensorQualityColor(sensorData.quality)}`}>
                          {sensorData.quality || 'N/A'}
                        </div>
                      </div>
                      
                      {/* Timestamp */}
                      {sensorData.timestamp && (
                        <div className="text-xs text-gray-500">
                          Updated: {new Date(sensorData.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actuators */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Actuators</h2>
              
              {Object.keys(currentMachine.actuators).length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No actuator data available for this machine
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(currentMachine.actuators).map(([actuatorName, actuatorData]) => (
                    <div key={actuatorName} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">{getActuatorIcon(actuatorName)}</span>
                          <div className="font-medium text-gray-800 capitalize">
                            {actuatorName.replace(/_/g, ' ')}
                          </div>
                        </div>
                      </div>
                      
                      <div className="mb-2">
                        <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${getActuatorStatusColor(actuatorData.status)}`}>
                          {actuatorData.status}
                        </span>
                      </div>
                      
                      {actuatorData.power && (
                        <div className="text-sm text-gray-600 mb-1">
                          Power: {actuatorData.power}W
                        </div>
                      )}
                      
                      {actuatorData.timestamp && (
                        <div className="text-xs text-gray-500">
                          {new Date(actuatorData.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  ))}
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
