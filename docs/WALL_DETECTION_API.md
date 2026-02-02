# Wall Detection API Documentation

## Base URL

```
http://localhost:8000/api/v1/walls
```

## Authentication

Currently no authentication required. Future versions will include API key authentication.

---

## Endpoints

### 1. Get System Status

Get current wall detection system status.

**Endpoint**: `GET /status`

**Response**:
```json
{
  "initialized": true,
  "calibrating": false,
  "current_layout": {
    "dimensions": [5.2, 4.1],
    "area": 21.32,
    "confidence": 0.91,
    "wall_count": 4
  },
  "last_detection": "2025-02-02T10:30:00",
  "metrics": {
    "detection_count": 15,
    "total_confidence": 13.5,
    "avg_processing_time": 8.2,
    "calibration_count": 2
  }
}
```

**Status Codes**:
- `200 OK`: Success
- `500 Internal Server Error`: Server error

---

### 2. Detect Walls

Trigger wall detection. Takes 30 seconds for data collection and processing.

**Endpoint**: `POST /detect`

**Request Body**:
```json
{
  "duration_seconds": 30,
  "classify_materials": true
}
```

**Parameters**:
- `duration_seconds` (integer, required): CSI collection duration (10-300 seconds)
- `classify_materials` (boolean, optional): Enable material classification (default: true)

**Response**:
```json
{
  "status": "success",
  "layout": {
    "dimensions": [5.2, 4.1],
    "area": 21.32,
    "perimeter": 18.6,
    "confidence": 0.91,
    "wall_count": 4,
    "walls": [
      {
        "start": [0.0, 0.0],
        "end": [5.2, 0.0],
        "thickness": 0.2,
        "material": "concrete",
        "confidence": 0.95
      },
      {
        "start": [5.2, 0.0],
        "end": [5.2, 4.1],
        "thickness": 0.2,
        "material": "brick",
        "confidence": 0.92
      }
    ]
  },
  "visualizations": {
    "floorplan": "/path/to/floorplan.png",
    "confidence": "/path/to/confidence_map.png",
    "3d": "/path/to/room_3d.png"
  },
  "detected_at": "2025-02-02T10:30:00"
}
```

**Status Codes**:
- `200 OK`: Detection successful
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Detection failed

**Error Response**:
```json
{
  "detail": "System not initialized. Call initialize() first."
}
```

---

### 3. Start Calibration

Start background calibration process. Takes 5 minutes with empty room.

**Endpoint**: `POST /calibrate`

**Request Body**:
```json
{
  "duration_seconds": 300
}
```

**Parameters**:
- `duration_seconds` (integer, required): Calibration duration (60-1800 seconds)

**Response**:
```json
{
  "message": "Calibration started",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_time_seconds": 300
}
```

**Status Codes**:
- `200 OK`: Calibration started
- `409 Conflict`: Calibration already in progress
- `400 Bad Request`: Invalid duration
- `500 Internal Server Error`: Failed to start calibration

---

### 4. Get Calibration Status

Check calibration job progress.

**Endpoint**: `GET /calibration/{job_id}`

