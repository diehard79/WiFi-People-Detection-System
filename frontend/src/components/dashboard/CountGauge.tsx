'use client'

import { Users } from 'lucide-react'

interface CountGaugeProps {
  count: number
  confidence: number
}

export function CountGauge({ count, confidence }: CountGaugeProps) {
  const getColor = (count: number) => {
    if (count === 0) return 'text-gray-400'
    if (count <= 3) return 'text-green-600'
    if (count <= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getBgColor = (count: number) => {
    if (count === 0) return 'bg-gray-400'
    if (count <= 3) return 'bg-green-500'
    if (count <= 6) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 transition-all duration-300 hover:shadow-lg">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">People Count</h3>
      <div className="text-center py-8">
        <div className="mb-4 flex justify-center">
          <div className={`w-20 h-20 rounded-full flex items-center justify-center ${getBgColor(count)} transition-all duration-300`}>
            <Users className="w-10 h-10 text-white" />
          </div>
        </div>
        <div className={`text-7xl font-bold transition-all duration-300 ${getColor(count)}`}>
          {count}
        </div>
        <p className="text-gray-600 mt-2 text-lg">people detected</p>
      </div>
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Confidence:</span>
          <span className="text-sm font-semibold text-gray-900">
            {(confidence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getBgColor(count)}`}
            style={{ width: `${confidence * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}
