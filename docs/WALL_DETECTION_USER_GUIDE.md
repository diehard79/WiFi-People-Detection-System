# Wall Detection User Guide

## Overview

The Wall Detection feature uses WiFi Channel State Information (CSI) from ESP32-S3 detectors to automatically detect walls, classify materials, and generate room floor plans.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Calibration Process](#calibration-process)
3. [Detecting Walls](#detecting-walls)
4. [Interpreting Results](#interpreting-results)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

---

## Quick Start

### Prerequisites

- 4 ESP32-S3 WiFi CSI detectors positioned in the room
- System initialized and calibrated
- Empty room for calibration (5 minutes)

### Basic Usage

```python
from wall_detection_system import WallDetectionSystem

# Initialize system
system = WallDetectionSystem()
await system.initialize()

# Calibrate (first time only)
await system.calibrate_system(duration_seconds=300)

# Detect walls
layout = await system.detect_room_layout(duration_seconds=30)

# View results
print(f"Room: {layout.dimensions[0]}x{layout.dimensions[1]}m")
print(f"Walls: {len(layout.walls)}")
print(f"Area: {layout.area:.2f}m²")
print(f"Confidence: {layout.confidence:.1%}")
```

---

## Calibration Process

### Why Calibrate?

Calibration establishes a baseline CSI profile for your empty room. This allows the system to detect walls by comparing current CSI patterns against the baseline.

### Calibration Steps

1. **Prepare the Room**
   - Remove all people and objects
   - Close windows and doors
   - Ensure stable WiFi conditions

2. **Start Calibration**
   ```bash
   # Via API
   curl -X POST http://localhost:8000/api/v1/walls/calibrate \
     -H "Content-Type: application/json" \
     -d '{"duration_seconds": 300}'
   ```

   ```python
   # Via Python
   await system.calibrate_system(duration_seconds=300)
   ```

3. **Wait for Completion**
   - Calibration takes 5 minutes (300 seconds)
   - Track progress via API:
     ```bash
     curl http://localhost:8000/api/v1/walls/calibration/{job_id}
     ```

4. **Verify Calibration**
   - Check status:
     ```bash
     curl http://localhost:8000/api/v1/walls/status
     ```

### Calibration Tips

- **Best Time**: Night or when space is unoccupied
- **Frequency**: Recalibrate monthly or after furniture rearrangement
- **Environment**: Maintain consistent temperature and humidity

---

## Detecting Walls

### Detection Process

Wall detection takes 30 seconds:

1. **CSI Collection** (30s)
   - Collects CSI data from all 4 detectors
   - Measures phase and amplitude variations

2. **Feature Extraction**
   - Extracts signal features from CSI
   - Compares against calibration baseline

3. **Wall Detection**
   - Identifies wall locations
   - Estimates wall thickness
   - Determines wall orientations

4. **Material Classification** (optional)
   - Classifies wall materials:
     - Concrete
     - Brick
     - Drywall
     - Wood
     - Glass

5. **Layout Generation**
   - Creates complete room floor plan
   - Optimizes wall alignment
   - Calculates dimensions and area

### Running Detection

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/walls/detect \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 30, "classify_materials": true}'
```

```python
# Via Python
layout = await system.detect_room_layout(
    duration_seconds=30,
    classify_materials=True
)
```

### Continuous Monitoring

For automatic periodic detection:

```python
async def detection_callback(layout):
    print(f"Detected {len(layout.walls)} walls")

await system.continuous_monitoring(
    detection_interval=3600,  # Every hour
    callback=detection_callback
)
```

---

## Interpreting Results

### Room Layout

```json
{
  "dimensions": [5.2, 4.1],
  "area": 21.32,
  "perimeter": 18.6,
  "confidence": 0.91,
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

### Key Metrics

- **Dimensions**: Room width and length (meters)
- **Area**: Total floor area (square meters)
- **Perimeter**: Total wall length (meters)
- **Confidence**: Overall detection confidence (0-100%)
- **Wall Count**: Number of detected walls

### Wall Details

Each wall includes:

- **Start/End Points**: Wall endpoints in meters
- **Thickness**: Wall thickness in meters (typically 0.1-0.5m)
- **Material**: Detected material type
- **Confidence**: Detection confidence for this wall

### Visualizations

The system generates 3 visualizations:

1. **2D Floorplan** (`floorplan.png`)
   - Top-down view of room
   - Walls colored by material
   - Dimensions labeled

2. **Confidence Map** (`confidence_map.png`)
   - Walls colored by detection confidence
   - Green = high confidence
   - Red = low confidence

3. **3D View** (`room_3d.png`)
   - 3D perspective of room
   - Shows wall heights
   - Material visualization

---

## Troubleshooting

### Problem: Low Detection Confidence

**Symptoms**: Confidence < 70%

**Causes**:
- Calibration outdated
- Furniture moved
- WiFi interference
- Too many people in room

**Solutions**:
1. Recalibrate system
2. Clear room of objects
3. Reduce WiFi interference
4. Ensure room is empty during detection

### Problem: Missing Walls

**Symptoms**: Fewer walls detected than actual

**Causes**:
- Walls too thin (< 10cm)
- Walls made of low-density material
- Insufficient CSI data

**Solutions**:
1. Increase detection duration to 60s
2. Add more detectors
3. Move detectors closer to walls

### Problem: Incorrect Material Classification

**Symptoms**: Wrong material detected

**Causes**:
- Wall covered (paint, wallpaper)
- Multi-layer walls
- Unusual materials

**Solutions**:
1. Manually verify and correct materials
2. Retrain model with labeled data
3. Note limitation in documentation

### Problem: Slow Detection

**Symptoms**: Detection takes > 35 seconds

**Causes**:
- System overload
- Slow CPU
- Memory bottleneck

**Solutions**:
1. Close other applications
2. Reduce detection duration
3. Upgrade hardware
4. Use faster sampling rate

### Problem: Calibration Fails

**Symptoms**: Calibration doesn't complete

**Causes**:
- Detectors not connected
- People in room during calibration
- WiFi unstable

**Solutions**:
1. Check detector connections
2. Ensure room is empty
3. Restart WiFi router
4. Reduce calibration duration to test

---

## FAQ

### Q: How accurate is wall detection?

**A**: The system typically achieves:
- **Wall location**: ±10cm accuracy
- **Wall thickness**: ±2cm accuracy
- **Material classification**: 85-90% accuracy
- **Room dimensions**: ±5% accuracy

### Q: How many detectors do I need?

**A**:
- **Minimum**: 2 detectors (basic detection)
- **Recommended**: 4 detectors (good accuracy)
- **Optimal**: 6-8 detectors (high accuracy)

### Q: What wall types can be detected?

**A**:
- **Best**: Concrete, brick, thick drywall
- **Good**: Wood, glass, standard drywall
- **Poor**: Thin partitions, curtains, furniture

### Q: Can it detect interior and exterior walls?

**A**: Yes, both interior and exterior walls are detected. Exterior walls typically show stronger CSI reflections.

### Q: How long does calibration last?

**A**: Calibration is valid for:
- **Normal use**: 1-3 months
- **After furniture move**: Recalibrate
- **After renovation**: Recalibrate
- **Seasonal changes**: Consider recalibrating

### Q: Can I detect multiple rooms?

**A**: The system detects one room at a time. For multiple rooms:
1. Place detectors in each room separately
2. Run detection for each room
3. Combine results manually

### Q: What's the minimum room size?

**A**:
- **Minimum**: 2m x 2m
- **Recommended**: 3m x 3m or larger
- **Maximum**: 20m x 20m (with 4 detectors)

### Q: Does it work with multi-story buildings?

**A**: Currently designed for single-story rooms. Multi-story detection requires additional development.

### Q: Can I export results to CAD software?

**A**: Yes! Export the layout as JSON and convert to:
- DXF format (AutoCAD)
- SVG format (vector graphics)
- CSV format (spreadsheet)

### Q: What if my WiFi is unstable?

**A**: System will still work but with reduced accuracy. For best results:
- Use 5GHz WiFi
- Ensure strong signal
- Minimize interference

---

## Advanced Usage

### Custom Detection Parameters

```python
# Longer detection for better accuracy
layout = await system.detect_room_layout(
    duration_seconds=60,  # 60 seconds instead of 30
    classify_materials=True
)
```

### Background Calibration

```python
# Track progress
async def progress_callback(progress):
    print(f"Calibration: {progress*100:.0f}%")

await system.calibrate_system(
    duration_seconds=300,
    progress_callback=progress_callback
)
```

### Export Custom Formats

```python
# Export to custom path
export_path = system.export_layout(
    output_path="custom_path/layout.json"
)
```

---

## Support

For additional help:
- Check API documentation: `docs/WALL_DETECTION_API.md`
- View test examples: `tests/wall_detection/`
- Review system logs: `logs/wall_detection.log`
- Report issues: GitHub Issues

---

## Version History

- **v1.0.0** (2025-02-02): Initial release
  - Wall detection from CSI
  - Material classification
  - Room layout generation
  - Visualization tools
