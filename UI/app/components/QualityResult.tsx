import React from 'react'

interface QualityResultProps {
  position: { x: number; y: number }
  lastPart: string | null
  qualityResult: string | null
  timestamp?: string
  machinePhase?: string
}

export default function QualityResult({ position, lastPart, qualityResult, timestamp, machinePhase }: QualityResultProps) {
  const getQualityColor = (result: string | null, phase?: string): string => {
    // If machine is not in idle or sorting phase, show inspecting state
    if (phase && phase !== 'idle') {
      return 'bg-yellow-100 border-yellow-300 text-yellow-800'
    }
    
    switch (result?.toLowerCase()) {
      case 'ok':
      case 'pass':
      case 'good':
        return 'bg-green-100 border-green-300 text-green-800'
      case 'nok':
      case 'fail':
      case 'bad':
      case 'reject':
        return 'bg-red-100 border-red-300 text-red-800'
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800'
    }
  }

  const getQualityIcon = (result: string | null, phase?: string): string => {
    // If machine is not in idle or sorting phase, show inspecting icon
    if (phase && phase !== 'idle') {
      return '⏳'
    }
    
    switch (result?.toLowerCase()) {
      case 'ok':
      case 'pass':
      case 'good':
        return '✓'
      case 'nok':
      case 'fail':
      case 'bad':
      case 'reject':
        return '✗'
      default:
        return '—'
    }
  }

  const getQualityLabel = (result: string | null, phase?: string): string => {
    // If machine is not in idle or sorting phase, show WAIT
    if (phase && phase !== 'idle') {
      return 'WAIT'
    }
    
    return result?.toUpperCase() || 'PENDING'
  }

  return (
    <div
      className="absolute z-20 transform -translate-x-1/2 -translate-y-1/2 group"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className={`w-16 h-32 rounded-lg border-2 shadow-lg flex flex-col items-center justify-center ${getQualityColor(qualityResult, machinePhase)}`}>
        {/* Quality Icon */}
        <div className="text-3xl font-bold mb-2">
          {getQualityIcon(qualityResult, machinePhase)}
        </div>
        
        {/* Quality Status */}
        <div className="text-sm font-semibold text-center mb-2">
          {getQualityLabel(qualityResult, machinePhase)}
        </div>
        
        {/* Part ID (multiline instead of truncating) */}
        {lastPart && (
          <div className="text-xs text-center opacity-90 px-1 leading-tight break-all" title={lastPart}>
            {lastPart}
          </div>
        )}
      </div>
      
      {/* Tooltip on hover */}
      <div className="invisible group-hover:visible absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-black text-white text-sm rounded-lg whitespace-nowrap z-30">
        <div className="font-semibold">Quality Inspection</div>
        <div>Part: {lastPart || 'None'}</div>
        <div>Result: {getQualityLabel(qualityResult, machinePhase)}</div>
        {timestamp && (
          <div className="text-xs opacity-75">
            {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}
        
        {/* Arrow pointing up */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-black"></div>
      </div>
    </div>
  )
}
