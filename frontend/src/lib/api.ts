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
  actual_people: number
  rssi_mean: number
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