**Parameters**:
- `job_id` (string, required): Calibration job ID

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45.5,
  "started_at": "2025-02-02T10:25:00",
  "completed_at": null,
  "error": null
}
```

**Status Values**:
- `pending`: Job queued
- `running`: Calibration in progress
- `completed`: Calibration finished successfully
- `failed`: Calibration failed

**Status Codes**:
- `200 OK`: Status retrieved
- `404 Not Found`: Job not found

---

### 5. Get Current Layout

Get the most recently detected room layout.

**Endpoint**: `GET /layout`

**Response**:
```json
{
  "dimensions": [5.2, 4.1],
  "area": 21.32,
  "perimeter": 18.6,
  "confidence": 0.91,
  "wall_count": 4,
  "walls": [
    {
      "start": [0.0, 0.0],
      "end": [5.2, 0.0],
      "thickness": 0.2,
      "material": "concrete",
      "confidence": 0.95
    }
  ],
  "detected_at": "2025-02-02T10:30:00"
}
```

**Status Codes**:
- `200 OK`: Layout retrieved
- `404 Not Found`: No layout detected yet

---

### 6. Get Visualizations

Get paths to all generated visualizations.

**Endpoint**: `GET /visualizations`

**Response**:
```json
{
  "visualizations": {
    "floorplan": "/path/to/floorplan.png",
    "confidence": "/path/to/confidence_map.png",
    "csi_heatmap": "/path/to/csi_heatmap.png",
    "3d": "/path/to/room_3d.png"
  },
  "generated_at": "2025-02-02T10:30:05"
}
```

**Status Codes**:
- `200 OK`: Visualizations retrieved
- `404 Not Found`: No layout detected
- `500 Internal Server Error`: Visualization generation failed

---

### 7. Export Layout

Export current room layout to JSON file.

**Endpoint**: `POST /export`

**Response**:
```json
{
  "message": "Layout exported successfully",
  "path": "/path/to/room_layout_20250202_103000.json"
}
```

**Exported JSON Format**:
```json
{
  "dimensions": [5.2, 4.1],
  "area": 21.32,
  "perimeter": 18.6,
  "confidence": 0.91,
  "detected_at": "2025-02-02T10:30:00",
  "walls": [
    {
      "start": [0.0, 0.0],
      "end": [5.2, 0.0],
      "thickness": 0.2,
      "material": "concrete",
      "confidence": 0.95
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Export successful
- `404 Not Found`: No layout detected
- `500 Internal Server Error`: Export failed

---

## Data Structures

### Wall Object

```typescript
{
  start: [number, number],    // [x, y] start point in meters
  end: [number, number],      // [x, y] end point in meters
  thickness: number,          // Wall thickness in meters
  material: string,           // Material type (nullable)
  confidence: number          // Confidence score (0-1)
}
```

### Room Layout Object

```typescript
{
  dimensions: [number, number],  // [width, length] in meters
  area: number,                  // Area in square meters
  perimeter: number,             // Perimeter in meters
  confidence: number,            // Overall confidence (0-1)
  wall_count: number,            // Number of walls
  walls: Wall[],                 // Array of wall objects
  detected_at: string            // ISO 8601 timestamp
}
```

### Material Types

Supported wall materials:
- `"concrete"`: Concrete walls
- `"brick"`: Brick walls
- `"drywall"`: Drywall/partition walls
- `"wood"`: Wooden walls
- `"glass"`: Glass walls/windows
- `null`: Material not classified

---

## WebSocket Events

### Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/wall-detection');
```

### Events

#### calibration_progress

Progress updates during calibration.

```json
{
  "type": "calibration_progress",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "progress": 45.5,
    "status": "running"
  }
}
```

#### detection_complete

Fired when wall detection completes.

```json
{
  "type": "detection_complete",
  "data": {
    "layout": {
      "dimensions": [5.2, 4.1],
      "wall_count": 4,
      "confidence": 0.91
    },
    "timestamp": "2025-02-02T10:30:00"
  }
}
```

#### error

Error events.

```json
{
  "type": "error",
  "data": {
    "message": "Calibration failed: Room not empty",
    "code": "CALIBRATION_ERROR"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `NOT_INITIALIZED` | System not initialized |
| `CALIBRATION_REQUIRED` | System requires calibration |
| `CALIBRATION_IN_PROGRESS` | Calibration already running |
| `CALIBRATION_FAILED` | Calibration failed |
| `DETECTION_FAILED` | Wall detection failed |
| `NO_LAYOUT` | No layout available |
| `INVALID_PARAMETERS` | Invalid request parameters |
| `INTERNAL_ERROR` | Internal server error |

---

## Rate Limiting

Currently no rate limiting. Future versions will implement:
- Detection endpoint: 10 requests per hour
- Calibration endpoint: 1 request per hour
- Other endpoints: 60 requests per minute

---

## Examples

### Python

```python
import requests
import time

# Initialize
response = requests.get('http://localhost:8000/api/v1/walls/status')
print(response.json())

# Detect walls
response = requests.post(
    'http://localhost:8000/api/v1/walls/detect',
    json={'duration_seconds': 30, 'classify_materials': True}
)
layout = response.json()
print(f"Detected {layout['layout']['wall_count']} walls")

# Get visualizations
response = requests.get('http://localhost:8000/api/v1/walls/visualizations')
viz = response.json()
print(f"Floorplan: {viz['visualizations']['floorplan']}")
```

### JavaScript

```javascript
// Detect walls
const response = await fetch('http://localhost:8000/api/v1/walls/detect', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    duration_seconds: 30,
    classify_materials: true
  })
});

const layout = await response.json();
console.log(`Detected ${layout.layout.wall_count} walls`);

// Get visualizations
const vizResponse = await fetch('http://localhost:8000/api/v1/walls/visualizations');
const viz = await vizResponse.json();
console.log(`Floorplan: ${viz.visualizations.floorplan}`);
```

### cURL

```bash
# Detect walls
curl -X POST http://localhost:8000/api/v1/walls/detect \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 30, "classify_materials": true}'

# Get layout
curl http://localhost:8000/api/v1/walls/layout

# Export layout
curl -X POST http://localhost:8000/api/v1/walls/export
```

---

## Performance

### Expected Response Times

- `GET /status`: < 100ms
- `POST /detect`: 30-35 seconds (includes data collection)
- `POST /calibrate`: Immediate (runs in background)
- `GET /calibration/{job_id}`: < 100ms
- `GET /layout`: < 100ms
- `GET /visualizations`: 1-2 seconds
- `POST /export`: < 500ms

### Resource Usage

- **Memory**: 200-500 MB during detection
- **CPU**: 20-40% during detection
- **Disk**: 10-50 MB for visualizations per detection

---

## SDKs

Official SDKs:
- Python: `pip install wall-detection-client`
- JavaScript: `npm install @wall-detection/client`
- Coming soon: Java, Go, C#

---

## Changelog

### v1.0.0 (2025-02-02)
- Initial release
- All core endpoints available
- WebSocket support
- Export functionality
