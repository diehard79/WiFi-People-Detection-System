# Wall Detection Integration Guide

## Overview

This guide covers integration of the Wall Detection System into the existing WiFi People Detection application.

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│           WiFi Detection System                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  People Detection (Existing)                     │  │
│  │  - RSSI Collection                               │  │
│  │  - People Counting                               │  │
│  │  - Presence Detection                            │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Wall Detection (New)                             │  │
│  │  - CSI Collection (ESP32-S3)                     │  │
│  │  - Wall Detection                                │  │
│  │  - Material Classification                       │  │
│  │  - Room Layout Mapping                           │  │
│  │  - Visualization                                 │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Shared Components                                │  │
│  │  - API Server (FastAPI)                           │  │
│  │  - WebSocket (Real-time Updates)                  │  │
│  │  - Database (Detection History)                   │  │
│  │  - Monitoring (Prometheus)                        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### 1. Update Requirements

Add to `requirements.txt`:

```txt
# Wall Detection Dependencies
scipy>=1.10.0
matplotlib>=3.7.0
psutil>=5.9.0
```

### 2. Update API Server

In `src/api.py`, add wall detection initialization:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    global wifi_sim, signal_processor, ml_models

    logger.info("Starting WiFi People Detection API")

    # Initialize existing components
    wifi_sim = WiFiRSSISimulator(num_detectors=4)
    signal_processor = SignalProcessor()
    ml_models = PeopleDetectorML()
    ml_models.load_models()

    # Initialize wall detection (NEW)
    try:
        from src.wall_detection_api import initialize_wall_detection_api
        await initialize_wall_detection_api(app)
        logger.info("Wall detection initialized")
    except Exception as e:
        logger.warning(f"Wall detection initialization failed: {e}")

    # Start background simulation
    asyncio.create_task(simulate_continuous_detection())

    logger.info("Startup complete")
```

### 3. Update Frontend

Add wall detection UI components to frontend:

```javascript
// Wall detection service
class WallDetectionService {
  async detectWalls(duration = 30) {
    const response = await fetch('/api/v1/walls/detect', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        duration_seconds: duration,
        classify_materials: true
      })
    });
    return response.json();
  }

  async getCalibrationStatus(jobId) {
    const response = await fetch(`/api/v1/walls/calibration/${jobId}`);
    return response.json();
  }

  async getLayout() {
    const response = await fetch('/api/v1/walls/layout');
    return response.json();
  }
}
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Wall Detection Configuration
ENABLE_WALL_DETECTION=true
WALL_NUM_DETECTORS=4
WALL_SAMPLING_RATE=10
WALL_CALIBRATION_TIME=300
WALL_DETECTION_DURATION=30
WALL_MODEL_DIR=models/wall_detection
WALL_OUTPUT_DIR=wall_detection_output
```

### Docker Configuration

Update `docker-compose.yml` (already created):

- Added wall detection environment variables
- Added volume mounts for models and outputs
- Added health checks
- Added monitoring (Prometheus, Grafana)

---

## API Integration

### New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/walls/status` | GET | Get wall detection status |
| `/api/v1/walls/detect` | POST | Trigger wall detection |
| `/api/v1/walls/calibrate` | POST | Start calibration |
| `/api/v1/walls/calibration/{job_id}` | GET | Get calibration status |
| `/api/v1/walls/layout` | GET | Get current layout |
| `/api/v1/walls/visualizations` | GET | Get visualizations |
| `/api/v1/walls/export` | POST | Export layout |

### WebSocket Events

New WebSocket events for real-time updates:

- `calibration_progress`: Calibration progress updates
- `detection_complete`: Wall detection completion
- `wall_detection_error`: Error events

---

## Database Schema

### New Tables

```sql
-- Wall detection history
CREATE TABLE wall_detections (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    dimensions JSONB,
    area FLOAT,
    perimeter FLOAT,
    confidence FLOAT,
    wall_count INTEGER,
    layout_data JSONB,
    visualizations JSONB
);

-- Calibration history
CREATE TABLE wall_calibrations (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    status VARCHAR(50),
    samples_collected INTEGER
);

-- Wall detections (individual walls)
CREATE TABLE detected_walls (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER REFERENCES wall_detections(id),
    start_x FLOAT,
    start_y FLOAT,
    end_x FLOAT,
    end_y FLOAT,
    thickness FLOAT,
    material VARCHAR(50),
    confidence FLOAT
);
```

