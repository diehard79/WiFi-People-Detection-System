# Spatial Mapping and Visualization Guide

## Overview

The Spatial Mapping system provides comprehensive room layout detection and visualization capabilities for WiFi-based wall detection. This module converts raw RSSI probability grids into structured architectural layouts with beautiful visualizations.

## Features

### 1. Room Layout Mapper
- **Probability Grid Processing**: Converts 10×10m probability grids into wall segments
- **Computer Vision Pipeline**:
  - Thresholding (>70% probability = wall)
  - Morphological operations (dilation, erosion)
  - Hough transform for line detection
  - Collinear segment merging
  - Corner and intersection detection
- **Material Classification**: Identifies wall materials based on signal attenuation
- **Layout Optimization**: Applies geometric constraints (right angles, parallel walls)
- **Area Calculation**: Computes room area using convex hull

### 2. Wall Visualizer
Multiple visualization formats:
- **Architectural Floorplans**: 2D overhead views with dimensions
- **3D Room Views**: Perspective renderings with material textures
- **Probability Heatmaps**: Color-gradient wall detection maps
- **High-Quality PIL Images**: Professional floorplan graphics
- **SVG Floorplans**: Interactive web-ready vector graphics

### 3. REST API Integration
Complete API endpoints for real-time layout detection and visualization.

## Installation

### Dependencies

Add to `requirements.txt`:
```txt
# Computer Vision & Image Processing
opencv-python>=4.5.0
pillow>=9.0.0
matplotlib>=3.5.0

# SVG Generation
svgwrite>=1.4.0
```

Install:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.spatial_mapper import (
    RoomLayoutMapper,
    WallVisualizer,
    generate_svg_floorplan,
    create_sample_wall_grid
)

# Create sample wall probability grid
wall_grid = create_sample_wall_grid(room_type="rectangular")

# Initialize mapper
mapper = RoomLayoutMapper(room_size=(10.0, 10.0))

# Define detector positions
detector_positions = [
    (2.0, 2.0),  # Bottom-left
    (8.0, 2.0),  # Bottom-right
    (2.0, 8.0),  # Top-left
    (8.0, 8.0)   # Top-right
]

# Convert to room layout
layout = mapper.walls_to_layout(wall_grid, detector_positions)

# Optimize layout
optimized_layout = mapper.optimize_layout(layout)

print(f"Detected {len(optimized_layout.walls)} walls")
print(f"Room area: {optimized_layout.area:.2f} m²")
print(f"Found {len(optimized_layout.corners)} corners")
```

### Generate Visualizations

```python
# Initialize visualizer
visualizer = WallVisualizer()

# Generate floorplan
visualizer.generate_floorplan_image(
    optimized_layout,
    "output/floorplan.png",
    size=(800, 800)
)

# Generate 3D view
visualizer.generate_3d_room_view(
    optimized_layout,
    "output/3d_view.png",
    wall_height=2.5
)

# Generate heatmap
visualizer.generate_heatmap(
    wall_grid,
    "output/heatmap.png",
    title="Wall Detection Probability"
)

# Generate SVG floorplan
svg_string = generate_svg_floorplan(optimized_layout)

# Save SVG
with open("output/floorplan.svg", 'w') as f:
    f.write(svg_string)
```

### Save/Load Layouts

```python
# Save layout to JSON
layout.save("output/layout.json")

# Load layout from JSON
loaded_layout = RoomLayout.load("output/layout.json")
```

## Data Structures

### WallSegment

```python
@dataclass
class WallSegment:
    start_point: Tuple[float, float]  # (x, y) in meters
    end_point: Tuple[float, float]    # (x, y) in meters
    material: str                      # concrete, drywall, wood, metal, glass
    thickness: float                   # Wall thickness in meters
    confidence: float                  # Detection confidence (0.0 to 1.0)
    length: float                      # Computed length in meters
```

### RoomLayout

```python
@dataclass
class RoomLayout:
    walls: List[WallSegment]           # Detected walls
    dimensions: Tuple[float, float]    # (width, length) in meters
    area: float                        # Room area in m²
    corners: List[Tuple[float, float]] # Corner coordinates
    detection_timestamp: datetime      # When detected
    grid_resolution: float             # Grid cell size in meters
    detector_positions: List[Tuple[float, float]]  # WiFi detector locations
