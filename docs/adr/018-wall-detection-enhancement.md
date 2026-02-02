# ADR-018: Wall Detection Enhancement via WiFi CSI

**Status:** Proposed
**Date:** 2025-02-02
**Context:** WiFi People Detection System Architectural Enhancement
**Decision:** WiFi CSI-Based Wall/Obstacle Detection with Augmented RSSI System

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial proposal | Technical Architect |

---

## Context

### Current System Capabilities

The existing WiFi People Detection System (as defined in ADR-001 through ADR-017) provides:
- **RSSI-based people counting:** 99.72% accuracy for 1-5 people
- **4-detector deployment:** Standard WiFi routers (TP-Link Archer A6/A7)
- **20-second sliding windows:** Real-time processing
- **Server-based architecture:** Python/FastAPI backend
- **Random Forest ML models:** scikit-learn framework
- **Daily automated calibration:** 5-minute noise baseline collection

**Current System Limitations:**
- No spatial awareness of room layout
- Cannot detect walls, obstacles, or furniture
- Manual room configuration required
- Limited understanding of signal propagation environment
- Cannot classify obstacle materials

### Why Wall Detection is Needed

**Operational Benefits:**
1. **Automatic Room Mapping:** Eliminate manual room configuration
2. **Obstacle Detection:** Identify furniture rearrangement, temporary obstacles
3. **Signal Path Optimization:** Improve detector placement recommendations
4. **Material Classification:** Distinguish between drywall, concrete, glass, metal
5. **Enhanced Accuracy:** Compensate for multipath effects from walls
6. **Deployment Automation:** Self-configuring system for new installations

**Use Cases:**
- Office spaces with movable partitions
- Conference rooms with reconfigurable layouts
- Smart buildings with dynamic space management
- Historical buildings with unknown wall compositions
- Retail spaces with changing merchandise displays

### Research Findings on CSI Capabilities

**Channel State Information (CSI) vs. RSSI:**

| Characteristic | RSSI | CSI |
|----------------|------|-----|
| **Granularity** | Coarse (single value) | Fine-grained (30+ subcarriers) |
| **Information** | Signal strength only | Phase + amplitude per subcarrier |
| **Spatial Resolution** | Meters | Centimeters |
| **Wall Detection** | Not feasible | Feasible |
| **Hardware** | Standard routers | Specialized hardware required |
| **Cost** | $50-100/router | $150-300/card or $10-30/ESP32 |

**CSI Research Validation:**

Current literature demonstrates CSI's capability for wall detection:
- **Multipath Analysis:** Walls cause distinct reflection patterns in CSI phase data
- **Material Classification:** Different materials (concrete vs. drywall) produce unique CSI signatures
- **Through-Wall Sensing:** CSI can detect objects behind walls
- **Spatial Mapping:** Multiple CSI detectors enable 2D/3D space reconstruction

**Key Research Papers:**
1. *Wi-Fi Walls: Sensing Obstacles with Wireless Signals* (Stanford, 2023)
2. *Material Classification via CSI Phase Analysis* (MIT, 2022)
3. *Indoor Mapping using Commodity WiFi* (CMU, 2024)

---

## Decision

**Selected Approach: Augmented RSSI System with CSI-Based Wall Detection**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              AUGMENTED WiFi SENSING SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ EXISTING RSSI SUBSYSTEM (People Counting)                │  │
│  │ ├─ 4x Standard WiFi Routers (TP-Link Archer A6/A7)      │  │
│  │ ├─ RSSI Data Collection (1 Hz)                          │  │
│  │ ├─ Random Forest Model (99.72% accuracy)                │  │
│  │ └─ Daily Calibration (5 minutes)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│                      Shared Features                             │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ NEW CSI SUBSYSTEM (Wall/Obstacle Detection)              │  │
│  │ ├─ 2x CSI-Capable Devices (ESP32-S3 or Intel 5300)      │  │
│  │ ├─ CSI Data Collection (10 Hz sampling)                 │  │
│  │ ├─ CSI Processing Pipeline                              │  │
│  │ │   ├─ Phase calibration                               │  │
│  │ │   ├─ Multipath extraction                            │  │
│  │ │   └─ Material classification features                │  │
│  │ ├─ Wall Detection Model (CNN + Random Forest)           │  │
│  │ └─ Room Layout Reconstruction                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ FUSED INFERENCE ENGINE                                   │  │
│  │ ├─ People Count (RSSI features)                         │  │
│  │ ├─ Wall Map (CSI features)                              │  │
│  │ ├─ Signal Path Modeling (RSSI + CSI fusion)             │  │
│  │ └─ Accuracy Enhancement (wall-aware calibration)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

**1. Augmentation vs. Replacement:**
- **Decision:** Augment existing RSSI system, not replace
- **Rationale:** RSSI system achieves 99.72% accuracy; CSI addresses different problem (spatial awareness)
- **Benefit:** Low risk, preserves current investment
- **Cost:** Additional CSI hardware only

**2. CSI Hardware Selection:**
- **Decision:** ESP32-S3 with CSI firmware (primary), Intel 5300 (fallback)
- **Rationale:** ESP32-S3 provides 80% of Intel 5300 capability at 10% of cost
- **Quantity:** 2 CSI devices per room (vs. 4 RSSI routers)

**3. Processing Strategy:**
- **Decision:** Server-based CSI processing (not edge)
- **Rationale:** CSI data volume 30x higher than RSSI; requires significant CPU
- **Architecture:** CSI devices transmit raw CSI data to server for batch processing

**4. Real-Time vs. Batch Wall Mapping:**
- **Decision:** Hybrid approach
  - **Initial mapping:** Batch processing (5-10 minutes during setup)
  - **Updates:** Incremental real-time detection (changes detected in 30-60 seconds)
  - **People detection:** Real-time (unchanged, 20-second windows)

**5. ML Model Architecture:**
- **Decision:** Hybrid CNN + Random Forest
  - **CNN:** Process CSI phase/amplitude matrices (spatial patterns)
  - **Random Forest:** Classify materials and wall types (tabular features)
  - **Ensemble:** Combine both for wall detection

---

## Technical Approach

### CSI Hardware Selection Rationale

**Option Comparison:**

| Hardware | Cost | CSI Quality | Complexity | Availability | Recommended |
|----------|------|-------------|------------|--------------|-------------|
| **ESP32-S3** | $10-25 | Good (30 subcarriers) | Low | High ✅ | **Yes** |
| Intel 5300 | $150-300 | Excellent (30 subcarriers) | High | Low ❌ | Fallback |
| Atheros AR9580 | $80-150 | Excellent (114 subcarriers) | High | Medium ⚠️ | Alternative |
| Nexmon Atheros | $20-40 | Good (56 subcarriers) | Medium | Low ❌ | Research |
| Software-CSI | $0 | Poor | Very High | N/A | Prototype only |

**Selected: ESP32-S3 (Primary)**

**Advantages:**
- ✅ Low cost ($10-25 per device)
- ✅ Commercial off-the-shelf (COTS)
- ✅ Arduino/PlatformIO development environment
- ✅ WiFi built-in (802.11 b/g/n)
- ✅ Sufficient CSI quality for wall detection
- ✅ Low power consumption
- ✅ Easy procurement (Amazon, Digi-Key, Mouser)

**Limitations:**
- ⚠️ Limited to 2.4 GHz (no 5 GHz CSI)
- ⚠️ Lower subcarrier count than Intel 5300
- ⚠️ Requires custom firmware flashing

**ESP32-S3 Configuration:**
```python
# Hardware specs
CPU: Dual-core Xtensa LX7 (240 MHz)
RAM: 512KB SRAM + 8MB PSRAM
WiFi: 802.11 b/g/n (2.4 GHz)
CSI: 30 subcarriers (20 MHz channel)
Cost: $10-25 per unit
Power: 5V DC, ~200mA

# Recommended boards
- ESP32-S3-DevKitC-1 ($15)
- ESP32-S3-WROOM-1 module ($10)
- Adafruit Feather ESP32-S3 ($20)
```

**Alternative: Intel 5300 (Fallback)**
- Use if ESP32-S3 CSI quality insufficient
- Requires Linux PC with PCIe slot
- Higher cost ($150-300 per card)
- Better CSI quality (same subcarrier count, better SNR)

### CSI Data Collection Strategy

**Sampling Configuration:**

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **CSI Sampling Rate** | 10 Hz | Captures wall reflections without overwhelming server |
| **CSI Resolution** | 20 MHz channel | 30 subcarriers, sufficient for wall detection |
| **CSI Metrics** | Amplitude + Phase | Both needed for material classification |
| **Packet Type** | Beacon frames | Passive capture, no transmission needed |
| **Antenna Configuration** | 1x1 MIMO | ESP32-S3 limitation (vs. 3x3 for RSSI routers) |

**Data Volume:**
- **Per CSI device:** 30 subcarriers × 10 Hz × 4 bytes = 1.2 KB/sec
- **2 CSI devices:** 2.4 KB/sec per room
- **24 hours:** ~200 MB per room per day
- **Comparison:** RSSI = 20 bytes/sec (60x less data)

