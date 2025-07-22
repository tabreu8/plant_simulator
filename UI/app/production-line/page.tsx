'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import Machine from '../components/Machine'
import Buffer from '../components/Buffer'

// TypeScript interfaces
interface MachineData {
  id: string
  name: string
  state: string
  phase: string
  currentPart: string | null
  partsProcessedToday: number
  cycleTime: number
  inputBufferCount?: number
  outputBufferCount?: number
  inputBufferParts?: string[]
  outputBufferParts?: string[]
  sensors?: Record<string, any>
}

interface BufferData {
  id: string
  parts: string[]
  capacity: number
}

interface ProductionLineData {
  machines: Record<string, MachineData>
  buffers: Record<string, BufferData>
  lastUpdate: string
}

export default function ProductionLinePage() {
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting to MQTT...')
  const [productionData, setProductionData] = useState<ProductionLineData>({
    machines: {},
    buffers: {},
    lastUpdate: ''
  })

    // MQTT Configuration from environment
  const mqttHost = process.env.NEXT_PUBLIC_MQTT_HOST || 'localhost'
  const mqttPort = parseInt(process.env.NEXT_PUBLIC_MQTT_PORT || '9001')
  const productionLine = process.env.NEXT_PUBLIC_PRODUCTION_LINE || 'Assembly_Line_A'

  useEffect(() => {
    const connectToMQTT = async () => {
      try {
        const PahoMQTT = await import('paho-mqtt')
        const client = new PahoMQTT.Client(mqttHost, mqttPort, 'production-line-' + Math.random().toString(16).substr(2, 8))

        const connectOptions = {
          onSuccess: () => {
            console.log('Connected to MQTT broker')
            setConnectionStatus('Connected - Receiving Data')
            
            // Subscribe to all production line topics
            const topicPrefix = `production/${productionLine}/machines/+/`
            client.subscribe(`${topicPrefix}+`)
            console.log(`Subscribed to: ${topicPrefix}+`)
          },
          onFailure: (error: any) => {
            console.error('MQTT connection failed:', error)
            setConnectionStatus('Connection Failed')
          }
        }

        client.onMessageArrived = (message: any) => {
          const topic = message.destinationName
          const payload = message.payloadString
          
          // Parse topic: production/Assembly_Line_A/machines/MACHINE_001/field_name
          const topicParts = topic.split('/')
          if (topicParts.length >= 5) {
            const machineId = topicParts[3]
            const fieldName = topicParts[4]
            
            setProductionData(prev => {
              const updated = { ...prev }
              
              // Initialize machine if not exists
              if (!updated.machines[machineId]) {
                updated.machines[machineId] = {
                  id: machineId,
                  name: getMachineName(machineId),
                  state: 'unknown',
                  phase: 'unknown',
                  currentPart: null,
                  partsProcessedToday: 0,
                  cycleTime: 0,
                  sensors: {}
                }
              }
              
              // Update machine data based on field
              const machine = updated.machines[machineId]
              
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
                case 'production_parts_processed_today':
                  machine.partsProcessedToday = parseInt(payload) || 0
                  break
                case 'production_cycle_time_target':
                  machine.cycleTime = parseInt(payload) || 0
                  break
                case 'production_input_buffer_count':
                  machine.inputBufferCount = parseInt(payload) || 0
                  break
                case 'production_output_buffer_count':
                  machine.outputBufferCount = parseInt(payload) || 0
                  break
                case 'production_input_buffer_parts':
                  try {
                    machine.inputBufferParts = JSON.parse(payload) || []
                  } catch {
                    machine.inputBufferParts = []
                  }
                  break
                case 'production_output_buffer_parts':
                  try {
                    machine.outputBufferParts = JSON.parse(payload) || []
                  } catch {
                    machine.outputBufferParts = []
                  }
                  break
                default:
                  // Store sensor data
                  if (fieldName.startsWith('sensor_') || fieldName.startsWith('actuator_')) {
                    if (!machine.sensors) machine.sensors = {}
                    machine.sensors[fieldName] = payload
                  }
              }
              
              updated.lastUpdate = new Date().toISOString()
              return updated
            })
          }
        }

        client.onConnectionLost = (responseObject: any) => {
          console.log('Connection lost:', responseObject.errorMessage)
          setConnectionStatus('Connection Lost - Reconnecting...')
        }

        // Connect to MQTT broker
        client.connect(connectOptions)

      } catch (error) {
        console.error('Failed to load MQTT client:', error)
        setConnectionStatus(`Error: ${error}`)
      }
    }

    connectToMQTT()
  }, [mqttHost, mqttPort, productionLine])

  const getMachineName = (machineId: string): string => {
    const names: Record<string, string> = {
      'MACHINE_001': 'Material Prep',
      'MACHINE_002': 'Assembly Station',
      'MACHINE_003': 'Quality Inspection'
    }
    return names[machineId] || machineId
  }

  // Simple tile-based layout configuration
  const layoutConfig = {
    tileWidth: 120,     // Reduced from 120 to 90 to fit all elements
    tileHeight: 250,   // Height of each tile in the grid (increased from 200 to 250)
    cols: 9,           // Total columns: Input + Machine + Output for 3 machines
    rows: 1,           // Single row layout
    startX: 20,        // Starting X position
    startY: 80        // Starting Y position (adjusted slightly)
  }

  // Simple tile-based positioning
  const createTileLayout = () => {
    const { tileWidth, tileHeight, startX, startY } = layoutConfig
    
    // Define the production line flow as tiles
    const productionFlow = [
      { type: 'buffer', id: 'MACHINE_001_INPUT', machineId: 'MACHINE_001', bufferType: 'input' },
      { type: 'machine', id: 'MACHINE_001' },
      { type: 'buffer', id: 'MACHINE_001_OUTPUT', machineId: 'MACHINE_001', bufferType: 'output' },
      { type: 'buffer', id: 'MACHINE_002_INPUT', machineId: 'MACHINE_002', bufferType: 'input' },
      { type: 'machine', id: 'MACHINE_002' },
      { type: 'buffer', id: 'MACHINE_002_OUTPUT', machineId: 'MACHINE_002', bufferType: 'output' },
      { type: 'buffer', id: 'MACHINE_003_INPUT', machineId: 'MACHINE_003', bufferType: 'input' },
      { type: 'machine', id: 'MACHINE_003' },
      { type: 'buffer', id: 'MACHINE_003_OUTPUT', machineId: 'MACHINE_003', bufferType: 'output' }
    ]

    const machinePositions: Record<string, { x: number; y: number }> = {}
    const bufferPositions: Record<string, { x: number; y: number }> = {}

    productionFlow.forEach((item, index) => {
      const col = index
      const x = startX + (col * tileWidth) + (tileWidth / 2) // Center in tile
      const y = startY + (tileHeight / 2) // Center in tile
      
      if (item.type === 'machine') {
        machinePositions[item.id] = { x, y }
      } else if (item.type === 'buffer') {
        bufferPositions[item.id] = { x, y }
      }
    })

    return { 
      machinePositions, 
      bufferPositions, 
      productionFlow,
      layoutDimensions: {
        width: layoutConfig.cols * tileWidth,
        height: layoutConfig.rows * tileHeight
      }
    }
  }

  // Get tile-based positions
  const { machinePositions, bufferPositions, productionFlow, layoutDimensions } = createTileLayout()

  // Create buffer data from real MQTT data
  const getBufferData = () => {
    const buffers: Record<string, BufferData> = {}
    
    Object.entries(productionData.machines).forEach(([machineId, machine]) => {
      // Input buffer
      buffers[`${machineId}_INPUT`] = {
        id: `In`,
        parts: machine.inputBufferParts || [],
        capacity: 3 // reduced to 3 slots
      }
      
      // Output buffer
      buffers[`${machineId}_OUTPUT`] = {
        id: `Out`,
        parts: machine.outputBufferParts || [],
        capacity: 3 // reduced to 3 slots
      }
    })
    
    return buffers
  }

  const bufferData = getBufferData()

  const isConveyorActive = (conveyorId: string): boolean => {
    // Simple logic to determine if conveyor is active based on machine states
    return Object.values(productionData.machines).some(machine => 
      machine.state === 'running'
    )
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
                Production Line Monitor
              </h1>
              <p className="text-gray-600">
                Real-time visualization of {productionLine} manufacturing process
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
              {productionData.lastUpdate && (
                <div className="text-xs text-gray-500 mt-1">
                  Last update: {new Date(productionData.lastUpdate).toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Production Line Visualization */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Production Line Layout - Tile Grid System
          </h2>
          
          {/* Tile-based Production Line Container */}
          <div 
            className="relative bg-gray-50 border-2 border-gray-200 rounded-lg overflow-visible mx-auto"
            style={{ 
              width: layoutDimensions.width + 80, // Reduced padding to ensure fit
              height: layoutDimensions.height + 100 
            }}
          >
            {/* Tile Grid Background */}
            <div className="absolute inset-0">
              <svg width="100%" height="100%">
                <defs>
                  <pattern 
                    id="tileGrid" 
                    width={layoutConfig.tileWidth} 
                    height={layoutConfig.tileHeight} 
                    patternUnits="userSpaceOnUse"
                  >
                    <rect 
                      width={layoutConfig.tileWidth} 
                      height={layoutConfig.tileHeight} 
                      fill="none" 
                      stroke="#e5e7eb" 
                      strokeWidth="1"
                      strokeDasharray="5,5"
                    />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#tileGrid)" />
              </svg>
            </div>


            {/* Buffers with integrated conveyors */}
            {Object.entries(bufferPositions).map(([bufferId, position]) => (
              <Buffer
                key={bufferId}
                id={bufferData[bufferId]?.id || bufferId}
                position={position}
                parts={bufferData[bufferId]?.parts || []}
                capacity={bufferData[bufferId]?.capacity || 3}
                orientation="vertical"
                showConveyor={true}
                conveyorLength={40}
                isActive={isConveyorActive(`conv_${bufferId}`)}
              />
            ))}

            {/* Machines */}
            {Object.entries(machinePositions).map(([machineId, position]) => {
              const machine = productionData.machines[machineId]
              return (
                <Machine
                  key={machineId}
                  id={machineId}
                  name={machine?.name || getMachineName(machineId)}
                  state={machine?.state || 'unknown'}
                  phase={machine?.phase || 'unknown'}
                  currentPart={machine?.currentPart}
                  position={position}
                  sensors={machine?.sensors}
                />
              )
            })}

            {/* Material Flow Labels */}
            <div className="absolute top-4 left-4 bg-white bg-opacity-90 rounded-lg p-2 text-sm">
              <div className="font-semibold text-gray-800 mb-1">Material Flow</div>
              <div className="flex items-center space-x-4 text-xs text-gray-600">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-gray-400 rounded mr-1"></div>
                  Raw Materials
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded mr-1"></div>
                  Work in Progress
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded mr-1"></div>
                  Finished Goods
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Production Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          {Object.values(productionData.machines).map((machine) => (
            <div key={machine.id} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                {machine.name} ({machine.id})
              </h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${
                    machine.state === 'running' ? 'text-green-600' :
                    machine.state === 'idle' ? 'text-blue-600' :
                    machine.state === 'malfunction' ? 'text-red-600' :
                    'text-gray-600'
                  }`}>
                    {machine.state.toUpperCase()}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Current Phase:</span>
                  <span className="font-medium text-gray-800">{machine.phase}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Current Part:</span>
                  <span className="font-medium text-gray-800">
                    {machine.currentPart || 'None'}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Parts Today:</span>
                  <span className="font-medium text-gray-800">{machine.partsProcessedToday}</span>
                </div>

              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
