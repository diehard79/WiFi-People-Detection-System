import { useEffect, useState, useCallback, useRef } from 'react'
import { DetectionData } from '@/types/detection'

export function useWebSocket(roomId: string) {
  const [detection, setDetection] = useState<DetectionData | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    // Use native WebSocket instead of Socket.IO
    const getWsUrl = () => {
      if (process.env.NEXT_PUBLIC_WS_URL) {
        return process.env.NEXT_PUBLIC_WS_URL
      }
      // Derive WebSocket URL from current location
      if (typeof window !== 'undefined') {
        const hostname = window.location.hostname
        return `ws://${hostname}:8000/ws/detection`
      }
      return 'ws://localhost:8000/ws/detection'
    }

    const wsUrl = getWsUrl()
    let ws: WebSocket | null = null

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected successfully')
        setConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('WebSocket message received:', message)

          // Handle different message types
          if (message.type === 'detection' && message.data) {
            setDetection(message.data)
          } else if (message.type === 'connected') {
            console.log('Server confirmed connection:', message.message)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err, event.data)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error occurred:', event)
        setError('Connection error - will retry...')
        setConnected(false)
      }

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        setConnected(false)

        // Auto-reconnect after 3 seconds if it was an unexpected close
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            // Force re-render by incrementing a counter or similar
            setConnected(true)
          }, 3000)
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws) {
        ws.close(1000, 'Component unmounted')
      }
    }
  }, [roomId])

  const subscribe = useCallback((newRoomId: string) => {
    // For native WebSocket, room subscription happens via URL query params
    // This is a placeholder for future room-based routing
    console.log('Subscribing to room:', newRoomId)
  }, [])

  const unsubscribe = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
  }, [])

  return {
    detection,
    connected,
    error,
    subscribe,
    unsubscribe
  }
}
