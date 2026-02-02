'use client'

import { useEffect, useState, useRef } from 'react'

export default function TestWebSocket() {
  const [messages, setMessages] = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const getWsUrl = () => {
      if (typeof window !== 'undefined') {
        const hostname = window.location.hostname
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        return `${wsProtocol}//${hostname}:8000/ws/detection`
      }
      return 'ws://localhost:8000/ws/detection'
    }

    const wsUrl = getWsUrl()
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
      addMessage('✅ Connected to WebSocket server')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('Message received:', data)

        if (data.type === 'connected') {
          addMessage(`📩 Server: ${data.message}`)
        } else if (data.type === 'detection') {
          const det = data.data
          addMessage(`👥 Detection: ${det.count} people (${det.scenario}) - Confidence: ${Math.round(det.count_confidence * 100)}%`)
        }
      } catch (err) {
        addMessage(`❌ Parse error: ${err}`)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      addMessage('❌ WebSocket error occurred')
      setConnected(false)
    }

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      addMessage(`🔌 Disconnected: ${event.code} - ${event.reason}`)
      setConnected(false)
    }

    wsRef.current = ws

    return () => {
      ws.close()
    }
  }, [])

  const addMessage = (msg: string) => {
    setMessages(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`])
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">WebSocket Connection Test</h1>

        <div className="mb-4">
          <div className={`inline-flex items-center px-4 py-2 rounded-full ${connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            <span className="w-3 h-3 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-red-500'}"></span>
            {connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">WebSocket Messages</h2>
            <button
              onClick={clearMessages}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Clear Messages
            </button>
          </div>

          <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {messages.length === 0 ? (
              <p className="text-gray-400">Waiting for messages...</p>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className="mb-1 text-green-400">
                  {msg}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">WebSocket Connection Details:</h3>
          <ul className="list-disc list-inside text-blue-800 space-y-1">
            <li><strong>URL:</strong> ws://localhost:8000/ws/detection</li>
            <li><strong>Status:</strong> {connected ? 'Connected' : 'Disconnected'}</li>
            <li><strong>Backend:</strong> http://localhost:8000</li>
            <li><strong>Frontend:</strong> http://localhost:8080</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
