# Component Map & Architecture

## Visual Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Page                            │
│                     (src/app/page.tsx)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────── Header ─────────────────┐               │
│  │  Title: WiFi People Detection Dashboard  │               │
│  │  Status: Live/Connected                   │               │
│  └──────────────────────────────────────────┘               │
│                                                               │
│  ┌────────────── StatusBar Component ──────────────┐        │
│  │  • Connection Status (Connected/Disconnected)   │        │
│  │  • Room ID                                      │        │
│  │  • Error Messages (if any)                      │        │
│  └─────────────────────────────────────────────────┘        │
│                                                               │
│  ┌─────────── ScenarioInfo Component ─────────────┐         │
│  │  • Current Scenario Badge                      │         │
│  │  • Scenario Description                        │         │
│  └─────────────────────────────────────────────────┘         │
│                                                               │
│  ┌───────────────── Detection Grid ─────────────────┐       │
│  │                                                    │       │
│  │  ┌──────────────────────┐  ┌─────────────────┐  │       │
│  │  │ PresenceIndicator    │  │  CountGauge     │  │       │
│  │  │                      │  │                 │  │       │
│  │  │ • ✓/✗ Icon           │  │ • People Count  │  │       │
│  │  │ • Status Text        │  │ • Icon Circle   │  │       │
│  │  │ • Confidence Bar     │  │ • Confidence    │  │       │
│  │  └──────────────────────┘  └─────────────────┘  │       │
│  └────────────────────────────────────────────────────┘       │
│                                                               │
│  ┌────────────── DetectionChart Component ──────────┐       │
│  │  • 60-Minute Historical Area Chart               │       │
│  │  • Time vs Count Visualization                   │       │
│  │  • Gradient Fill with Tooltips                   │       │
│  └───────────────────────────────────────────────────┘       │
│                                                               │
│  ┌─────────── TechnicalDetails Component ──────────┐        │
│  │  [Expandable Details Section]                   │        │
│  │  • Timestamp                                    │        │
│  │  • Scenario                                     │        │
│  │  • Feature Vector (Grid)                        │        │
│  │  • Raw JSON Data                                │        │
│  └──────────────────────────────────────────────────┘        │
│                                                               │
│  ┌────────────────── Footer ─────────────────────┐          │
│  │  WiFi People Detection System v1.0.0           │          │
│  └────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    WebSocket Connection                       │
│                    (useWebSocket Hook)                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Backend WebSocket Server                                    │
│         │                                                     │
│         │ socket.io                                          │
│         ↓                                                     │
│  ┌──────────────────────────────────────┐                   │
│  │   useWebSocket Hook                   │                   │
│  │   ┌────────────────────────────────┐ │                   │
│  │   │ Connection State               │ │                   │
│  │   │ • connected                    │ │                   │
│  │   │ • error                        │ │                   │
│  │   │ • socket                       │ │                   │
│  │   └────────────────────────────────┘ │                   │
│  │   ┌────────────────────────────────┐ │                   │
│  │   │ Detection Data                 │ │                   │
│  │   │ • detection (DetectionData)    │ │                   │
│  │   │   - presence                   │ │                   │
│  │   │   - count                      │ │                   │
│  │   │   - confidence                 │ │                   │
│  │   │   - scenario                   │ │                   │
│  │   │   - features                   │ │                   │
│  │   └────────────────────────────────┘ │                   │
│  └──────────────────────────────────────┘                   │
│         │                                                     │
│         │ props                                              │
│         ↓                                                     │
│  ┌──────────────────────────────────────┐                   │
│  │   Page Component                     │                   │
│  │   (src/app/page.tsx)                 │                   │
│  └──────────────────────────────────────┘                   │
│         │                                                     │
│         │ props distribution                                 │
│         ↓                                                     │
│  ┌──────────────────────────────────────┐                   │
│  │   Child Components                   │                   │
│  │                                      │                   │
│  │  • PresenceIndicator                 │                   │
│  │    - presence: boolean               │                   │
│  │    - confidence: number              │                   │
│  │                                      │                   │
│  │  • CountGauge                        │                   │
│  │    - count: number                   │                   │
│  │    - confidence: number              │                   │
│  │                                      │                   │
│  │  • DetectionChart                    │                   │
│  │    - (internal historical data)      │                   │
│  │                                      │                   │
│  │  • ScenarioInfo                      │                   │
│  │    - scenario: string                │                   │
│  │                                      │                   │
│  │  • StatusBar                         │                   │
│  │    - connected: boolean              │                   │
│  │    - error: string | null            │                   │
│  │    - roomId: string                  │                   │
│  │                                      │                   │
│  │  • TechnicalDetails                  │                   │
│  │    - detection: DetectionData        │                   │
│  └──────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

