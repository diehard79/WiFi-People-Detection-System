'use client'

import { Wifi, WifiOff, AlertCircle } from 'lucide-react'

interface StatusBarProps {
  connected: boolean
  error: string | null
  roomId: string
}

export function StatusBar({ connected, error, roomId }: StatusBarProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {connected ? (
              <>
                <Wifi className="w-5 h-5 text-green-600" />
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  Connected
                </span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-red-600" />
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                  Disconnected
                </span>
              </>
            )}
          </div>

          {/* Room ID */}
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>Room:</span>
            <span className="font-mono font-medium text-gray-900">{roomId}</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