```

## API Endpoints

### Get Room Layout

```bash
GET /api/v1/room-layout
```

Returns current detected room layout as JSON.

**Response:**
```json
{
  "walls": [...],
  "dimensions": [10.0, 10.0],
  "area": 98.34,
  "corners": [[0.1, 9.1], [8.9, 9.1], ...],
  "detection_timestamp": "2026-02-02T20:12:38",
  "grid_resolution": 0.1,
  "detector_positions": [[2.0, 2.0], [8.0, 2.0], ...]
}
```

### Get Floorplan (SVG)

```bash
GET /api/v1/room-layout/floorplan
```

Returns SVG floorplan for web display.

**Response:**
```json
{
  "svg": "<svg>...</svg>",
  "timestamp": "2026-02-02T20:12:38"
}
```

### Calibrate Room Layout

```bash
POST /api/v1/room-layout/calibrate
```

Triggers room layout detection and mapping.

**Response:**
```json
{
  "status": "success",
  "message": "Room layout calibration complete",
  "walls_detected": 29,
  "area_m2": 98.34,
  "corners": 19,
  "timestamp": "2026-02-02T20:12:38",
  "layout": {...}
}
```

### Get Wall Heatmap

```bash
GET /api/v1/room-layout/heatmap
```

Returns wall detection probability heatmap.

**Response:**
```json
{
  "status": "success",
  "heatmap_path": "docs/floorplan_examples/api_heatmap.png",
  "timestamp": "2026-02-02T20:12:38",
  "grid_shape": [100, 100],
  "description": "Wall detection probability heatmap (blue=low, red=high)"
}
```

### Get Available Images

```bash
GET /api/v1/room-layout/images
```

Lists all available layout visualization images.

**Response:**
```json
{
  "images": [
    {
      "name": "floorplan.png",
      "path": "docs/floorplan_examples/floorplan.png",
      "size": 35840,
      "modified": "2026-02-02T20:12:38"
    },
    ...
  ],
  "count": 7
}
```

## Algorithm Details

### Wall Detection Pipeline

1. **Thresholding**
   - Convert probability grid to binary (>0.7 = wall)

2. **Morphological Operations**
   - Dilation: Fill gaps in walls
   - Erosion: Remove noise
   - Closing: Smooth wall boundaries

3. **Line Detection (Hough Transform)**
   - Detect line segments in binary image
   - Parameters:
     - Threshold: 30
     - Min line length: 10 pixels
     - Max line gap: 5 pixels

4. **Segment Merging**
   - Group collinear segments (within 5° angle)
   - Merge nearby segments (within 0.5m)
   - Extend to encompass all points

5. **Material Classification**
   - Sample probabilities along each wall
   - Classify based on average probability:
     - Concrete: ≥90%
     - Metal: ≥85%
     - Wood: ≥75%
     - Drywall: ≥70%
     - Glass: ≥60%

6. **Corner Detection**
   - Find wall intersections
   - Filter by angle threshold (>20°)
   - Remove duplicates (within 20cm)

### Layout Optimization

**Geometric Constraints:**
- Walls are straight lines
- Parallel walls (opposite sides)
- Right angles at corners
- Minimum wall length: 1m

**Algorithm:**
1. Filter short walls (<1m)
2. Snap to cardinal directions (0°, 90°, 180°, 270°)
3. Recalculate corners
4. Recompute area

### Area Calculation

**Method:** Convex Hull
- Compute convex hull of all wall endpoints
- Hull area = room area
- Fallback: Bounding box if hull fails

## Visualization Guide

### Color Schemes

**Wall Materials:**
- Concrete: #808080 (Gray)
- Drywall: #F5F5DC (Beige)
- Wood: #DEB887 (Wood)
- Metal: #C0C0C0 (Silver)
- Glass: #E0F7FA (Light Blue)

**Heatmap Gradient:**
- Blue (0.0): Low probability
- Cyan (0.25)
- Green (0.5)
- Yellow (0.75)
- Red (1.0): High probability

### Floorplan Elements

**Symbols:**
- Walls: Colored lines with thickness
- WiFi Detectors: Red triangles
- Corners: Blue circles
- Dimensions: Text labels
- Compass Rose: North arrow

## Examples

### Example 1: Simple Rectangular Room

```python
# Create rectangular room grid
wall_grid = create_sample_wall_grid(room_type="rectangular")

# Detect layout
mapper = RoomLayoutMapper(room_size=(10.0, 10.0))
layout = mapper.walls_to_layout(wall_grid)

print(f"Walls: {len(layout.walls)}")
print(f"Area: {layout.area:.2f} m²")
print(f"Corners: {len(layout.corners)}")
```

**Output:**
```
Walls: 29
Area: 97.39 m²
Corners: 17
```

### Example 2: Custom Detector Positions

```python
# Custom detector layout
detectors = [
    (0.0, 0.0),    # Corner
    (10.0, 0.0),   # Corner
    (0.0, 10.0),   # Corner
    (10.0, 10.0),  # Corner
    (5.0, 5.0)     # Center
]

