'use client'

import { useEffect, useState } from 'react'

// Paho MQTT Client type definitions
declare global {
  interface Window {
    Paho: any;
  }
}

export default function Home() {
  const [machineState, setMachineState] = useState<string>('connecting...')
  const [connectionStatus, setConnectionStatus] = useState<string>('Connecting to MQTT...')

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
        const client = new PahoMQTT.Client(mqttHost, mqttPort, 'nextjs-client-' + Math.random().toString(16).substr(2, 8))

        // Set up connection options
        const connectOptions = {
          onSuccess: () => {
            console.log(`Connected to MQTT broker at ${mqttUrl}`)
            setConnectionStatus('Connected to MQTT')
            
            // Subscribe to the machine state topic
            try {
              client.subscribe(machineTopic)
              console.log(`Subscribed to topic: ${machineTopic}`)
              setConnectionStatus('Subscribed to machine state')
            } catch (err) {
              console.error('Failed to subscribe:', err)
              setConnectionStatus('Failed to subscribe to topic')
            }
          },
          onFailure: (responseObject: any) => {
            console.error('Failed to connect:', responseObject.errorMessage)
            setConnectionStatus(`Connection failed: ${responseObject.errorMessage}`)
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
        }

        // Set up connection lost handler
        client.onConnectionLost = (responseObject: any) => {
          if (responseObject.errorCode !== 0) {
            console.log('Connection lost:', responseObject.errorMessage)
            setConnectionStatus('Connection lost')
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
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Production Line Monitor
        </h1>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            MACHINE_001 - Material Preparation Station
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Connection Status
              </label>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                connectionStatus.includes('Connected') 
                  ? 'bg-green-100 text-green-800' 
                  : connectionStatus.includes('Error') || connectionStatus.includes('Failed')
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {connectionStatus}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Machine State
              </label>
              <div className={`inline-flex items-center px-4 py-2 rounded-lg text-lg font-semibold ${
                machineState === 'running' 
                  ? 'bg-green-100 text-green-800 border border-green-200' 
                  : machineState === 'idle'
                  ? 'bg-blue-100 text-blue-800 border border-blue-200'
                  : machineState === 'malfunction' || machineState === 'error'
                  ? 'bg-red-100 text-red-800 border border-red-200'
                  : machineState === 'maintenance'
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                  : 'bg-gray-100 text-gray-800 border border-gray-200'
              }`}>
                {machineState.toUpperCase()}
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium text-gray-800 mb-2">Configuration</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>MQTT Broker:</span>
                  <code className="bg-white p-1 rounded border">{mqttUrl}</code>
                </div>
                <div className="flex justify-between">
                  <span>MQTT Topic:</span>
                  <code className="bg-white p-1 rounded border text-xs">{machineTopic}</code>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 text-center text-gray-500 text-sm">
          Real-time data from Production Line Simulator
        </div>
      </div>
    </div>
  )
}