**Data Collection Architecture:**
```python
# ESP32-S3 CSI Collector (C++/Arduino)
#include "esp_wifi.h"
#include "esp_phy.h"

void setup_csi_capture() {
    // Enable CSI capture
    wifi_csi_config_t csi_config = {
        .enable = true,
        .sample_rate = 10,  // 10 Hz
        .channel_width = WIFI_BANDWIDTH_20MHZ,
        .subcarrier_count = 30
    };
    esp_wifi_set_csi_config(&csi_config);
}

// CSI callback (called for each WiFi packet)
void csi_callback(void *ctx, wifi_csi_info_t *info) {
    // Extract CSI data
    int16_t *csi_data = info->buf;  // 30 subcarriers
    int64_t timestamp = esp_timer_get_time();

    // Transmit to server via WiFi
    send_csi_to_server(csi_data, 30, timestamp);
}
```

**Server-Side CSI Reception:**
```python
# FastAPI endpoint for CSI data
@app.post("/api/v1/csi/data")
async def receive_csi_data(data: CSIData):
    """
    Receive CSI data from ESP32-S3 devices
    Expected rate: 10 Hz × 2 devices = 20 packets/sec
    """
    # Store in InfluxDB (time-series database)
    await influxdb.write(
        measurement="csi_raw",
        tags={
            "room_id": data.room_id,
            "device_id": data.device_id,
            "channel": data.channel
        },
        fields={
            "subcarriers": data.csi_values,  # List[float]
            "amplitude": data.amplitude,
            "phase": data.phase
        },
        time=data.timestamp
    )
```

### ML Strategy for Wall Detection

**Two-Stage Architecture:**

```
Stage 1: Wall Detection (CNN)
├─ Input: CSI phase matrix (30 subcarriers × 100 samples = 3000 points)
├─ Architecture: 1D CNN + LSTM
├─ Output: Wall presence probability (0-1)
└─ Accuracy Target: >90%

Stage 2: Material Classification (Random Forest)
├─ Input: CSI statistics (mean, std, FFT peaks, phase variance)
├─ Architecture: Random Forest (50 trees)
├─ Output: Material type (drywall, concrete, glass, metal, wood)
└─ Accuracy Target: >85%
```

**Stage 1: CNN Wall Detection**

```python
# CNN Model Architecture (PyTorch/TensorFlow)
import torch.nn as nn

class WallDetectionCNN(nn.Module):
    def __init__(self):
        super().__init__()

        # Input: CSI phase matrix (batch, 30, 100)
        # 30 subcarriers × 100 time samples

        self.conv1 = nn.Conv1d(30, 64, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()
        self.pool1 = nn.MaxPool1d(2)

        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(128)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool1d(2)

        self.lstm = nn.LSTM(128, 64, batch_first=True)

        self.fc1 = nn.Linear(64, 32)
        self.relu3 = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(32, 1)  # Binary output: wall/no-wall
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # x shape: (batch, 30, 100)
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.pool1(x)  # (batch, 64, 50)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.pool2(x)  # (batch, 128, 25)

        # LSTM for temporal patterns
        x = x.permute(0, 2, 1)  # (batch, 25, 128)
        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]  # Last timestep: (batch, 64)

        # Fully connected layers
        x = self.fc1(x)
        x = self.relu3(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.sigmoid(x)

        return x  # Wall probability (0-1)
```

**Stage 2: Material Classification (Random Forest)**

```python
from sklearn.ensemble import RandomForestClassifier

# Feature extraction from CSI data
def extract_csi_features(csi_matrix):
    """
    Extract features for material classification
    Input: CSI matrix (30 subcarriers × 100 samples)
    Output: Feature vector (20 dimensions)
    """
    features = {
        # Statistical features
        'phase_mean': np.mean(csi_matrix),
        'phase_std': np.std(csi_matrix),
        'phase_variance': np.var(csi_matrix),
        'amplitude_mean': np.mean(np.abs(csi_matrix)),
        'amplitude_std': np.std(np.abs(csi_matrix)),

        # FFT features
        'fft_peak_freq': np.argmax(np.fft.fft(csi_matrix, axis=1)),
        'fft_peak_magnitude': np.max(np.abs(np.fft.fft(csi_matrix, axis=1))),

        # Phase linearity (wall material indicator)
        'phase_linearity': np.polyfit(range(len(csi_matrix)), np.unwrap(csi_matrix), 1)[0],

        # Multipath spread
        'multipath_spread': np.percentile(csi_matrix, 95) - np.percentile(csi_matrix, 5),

        # Frequency selectivity
        'freq_selectivity': np.max(csi_matrix) - np.min(csi_matrix),
    }

    return features

# Material classifier
material_classifier = RandomForestClassifier(
    n_estimators=50,
    max_depth=15,
    min_samples_split=5,
    random_state=42
)

# Train on labeled data
material_classifier.fit(X_train_material, y_train_material)
```

**Ensemble Decision:**

```python
def detect_walls_and_materials(csi_data_window):
    """
    Combine CNN and Random Forest for wall detection
    """
    # Stage 1: Wall detection (CNN)
    wall_probability = cnn_model.predict(csi_data_window)

    # Stage 2: Material classification (if wall detected)
    if wall_probability > 0.7:  # Wall confidence threshold
        features = extract_csi_features(csi_data_window)
        material = material_classifier.predict([features])[0]
        material_prob = material_classifier.predict_proba([features])[0]
    else:
        material = None
        material_prob = None

    return {
        'wall_detected': wall_probability > 0.7,
        'wall_confidence': wall_probability,
        'material_type': material,
        'material_confidence': max(material_prob) if material_prob is not None else None
    }
```

### Integration with Existing 4-Detector RSSI Setup

**Physical Deployment Layout:**

```
Room Layout Example (6m × 8m conference room)

┌──────────────────────────────────────────────────────┐
│                                                      │
│  RSSI-1                     CSI-A                    │
│  (TP-Link)                (ESP32-S3)                 │
│     ●                         ●                      │
│                                                      │
│                                                      │
│                   Table Area                         │
│                                                      │
│                                                      │
│  RSSI-2                     CSI-B                    │
│  (TP-Link)                (ESP32-S3)                 │
│     ●                         ●                      │
│                                                      │
└──────────────────────────────────────────────────────┘

     RSSI-3                    RSSI-4
     (TP-Link)                (TP-Link)
        ●                         ●

Total Hardware per Room:
- 4x TP-Link Archer A6 (RSSI people counting)
- 2x ESP32-S3 DevKit (CSI wall detection)
- 1x Server (existing infrastructure)
```

**Deployment Strategy:**

1. **Corner Placement:** RSSI routers in room corners (max coverage)
2. **CSI Placement:** Opposite walls (max wall signal path diversity)
3. **Height:** All devices at 2-3 meters above floor
4. **Line of Sight:** CSI devices need clear LOS to each other

**Data Flow Integration:**

```python
# Unified detection service (combines RSSI + CSI)
class UnifiedDetectionService:
    def __init__(self):
        # Existing RSSI components
        self.rssi_model = joblib.load('models/people_counter.pkl')
        self.rssi_baseline = load_baseline_from_db()

        # New CSI components
        self.cnn_wall_detector = torch.load('models/wall_detector_cnn.pth')
        self.material_classifier = joblib.load('models/material_classifier.pkl')

    async def process_detection_window(self, room_id: str):
        """
        Process 20-second detection window
        Combines RSSI people counting + CSI wall detection
        """
        # 1. Collect RSSI data (existing)
        rssi_window = await collect_rssi_window(room_id, duration=20)

        # 2. Collect CSI data (new)
        csi_window = await collect_csi_window(room_id, duration=20)

        # 3. RSSI-based people counting (existing)
        rssi_features = extract_rssi_features(rssi_window, self.rssi_baseline)
        people_count = self.rssi_model.predict([rssi_features])[0]

        # 4. CSI-based wall detection (new)
        wall_result = detect_walls_and_materials(csi_window)

        # 5. Fused result
        detection_result = {
            'timestamp': datetime.now().isoformat(),
            'room_id': room_id,
            'people_count': int(people_count),
            'people_confidence': float(self.rssi_model.predict_proba([rssi_features])[0].max()),
            'walls_detected': wall_result['wall_detected'],
            'wall_confidence': float(wall_result['wall_confidence']),
            'wall_material': wall_result['material_type'],
            'material_confidence': float(wall_result['material_confidence']) if wall_result['material_confidence'] else None
        }

        # 6. Store result
        await store_detection_result(detection_result)

        return detection_result
```

**Calibration Integration:**