layout = mapper.walls_to_layout(wall_grid, detector_positions=detectors)
```

### Example 3: Web Dashboard Integration

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    # Get layout
    layout = await get_room_layout()

    # Generate SVG
    svg_string = generate_svg_floorplan(layout)

    # Return HTML with embedded SVG
    return f"""
    <html>
        <head><title>Room Layout Dashboard</title></head>
        <body>
            <h1>WiFi Room Detection</h1>
            {svg_string}
        </body>
    </html>
    """
```

## Performance

### Benchmarks

| Operation | Time | Memory |
|-----------|------|--------|
| Grid to Layout | ~50ms | 10MB |
| Layout Optimization | ~5ms | 1MB |
| Floorplan Generation | ~80ms | 20MB |
| 3D View Generation | ~140ms | 30MB |
| SVG Generation | ~2ms | 5MB |

### Scalability

- **Grid Size:** Up to 1000×1000 cells
- **Room Size:** Up to 100m × 100m
- **Walls:** Up to 1000 segments
- **Real-time:** 10-20 FPS for 10×10m rooms

## Troubleshooting

### No Walls Detected

**Problem:** Empty wall list after detection.

**Solutions:**
1. Check probability grid values (should be 0.0 to 1.0)
2. Lower threshold in `walls_to_layout()` method
3. Adjust Hough transform parameters
4. Verify grid resolution matches room size

### Too Many False Positives

**Problem:** Excessive wall segments detected.

**Solutions:**
1. Increase threshold (>0.7)
2. Add more morphological cleaning
3. Increase minimum line length
4. Run optimization multiple times

### Low Quality Visualizations

**Problem:** Blurry or pixelated images.

**Solutions:**
1. Increase DPI (default: 100)
2. Use PIL floorplan instead of matplotlib
3. Increase image size (default: 800×800)
4. Use SVG for web display (scalable)

## Advanced Usage

### Custom Material Detection

```python
# Custom material thresholds
mapper.material_thresholds = {
    'brick': 0.95,
    'concrete': 0.90,
    'metal': 0.85,
    'wood': 0.75,
    'drywall': 0.70,
    'glass': 0.60
}
```

### Custom Wall Thickness

```python
# Override thickness estimation
for wall in layout.walls:
    if wall.material == 'concrete':
        wall.thickness = 0.2  # 20cm
    elif wall.material == 'drywall':
        wall.thickness = 0.1  # 10cm
```

### Batch Processing

```python
# Process multiple rooms
room_grids = [...]  # List of probability grids

layouts = []
for grid in room_grids:
    layout = mapper.walls_to_layout(grid)
    layout = mapper.optimize_layout(layout)
    layouts.append(layout)

# Generate all floorplans
for i, layout in enumerate(layouts):
    visualizer.generate_floorplan_image(
        layout,
        f"output/room_{i}.png"
    )
```

## Integration with WiFi Detection

```python
from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML
from src.spatial_mapper import RoomLayoutMapper

# Initialize components
wifi_sim = WiFiRSSISimulator(num_detectors=4)
signal_proc = SignalProcessor()
ml_models = PeopleDetectorML()
mapper = RoomLayoutMapper()

# Collect RSSI data
rssi_data = {}
for det_id in range(4):
    rssi_data[f"detector_{det_id}"] = wifi_sim.simulate_rssi(
        f"detector_{det_id}",
        num_people=2,
        moving=True
    )

# Extract features
features = signal_proc.extract_features(rssi_data)

# Detect people
presence, conf = ml_models.predict_presence(features)

# Detect walls (separate process)
wall_grid = detect_walls_from_rssi(rssi_data)
layout = mapper.walls_to_layout(wall_grid)

print(f"People detected: {presence}")
print(f"Walls detected: {len(layout.walls)}")
```

## Best Practices

1. **Calibration**
   - Run calibration in empty room first
   - Collect baseline RSSI measurements
   - Update detector positions accurately

2. **Quality Assurance**
   - Verify wall detections match physical walls
   - Check corner positions for accuracy
   - Validate area measurements

3. **Performance**
   - Use SVG for web applications
   - Cache generated visualizations
   - Optimize grid resolution (0.1m recommended)

4. **Documentation**
   - Save layouts as JSON for version control
   - Keep timestamp metadata
   - Document detector configurations

## References

- **Hough Transform:** Line detection algorithm
- **Convex Hull:** Area calculation
- **Morphological Operations:** Image processing
- **SVG Specification:** Vector graphics

## Support

For issues or questions:
1. Check logs: `logs/spatial_mapper.log`
2. Verify dependencies installed
3. Test with sample data first
4. Review generated visualizations

## License

MIT License - See project LICENSE file.
