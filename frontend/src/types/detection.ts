export interface DetectionData {
  timestamp: string
  presence: boolean
  presence_confidence: number
  count: number
  count_confidence: number
  scenario: string
  features: Record<string, number>
}

export interface DetectionHistory {
  time: string
  count: number
  presence: boolean
}

export interface WebSocketMessage {
  type: 'detection_update' | 'error' | 'status'
  data: DetectionData | string
}