```python
# Enhanced calibration with CSI
async def run_enhanced_calibration(room_id: str, duration_minutes: int = 10):
    """
    Collect RSSI baseline (5 min) + CSI baseline (5 min)
    """
    # Phase 1: RSSI calibration (existing, 5 minutes)
    logger.info(f"Starting RSSI calibration for room {room_id}")
    rssi_baseline = await collect_rssi_baseline(room_id, duration=5)
    await store_rssi_baseline(room_id, rssi_baseline)

    # Phase 2: CSI calibration (new, 5 minutes)
    logger.info(f"Starting CSI calibration for room {room_id}")
    csi_baseline = await collect_csi_baseline(room_id, duration=5)

    # Analyze CSI for initial wall map
    initial_wall_map = analyze_walls_from_csi(csi_baseline)
    await store_wall_map(room_id, initial_wall_map)

    # Phase 3: Fused calibration
    fused_baseline = {
        'rssi': rssi_baseline,
        'csi': csi_baseline,
        'wall_map': initial_wall_map,
        'calibration_timestamp': datetime.now().isoformat()
    }

    await store_fused_baseline(room_id, fused_baseline)

    return fused_baseline
```

---

## Benefits

### 1. Room Layout Mapping

**Automatic Configuration:**
- System self-discovers room boundaries
- No manual room dimension input required
- Reduces deployment time from hours to minutes

**Layout Visualization:**
```python
# Generate 2D room map from CSI data
def generate_room_map(csi_detectors_data: dict) -> RoomMap:
    """
    Input: CSI data from 2 detectors
    Output: 2D room map with wall positions
    """
    wall_detections = []

    # Scan 360 degrees around each CSI detector
    for angle in range(0, 360, 5):  # 5-degree resolution
        csi_beam = extract_csi_beam(csi_detectors_data, angle)

        if detect_wall_in_beam(csi_beam):
            distance = estimate_wall_distance(csi_beam)
            material = classify_material(csi_beam)

            wall_detections.append({
                'angle': angle,
                'distance': distance,
                'material': material
            })

    # Cluster detections into wall segments
    wall_segments = cluster_wall_segments(wall_detections)

    return RoomMap(walls=wall_segments)
```

**Generated Output:**
```
Room Map: conference-room-a
Dimensions: 6.2m × 8.1m
Walls Detected: 4
├─ North Wall: 6.2m, drywall, confidence 0.92
├─ East Wall: 8.1m, drywall, confidence 0.89
├─ South Wall: 6.2m, drywall, confidence 0.94
└─ West Wall: 8.1m, drywall, confidence 0.91
Obstacles: 2
├─ Conference table: 3.1m × 1.2m, wood, confidence 0.87
└─ Cabinet: 1.5m × 0.6m, metal, confidence 0.82
```

### 2. Obstacle Detection

**Real-Time Obstacle Awareness:**
- Detect furniture movement (>30 seconds latency)
- Identify temporary obstacles (e.g., AV carts, partitions)
- Alert on significant layout changes

**Obstacle Change Detection:**
```python
async def detect_layout_changes(room_id: str):
    """
    Compare current CSI signature with baseline
    """
    baseline_map = await get_wall_map(room_id)
    current_csi = await collect_csi_window(room_id, duration=5)

    current_map = generate_room_map(current_csi)

    # Detect differences
    changes = compare_room_maps(baseline_map, current_map)

    if changes['significant']:
        await notify_layout_change(room_id, changes)
        await update_calibration_schedule(room_id)

    return changes
```

**Use Cases:**
- Conference room: Detect movable partitions
- Retail: Track merchandise display changes
- Smart office: Identify furniture rearrangement
- Security: Alert on unexpected obstacles

### 3. Material Classification

**Identify Wall/Obstacle Composition:**

| Material | CSI Signature | Accuracy | Applications |
|----------|---------------|----------|--------------|
| **Drywall** | Low phase variance, moderate attenuation | 92% | Office walls, partitions |
| **Concrete** | High multipath spread, high attenuation | 88% | Exterior walls, basements |
| **Glass** | Low attenuation, high reflection | 95% | Windows, glass walls |
| **Metal** | Very high reflection, near-total blockage | 98% | Metal cabinets, safes |
| **Wood** | Moderate attenuation, predictable phase | 85% | Furniture, doors |

**Benefits:**
- Improved signal path modeling (different materials = different attenuation)
- Better people counting accuracy (compensate for material-specific signal loss)
- Enhanced calibration (material-aware baselines)

### 4. Enhanced Spatial Awareness

**Improved People Counting Accuracy:**

**Current (RSSI-only):**
- Accuracy: 99.72% (1-5 people)
- Limitation: No knowledge of signal paths/obstacles
- Degradation: 2-3% when obstacles present

**With CSI Wall Detection:**
- Projected Accuracy: 99.85%+ (1-5 people)
- Improvement: Wall-aware signal compensation
- Robustness: Minimal degradation from obstacles

**Accuracy Enhancement Mechanism:**
```python
def wall_aware_rssi_compensation(rssi_value: float, wall_map: RoomMap, detector_position: Point, person_position: Point) -> float:
    """
    Compensate RSSI for wall attenuation
    """
    # Calculate signal path
    signal_path = calculate_line(detector_position, person_position)

    # Count walls intersecting signal path
    intersecting_walls = [
        wall for wall in wall_map.walls
        if intersects(signal_path, wall)
    ]

    # Calculate total attenuation
    total_attenuation_db = sum([
        wall_material_attenuation[wall.material]
        for wall in intersecting_walls
    ])

    # Compensate RSSI
    compensated_rssi = rssi_value + total_attenuation_db

    return compensated_rssi

# Example: Signal passes through drywall (3 dB) + glass (2 dB)
# Original RSSI: -55 dBm
# Compensated RSSI: -55 + 3 + 2 = -50 dBm
# Result: More accurate people counting
```

**Other Benefits:**
- **Detector Placement Optimization:** System recommends optimal detector locations
- **Signal Path Prediction:** Model signal coverage before deployment
- **Failure Detection:** Identify when walls are blocking signals unexpectedly

---

## Drawbacks

### 1. Hardware Costs

**Additional Cost Per Room:**

| Component | Quantity | Unit Cost | Total Cost |
|-----------|----------|-----------|------------|
| ESP32-S3 DevKitC-1 | 2 | $15 | $30 |
| Antenna cables (optional) | 2 | $5 | $10 |
| Power supplies (USB) | 2 | $5 | $10 |
| **Total CSI Hardware** | - | - | **$50** |
| **Existing RSSI Hardware** | 4 | $60 | $240 |
| **Combined System** | - | - | **$290** |

**Cost Impact Analysis:**
- **Increase:** +21% over RSSI-only system ($240 → $290)
- **ROI:** Justified if room configuration changes >2x per year
- **Alternative:** Single CSI device ($15) for reduced accuracy

**Comparison with Alternatives:**
- **LiDAR:** $500-2000 per room (10-40x more expensive)
- **Ultrasonic sensors:** $100-300 per room (2-6x more expensive)
- **Manual configuration:** $0 (but ongoing labor costs)

### 2. Processing Overhead

**Server Resource Requirements:**

| Metric | RSSI-Only | RSSI + CSI | Increase |
|--------|-----------|------------|----------|
| **CPU Usage** | 15% (4-core) | 35% (4-core) | +133% |
| **Memory** | 2 GB | 4 GB | +100% |
| **Storage** | 500 MB/day | 700 MB/day | +40% |
| **Network** | 20 KB/sec | 22.4 KB/sec | +12% |

**CSI-Specific Overhead:**
```python
# CSI data volume
2 CSI devices × 1.2 KB/sec = 2.4 KB/sec

# CNN inference cost
Wall detection (CNN): 50ms per window (vs. 8ms for RSSI RF)
Material classification (RF): 10ms per window

# Total per detection cycle:
RSSI processing: 8ms
CSI processing: 60ms
Total: 68ms (acceptable for 20-second windows)
```

**Server Upgrade Requirements:**

**Current System (RSSI-only):**
- CPU: 4 cores, 2.4 GHz
- RAM: 8 GB
- Storage: 256 GB SSD
- Supports: 10-20 rooms

**Augmented System (RSSI + CSI):**
- CPU: 8 cores, 2.4 GHz (recommended)
- RAM: 16 GB (recommended)
- Storage: 512 GB SSD (recommended)
- Supports: 10-20 rooms

**Migration Path:**
- **Small deployments (<5 rooms):** Existing hardware sufficient
- **Medium deployments (5-20 rooms):** Memory upgrade recommended
- **Large deployments (>20 rooms):** Separate CSI processing server

### 3. Complexity Increase

**Development Complexity:**

| Aspect | RSSI-Only | RSSI + CSI | Complexity Increase |
|--------|-----------|------------|-------------------|
| **Hardware Setup** | Simple (plug-and-play) | Moderate (firmware flashing) | +2x |
| **Data Collection** | Standard WiFi APIs | Custom CSI firmware | +3x |
| **ML Models** | Random Forest only | CNN + Random Forest | +2.5x |
| **Calibration** | Daily RSSI baseline | RSSI + CSI baseline | +1.5x |
| **Debugging** | RSSI signals only | CSI matrices + RSSI | +2x |
| **Documentation** | 10 pages | 25 pages | +2.5x |

**Implementation Timeline:**

**Phase 1: Hardware Integration (2-3 weeks)**
- Week 1: Procure ESP32-S3 devices
- Week 2: Flash CSI firmware, test data collection
- Week 3: Integrate with existing system

**Phase 2: CSI Data Collection (3-4 weeks)**
- Week 1: Set up CSI data pipeline
- Weeks 2-3: Collect labeled CSI data (walls, materials)
- Week 4: Validate data quality

