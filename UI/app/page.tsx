'use client'

import { useEffect, useState } from 'react'
import Navigation from './components/Navigation'

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
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Production Line Simulator Dashboard
              </h1>
              <p className="text-gray-600">
                Real-time monitoring and visualization of {productionLine}
              </p>
            </div>
            
            <div className="text-right">
              <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                connectionStatus.includes('Connected') || connectionStatus.includes('Monitoring')
                  ? 'bg-green-100 text-green-800' 
                  : connectionStatus.includes('Error') || connectionStatus.includes('Failed')
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  connectionStatus.includes('Connected') || connectionStatus.includes('Monitoring') ? 'bg-green-500' : 'bg-yellow-500'
                }`}></div>
                {connectionStatus}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <Navigation />

        {/* System Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Connection Status</p>
                <p className={`text-2xl font-bold ${
                  activeConnections > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {activeConnections > 0 ? 'Online' : 'Offline'}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                activeConnections > 0 ? 'bg-green-100' : 'bg-red-100'
              }`}>
                <span className="text-2xl">
                  {activeConnections > 0 ? '🟢' : '🔴'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Active Machines</p>
                <p className="text-2xl font-bold text-blue-600">{machineCount}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🏭</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Primary Machine</p>
                <p className={`text-2xl font-bold ${
                  machineState === 'running' ? 'text-green-600' :
                  machineState === 'idle' ? 'text-blue-600' :
                  machineState === 'malfunction' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {machineState.toUpperCase()}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                machineState === 'running' ? 'bg-green-100' :
                machineState === 'idle' ? 'bg-blue-100' :
                machineState === 'malfunction' ? 'bg-red-100' :
                'bg-gray-100'
              }`}>
                <span className="text-2xl">
                  {machineState === 'running' ? '▶️' :
                   machineState === 'idle' ? '⏸️' :
                   machineState === 'malfunction' ? '⚠️' : '❓'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Production Line</p>
                <p className="text-2xl font-bold text-purple-600">{productionLine}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">⚙️</span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="/production-line"
              className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
            >
              <div className="flex items-center">
                <span className="text-3xl mr-4">🏭</span>
                <div>
                  <h3 className="font-semibold text-gray-800">View Production Line</h3>
                  <p className="text-sm text-gray-600">Visual layout of machines, buffers, and material flow</p>
                </div>
              </div>
            </a>
            
            <a 
              href="/sensors"
              className="block p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all duration-200"
            >
              <div className="flex items-center">
                <span className="text-3xl mr-4">📡</span>
                <div>
                  <h3 className="font-semibold text-gray-800">Monitor Sensors</h3>
                  <p className="text-sm text-gray-600">Detailed sensor and actuator data for each machine</p>
                </div>
              </div>
            </a>
          </div>
        </div>

        {/* Configuration Display */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">System Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-800 mb-2">MQTT Broker</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Host:</span>
                  <code className="bg-gray-100 p-1 rounded">{mqttHost}</code>
                </div>
                <div className="flex justify-between">
                  <span>Port:</span>
                  <code className="bg-gray-100 p-1 rounded">{mqttPort}</code>
                </div>
                <div className="flex justify-between">
                  <span>Protocol:</span>
                  <code className="bg-gray-100 p-1 rounded">{mqttProtocol}</code>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Production Configuration</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Production Line:</span>
                  <code className="bg-gray-100 p-1 rounded">{productionLine}</code>
                </div>
                <div className="flex justify-between">
                  <span>Primary Machine:</span>
                  <code className="bg-gray-100 p-1 rounded">{machineId}</code>
                </div>
                <div className="flex justify-between">
                  <span>Topic:</span>
                  <code className="bg-gray-100 p-1 rounded text-xs">{machineTopic}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
