'use client'

import { CheckCircle2, XCircle } from 'lucide-react'

interface PresenceIndicatorProps {
  presence: boolean
  confidence: number
}

export function PresenceIndicator({ presence, confidence }: PresenceIndicatorProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 transition-all duration-300 hover:shadow-lg">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">People Presence</h3>
      <div className="flex items-center justify-center py-8">
        <div className={`text-center transition-all duration-300 ${
          presence ? 'text-green-600' : 'text-gray-400'
        }`}>
          <div className="mb-4 flex justify-center">
            {presence ? (
              <CheckCircle2 className="w-20 h-20 animate-pulse" />
            ) : (
              <XCircle className="w-20 h-20" />
            )}
          </div>
          <p className="text-2xl font-bold">
            {presence ? 'People Detected' : 'No People Detected'}
          </p>
        </div>
      </div>
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Confidence:</span>
          <span className="text-sm font-semibold text-gray-900">
            {(confidence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              presence ? 'bg-green-500' : 'bg-gray-400'
            }`}
            style={{ width: `${confidence * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}
