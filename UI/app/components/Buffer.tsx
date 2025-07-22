import React from 'react'

interface BufferProps {
  id: string
  position: { x: number; y: number }
  parts: string[]
  capacity: number
  orientation?: 'horizontal' | 'vertical'
  showConveyor?: boolean
  conveyorLength?: number
  isActive?: boolean
}

const Buffer: React.FC<BufferProps> = ({ 
  id, 
  position, 
  parts, 
  capacity, 
  orientation = 'horizontal',
  showConveyor = true,
  conveyorLength = 120,
  isActive = false
}) => {
  const isHorizontal = orientation === 'horizontal'
  const utilization = parts.length / capacity
  
  // Buffer utilization color
  const getUtilizationColor = (utilization: number) => {
    if (utilization < 0.3) return 'bg-green-400'
    if (utilization < 0.7) return 'bg-yellow-400'
    if (utilization < 0.9) return 'bg-orange-400'
    return 'bg-red-400'
  }

  return (
    <div 
      className="absolute transform -translate-x-1/2 -translate-y-1/2 z-20"
      style={{ left: position.x, top: position.y }}
    >
      {/* Conveyor Section (Before Buffer) */}
      {showConveyor && (
        <div className={`
          absolute bg-gray-400 border border-gray-500
          ${isHorizontal 
            ? `w-${conveyorLength/4} h-4 -left-${conveyorLength/8} top-6` 
            : `w-4 h-${conveyorLength/4} left-6 -top-${conveyorLength/8}`
          }
          ${isActive ? 'animate-pulse bg-blue-400' : ''}
        `}>
          {/* Conveyor Belt Lines */}
          <div className={`
            absolute inset-0 
            ${isHorizontal ? 'flex flex-col justify-around' : 'flex flex-row justify-around'}
          `}>
            <div className="bg-gray-600 ${isHorizontal ? 'h-0.5 w-full' : 'w-0.5 h-full'}"></div>
            <div className="bg-gray-600 ${isHorizontal ? 'h-0.5 w-full' : 'w-0.5 h-full'}"></div>
          </div>
        </div>
      )}

      {/* Buffer Container */}
      <div className={`
        ${isHorizontal ? 'w-24 h-12' : 'w-16 h-32'}
        border-2 border-gray-600 bg-gray-100 rounded-lg shadow-lg
        relative overflow-visible z-10 flex flex-col
        before:content-[''] before:absolute before:inset-1 before:border before:border-gray-400 before:rounded-md
      `}>
        {/* Buffer Header with Container Styling */}
        <div className="bg-gray-700 text-white text-center py-0.5 text-2xs font-medium relative rounded-t-md">
          <span className="text-2xs">{id.split(' ')[0]}</span>
        </div>
        
        {/* Buffer Slots with Container Look */}
        <div className={`
          p-1 flex bg-gray-50 border border-gray-300 rounded-b-md items-center justify-center overflow-visible
          ${isHorizontal ? 'flex-row gap-1' : 'flex-col gap-1 flex-1'}
        `}>
          {Array.from({ length: capacity }, (_, index) => (
            <div
              key={index}
              className={`
                group relative border-2 rounded-md shadow-sm
                ${index < parts.length 
                  ? 'bg-blue-500 bg-opacity-80 border-blue-600 shadow-blue-200' 
                  : 'bg-gray-200 bg-opacity-60 border-gray-400 border-dashed'
                }
                ${orientation === 'horizontal' ? 'w-6 h-6' : 'w-5 h-5'}
                flex items-center justify-center
                transition-all duration-300 ease-in-out
                hover:scale-110 hover:z-10
                ${index < parts.length ? 'hover:bg-opacity-90 cursor-pointer animate-pulse' : ''}
              `}
              title={index < parts.length ? `Slot ${index + 1}: ${parts[index]}` : `Slot ${index + 1}: Empty`}
            >
              {/* Always show slot number */}
              <div className="text-white text-xs font-bold">
                {index + 1}
              </div>
              
              {/* Show part ID in external tooltip bubble on hover */}
              {index < parts.length && (
                <div 
                  className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-1 rounded-md shadow-xl opacity-0 group-hover:opacity-100 whitespace-nowrap border border-gray-700"
                  style={{ zIndex: 999999 }}
                >
                  <div className="text-center font-medium">
                    {parts[index]}
                  </div>
                  {/* Tooltip arrow */}
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-transparent border-t-gray-900"></div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Utilization Indicator */}
        <div className="absolute top-1 right-1">
          <div className={`
            w-3 h-3 rounded-full ${getUtilizationColor(utilization)}
            border border-gray-600
          `} title={`${parts.length}/${capacity} parts`}>
          </div>
        </div>
      </div>

      {/* Conveyor Section (After Buffer) */}
      {showConveyor && (
        <div className={`
          absolute bg-gray-400 border border-gray-500
          ${isHorizontal 
            ? `w-${conveyorLength/4} h-4 -right-${conveyorLength/8} top-6` 
            : `w-4 h-${conveyorLength/4} left-6 -bottom-${conveyorLength/8}`
          }
          ${isActive ? 'animate-pulse bg-blue-400' : ''}
        `}>
          {/* Conveyor Belt Lines */}
          <div className={`
            absolute inset-0 
            ${isHorizontal ? 'flex flex-col justify-around' : 'flex flex-row justify-around'}
          `}>
            <div className="bg-gray-600 ${isHorizontal ? 'h-0.5 w-full' : 'w-0.5 h-full'}"></div>
            <div className="bg-gray-600 ${isHorizontal ? 'h-0.5 w-full' : 'w-0.5 h-full'}"></div>
          </div>
        </div>
      )}
      
      {/* Parts Count Label */}
      <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 font-medium">
        {parts.length}/{capacity}
      </div>
    </div>
  )
}

export default Buffer
