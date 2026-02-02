'use client'

import { useEffect, useRef, useState } from 'react'
import { RoomLayout, DetectorPosition } from '@/types/room-layout'

interface RoomLayoutVisualizationProps {
  layout: RoomLayout | null
  detectors?: DetectorPosition[]
  loading?: boolean
}

export function RoomLayoutVisualization({
  layout,
  detectors = [],
  loading = false
}: RoomLayoutVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [hoveredWall, setHoveredWall] = useState<number | null>(null)

  // Default detector positions if not provided
  const defaultDetectors: DetectorPosition[] = detectors.length > 0 ? detectors : [
    { id: 'D1', x: 10, y: 10, active: true },
    { id: 'D2', x: 90, y: 10, active: true },
    { id: 'D3', x: 10, y: 90, active: true },
    { id: 'D4', x: 90, y: 90, active: true },
  ]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !layout) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Apply transformations
    ctx.save()
    ctx.translate(offset.x, offset.y)
    ctx.scale(scale, scale)

    const padding = 40
    const drawWidth = canvas.width - 2 * padding
    const drawHeight = canvas.height - 2 * padding

    // Calculate scale to fit room in canvas
    const roomWidth = layout.dimensions.width
    const roomLength = layout.dimensions.length
    const scaleX = drawWidth / roomWidth
    const scaleY = drawHeight / roomLength
    const canvasScale = Math.min(scaleX, scaleY) * 0.8

    // Center the room
    const centerX = padding + drawWidth / 2
    const centerY = padding + drawHeight / 2

    ctx.translate(centerX, centerY)
    ctx.scale(canvasScale, canvasScale)
    ctx.translate(-roomWidth / 2, -roomLength / 2)

    // Draw grid
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 0.5 / canvasScale
    const gridSize = 1 // 1 meter grid
    for (let x = 0; x <= roomWidth; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, roomLength)
      ctx.stroke()
    }
    for (let y = 0; y <= roomLength; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(roomWidth, y)
      ctx.stroke()
    }

    // Draw walls
    layout.walls.forEach((wall, index) => {
      const isHovered = hoveredWall === index

      // Wall color based on material
      const materialColors: Record<string, string> = {
        'concrete': '#6b7280',
        'brick': '#b45309',
        'drywall': '#d1d5db',
        'glass': '#93c5fd',
        'wood': '#92400e',
        'metal': '#9ca3af',
      }

      ctx.strokeStyle = materialColors[wall.material] || '#6b7280'
      ctx.lineWidth = (wall.thickness || 0.2)
      ctx.lineCap = 'round'

      // Highlight hovered wall
      if (isHovered) {
        ctx.shadowColor = '#3b82f6'
        ctx.shadowBlur = 10 / canvasScale
        ctx.strokeStyle = '#3b82f6'
        ctx.lineWidth *= 1.5
      } else {
        ctx.shadowBlur = 0
      }

      // Draw wall segment
      ctx.beginPath()
      ctx.moveTo(wall.start.x, wall.start.y)
      ctx.lineTo(wall.end.x, wall.end.y)
      ctx.stroke()

      // Reset shadow
      ctx.shadowBlur = 0

      // Draw wall label if hovered
      if (isHovered) {
        const midX = (wall.start.x + wall.end.x) / 2
        const midY = (wall.start.y + wall.end.y) / 2

        ctx.save()
        ctx.translate(midX, midY)
        ctx.scale(1 / canvasScale, 1 / canvasScale)

        // Draw tooltip background
        const text = `${wall.material} (${(wall.thickness * 100).toFixed(0)}cm) - ${(wall.confidence * 100).toFixed(0)}%`
        ctx.font = '12px sans-serif'
        const textMetrics = ctx.measureText(text)
        const padding = 6
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
        ctx.beginPath()
        ctx.roundRect(
          -textMetrics.width / 2 - padding,
          -20 - padding,
          textMetrics.width + 2 * padding,
          16 + 2 * padding,
          4
        )
        ctx.fill()

        // Draw text
        ctx.fillStyle = 'white'
        ctx.textAlign = 'center'
        ctx.fillText(text, 0, -12)
        ctx.restore()
      }
    })

    // Draw corners
    ctx.fillStyle = '#ef4444'
    layout.corners.forEach((corner) => {
      ctx.beginPath()
      ctx.arc(corner.x, corner.y, 0.15 / canvasScale, 0, Math.PI * 2)
      ctx.fill()
    })

    // Draw detectors
    defaultDetectors.forEach((detector) => {
      const x = (detector.x / 100) * roomWidth
      const y = (detector.y / 100) * roomLength

      // Detector circle
      ctx.beginPath()
      ctx.arc(x, y, 0.3 / canvasScale, 0, Math.PI * 2)
      ctx.fillStyle = detector.active ? '#3b82f6' : '#9ca3af'
      ctx.fill()
      ctx.strokeStyle = '#1e40af'
      ctx.lineWidth = 0.1 / canvasScale
      ctx.stroke()

      // Detector label
      ctx.save()
      ctx.translate(x, y)
      ctx.scale(1 / canvasScale, 1 / canvasScale)
      ctx.fillStyle = 'white'
      ctx.font = 'bold 11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(detector.id, 0, 0)
      ctx.restore()
    })

    // Draw dimensions
    ctx.save()
    ctx.scale(1 / canvasScale, 1 / canvasScale)
    ctx.fillStyle = '#374151'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'center'

    // Width dimension
    ctx.fillText(`${layout.dimensions.width.toFixed(1)}m`, 0, -25)

    // Length dimension
    ctx.save()
    ctx.translate(-roomWidth * canvasScale / 2 - 25, 0)
    ctx.rotate(-Math.PI / 2)
    ctx.fillText(`${layout.dimensions.length.toFixed(1)}m`, 0, 0)
    ctx.restore()

    ctx.restore()

    // Draw area
    ctx.fillStyle = '#374151'
    ctx.font = 'bold 16px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(`Area: ${layout.area.toFixed(1)} m²`, 0, roomLength * canvasScale / 2 + 40)

    ctx.restore()
  }, [layout, scale, offset, hoveredWall, defaultDetectors])

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setScale((prev) => Math.max(0.5, Math.min(3, prev * delta)))
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    } else if (layout) {
      // Check for wall hover
      const canvas = canvasRef.current
      if (!canvas) return

      const rect = canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      // Convert to canvas coordinates
      const canvasX = (x - offset.x) / scale
      const canvasY = (y - offset.y) / scale

      // Simple distance check for each wall
      let foundWall: number | null = null
      layout.walls.forEach((wall, index) => {
        const dist = pointToLineDistance(
          canvasX,
          canvasY,
          wall.start.x,
          wall.start.y,
          wall.end.x,
          wall.end.y
        )
        if (dist < 10) {
          foundWall = index
        }
      })

      setHoveredWall(foundWall)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
    setHoveredWall(null)
  }

  const pointToLineDistance = (
    px: number,
    py: number,
    x1: number,
    y1: number,
    x2: number,
    y2: number
  ) => {
    const A = px - x1
    const B = py - y1
    const C = x2 - x1
    const D = y2 - y1

    const dot = A * C + B * D
    const lenSq = C * C + D * D
    let param = -1
    if (lenSq !== 0) param = dot / lenSq

    let xx, yy

    if (param < 0) {
      xx = x1
      yy = y1
    } else if (param > 1) {
      xx = x2
      yy = y2
    } else {
      xx = x1 + param * C
      yy = y1 + param * D
    }

    const dx = px - xx
    const dy = py - yy
    return Math.sqrt(dx * dx + dy * dy)
  }

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading room layout...</p>
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
            <div className="text-6xl mb-4">📐</div>
            <p className="text-gray-600">No room layout data available</p>
            <p className="text-sm text-gray-500 mt-2">Run calibration to detect walls</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Room Layout</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setScale((s) => Math.min(3, s * 1.2))}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            +
          </button>
          <button
            onClick={() => setScale((s) => Math.max(0.5, s * 0.8))}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            -
          </button>
          <button
            onClick={() => {
              setScale(1)
              setOffset({ x: 0, y: 0 })
            }}
            className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          className="w-full cursor-move"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        />
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
          <span className="text-gray-700">WiFi Detector</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
          <span className="text-gray-700">Corner</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-gray-600 mr-2"></div>
          <span className="text-gray-700">Wall</span>
        </div>
        <div className="flex items-center">
          <div className="text-xs text-gray-500">
            Hover walls for details • Drag to pan • Scroll to zoom
          </div>
        </div>
      </div>

      {/* Wall Materials Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Wall Materials</h3>
        <div className="flex flex-wrap gap-3 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-500 mr-1"></div>
            <span>Concrete</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-amber-700 mr-1"></div>
            <span>Brick</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-300 mr-1"></div>
            <span>Drywall</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-300 mr-1"></div>
            <span>Glass</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-amber-800 mr-1"></div>
            <span>Wood</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-400 mr-1"></div>
            <span>Metal</span>
          </div>
        </div>
      </div>

      {/* Room Info */}
      {layout && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {layout.dimensions.width.toFixed(1)}m
              </p>
              <p className="text-sm text-gray-600">Width</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {layout.dimensions.length.toFixed(1)}m
              </p>
              <p className="text-sm text-gray-600">Length</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
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
