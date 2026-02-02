/**
 * API client for backend communication
 */

// Get API base URL dynamically
const getApiBaseUrl = () => {
  // First check environment variable
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  // Client-side: derive from window location
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    return `${protocol}//${hostname}:8000`
  }
  // Server-side fallback (shouldn't be used but needed for SSR)
  return 'http://localhost:8000'
}

// Get WebSocket URL dynamically
const getWsUrl = () => {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL
  }
  // Derive WebSocket URL from frontend location
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    return `ws://${hostname}:8000/ws/detection`
  }
  return 'ws://localhost:8000/ws/detection'
}

export interface DetectionData {
  timestamp: string
  presence: boolean
  presence_confidence: number
  count: number
  count_confidence: number
  scenario: string
  actual_people?: number
  rssi_mean?: number
  features?: Record<string, number>
}

/**
 * Fetch latest detection via REST API
 */
export async function getLatestDetection(): Promise<DetectionData | null> {
  try {
    const API_BASE_URL = getApiBaseUrl()
    const url = `${API_BASE_URL}/api/v1/detection/latest`
    console.log('[API] Fetching from:', url)

    const response = await fetch(url)
    if (!response.ok) {
      console.error('[API] Response not OK:', response.status, response.statusText)
      return null
    }
    const data = await response.json()

    // Check if it's an error message
    if ('message' in data && data.message === 'No detections available yet') {
      return null
    }

    console.log('[API] Successfully fetched detection data')
    return data as DetectionData
  } catch (error) {
    console.error('[API] Failed to fetch detection:', error)
    console.error('[API] Window available:', typeof window !== 'undefined')
    if (typeof window !== 'undefined') {
      console.error('[API] Window location:', window.location.hostname)
    }
    return null
  }
}

/**
 * Test WebSocket connection with detailed logging
 */
export function testWebSocketConnection(): void {
  const WS_URL = getWsUrl()
  console.log('[WebSocket Test] Starting connection test...')
  console.log('[WebSocket Test] URL:', WS_URL)

  const ws = new WebSocket(WS_URL)

  ws.onopen = () => {
    console.log('[WebSocket Test] ✅ Connection successful!')
    console.log('[WebSocket Test] Ready state:', ws.readyState)
  }

  ws.onmessage = (event) => {
    console.log('[WebSocket Test] 📩 Message received:', event.data)
    try {
      const data = JSON.parse(event.data)
      console.log('[WebSocket Test] Parsed data:', data)
    } catch (e) {
      console.log('[WebSocket Test] Raw data (not JSON):', event.data)
    }
  }

  ws.onerror = (error) => {
    console.error('[WebSocket Test] ❌ Error:', error)
    console.error('[WebSocket Test] Ready state:', ws.readyState)
    console.error('[WebSocket Test] URL:', WS_URL)
  }

  ws.onclose = (event) => {
    console.log('[WebSocket Test] 🔌 Connection closed')
    console.log('[WebSocket Test] Close code:', event.code)
    console.log('[WebSocket Test] Close reason:', event.reason)
    console.log('[WebSocket Test] Was clean:', event.wasClean)
  }
}

/**
 * Fetch health status
 */
export async function getHealthStatus(): Promise<{
  status: string
  timestamp: string
  models_loaded: boolean
  simulation_running: boolean
} | null> {
  try {
    const API_BASE_URL = getApiBaseUrl()
    const response = await fetch(`${API_BASE_URL}/api/v1/health`)
    if (!response.ok) {
      return null
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch health:', error)
    return null
  }
}

/**
 * Room layout types
 */
export interface WallSegment {
  start: { x: number; y: number }
  end: { x: number; y: number }
  material: string
  thickness: number
  confidence: number
}

export interface RoomLayout {
  walls: WallSegment[]
  dimensions: { width: number; length: number }
  area: number
  corners: Array<{ x: number; y: number }>
  timestamp: string
}

/**
 * Fetch room layout data
 */
export async function getRoomLayout(): Promise<RoomLayout | null> {
  try {
    const API_BASE_URL = getApiBaseUrl()
    const url = `${API_BASE_URL}/api/v1/room-layout`
    console.log('[API] Fetching room layout from:', url)

    const response = await fetch(url)
    if (!response.ok) {
      console.error('[API] Response not OK:', response.status, response.statusText)
      return null
    }
    const data = await response.json()

    // Check if it's an error message
    if ('message' in data && (data.message === 'No room layout available' || data.detail)) {
      return null
    }

    console.log('[API] Successfully fetched room layout')
    return data as RoomLayout
  } catch (error) {
    console.error('[API] Failed to fetch room layout:', error)
    return null
  }
}

/**
 * Fetch wall detection heatmap
 */
export async function getWallHeatmap(): Promise<number[][] | null> {
  try {
    const API_BASE_URL = getApiBaseUrl()
    const url = `${API_BASE_URL}/api/v1/room-layout/heatmap`
    console.log('[API] Fetching wall heatmap from:', url)

    const response = await fetch(url)
    if (!response.ok) {
      console.error('[API] Response not OK:', response.status, response.statusText)
      return null
    }
    const data = await response.json()

    // Check if it's an error message
    if ('message' in data || 'detail' in data) {
      return null
    }

    console.log('[API] Successfully fetched wall heatmap')
    return data as number[][]
  } catch (error) {
    console.error('[API] Failed to fetch wall heatmap:', error)
    return null
  }
}

/**
 * Trigger room calibration
 */
export async function calibrateRoomLayout(): Promise<{ success: boolean; message?: string }> {
  try {
    const API_BASE_URL = getApiBaseUrl()
    const url = `${API_BASE_URL}/api/v1/room-layout/calibrate`
    console.log('[API] Triggering room calibration:', url)

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      console.log('[API] Calibration successful:', data)
      return { success: true, message: data.message || 'Calibration started' }
    } else {
      const error = await response.json()
      console.error('[API] Calibration failed:', error)
      return { success: false, message: error.detail || error.message || 'Calibration failed' }
    }
  } catch (error) {
    console.error('[API] Failed to calibrate room:', error)
    return { success: false, message: 'Failed to connect to server' }
  }
}
