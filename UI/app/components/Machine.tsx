import React from 'react'

interface MachineProps {
  id: string
  name: string
  state: string
  phase: string
  currentPart: string | null
  position: { x: number; y: number }
  sensors?: Record<string, any>
}

const Machine: React.FC<MachineProps> = ({ 
  id, 
  name, 
  state, 
  phase, 
  currentPart, 
  position,
  sensors 
}) => {
  // State color mapping
  const getStateColor = (state: string) => {
    switch (state.toLowerCase()) {
      case 'running':
        return 'bg-green-500'
      case 'idle':
        return 'bg-blue-500'
      case 'malfunction':
      case 'error':
        return 'bg-red-500'
      case 'maintenance':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  // Phase color mapping
  const getPhaseColor = (phase: string) => {
    switch (phase.toLowerCase()) {
      case 'loading':
      case 'preparation':
        return 'bg-orange-400'
      case 'processing':
      case 'assembling':
      case 'fastening':
        return 'bg-blue-400'
      case 'inspecting':
      case 'measuring':
        return 'bg-purple-400'
      case 'unloading':
      case 'sorting':
        return 'bg-indigo-400'
      default:
        return 'bg-gray-400'
    }
  }

  return (
    <div 
      className="absolute transform -translate-x-1/2 -translate-y-1/2 z-10"
      style={{ left: position.x, top: position.y }}
    >
      {/* Machine Body */}
      <div className={`
        w-44 h-44 rounded-lg border-2 border-gray-800 shadow-lg
        ${getStateColor(state)} bg-opacity-90 backdrop-blur-sm
        relative overflow-hidden
      `}>
        {/* Machine Header */}
        <div className="bg-gray-800 text-white p-2">
          <div className="flex justify-between items-center">
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold text-white truncate pr-2" title={name}>
                {name}
              </div>
            </div>
          </div>
        </div>
        
        {/* Machine Content */}
        <div className="p-3 h-full">
          {/* State Indicator */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-800 text-xs font-medium">Status:</span>
            <span className="bg-white bg-opacity-90 text-gray-800 px-2 py-1 rounded text-xs font-bold">
              {state.toUpperCase()}
            </span>
          </div>
          
          {/* Phase Indicator */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-800 text-xs font-medium">Phase:</span>
            <span className={`
              ${getPhaseColor(phase)} text-white px-2 py-1 rounded text-xs font-medium
            `}>
              {phase}
            </span>
          </div>
          
          {/* Current Part */}
          <div className="text-gray-800 text-xs">
            <div className="font-medium mb-1">Current Part:</div>
            <div className="bg-white bg-opacity-20 rounded px-2 py-1 text-center font-mono text-xs">
              {currentPart || 'No Part'}
            </div>
          </div>
        </div>
        
        {/* Status Pulse Animation */}
        {state === 'running' && (
          <div className="absolute inset-0 border-4 border-green-300 rounded-lg animate-pulse opacity-50"></div>
        )}
      </div>
    </div>
  )
}

export default Machine
