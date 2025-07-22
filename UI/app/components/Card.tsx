import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'elevated' | 'interactive'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export default function Card({ 
  children, 
  className = '', 
  variant = 'default', 
  size = 'md',
  loading = false 
}: CardProps) {
  const baseClasses = 'bg-white rounded-lg border border-gray-200 transition-all duration-200'
  
  const variantClasses = {
    default: 'shadow-sm',
    elevated: 'shadow-lg',
    interactive: 'shadow-md hover:shadow-lg hover:-translate-y-1 cursor-pointer'
  }
  
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5'
  }
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`
  
  if (loading) {
    return (
      <div className={classes}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    )
  }
  
  return (
    <div className={classes}>
      {children}
    </div>
  )
}

// StatusCard component specifically for dashboard status displays
interface StatusCardProps {
  title: string
  value: string | number
  status?: 'online' | 'offline' | 'warning' | 'error'
  icon?: React.ReactNode
  subtitle?: string
  className?: string
}

export function StatusCard({ 
  title, 
  value, 
  status = 'online', 
  icon, 
  subtitle,
  className = '' 
}: StatusCardProps) {
  const statusColors = {
    online: 'text-success-green border-success-green bg-green-50',
    offline: 'text-gray-500 border-gray-300 bg-gray-50',
    warning: 'text-warning-amber border-warning-amber bg-amber-50',
    error: 'text-danger-red border-danger-red bg-red-50'
  }
  
  const statusDots = {
    online: 'bg-success-green',
    offline: 'bg-gray-400',
    warning: 'bg-warning-amber',
    error: 'bg-danger-red'
  }
  
  return (
    <Card variant="elevated" size="sm" className={`${statusColors[status]} ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-1">
            {icon && <div className="text-base">{icon}</div>}
            <h3 className="text-xs font-medium text-gray-600">{title}</h3>
            <div className={`w-1.5 h-1.5 rounded-full ${statusDots[status]}`}></div>
          </div>
          <div className="text-xl font-bold mb-0.5" style={{ color: 'var(--foreground)' }}>
            {value}
          </div>
          {subtitle && (
            <div className="text-xs text-gray-500">{subtitle}</div>
          )}
        </div>
      </div>
    </Card>
  )
}