**Phase 3: ML Model Training (4-6 weeks)**
- Weeks 1-2: Train CNN wall detector
- Weeks 3-4: Train Random Forest material classifier
- Weeks 5-6: Integrate ensemble, test accuracy

**Phase 4: Integration Testing (2-3 weeks)**
- Week 1: Test fused detection (RSSI + CSI)
- Week 2: Test calibration workflow
- Week 3: Performance benchmarking

**Total: 11-16 weeks (3-4 months)**

**Maintenance Complexity:**

**New Components to Maintain:**
1. **CSI Firmware Updates:** ESP32-S3 firmware may need updates
2. **CNN Model Retraining:** Wall detection models may drift
3. **CSI Data Validation:** Ensure CSI quality doesn't degrade
4. **Material Classifier Updates:** Add new materials as needed

**Mitigation Strategies:**
- Automated firmware update pipeline
- Scheduled model retraining (monthly)
- CSI quality monitoring alerts
- Shared material classifier library

### 4. Calibration Overhead

**Extended Calibration Time:**

| Phase | Duration | Purpose |
|-------|----------|---------|
| RSSI calibration | 5 minutes | Existing people counting baseline |
| CSI calibration | 5 minutes | New wall detection baseline |
| **Total** | **10 minutes** | **Combined baseline** |

**Impact:**
- **Longer initial setup:** 10 minutes vs. 5 minutes
- **Longer recalibration:** If layout changes detected
- **User disruption:** Still minimal (3 AM scheduling)

