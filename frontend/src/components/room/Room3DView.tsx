'use client'

import { Suspense, useEffect, useRef, useState } from 'react'
import { RoomLayout } from '@/types/room-layout'

interface Room3DViewProps {
  layout: RoomLayout | null
  loading?: boolean
}

// Simple 3D renderer without Three.js dependency
export function Room3DView({ layout, loading = false }: Room3DViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [rotation, setRotation] = useState({ x: -0.5, y: 0.5 })
  const [zoom, setZoom] = useState(1)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [hoveredWall, setHoveredWall] = useState<number | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !layout) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Camera parameters
    const fov = 60
    const cameraDistance = 15 / zoom

    // 3D to 2D projection
    const project3D = (x: number, y: number, z: number) => {
      // Rotate around X axis
      const cosX = Math.cos(rotation.x)
      const sinX = Math.sin(rotation.x)
      const y1 = y * cosX - z * sinX
      const z1 = y * sinX + z * cosX

      // Rotate around Y axis
      const cosY = Math.cos(rotation.y)
      const sinY = Math.sin(rotation.y)
      const x2 = x * cosY + z1 * sinY
      const z2 = -x * sinY + z1 * cosY + cameraDistance

      // Perspective projection
      const scale = fov / z2
      return {
        x: canvas.width / 2 + x2 * scale * 20,
        y: canvas.height / 2 - y1 * scale * 20,
        z: z2,
        scale
      }
    }

    const roomWidth = layout.dimensions.width
    const roomLength = layout.dimensions.length
    const roomHeight = 3 // Standard room height

    // Draw floor grid
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 0.5
    const gridSize = 1
    for (let x = 0; x <= roomWidth; x += gridSize) {
      const start = project3D(x - roomWidth / 2, 0, 0)
      const end = project3D(x - roomWidth / 2, 0, roomLength)
      ctx.beginPath()
      ctx.moveTo(start.x, start.y)
      ctx.lineTo(end.x, end.y)
      ctx.stroke()
    }
    for (let z = 0; z <= roomLength; z += gridSize) {
      const start = project3D(-roomWidth / 2, 0, z)
      const end = project3D(roomWidth / 2, 0, z)
      ctx.beginPath()
      ctx.moveTo(start.x, start.y)
      ctx.lineTo(end.x, end.y)
      ctx.stroke()
    }

    // Draw walls as 3D boxes
    layout.walls.forEach((wall, index) => {
      const isHovered = hoveredWall === index

      const dx = wall.end.x - wall.start.x
      const dy = wall.end.y - wall.start.y
      const length = Math.sqrt(dx * dx + dy * dy)
      const angle = Math.atan2(dy, dx)

      // Material colors
      const materialColors: Record<string, { top: string; side: string }> = {
        'concrete': { top: '#9ca3af', side: '#6b7280' },
        'brick': { top: '#d97706', side: '#b45309' },
        'drywall': { top: '#f3f4f6', side: '#d1d5db' },
        'glass': { top: '#bfdbfe', side: '#93c5fd' },
        'wood': { top: '#b45309', side: '#92400e' },
        'metal': { top: '#d1d5db', side: '#9ca3af' },
      }
      const colors = materialColors[wall.material] || materialColors['concrete']

      // Draw wall faces (simplified as a thick plane)
      const thickness = wall.thickness || 0.2

      // Wall vertices
      const x1 = wall.start.x - roomWidth / 2
      const z1 = wall.start.y
      const x2 = wall.end.x - roomWidth / 2
      const z2 = wall.end.y

      // Top face corners
      const topFace = [
        project3D(x1, roomHeight, z1),
        project3D(x2, roomHeight, z2),
        project3D(x2, roomHeight, z2),
        project3D(x1, roomHeight, z1),
      ]

      // Side face corners
      const sideFace = [
        project3D(x1, 0, z1),
        project3D(x2, 0, z2),
        project3D(x2, roomHeight, z2),
        project3D(x1, roomHeight, z1),
      ]

      // Draw top face
      if (topFace[0].z > 0 && topFace[2].z > 0) {
        ctx.fillStyle = isHovered ? '#3b82f6' : colors.top
        ctx.beginPath()
        ctx.moveTo(topFace[0].x, topFace[0].y)
        for (let i = 1; i < topFace.length; i++) {
          ctx.lineTo(topFace[i].x, topFace[i].y)
        }
        ctx.closePath()
        ctx.fill()
        ctx.strokeStyle = isHovered ? '#1e40af' : '#374151'
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // Draw side face
      if (sideFace[0].z > 0 && sideFace[2].z > 0) {
        ctx.fillStyle = colors.side
        ctx.beginPath()
        ctx.moveTo(sideFace[0].x, sideFace[0].y)
        for (let i = 1; i < sideFace.length; i++) {
          ctx.lineTo(sideFace[i].x, sideFace[i].y)
        }
        ctx.closePath()
        ctx.fill()
        ctx.strokeStyle = '#374151'
        ctx.lineWidth = 1
        ctx.stroke()
      }

      // Draw wall label if hovered
      if (isHovered) {
        const midX = (wall.start.x + wall.end.x) / 2 - roomWidth / 2
        const midZ = (wall.start.y + wall.end.y) / 2
        const midY = roomHeight / 2

        const proj = project3D(midX, midY, midZ)
        if (proj.z > 0) {
          ctx.save()
          ctx.translate(proj.x, proj.y)

          const text = `${wall.material}`
          ctx.font = 'bold 12px sans-serif'
          const textMetrics = ctx.measureText(text)
          const padding = 6

          ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
          ctx.beginPath()
          ctx.roundRect(
            -textMetrics.width / 2 - padding,
            -12 - padding,
            textMetrics.width + 2 * padding,
            16 + 2 * padding,
            4
          )
          ctx.fill()

          ctx.fillStyle = 'white'
          ctx.textAlign = 'center'
          ctx.fillText(text, 0, 0)
          ctx.restore()
        }
      }
    })

    // Draw corners as spheres
    layout.corners.forEach((corner) => {
      const x = corner.x - roomWidth / 2
      const z = corner.y
      const y = 0

      const proj = project3D(x, y, z)
      if (proj.z > 0) {
        const radius = 0.2 * proj.scale * 20
        ctx.beginPath()
        ctx.arc(proj.x, proj.y, radius, 0, Math.PI * 2)
        ctx.fillStyle = '#ef4444'
        ctx.fill()
        ctx.strokeStyle = '#dc2626'
        ctx.lineWidth = 1
        ctx.stroke()
      }
    })

    // Draw detector positions
    const detectors = [
      { id: 'D1', x: 0, z: 0 },
      { id: 'D2', x: roomWidth, z: 0 },
      { id: 'D3', x: 0, z: roomLength },
      { id: 'D4', x: roomWidth, z: roomLength },
    ]

    detectors.forEach((detector) => {
      const x = detector.x - roomWidth / 2
      const z = detector.z
      const y = 0

      const proj = project3D(x, y, z)
      if (proj.z > 0) {
        const radius = 0.3 * proj.scale * 20

        // Detector circle
        ctx.beginPath()
        ctx.arc(proj.x, proj.y, radius, 0, Math.PI * 2)
        ctx.fillStyle = '#3b82f6'
        ctx.fill()
        ctx.strokeStyle = '#1e40af'
        ctx.lineWidth = 2
        ctx.stroke()

        // Detector label
        ctx.fillStyle = 'white'
        ctx.font = 'bold 11px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(detector.id, proj.x, proj.y)
      }
    })

    // Draw room info overlay
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
    ctx.fillRect(10, 10, 180, 90)
    ctx.fillStyle = 'white'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`Room: ${roomWidth}m × ${roomLength}m × ${roomHeight}m`, 20, 30)
    ctx.fillText(`Walls: ${layout.walls.length}`, 20, 50)
    ctx.fillText(`Area: ${layout.area.toFixed(1)} m²`, 20, 70)
    ctx.fillText(`Corners: ${layout.corners.length}`, 20, 90)
  }, [layout, rotation, zoom, hoveredWall])

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    setDragStart({ x: e.clientX, y: e.clientY })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      const deltaX = e.clientX - dragStart.x
      const deltaY = e.clientY - dragStart.y

      setRotation((prev) => ({
        x: prev.x + deltaY * 0.01,
        y: prev.y + deltaX * 0.01,
      }))

      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    setZoom((prev) => Math.max(0.5, Math.min(3, prev + (e.deltaY > 0 ? -0.1 : 0.1))))
  }

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading 3D view...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!layout) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="text-6xl mb-4">🏗️</div>
            <p className="text-gray-600">No 3D data available</p>
            <p className="text-sm text-gray-500 mt-2">Run calibration to generate 3D room model</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">3D Room View</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setRotation({ x: -0.5, y: 0.5 })}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
          >
            Reset View
          </button>
          <button
            onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            +
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            -
          </button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          className="w-full cursor-move bg-gradient-to-b from-gray-50 to-gray-100"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        />
      </div>

      {/* Controls Info */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-50 rounded-lg p-3">
          <h3 className="font-semibold text-gray-900 mb-2">Controls</h3>
          <ul className="text-gray-600 space-y-1">
            <li>🖱️ Drag to rotate</li>
            <li>🔍 Scroll to zoom</li>
            <li>📍 Hover walls for info</li>
          </ul>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <h3 className="font-semibold text-gray-900 mb-2">Legend</h3>
          <div className="space-y-1">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span className="text-gray-600">WiFi Detector</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
              <span className="text-gray-600">Corner</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-600 mr-2"></div>
              <span className="text-gray-600">Wall</span>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <h3 className="font-semibold text-gray-900 mb-2">View Info</h3>
          <div className="text-gray-600 space-y-1">
            <p>Zoom: {zoom.toFixed(1)}x</p>
            <p>Rotation X: {(rotation.x * 180 / Math.PI).toFixed(0)}°</p>
            <p>Rotation Y: {(rotation.y * 180 / Math.PI).toFixed(0)}°</p>
          </div>
        </div>
      </div>

      {/* Room Dimensions */}
      {layout && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-blue-600">
                {layout.dimensions.width.toFixed(1)}m
              </p>
              <p className="text-sm text-gray-600">Width</p>
            </div>
            <div>
              <p className="text-xl font-bold text-blue-600">
                {layout.dimensions.length.toFixed(1)}m
              </p>
              <p className="text-sm text-gray-600">Length</p>
            </div>
            <div>
              <p className="text-xl font-bold text-blue-600">3.0m</p>
              <p className="text-sm text-gray-600">Height</p>
            </div>
            <div>
              <p className="text-xl font-bold text-blue-600">
                {layout.area.toFixed(1)} m²
              </p>
              <p className="text-sm text-gray-600">Area</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