---

## Monitoring

### Prometheus Metrics

Add to Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'wall_detection'
    static_configs:
      - targets: ['wifi-detection:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Import dashboard JSON from:
`config/grafana/dashboards/wall_detection.json`

Metrics to track:
- Detection success rate
- Average processing time
- Average confidence
- Memory usage
- CPU usage
- Calibration count

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/wall_detection/test_wall_detection.py -v

# E2E tests
pytest tests/wall_detection/test_wall_detection_e2e.py -v

# All tests
pytest tests/wall_detection/ -v
```

### Test Coverage

```bash
pytest tests/wall_detection/ --cov=src/wall_detection --cov-report=html
```

---

## Deployment

### Production Deployment

1. **Build Docker Image**
   ```bash
   docker-compose build
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize Wall Detection**
   ```bash
   curl -X POST http://localhost:8000/api/v1/walls/calibrate \
     -H "Content-Type: application/json" \
     -d '{"duration_seconds": 300}'
   ```

4. **Verify Health**
   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/api/v1/walls/status
   ```

### Rollback Procedure

If issues occur:

1. **Disable Wall Detection**
   ```bash
   # Set environment variable
   ENABLE_WALL_DETECTION=false
   ```

2. **Restart Services**
   ```bash
   docker-compose restart wifi-detection
   ```

3. **Verify People Detection Still Works**
   ```bash
   curl http://localhost:8000/api/v1/detection/latest
   ```

---

## Troubleshooting

### Issue: Wall Detection Slows Down People Detection

**Solution**:
- Run wall detection less frequently
- Use separate processes for wall and people detection
- Add queue system for wall detection requests

### Issue: High Memory Usage

**Solution**:
- Reduce model complexity
- Clear visualization cache
- Limit detection history

### Issue: Calibration Fails

**Solution**:
- Check detector connections
- Ensure room is empty
- Reduce calibration duration for testing
- Check WiFi stability

---

## Performance Tuning

### Optimization Strategies

1. **Reduce Detection Duration**
   - Default: 30 seconds
   - Fast: 10 seconds (lower accuracy)
   - High quality: 60 seconds (better accuracy)

2. **Adjust Sampling Rate**
   - Default: 10 Hz
   - Fast: 5 Hz (lower CPU)
   - High quality: 20 Hz (higher CPU)

3. **Disable Material Classification**
   - Saves ~20% processing time
   - Reduces model complexity

4. **Use Caching**
   - Cache layouts for same room
   - Cache visualization results

---

## Security Considerations

1. **API Authentication**
   - Add API key authentication
   - Rate limit wall detection endpoints

2. **Data Privacy**
   - CSI data may reveal room structure
   - Encrypt stored layouts
   - Anonymize detection data

3. **Access Control**
   - Restrict who can trigger calibration
   - Limit access to exported layouts

---

## Maintenance

### Regular Tasks

1. **Recalibrate Monthly**
   - Room conditions change over time
   - Furniture rearrangements affect CSI

2. **Clean Up Old Data**
   - Remove old visualizations (> 30 days)
   - Archive old detection records

3. **Monitor Performance**
   - Check processing time trends
   - Monitor confidence scores
   - Review error logs

4. **Update Models**
   - Retrain with new data
   - Improve accuracy over time

---

## Future Enhancements

### Planned Features

1. **Multi-Room Detection**
   - Detect multiple rooms simultaneously
   - Generate complete floor plans

2. **Real-Time Wall Detection**
   - Continuous wall monitoring
   - Detect structural changes

3. **Integration with Smart Home**
   - Automatic room mapping
   - Furniture detection
   - Occupancy heat maps

4. **Advanced Analytics**
   - Room usage patterns
   - Traffic flow analysis
   - Space optimization

---

## Support

For issues or questions:
- Documentation: `docs/WALL_DETECTION_USER_GUIDE.md`
- API Reference: `docs/WALL_DETECTION_API.md`
- Tests: `tests/wall_detection/`
- Logs: `logs/wall_detection.log`

---

## Changelog

### v1.0.0 (2025-02-02)
- Initial wall detection integration
- CSI data collection from ESP32-S3
- Wall detection ML models
- Material classification
- Room layout mapping
- Visualization tools
- API endpoints
- Monitoring and logging
- Comprehensive testing
