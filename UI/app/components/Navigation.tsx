'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface NavigationProps {
  connectionStatus?: string
  lastUpdate?: string
  className?: string
}

const Navigation: React.FC<NavigationProps> = ({ 
  connectionStatus, 
  lastUpdate, 
  className = '' 
}) => {
  const pathname = usePathname()
  
  const navigationItems = [
    { 
      href: '/', 
      label: 'Dashboard', 
      icon: '📊',
      description: 'System overview'
    },
    { 
      href: '/production-line', 
      label: 'Production Line', 
      icon: '🏭',
      description: 'Visual layout'
    },
    { 
      href: '/sensors', 
      label: 'Sensors', 
      icon: '�',
      description: 'Real-time monitoring'
    }
  ]

  const getBreadcrumbs = () => {
    switch (pathname) {
      case '/':
        return [{ label: 'Dashboard', href: '/' }]
      case '/production-line':
        return [
          { label: 'Dashboard', href: '/' },
          { label: 'Production Line', href: '/production-line' }
        ]
      case '/sensors':
        return [
          { label: 'Dashboard', href: '/' },
          { label: 'Sensors', href: '/sensors' }
        ]
      default:
        return [{ label: 'Dashboard', href: '/' }]
    }
  }

  const getPageInfo = () => {
    switch (pathname) {
      case '/':
        return {
          title: 'Production Line Simulator Dashboard',
          subtitle: 'Real-time monitoring and visualization of Assembly_Line_A'
        }
      case '/production-line':
        return {
          title: 'Production Line Monitor',
          subtitle: 'Real-time visualization of Assembly_Line_A manufacturing process'
        }
      case '/sensors':
        return {
          title: 'Sensor & Actuator Monitor',
          subtitle: 'Real-time monitoring of machine sensors and actuators'
        }
      default:
        return {
          title: 'Production Line Simulator',
          subtitle: 'Industrial manufacturing simulation'
        }
    }
  }

  const breadcrumbs = getBreadcrumbs()
  const pageInfo = getPageInfo()

  return (
    <div className={`bg-white border-b border-gray-200 sticky top-0 z-50 ${className}`}>
      {/* Main Navigation Bar */}
      <div className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo/Brand */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PS</span>
              </div>
              <span className="font-semibold text-lg">Plant Simulator</span>
            </div>

            {/* Navigation Items */}
            <nav className="flex space-x-1">
              {navigationItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200
                    ${pathname === item.href 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : 'text-gray-300 hover:text-white hover:bg-gray-800'
                    }
                  `}
                >
                  <span className="text-lg">{item.icon}</span>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{item.label}</span>
                    <span className="text-xs opacity-75">{item.description}</span>
                  </div>
                </Link>
              ))}
            </nav>

            {/* Connection Status */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus?.includes('Connected') 
                    ? 'bg-green-400' 
                    : connectionStatus?.includes('Error') || connectionStatus?.includes('Failed')
                    ? 'bg-red-400'
                    : 'bg-yellow-400 animate-pulse'
                }`}></div>
                <span className="text-sm text-gray-300">
                  {connectionStatus?.includes('Connected') ? 'Online' : 
                   connectionStatus?.includes('Error') ? 'Offline' : 'Connecting'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Breadcrumbs and Page Header */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        {/* Breadcrumbs */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-3">
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.href}>
              {index > 0 && <span className="text-gray-400">/</span>}
              <Link 
                href={crumb.href}
                className={`
                  ${index === breadcrumbs.length - 1 
                    ? 'text-gray-900 font-medium' 
                    : 'hover:text-gray-900 transition-colors'
                  }
                `}
              >
                {crumb.label}
              </Link>
            </React.Fragment>
          ))}
        </nav>

        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              {pageInfo.title}
            </h1>
            <p className="text-sm text-gray-600">
              {pageInfo.subtitle}
            </p>
          </div>

          {/* Status and Last Update */}
          {(connectionStatus || lastUpdate) && (
            <div className="text-right">
              {connectionStatus && (
                <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                  connectionStatus.includes('Connected') 
                    ? 'bg-green-100 text-green-800' 
                    : connectionStatus.includes('Error') || connectionStatus.includes('Failed')
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus.includes('Connected') 
                      ? 'bg-green-500' 
                      : connectionStatus.includes('Error') || connectionStatus.includes('Failed')
                      ? 'bg-red-500'
                      : 'bg-yellow-500'
                  }`}></div>
                  <span className="font-medium">
                    {connectionStatus.includes('Connected') ? 'Online' : 
                     connectionStatus.includes('Error') ? 'Offline' : 'Connecting'}
                  </span>
                </div>
              )}
              {lastUpdate && (
                <div className="text-xs text-gray-500 mt-1">
                  Last update: {new Date(lastUpdate).toLocaleTimeString()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Navigation
