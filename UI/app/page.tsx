'use client'

import { useEffect, useState } from 'react'
import Navigation from './components/Navigation'
import { StatusCard } from './components/Card'
import StatusBadge from './components/StatusBadge'

export default function Home() {
  const [machineState, setMachineState] = useState<string>('connecting...')
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting to MQTT...')
  const [machineCount, setMachineCount] = useState<number>(0)
  const [activeConnections, setActiveConnections] = useState<number>(0)

  // Get configuration from environment variables with defaults
  const mqttHost = process.env.NEXT_PUBLIC_MQTT_HOST || 'localhost'
  const mqttPort = parseInt(process.env.NEXT_PUBLIC_MQTT_PORT || '9001')
  const mqttProtocol = process.env.NEXT_PUBLIC_MQTT_PROTOCOL || 'ws'
  const productionLine = process.env.NEXT_PUBLIC_PRODUCTION_LINE || 'Assembly_Line_A'
  const machineId = process.env.NEXT_PUBLIC_MACHINE_ID || 'MACHINE_001'
  
  // Construct MQTT broker URL and topic
  const mqttUrl = `${mqttProtocol}://${mqttHost}:${mqttPort}`
  const machineTopic = `production/${productionLine}/machines/${machineId}/production_machine_state`

  useEffect(() => {
    // Load Paho MQTT client dynamically
    const connectToMQTT = async () => {
      try {
        // Import Paho MQTT - using correct import pattern
        const PahoMQTT = await import('paho-mqtt')
        
        // Create MQTT client using the correct Paho structure
        const client = new PahoMQTT.Client(mqttHost, mqttPort, 'overview-client-' + Math.random().toString(16).substr(2, 8))

        // Set up connection options
        const connectOptions = {
          onSuccess: () => {
            console.log(`Connected to MQTT broker at ${mqttUrl}`)
            setConnectionStatus('Connected to MQTT')
            setActiveConnections(1)
            
            // Subscribe to the machine state topic and general stats
            try {
              client.subscribe(machineTopic)
              client.subscribe(`production/${productionLine}/machines/+/production_machine_state`)
              console.log(`Subscribed to topics`)
              setConnectionStatus('Monitoring Production Line')
            } catch (err) {
              console.error('Failed to subscribe:', err)
              setConnectionStatus('Failed to subscribe to topics')
            }
          },
          onFailure: (responseObject: any) => {
            console.error('Failed to connect:', responseObject.errorMessage)
            setConnectionStatus(`Connection failed: ${responseObject.errorMessage}`)
            setActiveConnections(0)
          },
          timeout: 10,
          keepAliveInterval: 30,
        }

        // Set up message handler
        client.onMessageArrived = (message: any) => {
          console.log('Received message:', message.destinationName, message.payloadString)
          
          if (message.destinationName === machineTopic) {
            setMachineState(message.payloadString)
          }
          
          // Count unique machines
          if (message.destinationName.includes('production_machine_state')) {
            setMachineCount(prev => {
              const topicParts = message.destinationName.split('/')
              const foundMachineId = topicParts[3]
              // Simple way to track unique machines - in real app would use Set
              return Math.max(prev, parseInt(foundMachineId.replace('MACHINE_', '')) || 1)
            })
          }
        }

        // Set up connection lost handler
        client.onConnectionLost = (responseObject: any) => {
          if (responseObject.errorCode !== 0) {
            console.log('Connection lost:', responseObject.errorMessage)
            setConnectionStatus('Connection lost')
            setActiveConnections(0)
          }
        }

        // Connect to MQTT broker
        client.connect(connectOptions)

        // Cleanup on component unmount
        return () => {
          if (client && client.isConnected()) {
            client.disconnect()
          }
        }
      } catch (error) {
        console.error('Failed to load MQTT client:', error)
        setConnectionStatus(`Failed to load MQTT: ${error}`)
      }
    }

    connectToMQTT()
  }, [mqttHost, mqttPort, machineTopic, mqttUrl, productionLine])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Navigation */}
      <Navigation 
        connectionStatus={connectionStatus}
      />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4 mt-4">
          <StatusCard
            title="Connection Status"
            value={activeConnections > 0 ? 'Online' : 'Offline'}
            status={activeConnections > 0 ? 'online' : 'offline'}
            icon="🌐"
            subtitle={`${activeConnections} active connection${activeConnections !== 1 ? 's' : ''}`}
          />

          <StatusCard
            title="Active Machines"
            value={machineCount}
            status="online"
            icon="🏭"
            subtitle="Manufacturing units"
          />

          <StatusCard
            title="Primary Machine"
            value={machineState.toUpperCase()}
            status={
              machineState === 'running' ? 'online' :
              machineState === 'idle' ? 'warning' :
              machineState === 'malfunction' ? 'error' :
              'offline'
            }
            icon={
              machineState === 'running' ? '▶️' :
              machineState === 'idle' ? '⏸️' :
              machineState === 'malfunction' ? '⚠️' : '❓'
            }
            subtitle={machineId}
          />

          <StatusCard
            title="Production Line"
            value={productionLine}
            status="online"
            icon="⚙️"
            subtitle="Assembly line"
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-4 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <a 
              href="/production-line"
              className="block p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 hover:shadow-sm transition-all duration-200 group"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3 group-hover:scale-105 transition-transform duration-200">🏭</span>
                <div>
                  <h3 className="font-semibold text-gray-800 text-sm">View Production Line</h3>
                  <p className="text-xs text-gray-600">Visual layout and material flow</p>
                </div>
              </div>
            </a>
            
            <a 
              href="/sensors"
              className="block p-3 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 hover:shadow-sm transition-all duration-200 group"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3 group-hover:scale-105 transition-transform duration-200">📡</span>
                <div>
                  <h3 className="font-semibold text-gray-800 text-sm">Monitor Sensors</h3>
                  <p className="text-xs text-gray-600">Real-time sensor data</p>
                </div>
              </div>
            </a>
          </div>
        </div>

        {/* Configuration Display */}
        <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">System Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-800 mb-2">MQTT Broker</h3>
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex justify-between items-center py-1 border-b border-gray-100">
                  <span className="font-medium">Host:</span>
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{mqttHost}</code>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-gray-100">
                  <span className="font-medium">Port:</span>
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{mqttPort}</code>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="font-medium">Protocol:</span>
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{mqttProtocol}</code>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-800 mb-2">Production Configuration</h3>
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex justify-between items-center py-1 border-b border-gray-100">
                  <span className="font-medium">Production Line:</span>
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{productionLine}</code>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-gray-100">
                  <span className="font-medium">Primary Machine:</span>
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{machineId}</code>
                </div>
                <div className="flex justify-between items-start py-2">
                  <span className="font-medium">Topic:</span>
                  <code className="bg-gray-100 px-3 py-1 rounded-md font-mono text-xs max-w-xs break-all text-right">
                    {machineTopic}
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