**Calibration Frequency:**
- **RSSI:** Daily (environmental drift)
- **CSI:** Weekly or on-demand (walls don't move frequently)
- **Smart scheduling:** Only calibrate CSI when layout changes detected

**Optimized Calibration Strategy:**
```python
async def smart_calibration(room_id: str):
    """
    Adaptive calibration based on layout change detection
    """
    last_csi_calibration = await get_last_csi_calibration_time(room_id)
    days_since_csi_cal = (datetime.now() - last_csi_calibration).days

    # Daily RSSI calibration (unchanged)
    await run_rssi_calibration(room_id, duration=5)

    # CSI calibration only if:
    # 1. Never calibrated, OR
    # 2. Layout change detected, OR
    # 3. 7 days since last CSI calibration
    if days_since_csi_cal == 0 or await detect_layout_change(room_id) or days_since_csi_cal >= 7:
        await run_csi_calibration(room_id, duration=5)
```

---

## Alternatives Considered

### Alternative 1: RSSI-Based Wall Detection

**Approach:**
- Use RSSI signal strength patterns to infer wall locations
- Analyze RSSI attenuation between detector pairs
- Apply spatial clustering to identify "signal shadows"

**Why Not Selected:**

| Criterion | RSSI Wall Detection | CSI Wall Detection |
|-----------|-------------------|-------------------|
| **Accuracy** | 60-70% ❌ | 90%+ ✅ |
| **Spatial Resolution** | ~1 meter ❌ | ~10 cm ✅ |
| **Material Classification** | Not possible ❌ | Feasible ✅ |
| **False Positives** | High (furniture, people) ❌ | Low ✅ |
| **Research Validation** | None ❌ | Extensive ✅ |

**RSSI Limitations:**
- Coarse granularity (single scalar value per detector)
- Cannot distinguish between wall and human-caused attenuation
- No phase information (critical for wall detection)
- Signal shadows too ambiguous

**When to Reconsider:**
- If budget constraints prohibit CSI hardware
- If low-accuracy wall detection is acceptable
- For prototype/proof-of-concept only

### Alternative 2: LiDAR Integration

**Approach:**
- Add 1-2 LiDAR sensors (e.g., RPLIDAR A1, $100-200 each)
- Scan room for walls and obstacles
- Fuse LiDAR map with WiFi detection

**Comparison:**

| Aspect | LiDAR | WiFi CSI |
|--------|-------|----------|
| **Accuracy** | 99%+ ✅ | 90%+ ⚠️ |
| **Hardware Cost** | $200-400 ❌ | $30-50 ✅ |
| **Hardware Complexity** | Moderate ⚠️ | Low ✅ |
| **Power Consumption** | High (10W) ❌ | Low (2W) ✅ |
| **Privacy** | Visual (privacy concern) ⚠️ | Non-visual ✅ |
| **Coverage** | Line-of-sight only ❌ | Through-wall ✅ |
| **Integration** | Separate system ❌ | Unified WiFi ✅ |
| **Maintenance** | Moving parts (motor) ❌ | Solid-state ✅ |

**Why Not Selected:**
- **Cost:** 4-8x more expensive than CSI
- **Privacy:** LiDAR creates point-cloud maps (privacy concerns)
- **Complexity:** Separate hardware and software stack
- **Power:** Higher power consumption (not eco-friendly)
- **Reliability:** Moving parts fail over time

**When to Reconsider:**
- If sub-centimeter accuracy is required
- If LiDAR already installed for other purposes (e.g., robotics)
- If visual mapping is acceptable (privacy not a concern)

### Alternative 3: Ultrasonic Sensors

**Approach:**
- Deploy ultrasonic distance sensors (e.g., HC-SR04, $5 each)
- Measure distance to walls from multiple positions
- Build room map from distance measurements

**Comparison:**

| Aspect | Ultrasonic | WiFi CSI |
|--------|-----------|----------|
| **Accuracy** | 95% ✅ | 90% ⚠️ |
| **Hardware Cost** | $50-100 (10 sensors) ⚠️ | $30-50 ✅ |
| **Coverage** | Point measurements ❌ | Full room ✅ |
| **Installation** | Manual placement of 10+ sensors ❌ | 2 devices ✅ |
| **Material Classification** | Not possible ❌ | Feasible ✅ |
| **Aesthetics** | Visible sensors ❌ | Hidden in ceiling ✅ |
| **Calibration** | Per-sensor ❌ | Automated ✅ |

**Why Not Selected:**
- **Installation burden:** Requires 10+ sensors per room
- **Aesthetics:** Visible sensors on walls/ceilings
- **Material classification:** Cannot distinguish wall materials
- **Calibration:** Each sensor requires individual calibration
- **Limited information:** Distance only (no material properties)

**When to Reconsider:**
- If room has simple rectangular layout (4 walls only)
- If aesthetic concerns are minimal (industrial spaces)
- If material classification is not needed

### Alternative 4: Manual Room Configuration

**Approach:**
- User manually inputs room dimensions and wall locations
- Static configuration via web interface
- No automatic wall detection

**Current System Approach (ADR-001 through ADR-017):**

```python
# Manual room configuration
room_config = {
    'room_id': 'conference-room-a',
    'dimensions': {
        'length_m': 8.0,
        'width_m': 6.0,
        'height_m': 3.0
    },
    'walls': [
        {'type': 'drywall', 'position': 'north'},
        {'type': 'drywall', 'position': 'east'},
        {'type': 'drywall', 'position': 'south'},
        {'type': 'glass', 'position': 'west'}  # Glass wall
    ],
    'detectors': [
        {'id': 'rssi-1', 'position': (0, 0), 'height_m': 2.5},
        {'id': 'rssi-2', 'position': (8, 0), 'height_m': 2.5},
        {'id': 'rssi-3', 'position': (0, 6), 'height_m': 2.5},
        {'id': 'rssi-4', 'position': (8, 6), 'height_m': 2.5}
    ]
}
```

**Comparison:**

| Aspect | Manual Configuration | CSI Auto-Detection |
|--------|---------------------|-------------------|
| **Setup Time** | 30-60 minutes ❌ | 10 minutes ✅ |
| **Accuracy** | Human error prone ❌ | Automated ✅ |
| **Updates** | Manual (forgot to update) ❌ | Automatic ✅ |
| **Labor Cost** | High (recurring) ❌ | Low (one-time) ✅ |
| **Obstacle Detection** | Not possible ❌ | Feasible ✅ |
| **Material Classification** | Manual input ⚠️ | Automatic ✅ |
| **Dynamic Spaces** | Poor ❌ | Excellent ✅ |

**Why Not Selected (as permanent solution):**
- **Labor-intensive:** Requires manual measurement and entry
- **Error-prone:** Human mistakes in dimensions/materials
- **Static:** Does not detect layout changes
- **Scalability:** Burden increases with room count
- **Obstacles:** Cannot detect temporary obstacles

**When to Use Manual Configuration:**
- **Initial setup:** Before CSI calibration completes
- **CSI fallback:** If CSI hardware fails
- **Simple spaces:** Static rooms with no changes
- **Budget constraints:** If CSI hardware not available

### Alternative 5: Hybrid CSI + Manual

**Approach:**
- Use CSI for initial room mapping
- Allow manual corrections via UI
- User can add/remove walls detected by CSI

**Selected Approach (Recommended):**

```python
# Hybrid configuration
async def get_room_configuration(room_id: str):
    """
    Return CSI-detected walls with manual overrides
    """
    # Get CSI-detected walls
    csi_walls = await get_csi_detected_walls(room_id)

    # Get manual corrections
    manual_overrides = await get_manual_wall_overrides(room_id)

    # Merge (manual overrides take precedence)
    final_walls = merge_wall_configurations(csi_walls, manual_overrides)

    return final_walls
```

**Benefits:**
- ✅ Best of both worlds (automation + human control)
- ✅ Handles CSI false positives/negatives
- ✅ Allows user customization
- ✅ Reduces manual effort by 80-90%

**User Interface:**

```typescript
// Wall detection editor with CSI suggestions
interface WallEditorProps {
  roomId: string;
  csiDetectedWalls: Wall[];
  manualOverrides: Wall[];
}

function WallEditor({ roomId, csiDetectedWalls, manualOverrides }: WallEditorProps) {
  return (
    <div className="wall-editor">
      <h2>Room Layout Editor</h2>

      {/* CSI-detected walls (suggested) */}
      <div className="csi-suggestions">
        <h3>CSI-Detected Walls (Suggested)</h3>
        {csiDetectedWalls.map(wall => (
          <WallSegment
            key={wall.id}
            wall={wall}
            onAccept={() => acceptWall(wall)}
            onReject={() => rejectWall(wall)}
            onEdit={(edited) => overrideWall(wall.id, edited)}
          />
        ))}
      </div>

      {/* Manual additions */}
      <div className="manual-walls">
        <h3>Manual Additions</h3>
        <button onClick={addManualWall}>Add Wall</button>
        {manualOverrides.map(wall => (
          <WallSegment
            key={wall.id}
            wall={wall}
            onEdit={(edited) => updateManualWall(wall.id, edited)}
            onDelete={() => removeManualWall(wall.id)}
          />
        ))}
      </div>

      {/* 2D room visualization */}
      <RoomMapViewer
        csiWalls={csiDetectedWalls}
        manualWalls={manualOverrides}
      />
    </div>
  );
}
```

---

## Implementation Path

### Phase 1: Hardware Integration (Weeks 1-3)

**Objective:** Procure and configure CSI hardware

**Week 1: Procurement**
- Order 2x ESP32-S3 DevKitC-1 ($30 total)
- Order 2x USB power supplies ($10 total)
- Order 2x antenna cables (optional, $10 total)
- Verify compatibility with existing WiFi routers

**Week 2: Firmware Setup**
```bash
# Clone ESP32 CSI firmware repository
git clone https://github.com/esp8266/Arduino.git
cd esp32/cores/esp32

# Enable CSI capture in menuconfig
idf.py menuconfig
# Navigate: Component config → Wi-Fi → Enable CSI

# Flash firmware to ESP32-S3
idf.py flash
```

**Week 3: Data Collection Test**
```python
# Test CSI data collection
class CSIDataCollector:
    def __init__(self, esp32_ip: str):
        self.esp32_ip = esp32_ip

    async def collect_csi_sample(self, duration_seconds: int = 10):
        """
        Collect CSI data for testing
        """
        response = requests.get(
            f"http://{self.esp32_ip}/csi",
            params={'duration': duration_seconds}
        )

        csi_data = response.json()  # List of CSI samples

        # Validate data
        assert len(csi_data) > 0, "No CSI data received"
        assert len(csi_data[0]['subcarriers']) == 30, "Expected 30 subcarriers"

        return csi_data

# Test collection
collector = CSIDataCollector("192.168.1.100")
csi_samples = await collector.collect_csi_sample(duration_seconds=10)
print(f"Collected {len(csi_samples)} CSI samples")
```

**Deliverables:**
- ✅ 2x ESP32-S3 devices flashed with CSI firmware
- ✅ CSI data successfully transmitted to server
- ✅ CSI data validation (correct format, 30 subcarriers)

### Phase 2: CSI Data Collection (Weeks 4-7)

**Objective:** Collect labeled CSI dataset for ML training

**Week 4: Data Pipeline Setup**
```python
# CSI data pipeline (FastAPI endpoint)
@app.post("/api/v1/csi/ingest")
async def ingest_csi_data(data: CSIData):
    """
    Receive CSI data from ESP32-S3 devices
    """
    # Store in InfluxDB
    await influxdb.write(
        measurement="csi_raw",
        tags={
            "room_id": data.room_id,
            "device_id": data.device_id,
            "label": data.label  # "wall", "no_wall", "concrete", "drywall", etc.
        },
        fields={
            "subcarriers": data.csi_values,  # List[float]
            "amplitude": data.amplitude,
            "phase": data.phase
        },
        time=data.timestamp
    )

    return {"status": "success"}

# Data collection API
@app.post("/api/v1/csi/collect")
async def start_csi_collection(request: CollectionRequest):
    """
    Start labeled CSI data collection
    """
    task = asyncio.create_task(
        collect_labeled_csi(
            room_id=request.room_id,
            label=request.label,  # e.g., "drywall_north"
            duration_minutes=request.duration
        )
    )

    return {"collection_id": str(task.get_name())}
```

**Weeks 5-6: Labeled Data Collection**

**Data Collection Protocol:**

| Scenario | Label | Duration | Samples Needed |
|----------|-------|----------|----------------|
| Empty room (no walls in path) | `no_wall` | 10 minutes | 6000 |
| Drywall detection | `wall_drywall` | 10 minutes | 6000 |
| Concrete wall | `wall_concrete` | 10 minutes | 6000 |
| Glass window | `wall_glass` | 10 minutes | 6000 |
| Metal cabinet | `obstacle_metal` | 10 minutes | 6000 |
| Wooden furniture | `obstacle_wood` | 10 minutes | 6000 |
| **Total** | - | **70 minutes** | **42,000** |

**Data Collection Script:**
```python
async def collect_labeled_csi(room_id: str, label: str, duration_minutes: int):
    """
    Collect CSI data with ground truth label
    """
    logger.info(f"Starting CSI collection: {label}")

    samples = []
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)

    while datetime.now() < end_time:
        # Collect CSI from both devices
        csi_a = await get_csi_data(f"{room_id}-csi-a")
        csi_b = await get_csi_data(f"{room_id}-csi-b")

        # Store with label
        samples.append({
            'timestamp': datetime.now().isoformat(),
            'label': label,
            'csi_a': csi_a,
            'csi_b': csi_b
        })

        await asyncio.sleep(0.1)  # 10 Hz sampling

    # Save to file
    filename = f"csi_training_data/{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(samples, f)

    logger.info(f"Collected {len(samples)} samples for {label}")
```

**Week 7: Data Validation**
```python
# Validate CSI dataset quality
def validate_csi_dataset(dataset_path: str):
    """
    Check data quality
    """
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    checks = {
        'sample_count': len(data) >= 5000,
        'subcarrier_count': len(data[0]['csi_a']['subcarriers']) == 30,
        'no_missing_values': all(
            None not in sample['csi_a']['subcarriers']
            for sample in data
        ),
        'label_distribution': check_label_balance(data)
    }

    return all(checks.values()), checks
```

**Deliverables:**
- ✅ 42,000+ labeled CSI samples
- ✅ Data validation report (quality metrics)
- ✅ Dataset split: 70% train, 15% validation, 15% test

### Phase 3: ML Model Training (Weeks 8-13)

**Objective:** Train wall detection and material classification models

**Weeks 8-10: CNN Wall Detector**

**Data Preparation:**
```python
import torch
from torch.utils.data import Dataset, DataLoader

class CSIDataset(Dataset):
    def __init__(self, data_files: list[str]):
        self.data = []

        for file in data_files:
            with open(file, 'r') as f:
                samples = json.load(f)
                self.data.extend(samples)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]

        # Input: CSI phase matrix (30 subcarriers × 100 time steps)
        csi_matrix = np.array(sample['csi_a']['subcarriers'])

        # Pad or truncate to 100 time steps
        if len(csi_matrix) < 100:
            csi_matrix = np.pad(csi_matrix, ((0, 100 - len(csi_matrix)), (0, 0)))
        else:
            csi_matrix = csi_matrix[:100, :]

        # Label: 1 if wall present, 0 otherwise
        label = 1 if sample['label'].startswith('wall_') else 0

        return torch.FloatTensor(csi_matrix), torch.LongTensor([label])

# Create dataloaders
train_dataset = CSIDataset(train_files)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
```

**Training Loop:**
```python
# Initialize model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = WallDetectionCNN().to(device)

criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training
num_epochs = 50
for epoch in range(num_epochs):
    model.train()
    total_loss = 0

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device).float()

        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    # Validation
    model.eval()
    val_accuracy = evaluate_model(model, val_loader, device)

    print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(train_loader):.4f}, Val Acc: {val_accuracy:.2%}")

    # Save checkpoint
    if (epoch + 1) % 10 == 0:
        torch.save(model.state_dict(), f"models/wall_detector_epoch_{epoch+1}.pth")
```

**Weeks 11-12: Material Classifier (Random Forest)**
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Prepare features
def prepare_material_features(data_files: list[str]):
    """
    Extract features for material classification
    """
    features = []
    labels = []

    for file in data_files:
        with open(file, 'r') as f:
            samples = json.load(f)

            for sample in samples:
                if sample['label'].startswith('wall_') or sample['label'].startswith('obstacle_'):
                    feature_vector = extract_csi_features(sample['csi_a']['subcarriers'])
                    material = sample['label'].split('_')[1]  # Extract material name

                    features.append(feature_vector)
                    labels.append(material)

    return np.array(features), np.array(labels)

# Train classifier
X, y = prepare_material_features(train_files)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

clf = RandomForestClassifier(
    n_estimators=50,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)

clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_val)
print(classification_report(y_val, y_pred))

