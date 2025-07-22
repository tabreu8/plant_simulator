import React from 'react'

interface StatusBadgeProps {
  status: string
  variant?: 'default' | 'large' | 'pill'
  animated?: boolean
  className?: string
}

export default function StatusBadge({ 
  status, 
  variant = 'default', 
  animated = false,
  className = '' 
}: StatusBadgeProps) {
  
  const getStatusConfig = (status: string) => {
    const normalizedStatus = status.toLowerCase()
    
    const configs: Record<string, { color: string; icon: string; pulse: boolean }> = {
      // Machine States
      'running': {
        color: 'bg-green-100 text-green-800 border-green-200',
        icon: '▶️',
        pulse: true
      },
      'idle': {
        color: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: '⏸️',
        pulse: false
      },
      'error': {
        color: 'bg-red-100 text-red-800 border-red-200',
        icon: '❌',
        pulse: true
      },
      'maintenance': {
        color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: '🔧',
        pulse: false
      },
      'stopped': {
        color: 'bg-gray-100 text-gray-800 border-gray-200',
        icon: '⏹️',
        pulse: false
      },
      
      // Connection States
      'online': {
        color: 'bg-green-100 text-green-800 border-green-200',
        icon: '🟢',
        pulse: false
      },
      'offline': {
        color: 'bg-red-100 text-red-800 border-red-200',
        icon: '🔴',
        pulse: false
      },
      'connecting': {
        color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: '🟡',
        pulse: true
      },
      
      // Quality States
      'ok': {
        color: 'bg-green-100 text-green-800 border-green-200',
        icon: '✅',
        pulse: false
      },
      'nok': {
        color: 'bg-red-100 text-red-800 border-red-200',
        icon: '❌',
        pulse: false
      },
      'pending': {
        color: 'bg-gray-100 text-gray-800 border-gray-200',
        icon: '⏳',
        pulse: true
      },
      'wait': {
        color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: '⏳',
        pulse: true
      }
    }
    
    return configs[normalizedStatus] || {
      color: 'bg-gray-100 text-gray-800 border-gray-200',
      icon: '❓',
      pulse: false
    }
  }
  
  const config = getStatusConfig(status)
  
  const variantClasses = {
    default: 'px-2 py-1 text-xs font-medium',
    large: 'px-3 py-2 text-sm font-semibold',
    pill: 'px-3 py-1 text-xs font-medium rounded-full'
  }
  
  const baseClasses = `
    inline-flex items-center gap-1 rounded-md border
    transition-all duration-200
    ${config.color}
    ${variantClasses[variant]}
  `
  
  const pulseClasses = animated && config.pulse ? 'animate-pulse' : ''
  
  return (
    <span className={`${baseClasses} ${pulseClasses} ${className}`}>
      <span className="text-xs">{config.icon}</span>
      <span className="capitalize">{status}</span>
    </span>
  )
}

// Machine Status Badge - specialized for machine states
interface MachineStatusBadgeProps {
  status: string
  phase?: string
  className?: string
}

export function MachineStatusBadge({ status, phase, className = '' }: MachineStatusBadgeProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <StatusBadge status={status} variant="large" animated />
      {phase && phase !== status && (
        <span className="text-xs text-gray-500">
          Phase: <span className="font-medium">{phase}</span>
        </span>
      )}
    </div>
  )
}
