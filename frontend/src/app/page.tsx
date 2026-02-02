'use client'

import { useEffect, useState } from 'react'
import {
  getLatestDetection,
  getRoomLayout,
  getWallHeatmap,
  calibrateRoomLayout,
  RoomLayout,
  DetectionData
} from '@/lib/api'
import { RoomLayoutVisualization, WallHeatmap, Room3DView } from '@/components/room'

type TabValue = 'people' | 'layout' | 'heatmap' | '3d'

export default function HomePage() {
  const [detection, setDetection] = useState<DetectionData | null>(null)
  const [roomLayout, setRoomLayout] = useState<RoomLayout | null>(null)
  const [wallProbabilities, setWallProbabilities] = useState<number[][] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [activeTab, setActiveTab] = useState<TabValue>('people')
  const [calibrating, setCalibrating] = useState(false)

  // Ensure we only run on client side
  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    // Only run on client side after mounting
    if (!mounted) {
      return
    }

    // Poll for detection updates every 5 seconds
    const fetchDetection = async () => {
      try {
        setLoading(false)
        const data = await getLatestDetection()
        if (data) {
          setDetection(data)
          setConnected(true)
          setError(null)
        } else {
          setError('Waiting for detection data...')
          setConnected(false)
        }
      } catch (err) {
        setError('Failed to connect to backend')
        setConnected(false)
        console.error('Fetch error:', err)
      }
    }

    fetchDetection()
    const interval = setInterval(fetchDetection, 5000)

    return () => clearInterval(interval)
  }, [mounted])

  // Fetch room layout data when switching to layout tabs
  useEffect(() => {
    if (!mounted) return

    const fetchRoomData = async () => {
      if (activeTab === 'layout' || activeTab === '3d') {
        const layout = await getRoomLayout()
        setRoomLayout(layout)
      }
      if (activeTab === 'heatmap') {
        const heatmap = await getWallHeatmap()
        setWallProbabilities(heatmap)
      }
    }

    fetchRoomData()
  }, [activeTab, mounted])

  const handleCalibrate = async () => {
    setCalibrating(true)
    const result = await calibrateRoomLayout()
    if (result.success) {
      // Fetch updated data
      const layout = await getRoomLayout()
      setRoomLayout(layout)
      const heatmap = await getWallHeatmap()
      setWallProbabilities(heatmap)
    }
    setCalibrating(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connecting to Detection System</h2>
          <p className="text-gray-600">Initializing WiFi detection...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">WiFi People Detection System</h1>
              <p className="text-gray-600 mt-1">Real-time occupancy detection using WiFi signal analysis</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleCalibrate}
                disabled={calibrating}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {calibrating ? 'Calibrating...' : 'Calibrate Room'}
              </button>
              <div className={`px-4 py-2 rounded-full text-sm font-medium ${
                connected ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {connected ? '✓ System Online' : '⚠ Connecting...'}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-2xl shadow-lg p-2 mb-8">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveTab('people')}
              className={`flex-1 min-w-[150px] px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'people'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              👥 People Detection
            </button>
            <button
              onClick={() => setActiveTab('layout')}
              className={`flex-1 min-w-[150px] px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'layout'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              📐 Room Layout
            </button>
            <button
              onClick={() => setActiveTab('heatmap')}
              className={`flex-1 min-w-[150px] px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'heatmap'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🌡️ Wall Heatmap
            </button>
            <button
              onClick={() => setActiveTab('3d')}
              className={`flex-1 min-w-[150px] px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === '3d'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🏗️ 3D View
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="mb-8">
          {/* People Detection Tab */}
          {activeTab === 'people' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Detection Table */}
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Detection Summary</h2>

                {detection ? (
                  <div className="overflow-hidden">
                    <table className="w-full">
                      <tbody className="divide-y divide-gray-200">
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Presence</td>
                          <td className="py-4 px-4 text-right">
                            <span className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-bold ${
                              detection.presence
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {detection.presence ? '👥 Detected' : '🏠 Empty'}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">People Count</td>
                          <td className="py-4 px-4 text-right">
                            <span className="text-4xl font-bold text-blue-600">
                              {detection.count}
                            </span>
                            <span className="text-gray-500 ml-2">people</span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Count Confidence</td>
                          <td className="py-4 px-4 text-right">
                            <span className="text-2xl font-bold text-green-600">
                              {Math.round(detection.count_confidence * 100)}%
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Presence Confidence</td>
                          <td className="py-4 px-4 text-right">
                            <span className="text-2xl font-bold text-purple-600">
                              {Math.round(detection.presence_confidence * 100)}%
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Signal Strength (RSSI)</td>
                          <td className="py-4 px-4 text-right">
                            <span className="text-2xl font-bold text-orange-600">
                              {detection.rssi_mean?.toFixed(1) ?? 'N/A'} dBm
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Scenario</td>
                          <td className="py-4 px-4 text-right">
                            <span className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full font-medium">
                              {detection.scenario}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Actual People</td>
                          <td className="py-4 px-4 text-right">
                            <span className="text-2xl font-bold text-gray-900">
                              {detection.actual_people ?? 'N/A'}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td className="py-4 px-4 text-gray-600 font-medium">Last Updated</td>
                          <td className="py-4 px-4 text-right text-sm text-gray-500">
                            {new Date(detection.timestamp).toLocaleString()}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mb-4"></div>
                    <p className="text-gray-600">Waiting for detection data...</p>
                  </div>
                )}
              </div>

              {/* Room Visualization */}
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Room Overview</h2>

                {/* Room Visual */}
                <div className="relative bg-gray-100 rounded-xl p-8" style={{ height: '400px' }}>
                  {/* Room Border */}
                  <div className="absolute inset-4 border-4 border-gray-300 rounded-lg"></div>

                  {/* WiFi Detectors */}
                  <div className="absolute top-8 left-8 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg" title="Detector 1">
                    D1
                  </div>
                  <div className="absolute top-8 right-8 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg" title="Detector 2">
                    D2
                  </div>
                  <div className="absolute bottom-8 left-8 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg" title="Detector 3">
                    D3
                  </div>
                  <div className="absolute bottom-8 right-8 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg" title="Detector 4">
                    D4
                  </div>

                  {/* People Indicators */}
                  {detection && detection.presence && detection.count > 0 && (
                    <>
                      {Array.from({ length: detection.count }).map((_, i) => {
                        // Distribute people across the room based on count
                        const positions = [
                          { top: '30%', left: '40%' },
                          { top: '50%', left: '60%' },
                          { top: '60%', left: '35%' },
                          { top: '40%', left: '55%' },
                          { top: '70%', left: '50%' },
                        ]
                        const pos = positions[i % positions.length]
                        const offset = (i * 15) % 30

                        return (
                          <div
                            key={i}
                            className="absolute animate-pulse"
                            style={{
                              top: `calc(${pos.top} + ${offset}px)`,
                              left: `calc(${pos.left} + ${offset}px)`,
                            }}
                          >
                            <div className="flex flex-col items-center">
                              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white shadow-lg border-3 border-white">
                                <span className="text-2xl">👤</span>
                              </div>
                              <span className="mt-1 text-xs font-medium text-gray-700 bg-white px-2 py-1 rounded shadow">
                                Person {i + 1}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </>
                  )}

                  {/* Empty Room Message */}
                  {(!detection || !detection.presence || detection.count === 0) && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-6xl mb-4">🏠</div>
                        <p className="text-gray-500 text-lg">Room Empty</p>
                      </div>
                    </div>
                  )}

                  {/* Legend */}
                  <div className="absolute bottom-2 left-2 right-2 flex justify-center space-x-4 text-xs">
                    <div className="flex items-center bg-white px-3 py-1 rounded-full shadow">
                      <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
                      <span>WiFi Detector</span>
                    </div>
                    <div className="flex items-center bg-white px-3 py-1 rounded-full shadow">
                      <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                      <span>Detected Person</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Room Layout Tab */}
          {activeTab === 'layout' && (
            <RoomLayoutVisualization layout={roomLayout} loading={false} />
          )}

          {/* Wall Heatmap Tab */}
          {activeTab === 'heatmap' && (
            <WallHeatmap probabilities={wallProbabilities} loading={false} />
          )}

          {/* 3D View Tab */}
          {activeTab === '3d' && (
            <Room3DView layout={roomLayout} loading={false} />
          )}
        </div>

        {/* System Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-blue-800">
            <div>
              <p className="font-medium">Backend API:</p>
              <p className="text-blue-700">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
            </div>
            <div>
              <p className="font-medium">API Documentation:</p>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-700 underline hover:text-blue-900"
              >
                View API Docs →
              </a>
            </div>
            <div>
              <p className="font-medium">Update Rate:</p>
              <p className="text-blue-700">Every 5 seconds</p>
            </div>
            <div>
              <p className="font-medium">Status:</p>
              <p className={connected ? 'text-green-700' : 'text-yellow-700'}>
                {connected ? '● Connected' : '○ Connecting...'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
