/**
 * Application constants
 */

export const DEFAULT_ROOM_ID = 'default-room'

export const WEBSOCKET_RECONNECT_DELAY = 1000
export const WEBSOCKET_RECONNECT_ATTEMPTS = 10
export const WEBSOCKET_TIMEOUT = 10000

export const CHART_DATA_POINTS = 60 // 60 minutes of historical data

export const CONFIDENCE_THRESHOLD = 0.5

export const SCENARIOS = {
  EMPTY_ROOM: 'Empty room',
  ONE_PERSON_MOVING: 'One person moving',
  TWO_PEOPLE_TALKING: 'Two people talking',
  THREE_PEOPLE_SITTING: 'Three people sitting',
  MULTIPLE_PEOPLE: 'Multiple people',
} as const

export const SCENARIO_DESCRIPTIONS: Record<string, string> = {
  [SCENARIOS.EMPTY_ROOM]: 'No people detected in the monitored area',
  [SCENARIOS.ONE_PERSON_MOVING]: 'Single person moving in the area',
  [SCENARIOS.TWO_PEOPLE_TALKING]: 'Two people present, minimal movement',
  [SCENARIOS.THREE_PEOPLE_SITTING]: 'Three people present, stationary',
  [SCENARIOS.MULTIPLE_PEOPLE]: 'Multiple people detected in the area',
}

export const REFRESH_INTERVAL = 1000 // 1 second

export const MAX_HISTORY_LENGTH = 100