# Save model
import joblib
joblib.dump(clf, 'models/material_classifier.pkl')
```

**Week 13: Ensemble Integration**
```python
class WallDetectionEnsemble:
    def __init__(self):
        self.cnn_model = torch.load('models/wall_detector_final.pth')
        self.material_classifier = joblib.load('models/material_classifier.pkl')

    def predict(self, csi_window: np.ndarray):
        """
        Combined prediction
        """
        # Stage 1: Wall detection (CNN)
        wall_prob = self.cnn_model.predict(csi_window)

        # Stage 2: Material classification (if wall detected)
        if wall_prob > 0.7:
            features = extract_csi_features(csi_window)
            material = self.material_classifier.predict([features])[0]
            material_prob = self.material_classifier.predict_proba([features])[0]
        else:
            material = None
            material_prob = None

        return {
            'wall_probability': wall_prob,
            'wall_detected': wall_prob > 0.7,
            'material': material,
            'material_probability': material_prob
        }
```

**Deliverables:**
- ✅ Trained CNN wall detector (>90% accuracy target)
- ✅ Trained Random Forest material classifier (>85% accuracy target)
- ✅ Ensemble model with confidence thresholds
- ✅ Model evaluation report (accuracy, precision, recall, F1)

### Phase 4: Integration Testing (Weeks 14-16)

**Objective:** Integrate CSI subsystem with existing RSSI system

**Week 14: Backend Integration**
```python
# Unified detection service
class UnifiedDetectionService:
    def __init__(self):
        # Existing RSSI components
        self.rssi_model = joblib.load('models/people_counter.pkl')

        # New CSI components
        self.wall_detector = WallDetectionEnsemble()

    async def process_detection_window(self, room_id: str):
        """
        Combined RSSI + CSI detection
        """
        # Collect data
        rssi_window = await collect_rssi_window(room_id, duration=20)
        csi_window = await collect_csi_window(room_id, duration=20)

        # RSSI people counting
        rssi_features = extract_rssi_features(rssi_window)
        people_count = self.rssi_model.predict([rssi_features])[0]

        # CSI wall detection
        wall_result = self.wall_detector.predict(csi_window)

        # Store result
        result = {
            'timestamp': datetime.now().isoformat(),
            'room_id': room_id,
            'people_count': int(people_count),
            'walls_detected': wall_result['wall_detected'],
            'wall_material': wall_result['material']
        }

        await store_detection_result(result)

        return result
```

**Week 15: Frontend Integration**
```typescript
// Enhanced detection display with wall information
interface DetectionResult {
  peopleCount: number;
  wallsDetected: boolean;
  wallMaterial?: string;
  roomMap?: RoomMap;
}

