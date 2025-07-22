'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import Navigation from '../components/Navigation'
import Machine from '../components/Machine'
import Buffer from '../components/Buffer'
import QualityResult from '../components/QualityResult'
import StatusBadge from '../components/StatusBadge'

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
  lastInspectedPart?: string | null
  inspectionResult?: string | null
  inspectionTimestamp?: string
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
                case 'production_inspection_status':
                  // Handle quality inspection result for MACHINE_003 only during sorting phase
                  if (machineId === 'MACHINE_003' && machine.phase === 'sorting') {
                    machine.inspectionResult = payload
                    machine.inspectionTimestamp = new Date().toISOString()
                    // Assume the last part processed is the one being inspected
                    if (machine.currentPart) {
                      machine.lastInspectedPart = machine.currentPart
                    }
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
    startY: 50        // Starting Y position (adjusted slightly)
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
      { type: 'quality', id: 'MACHINE_003_QUALITY', machineId: 'MACHINE_003' }
    ]

    const machinePositions: Record<string, { x: number; y: number }> = {}
    const bufferPositions: Record<string, { x: number; y: number }> = {}
    const qualityPositions: Record<string, { x: number; y: number }> = {}

    productionFlow.forEach((item, index) => {
      const col = index
      const x = startX + (col * tileWidth) + (tileWidth / 2) // Center in tile
      const y = startY + (tileHeight / 2) // Center in tile
      
      if (item.type === 'machine') {
        machinePositions[item.id] = { x, y }
      } else if (item.type === 'buffer') {
        bufferPositions[item.id] = { x, y }
      } else if (item.type === 'quality') {
        qualityPositions[item.id] = { x, y }
      }
    })

    return { 
      machinePositions, 
      bufferPositions, 
      qualityPositions,
      productionFlow,
      layoutDimensions: {
        width: layoutConfig.cols * tileWidth,
        height: layoutConfig.rows * tileHeight
      }
    }
  }

  // Get tile-based positions
  const { machinePositions, bufferPositions, qualityPositions, productionFlow, layoutDimensions } = createTileLayout()

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
      
      // Output buffer - except for MACHINE_003 which has quality result instead
      if (machineId !== 'MACHINE_003') {
        buffers[`${machineId}_OUTPUT`] = {
          id: `Out`,
          parts: machine.outputBufferParts || [],
          capacity: 3 // reduced to 3 slots
        }
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Navigation */}
      <Navigation 
        connectionStatus={connectionStatus}
        lastUpdate={productionData.lastUpdate}
      />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">

        {/* Production Line Visualization */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-base font-semibold text-gray-800 mb-3">
            Production Line Layout
          </h2>
          
          {/* Tile-based Production Line Container */}
          <div 
            className="relative bg-gray-50 border-2 border-gray-200 rounded-lg overflow-visible mx-auto"
            style={{ 
              width: layoutDimensions.width + 60, // Increased padding for more space
              height: layoutDimensions.height + 80 // Increased height padding for more space
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

            {/* Quality Result Widget for MACHINE_003 */}
            {Object.entries(qualityPositions).map(([qualityId, position]) => {
              const machineId = qualityId.replace('_QUALITY', '')
              const machine = productionData.machines[machineId]
              return (
                <QualityResult
                  key={qualityId}
                  position={position}
                  lastPart={machine?.lastInspectedPart || machine?.currentPart || null}
                  qualityResult={machine?.inspectionResult || null}
                  timestamp={machine?.inspectionTimestamp}
                  machinePhase={machine?.phase}
                />
              )
            })}

            {/* Material Flow Labels */}
            <div className="absolute top-4 left-4 bg-white bg-opacity-90 rounded-lg p-2 text-sm">
              <div className="font-semibold text-gray-800 mb-1">Material Flow</div>
              
            </div>
          </div>
        </div>

        {/* Parts Tracking Section */}
        <div className="bg-white rounded-lg shadow-md p-4 mt-4">
          <h2 className="text-base font-semibold text-gray-800 mb-3">
            Parts in Production
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Current Parts in Machines */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 border border-blue-200">
              <h3 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                Currently Processing
              </h3>
              <div className="space-y-2">
                {Object.values(productionData.machines)
                  .filter(machine => machine.currentPart && machine.currentPart !== '(null)')
                  .map((machine) => (
                    <div key={machine.id} className="bg-white rounded-md p-2 text-xs border border-blue-200">
                      <div className="font-medium text-gray-800">{machine.currentPart}</div>
                      <div className="text-gray-600">{machine.name} - {machine.phase}</div>
                    </div>
                  ))}
                {Object.values(productionData.machines).filter(machine => machine.currentPart && machine.currentPart !== '(null)').length === 0 && (
                  <div className="text-gray-500 text-xs italic">No parts currently being processed</div>
                )}
              </div>
            </div>

            {/* Parts in Input Buffers */}
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-3 border border-yellow-200">
              <h3 className="text-sm font-medium text-yellow-800 mb-2 flex items-center">
                <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                Waiting in Input Buffers
              </h3>
              <div className="space-y-2">
                {Object.entries(productionData.machines)
                  .filter(([_, machine]) => machine.inputBufferParts && machine.inputBufferParts.length > 0)
                  .map(([machineId, machine]) => (
                    <div key={`input-${machineId}`} className="bg-white rounded-md p-2 text-xs border border-yellow-200">
                      <div className="font-medium text-gray-700 mb-1">{machine.name} Input</div>
                      {machine.inputBufferParts?.map((part, index) => (
                        <div key={index} className="text-gray-600 ml-2">• {part}</div>
                      ))}
                    </div>
                  ))}
                {Object.values(productionData.machines).every(machine => !machine.inputBufferParts || machine.inputBufferParts.length === 0) && (
                  <div className="text-gray-500 text-xs italic">No parts waiting in input buffers</div>
                )}
              </div>
            </div>

            {/* Parts in Output Buffers */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-3 border border-green-200">
              <h3 className="text-sm font-medium text-green-800 mb-2 flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Ready in Output Buffers
              </h3>
              <div className="space-y-2">
                {Object.entries(productionData.machines)
                  .filter(([_, machine]) => machine.outputBufferParts && machine.outputBufferParts.length > 0)
                  .map(([machineId, machine]) => (
                    <div key={`output-${machineId}`} className="bg-white rounded-md p-2 text-xs border border-green-200">
                      <div className="font-medium text-gray-700 mb-1">{machine.name} Output</div>
                      {machine.outputBufferParts?.map((part, index) => (
                        <div key={index} className="text-gray-600 ml-2">• {part}</div>
                      ))}
                    </div>
                  ))}
                {Object.values(productionData.machines).every(machine => !machine.outputBufferParts || machine.outputBufferParts.length === 0) && (
                  <div className="text-gray-500 text-xs italic">No parts ready in output buffers</div>
                )}
              </div>
            </div>
          </div>

          {/* Summary Statistics */}
          <div className="mt-4 pt-3 border-t border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-lg font-bold text-gray-800">
                  {Object.values(productionData.machines).filter(machine => machine.currentPart && machine.currentPart !== '(null)').length}
                </div>
                <div className="text-xs text-gray-600">Processing</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-lg font-bold text-gray-800">
                  {Object.values(productionData.machines).reduce((total, machine) => total + (machine.inputBufferParts?.length || 0), 0)}
                </div>
                <div className="text-xs text-gray-600">In Input Buffers</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-lg font-bold text-gray-800">
                  {Object.values(productionData.machines).reduce((total, machine) => total + (machine.outputBufferParts?.length || 0), 0)}
                </div>
                <div className="text-xs text-gray-600">In Output Buffers</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-2">
                <div className="text-lg font-bold text-gray-800">
                  {Object.values(productionData.machines).reduce((total, machine) => total + machine.partsProcessedToday, 0)}
                </div>
                <div className="text-xs text-gray-600">Completed Today</div>
              </div>
            </div>
          </div>
        </div>

        {/* Production Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
          {Object.values(productionData.machines).map((machine) => (
            <div key={machine.id} className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">
                {machine.name} ({machine.id})
              </h3>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
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
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Current Phase:</span>
                  <span className="font-medium text-gray-800">{machine.phase}</span>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Current Part:</span>
                  <span className="font-medium text-gray-800">
                    {machine.currentPart || 'None'}
                  </span>
                </div>
                
                <div className="flex justify-between text-sm">
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
