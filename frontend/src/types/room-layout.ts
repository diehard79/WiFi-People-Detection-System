/**
 * Room layout and wall detection types
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

export interface DetectorPosition {
  id: string
  x: number
  y: number
  active: boolean
}