## Component Props Reference

### Page Component (src/app/page.tsx)
- Uses `useWebSocket('default-room')` hook
- Distributes data to child components
- Manages loading and error states

### PresenceIndicator
```typescript
interface Props {
  presence: boolean       // From detection.presence
  confidence: number      // From detection.presence_confidence
}
```

### CountGauge
```typescript
interface Props {
  count: number          // From detection.count
  confidence: number     // From detection.count_confidence
}
```

### ScenarioInfo
```typescript
interface Props {
  scenario: string       // From detection.scenario
}
```

### StatusBar
```typescript
interface Props {
  connected: boolean     // From socket connection
  error: string | null   // From connection errors
  roomId: string         // Fixed or user-provided
}
```

### TechnicalDetails
```typescript
interface Props {
  detection: DetectionData | null  // Full detection object
}
```

### DetectionChart
```typescript
interface Props {
  // No props - generates internal historical data
}
```

## State Management

```
┌─────────────────────────────────────────────────────────┐
│                  Application State                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  WebSocket State (useWebSocket Hook)                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │ • socket: Socket | null                          │   │
│  │ • connected: boolean                            │   │
│  │ • detection: DetectionData | null               │   │
│  │ • error: string | null                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  Local Component State                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ • roomId: string (fixed in page.tsx)            │   │
│  │ • historical data: DetectionHistory[] (chart)   │   │
│  │ • expanded: boolean (TechnicalDetails)          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Event Flow

```
User Action / System Event
         ↓
┌─────────────────────────────────┐
│  Component Event Handler        │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  State Update (useState)        │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  Re-render with New State       │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  Props Propagation to Children │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  Child Components Update UI     │
└─────────────────────────────────┘
```

## WebSocket Event Handlers

```typescript
// Connection Events
socket.on('connect', handler)          // Connected to server
socket.on('disconnect', handler)       // Disconnected from server
socket.on('connect_error', handler)    // Connection error
socket.on('reconnect', handler)        // Reconnected after loss
socket.on('reconnect_attempt', handler)// Reconnection attempt
socket.on('reconnect_failed', handler) // All attempts failed

// Data Events
socket.on('detection_update', handler) // New detection data

// Client Events (emit)
socket.emit('subscribe', { room_id })  // Subscribe to room
socket.emit('unsubscribe', {})         // Unsubscribe from room
```

## Styling Architecture

```
Global Styles (src/app/globals.css)
  └─ TailwindCSS Directives
      ├─ @tailwind base
      ├─ @tailwind components
      └─ @tailwind utilities

Component-Level Styles
  └─ TailwindCSS Utility Classes
      ├─ Layout (flex, grid, etc.)
      ├─ Spacing (p-6, m-4, etc.)
      ├─ Colors (bg-white, text-gray-900, etc.)
      ├─ Typography (text-lg, font-bold, etc.)
      ├─ Effects (shadow, rounded, etc.)
      └─ Transitions (duration-300, etc.)

Custom Styles
  └─ CSS Variables & Animations
      ├─ :root variables
      └─ @keyframes (pulse-slow)
```

## Type Hierarchy

```
DetectionData (src/types/detection.ts)
  ├─ timestamp: string
  ├─ presence: boolean
  ├─ presence_confidence: number
  ├─ count: number
  ├─ count_confidence: number
  ├─ scenario: string
  └─ features: Record<string, number>

DetectionHistory
  ├─ time: string
  ├─ count: number
  └─ presence: boolean

WebSocketMessage
  ├─ type: 'detection_update' | 'error' | 'status'
  └─ data: DetectionData | string
```

## File Dependencies

```
page.tsx
  ├─ useWebSocket hook
  │   └─ detection types
  ├─ PresenceIndicator component
  ├─ CountGauge component
  ├─ DetectionChart component
  ├─ ScenarioInfo component
  ├─ StatusBar component
  └─ TechnicalDetails component
      └─ detection types

Each component
  └─ detection types (imported from @/types/detection)
```

## Import Paths

```typescript
// Absolute imports (configured in tsconfig.json)
import { useWebSocket } from '@/hooks/useWebSocket'
import { PresenceIndicator } from '@/components/dashboard/PresenceIndicator'
import { DetectionData } from '@/types/detection'
import { formatTimestamp } from '@/lib/utils'

// Relative imports (barrel export)
import { PresenceIndicator, CountGauge } from '@/components/dashboard'
```

This architecture provides a clear separation of concerns, making the codebase maintainable and scalable.
