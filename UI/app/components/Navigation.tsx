'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface NavigationProps {
  className?: string
  showReturnButton?: boolean
}

const Navigation: React.FC<NavigationProps> = ({ className = '', showReturnButton = false }) => {
  const pathname = usePathname()

  const navigationItems = [
    { href: '/', label: 'Overview', icon: '📊' },
    { href: '/production-line', label: 'Production Line', icon: '🏭' },
    { href: '/sensors', label: 'Sensors', icon: '📡' }
  ]

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  return (
    <nav className={`${className}`}>
      {showReturnButton && pathname !== '/' && (
        <div className="mb-4 p-4">
          <Link 
            href="/" 
            className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200"
          >
            <span>←</span>
            <span>Back to Main</span>
          </Link>
        </div>
      )}

      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        {navigationItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium
              transition-all duration-200 ease-in-out
              ${isActive(item.href)
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
              }
            `}
          >
            <span className="text-lg">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  )
}

export default Navigation