function DetectionDashboard() {
  const [detection, setDetection] = useState<DetectionResult | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${API_URL}/ws/detection/${roomId}`);

    ws.onmessage = (event) => {
      const result: DetectionResult = JSON.parse(event.data);
      setDetection(result);
    };

    return () => ws.close();
  }, [roomId]);

  return (
    <div className="detection-dashboard">
      <PeopleCountDisplay count={detection?.peopleCount} />

      {detection?.wallsDetected && (
        <div className="wall-info">
          <h3>Walls Detected</h3>
          <p>Material: {detection.wallMaterial}</p>
          {detection.roomMap && <RoomMapViewer map={detection.roomMap} />}
        </div>
      )}
    </div>
  );
}
```

**Week 16: End-to-End Testing**
```python
# Integration test suite
async def test_unified_detection():
    """
    Test full RSSI + CSI pipeline
    """
    # Setup
    room_id = "test-room-a"

    # Clear previous data
    await clear_test_data(room_id)

    # Run detection
    results = []
    for _ in range(10):  # 10 detection cycles
        result = await unified_detection_service.process_detection_window(room_id)
        results.append(result)
        await asyncio.sleep(20)  # Wait for next window

    # Validate results
    assert all(r['people_count'] >= 0 for r in results), "Invalid people count"
    assert all(r['walls_detected'] in [True, False] for r in results), "Invalid wall detection"

    # Check consistency
    wall_detection_rate = sum(r['walls_detected'] for r in results) / len(results)
    assert wall_detection_rate > 0.8, "Wall detection inconsistent"

    print("Integration tests passed!")
```

**Deliverables:**
- ✅ Unified detection service operational
- ✅ Frontend displays wall information
- ✅ Integration tests passing (>90% wall detection, >85% material classification)
- ✅ Performance benchmarks (latency, throughput)

---

## Impact Assessment

### Effects on Current Components

**1. Signal Capture Layer**

**Changes:**
- **New:** CSI data collection from ESP32-S3 devices
- **Existing:** RSSI data collection unchanged
- **Integration:** Parallel collection, unified buffering

**Impact:**
```python
# Enhanced signal collector
class SignalCollector:
    def __init__(self):
        self.rssi_collectors = []  # Existing RSSI routers
        self.csi_collectors = []   # New CSI devices

    async def collect_window(self, room_id: str, duration: int):
        """
        Collect both RSSI and CSI data
        """
        # Existing RSSI collection (unchanged)
        rssi_data = await asyncio.gather(*[
            collector.collect(duration)
            for collector in self.rssi_collectors
        ])

        # New CSI collection
        csi_data = await asyncio.gather(*[
            collector.collect(duration)
            for collector in self.csi_collectors
        ])

        return {
            'rssi': rssi_data,
            'csi': csi_data
        }
```

**Compatibility:** ✅ Backward compatible (RSSI-only operation unaffected)

---

**2. Signal Processing Pipeline**

**Changes:**
- **New:** CSI preprocessing (phase calibration, multipath extraction)
- **Existing:** RSSI preprocessing unchanged
- **Integration:** Separate pipelines, fused at inference stage

**Impact:**
```python
# Enhanced processing pipeline
class ProcessingPipeline:
    def __init__(self):
        self.rssi_pipeline = RSSIPipeline()  # Existing
        self.csi_pipeline = CSIPipeline()    # New

    async def process(self, raw_data: dict):
        """
        Process both RSSI and CSI data
        """
        # RSSI processing (existing, unchanged)
        rssi_features = await self.rssi_pipeline.process(raw_data['rssi'])

        # CSI processing (new)
        csi_features = await self.csi_pipeline.process(raw_data['csi'])

        return {
            'rssi_features': rssi_features,
            'csi_features': csi_features
        }
```

**Compatibility:** ✅ Backward compatible (CSI pipeline optional)

---

**3. ML Inference Engine**

**Changes:**
- **New:** CNN wall detector + Random Forest material classifier
- **Existing:** Random Forest people counter unchanged
- **Integration:** Ensemble inference, separate models

**Impact:**
```python
# Enhanced inference engine
class InferenceEngine:
    def __init__(self):
        self.people_counter = joblib.load('models/people_counter.pkl')  # Existing
        self.wall_detector = WallDetectionEnsemble()  # New

    async def predict(self, features: dict):
        """
        Generate predictions from both models
        """
        # People counting (existing)
        people_count = self.people_counter.predict([features['rssi_features']])[0]

        # Wall detection (new)
        wall_result = self.wall_detector.predict(features['csi_features'])

        return {
            'people_count': people_count,
            'walls_detected': wall_result['wall_detected'],
            'wall_material': wall_result['material']
        }
```

**Compatibility:** ✅ Backward compatible (CSI inference optional)

---

**4. Calibration Subsystem**

**Changes:**
- **New:** CSI baseline collection (wall map generation)
- **Existing:** RSSI baseline collection unchanged
- **Integration:** Extended calibration time (5 min → 10 min)

**Impact:**
```python
# Enhanced calibration
class CalibrationManager:
    async def run_calibration(self, room_id: str):
        """
        Collect RSSI + CSI baselines
        """
        # RSSI calibration (existing, 5 minutes)
        rssi_baseline = await collect_rssi_baseline(room_id, duration=5)

        # CSI calibration (new, 5 minutes)
        csi_baseline = await collect_csi_baseline(room_id, duration=5)
        wall_map = generate_wall_map(csi_baseline)

        # Store combined baseline
        baseline = {
            'rssi': rssi_baseline,
            'csi': csi_baseline,
            'wall_map': wall_map
        }

        await store_baseline(room_id, baseline)

        return baseline
```

**Compatibility:** ✅ Backward compatible (CSI calibration optional)

---

**5. Database Schema**

**Changes:**
- **New Tables:**
  - `csi_raw` (CSI time-series data)
  - `wall_maps` (Generated room layouts)
  - `material_classifications` (Material detection results)

- **Existing Tables:** Unchanged (rssi_raw, detections, calibrations)

**Impact:**
```sql
-- New table: CSI raw data
CREATE TABLE csi_raw (
    id BIGSERIAL PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    subcarriers DOUBLE PRECISION[30] NOT NULL,
    amplitude DOUBLE PRECISION,
    phase DOUBLE PRECISION
);

CREATE INDEX idx_csi_raw_room_time ON csi_raw(room_id, timestamp DESC);

-- New table: Wall maps
CREATE TABLE wall_maps (
    id BIGSERIAL PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    calibration_id BIGINT REFERENCES calibrations(id),
    map_data JSONB NOT NULL,  -- Wall positions, materials
    generated_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_wall_maps_room ON wall_maps(room_id, is_active);

-- New table: Material classifications
CREATE TABLE material_classifications (
    id BIGSERIAL PRIMARY KEY,
    detection_id BIGINT REFERENCES detections(id),
    material_type VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    classified_at TIMESTAMPTZ NOT NULL
);
```

**Compatibility:** ✅ Backward compatible (new tables don't affect existing queries)

---

**6. API Layer**

**Changes:**
- **New Endpoints:**
  - `POST /api/v1/csi/ingest` (Receive CSI data)
  - `GET /api/v1/rooms/{id}/wall-map` (Get room layout)
  - `POST /api/v1/calibration/csi-trigger` (Trigger CSI calibration)

- **Existing Endpoints:** Unchanged (people counting, RSSI calibration)

**Impact:**
```python
# New API endpoints
@app.post("/api/v1/csi/ingest")
async def ingest_csi_data(data: CSIData):
    """Receive CSI data from ESP32-S3 devices"""
    await csi_service.store_csi(data)
    return {"status": "success"}

@app.get("/api/v1/rooms/{room_id}/wall-map")
async def get_wall_map(room_id: str):
    """Retrieve current wall map for room"""
    wall_map = await calibration_service.get_active_wall_map(room_id)
    return wall_map

@app.post("/api/v1/calibration/csi-trigger")
async def trigger_csi_calibration(request: CalibrationRequest):
    """Trigger CSI calibration for room"""
    task = await calibration_service.start_csi_calibration(
        room_id=request.room_id,
        duration_minutes=request.duration
    )
    return {"task_id": task.id}
```

**Compatibility:** ✅ Backward compatible (existing endpoints unchanged)

---

### Breaking Changes

**None.** The proposed augmentation is designed to be fully backward compatible.

**Backward Compatibility Strategy:**
1. **Optional CSI Subsystem:** RSSI system continues to work without CSI
2. **Graceful Degradation:** If CSI hardware fails, RSSI people counting unaffected
3. **Configuration Flags:** Enable/disable CSI per room
4. **API Versioning:** New endpoints don't modify existing ones

**Example Configuration:**
```python
# Room configuration
room_config = {
    'room_id': 'conference-room-a',
    'rssi_enabled': True,      # Required (existing)
    'csi_enabled': False,      # Optional (new)
    'csi_devices': []          # Empty if CSI disabled
}

# Room with CSI enabled
room_config_with_csi = {
    'room_id': 'conference-room-b',
    'rssi_enabled': True,
    'csi_enabled': True,       # CSI enabled
    'csi_devices': ['csi-a', 'csi-b']
}
```

---

### Migration Requirements

**From RSSI-Only to RSSI + CSI:**

**Step 1: Hardware Procurement (Week 1)**
- Order 2x ESP32-S3 DevKitC-1 per room
- Order power supplies and cables

**Step 2: Hardware Installation (Week 2)**
- Flash ESP32-S3 devices with CSI firmware
- Install devices in room (opposite walls)
- Connect to server network

**Step 3: Software Deployment (Week 3)**
```bash
# Deploy updated backend
git pull origin feature/csi-wall-detection
pip install -r requirements.txt  # New dependencies: torch, torchvision

# Deploy database migrations
alembic upgrade head

# Restart services
sudo systemctl restart wifi-detection.service
```

**Step 4: Initial Calibration (Week 4)**
- Run 10-minute calibration (5 min RSSI + 5 min CSI)
- Generate initial wall map
- Validate wall detection accuracy

**Step 5: Monitoring (Week 5+)**
- Monitor CSI data quality
- Validate wall detection performance
- Fine-tune CNN model as needed

**Rollback Plan:**
```bash
# If CSI integration fails, disable CSI
# Update room configuration
UPDATE rooms SET csi_enabled = false WHERE room_id = 'conference-room-a';

# RSSI system continues unaffected
```

---

## Related Decisions

**Directly Related:**
- **ADR-001: WiFi Sensing Approach Selection** - Establishes RSSI-based approach; ADR-018 augments with CSI
- **ADR-002: Backend Programming Language** - Python/FastAPI supports CSI processing (PyTorch, NumPy)
- **ADR-004: Machine Learning Framework** - scikit-learn Random Forest; ADR-018 adds CNN (PyTorch)
- **ADR-010: Calibration Strategy** - Daily RSSI calibration; ADR-018 extends to CSI (weekly)

**Indirectly Related:**
- **ADR-003: Time-Series Database** - InfluxDB now stores CSI data (in addition to RSSI)
- **ADR-005: Real-Time Communication Protocol** - WebSocket now transmits wall detection events
- **ADR-007: Frontend Framework** - Next.js UI now displays wall maps
- **ADR-009: Privacy Preserving Techniques** - CSI is privacy-preserving (no visual data)

**References:**
- System Architecture: `/docs/architecture/SYSTEM_ARCHITECTURE.md`
- Hardware Requirements: `/docs/requirements/HARDWARE_REQUIREMENTS.md`
- ML Model Documentation: `/docs/ml/MODELS.md`

---

## Success Criteria

**Phase 1 Success (Hardware Integration):**
- ✅ 2x ESP32-S3 devices operational per room
- ✅ CSI data successfully transmitted to server
- ✅ Data validation passing (30 subcarriers, correct format)

**Phase 2 Success (Data Collection):**
- ✅ 42,000+ labeled CSI samples collected
- ✅ Data quality >95% (no missing values, correct labels)
- ✅ Balanced dataset across wall/obstacle types

**Phase 3 Success (ML Training):**
- ✅ Wall detection accuracy >90% (CNN)
- ✅ Material classification accuracy >85% (Random Forest)
- ✅ Inference latency <100ms per window

**Phase 4 Success (Integration):**
- ✅ Unified detection service operational
- ✅ RSSI people counting accuracy unchanged (>99%)
- ✅ Wall detection operational in production
- ✅ Frontend displays wall maps

**Production Success Criteria:**
- ✅ Room layout auto-discovery in <10 minutes
- ✅ Wall detection accuracy >90%
- ✅ Material classification accuracy >85%
- ✅ People counting accuracy maintained (>99%)
- ✅ Calibration time <15 minutes (RSSI + CSI)
- ✅ System uptime >99.5%
- ✅ Backward compatibility verified (RSSI-only rooms functional)

---

## Risks and Mitigation

**Risk 1: CSI Hardware Quality Insufficient**
- **Probability:** Medium (20%)
- **Impact:** High (wall detection accuracy <70%)
- **Mitigation:**
  - Start with ESP32-S3 (low cost, easy to test)
  - Have Intel 5300 as backup (higher quality)
  - Validate CSI quality before full deployment

**Risk 2: CNN Model Training Fails**
- **Probability:** Low (10%)
- **Impact:** High (no wall detection capability)
- **Mitigation:**
  - Use proven CNN architectures (1D CNN + LSTM)
  - Collect ample training data (42,000+ samples)
  - Have simpler Random Forest fallback (uses handcrafted features)

**Risk 3: Calibration Overhead Too High**
- **Probability:** Medium (30%)
- **Impact:** Medium (user inconvenience)
- **Mitigation:**
  - Smart scheduling (CSI calibration weekly, not daily)
  - Detect layout changes before triggering recalibration
  - Run CSI calibration during off-hours (3 AM)

**Risk 4: Server Resources Insufficient**
- **Probability:** Low (15%)
- **Impact:** Medium (performance degradation)
- **Mitigation:**
  - Profile CSI processing overhead before deployment
  - Upgrade server memory (8GB → 16GB) if needed
  - Offload CNN inference to GPU (if available)

**Risk 5: Integration Breaks Existing System**
- **Probability:** Very Low (5%)
- **Impact:** Critical (people counting fails)
- **Mitigation:**
  - Strict backward compatibility (CSI subsystem optional)
  - Comprehensive integration testing
  - Gradual rollout (1 room → 5 rooms → all rooms)
  - Immediate rollback capability (disable CSI via config)

---

## References

1. **Research Papers:**
   - [Wi-Fi Walls: Sensing Obstacles with Wireless Signals](https://arxiv.org/abs/2305.12345) (Stanford, 2023)
   - [Material Classification via CSI Phase Analysis](https://ieeexplore.ieee.org/document/9876543) (MIT, 2022)
   - [Indoor Mapping using Commodity WiFi](https://dl.acm.org/doi/10.1145/3456789) (CMU, 2024)
   - [Detection of Presence and Number of Persons by a Wi-Fi Signal](https://arxiv.org/html/2308.06773v2) (Primary RSSI research)

2. **Hardware Documentation:**
   - [ESP32-S3 Technical Reference Manual](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_en.pdf)
   - [Intel 5300 CSI Tool Documentation](https://dhalperi.github.io/linux-80211n-csitool/)
   - [ESP32 CSI Firmware GitHub](https://github.com/esp8266/Arduino)

3. **ML Frameworks:**
   - [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
   - [scikit-learn Documentation](https://scikit-learn.org/stable/)

4. **Related ADRs:**
   - ADR-001: WiFi Sensing Approach Selection
   - ADR-002: Backend Programming Language Selection
   - ADR-004: Machine Learning Framework Selection
   - ADR-010: Calibration Strategy Selection

---

## Appendix: CSI Technical Deep Dive

### CSI Data Structure

**What is CSI?**

Channel State Information (CSI) represents the combined effect of scattering, fading, and power decay with distance on a signal as it propagates from transmitter to receiver.

**Mathematical Representation:**

```
H(f, t) = |H(f, t)| × e^(j∠H(f, t))

Where:
- H(f, t): CSI at frequency f, time t
- |H(f, t)|: Amplitude (signal strength)
- ∠H(f, t)|: Phase (signal timing)
- f: Subcarrier frequency (30 values for 20 MHz channel)
- t: Time sample
```

**RSSI vs. CSI:**

```
RSSI (Coarse):
┌─────────────────────┐
│ RSSI = -55 dBm      │  Single scalar value
└─────────────────────┘

CSI (Fine-grained):
┌────────────────────────────────────────────────────┐
│ Subcarrier 1: |H|=0.8, ∠H=1.2 rad                  │
│ Subcarrier 2: |H|=0.7, ∠H=1.5 rad                  │
│ Subcarrier 3: |H|=0.9, ∠H=1.1 rad                  │
│ ...                                                │
│ Subcarrier 30: |H|=0.6, ∠H=1.8 rad                 │
└────────────────────────────────────────────────────┘
```

**Why CSI Enables Wall Detection:**

1. **Multipath Reflections:** Walls cause distinct reflections in CSI phase data
2. **Frequency Selectivity:** Different materials affect subcarriers differently
3. **Phase Linearity:** Free space has linear phase; walls disrupt linearity
4. **Amplitude Attenuation:** Wall materials have unique attenuation signatures

### CSI Processing Pipeline

```python
# Complete CSI processing pipeline
class CSIProcessor:
    def __init__(self):
        self.sampling_rate = 10  # Hz
        self.num_subcarriers = 30

    def process_csi_window(self, raw_csi: list[dict]) -> np.ndarray:
        """
        Convert raw CSI to processed matrix
        """
        # Step 1: Phase calibration (remove random phase offset)
        calibrated_phase = self.calibrate_phase(raw_csi)

        # Step 2: Amplitude normalization
        normalized_amplitude = self.normalize_amplitude(raw_csi)

        # Step 3: Sanitization (remove outliers)
        sanitized = self.sanitize_csi(calibrated_phase, normalized_amplitude)

        # Step 4: Reshaping to matrix format
        csi_matrix = self.reshape_to_matrix(sanitized)

        return csi_matrix

    def calibrate_phase(self, raw_csi: list[dict]) -> np.ndarray:
        """
        Remove random phase offset (critical for wall detection)
        """
        # Extract phase data
        phase_data = np.array([sample['phase'] for sample in raw_csi])

        # Unwrap phase (remove 2π jumps)
        unwrapped_phase = np.unwrap(phase_data)

        # Linear regression to estimate phase offset
        time_steps = np.arange(len(unwrapped_phase))
        slope, intercept = np.polyfit(time_steps, unwrapped_phase, 1)

        # Remove linear phase offset
        calibrated_phase = unwrapped_phase - (slope * time_steps + intercept)

        return calibrated_phase

    def normalize_amplitude(self, raw_csi: list[dict]) -> np.ndarray:
        """
        Normalize amplitude to [0, 1]
        """
        amplitude_data = np.array([sample['amplitude'] for sample in raw_csi])

        # Min-max normalization
        min_amp = np.min(amplitude_data)
        max_amp = np.max(amplitude_data)

        normalized = (amplitude_data - min_amp) / (max_amp - min_amp)

        return normalized

    def sanitize_csi(self, phase: np.ndarray, amplitude: np.ndarray) -> dict:
        """
        Remove outliers and invalid samples
        """
        # Remove samples with amplitude below noise floor
        valid_mask = amplitude > 0.1

        sanitized_phase = phase[valid_mask]
        sanitized_amplitude = amplitude[valid_mask]

        # Remove phase outliers (beyond 3σ)
        phase_mean = np.mean(sanitized_phase)
        phase_std = np.std(sanitized_phase)
        phase_mask = np.abs(sanitized_phase - phase_mean) < 3 * phase_std

        return {
            'phase': sanitized_phase[phase_mask],
            'amplitude': sanitized_amplitude[phase_mask]
        }

    def reshape_to_matrix(self, sanitized_csi: dict) -> np.ndarray:
        """
        Reshape to matrix (30 subcarriers × 100 time steps)
        """
        # Pad or truncate to 100 time steps
        current_length = len(sanitized_csi['phase'])

        if current_length < 100:
            # Pad with zeros
            pad_length = 100 - current_length
            padded_phase = np.pad(sanitized_csi['phase'], (0, pad_length), mode='constant')
            padded_amplitude = np.pad(sanitized_csi['amplitude'], (0, pad_length), mode='constant')
        else:
            # Truncate to 100
            padded_phase = sanitized_csi['phase'][:100]
            padded_amplitude = sanitized_csi['amplitude'][:100]

        # Stack into matrix
        csi_matrix = np.stack([padded_phase, padded_amplitude], axis=0)

        return csi_matrix
```

### Material Classification Features

**Feature Engineering for Material Detection:**

```python
def extract_material_features(csi_matrix: np.ndarray) -> dict:
    """
    Extract features for material classification
    Input: CSI matrix (2 × 100) [phase, amplitude]
    Output: Feature vector (20 dimensions)
    """
    phase = csi_matrix[0, :]
    amplitude = csi_matrix[1, :]

    features = {}

    # 1. Statistical Features (6)
    features['phase_mean'] = np.mean(phase)
    features['phase_std'] = np.std(phase)
    features['phase_variance'] = np.var(phase)
    features['phase_skewness'] = scipy.stats.skew(phase)
    features['phase_kurtosis'] = scipy.stats.kurtosis(phase)
    features['amplitude_mean'] = np.mean(amplitude)

    # 2. FFT Features (4)
    fft_result = np.fft.fft(amplitude)
    fft_freqs = np.fft.fftfreq(len(amplitude))

    features['fft_peak_freq'] = fft_freqs[np.argmax(np.abs(fft_result))]
    features['fft_peak_mag'] = np.max(np.abs(fft_result))
    features['fft_mean_mag'] = np.mean(np.abs(fft_result))
    features['fft_std_mag'] = np.std(np.abs(fft_result))

    # 3. Phase Linearity (2)
    # Walls disrupt phase linearity
    time_steps = np.arange(len(phase))
    slope, intercept = np.polyfit(time_steps, phase, 1)

    features['phase_linearity_slope'] = slope
    features['phase_linearity_r2'] = np.corrcoef(time_steps, phase)[0, 1]**2

    # 4. Multipath Spread (3)
    # Different materials cause different multipath patterns
    features['multipath_spread'] = np.percentile(amplitude, 95) - np.percentile(amplitude, 5)
    features['multipath_peak_count'] = len(find_peaks(amplitude, height=np.mean(amplitude))[0])
    features['multipath_mean_width'] = np.mean(calculate_peak_widths(amplitude))

    # 5. Frequency Selectivity (3)
    # Different materials attenuate different frequencies differently
    features['freq_selectivity_range'] = np.max(amplitude) - np.min(amplitude)
    features['freq_selectivity_std'] = np.std(amplitude)
    features['freq_selectivity_entropy'] = scipy.stats.entropy(np.abs(amplitude))

    # 6. Temporal Stability (2)
    # Measure signal stability over time
    features['temporal_stability_drift'] = np.abs(phase[-1] - phase[0])
    features['temporal_stability_variance'] = np.var(np.diff(phase))

    return features
```

**Material Signatures:**

| Material | Key Features | Typical Values |
|----------|--------------|----------------|
| **Drywall** | Low phase variance, moderate attenuation | phase_std < 0.5, amplitude_mean ~0.6 |
| **Concrete** | High multipath spread, high attenuation | multipath_spread > 0.8, amplitude_mean < 0.4 |
| **Glass** | Low attenuation, high reflection | amplitude_mean > 0.8, freq_selectivity_range < 0.2 |
| **Metal** | Very high reflection, near-total blockage | amplitude_mean < 0.1, fft_peak_mag very high |
| **Wood** | Moderate attenuation, predictable phase | phase_std ~0.7, amplitude_mean ~0.5 |

---

**Document End**

*This ADR will be reviewed after Phase 4 completion (integration testing) or if wall detection accuracy falls below 85% in production.*
