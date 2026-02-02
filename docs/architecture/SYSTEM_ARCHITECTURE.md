# WiFi-Based People Detection System - Architecture Document

**Version:** 1.0.0
**Date:** 2025-02-02
**Author:** System Architecture Team
**Status:** Design Draft

---

## Executive Summary

This document presents a comprehensive system architecture for a WiFi-based people detection web application. The system leverages Radio Signal Strength Indicator (RSSI) data and Channel State Information (CSI) from standard WiFi routers to detect human presence, count individuals, and potentially estimate poses/movements. The architecture supports real-time processing with 20-second time windows, requires daily calibration with noise data, and achieves 98-99% accuracy using Random Forest machine learning models.

### Key Requirements
- **Minimum Hardware:** 4-5 WiFi detectors per space for optimal accuracy
- **Processing Latency:** Real-time processing with 20-second sliding windows
- **Calibration:** Daily noise baseline collection required
- **Accuracy:** 98-99% for people counting (presence detection higher)
- **Scalability:** Support multi-room deployments and edge processing options

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [High-Level System Architecture](#3-high-level-system-architecture)
4. [Signal Capture Layer](#4-signal-capture-layer)
5. [Signal Processing Pipeline](#5-signal-processing-pipeline)
6. [ML/AI Inference Engine](#6-mlai-inference-engine)
7. [Web Application Backend](#7-web-application-backend)
8. [Frontend Visualization](#8-frontend-visualization)
9. [Technology Stack](#9-technology-stack)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Security and Privacy](#11-security-and-privacy)
12. [Architecture Decision Records](#12-architecture-decision-records)
13. [Scalability Strategy](#13-scalability-strategy)
14. [Monitoring and Observability](#14-monitoring-and-observability)

---

## 1. System Overview

### 1.1 System Purpose

The WiFi-Based People Detection System provides a non-intrusive, camera-free solution for monitoring human presence and occupancy in indoor spaces. By analyzing WiFi signal variations caused by human bodies, the system enables:

- **Presence Detection:** Binary determination of whether humans are present
- **People Counting:** Accurate estimation of the number of individuals (0-10+)
- **Movement Tracking:** Detection of motion patterns and pose estimation (stretch goal)

### 1.2 Core Capabilities

```
┌─────────────────────────────────────────────────────────────┐
│                   SYSTEM CAPABILITIES                        │
├─────────────────────────────────────────────────────────────┤
│ ✓ Real-time Detection (20-second windows)                   │
│ ✓ Multi-room Support                                        │
│ ✓ Edge Processing Option                                    │
│ ✓ Cloud Backup & Analytics                                  │
│ ✓ RESTful API + WebSocket Real-time Updates                 │
│ ✓ Historical Data Visualization                             │
│ ✓ Alert System (threshold-based)                            │
│ ✓ Configuration Web UI                                       │
│ ✓ Daily Auto-calibration                                    │
│ ✓ Privacy-Preserving (no camera/video)                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 System Boundaries

**In Scope:**
- WiFi signal capture from standard 802.11n/ac/ax routers
- RSSI and CSI data processing
- Machine learning inference for counting
- Web-based dashboard and configuration
- Multi-room deployment support
- Historical data analytics

**Out of Scope:**
- Individual identification (who is present)
- Precise localization (cm-level accuracy)
- Biometric data collection
- Outdoor environments
- Integration with building automation (future enhancement)

---

## 2. Architecture Principles

### 2.1 Design Principles

1. **Privacy-First:** No cameras, no biometric data, no personal identification
2. **Real-Time Responsiveness:** 20-second sliding windows for live detection
3. **Scalability:** Support single-room to multi-building deployments
4. **Fault Tolerance:** Graceful degradation when detectors fail
5. **Modularity:** Loosely coupled components for independent evolution
6. **Observability:** Comprehensive monitoring and debugging capabilities
7. **Security:** End-to-end encryption, secure authentication
8. **Cost-Effectiveness:** Leverage existing WiFi infrastructure

### 2.2 Quality Attributes

| Attribute | Priority | Target Metric |
|-----------|----------|---------------|
| **Accuracy** | Critical | 98-99% counting, >99% presence |
| **Latency** | High | <25 seconds end-to-end |
| **Availability** | High | 99.5% uptime |
| **Scalability** | Medium | Support 100+ concurrent rooms |
| **Security** | Critical | Zero known vulnerabilities |
| **Maintainability** | Medium | <2 days to onboard developers |

---

## 3. High-Level System Architecture

### 3.1 Conceptual Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHYSICAL LAYER                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Router 1 │  │ Router 2 │  │ Router 3 │  │ Router 4 │  │ Router 5 │     │
│  │ (AP)     │  │ (AP)     │  │ (AP)     │  │ (AP)     │  │ (AP)     │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┴─────────────┘           │
│                             WiFi Signal Space                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL CAPTURE LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Signal Collector Service (Python/Node.js on Edge Device)            │  │
│  │  - RSSI Data Collection (1Hz sampling per detector)                   │  │
│  │  - CSI Extraction (if supported by hardware)                         │  │
│  │  - Data Buffering (20-second sliding windows)                        │  │
│  │  - Transmission to Processing Layer                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SIGNAL PROCESSING PIPELINE                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Noise      │→ │ Feature    │→ │ Window     │→ │ Normalized │           │
│  │ Calibration│  │ Extraction │  │ Aggregation│  │ Features   │           │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Calibration Manager                                                 │  │
│  │  - Daily noise baseline collection (empty room, 5 min)               │  │
│  │  - Statistical baseline storage                                      │  │
│  │  - Automatic scheduling                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML/AI INFERENCE ENGINE                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Model Deployment Service                                             │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │  │
│  │  │ Presence       │  │ People Count   │  │ Movement       │         │  │
│  │  │ Detection Model│  │ Model (RF)     │  │ Analysis (SVM) │         │  │
│  │  │ (Statistical)  │  │ 98-99% Acc.    │  │ (Stretch Goal) │         │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Training Pipeline                                                    │  │
│  │  - Labeled data collection                                            │  │
│  │  - Feature engineering                                                 │  │
│  │  - Model training (scikit-learn)                                      │  │
│  │  - Model versioning & deployment                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WEB APPLICATION BACKEND                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  REST API Layer (FastAPI/Flask/Express)                               │  │
│  │  - /api/detection/presence                                             │  │
│  │  - /api/detection/count                                                │  │
│  │  - /api/calibration/schedule                                           │  │
│  │  - /api/config/detectors                                               │  │
│  │  - /api/history/occupancy                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  WebSocket Service (Socket.io/WS)                                     │  │
│  │  - Real-time detection updates                                         │  │
│  │  - Live occupancy streaming                                            │  │
│  │  - Alert notifications                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│       │                                                                     │
│       ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Data Management Layer                                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ Time-Series  │  │ PostgreSQL   │  │ Redis Cache  │               │  │
│  │  │ DB           │  │ (Metadata)   │  │ (Session)    │               │  │
│  │  │ (InfluxDB)   │  │              │  │              │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND VISUALIZATION                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Web Dashboard (React/Next.js + TailwindCSS)                          │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │  │
│  │  │ Real-time      │  │ Historical     │  │ Configuration  │          │  │
│  │  │ Dashboard      │  │ Analytics      │  │ Panel          │          │  │
│  │  │ - Count Gauge  │  │ - Trends       │  │ - Detector Mgmt│          │  │
│  │  │ - Presence LED │  │ - Heatmaps     │  │ - Cal. Sched.  │          │  │
│  │  │ - Alert Feed   │  │ - Export Data  │  │ - User Settings│          │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Interaction Flow

**Detection Flow (Real-time):**
```
1. WiFi Router → RSSI Broadcast (1Hz)
2. Signal Collector → Buffer 20-second window
3. Signal Processing → Feature extraction (std dev, mean, etc.)
4. Noise Calibration → Subtract baseline
5. ML Inference → Presence + Count prediction
6. WebSocket Service → Push update to frontend
7. Dashboard → Visual update (gauge, chart, alert)
```

**Calibration Flow (Daily):**
```
1. Scheduler (Cron) → Trigger calibration job
2. Calibration Manager → Request empty room
3. Signal Collector → Capture 5 min noise data
4. Noise Calibration → Compute baseline statistics
5. Database → Store calibration parameters
6. Notification → Alert user calibration complete
```

---

## 4. Signal Capture Layer

### 4.1 Hardware Interface

**Supported WiFi Router Standards:**
- 802.11n (WiFi 4) - Minimum requirement
- 802.11ac (WiFi 5) - Recommended for CSI
- 802.11ax (WiFi 6) - Advanced CSI capabilities

**Hardware Requirements per Detector:**
- WiFi Access Point with promiscuous mode support
- OpenWRT or custom firmware (for CSI extraction)
- Network connectivity to edge processing device
- Power-over-Ethernet (PoE) or reliable power supply

**Data Capture Methods:**

| Method | Accuracy | Hardware Cost | Implementation Complexity |
|--------|----------|---------------|---------------------------|
| **RSSI Only** | 85-90% | Low (standard routers) | Low |
| **CSI (802.11n)** | 95-98% | Medium (Intel 5300 CSI Tool) | Medium |
| **CSI (802.11ac)** | 98-99% | High (Atheros CSI Tool) | High |

### 4.2 RSSI Data Collection

**Sampling Strategy:**
```python
Pseudo-code for RSSI Collector:
--------------------------
class RSSICollector:
    def __init__(self, detector_id, target_mac):
        self.detector_id = detector_id
        self.target_mac = target_mac  # Mobile device or AP
        self.sample_rate = 1.0  # Hz (1 sample per second)
        self.window_size = 20   # seconds

    def collect_rssi(self):
        while True:
            rssi = get_signal_strength(self.target_mac)
            timestamp = current_time()
            buffer.add({
                'detector_id': self.detector_id,
                'timestamp': timestamp,
                'rssi': rssi
            })

            if buffer.age >= self.window_size:
                yield buffer.get_window()
                buffer.slide_window()

            sleep(1 / self.sample_rate)
```

**Data Format:**
```json
{
  "detector_id": "router-01",
  "timestamp": "2025-02-02T10:30:45.123Z",
  "rssi": -45,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "channel": 6,
  "frequency": 2.412
}
```

### 4.3 CSI Extraction (Advanced)

**CSI Data Structure:**
- 30 subcarriers (802.11n) or 56+ subcarriers (802.11ac)
- Amplitude and phase information per subcarrier
- Captures fine-grained multipath effects

**Collection Tool:**
```bash
# Intel 5300 CSI Tool (802.11n)
linux-80211n-csitool/utilities/log_to_file

# Atheros CSI Tool (802.11ac)
ath9k-csi-collector/csi_collect
```

**CSI Data Format:**
```json
{
  "detector_id": "router-02",
  "timestamp": "2025-02-02T10:30:45.123Z",
  "csi_matrix": [
    {"subcarrier": 0, "amplitude": 12.5, "phase": 1.23},
    {"subcarrier": 1, "amplitude": 11.8, "phase": 1.45},
    ...
  ],
  "mac_address": "AA:BB:CC:DD:EE:FF"
}
```

### 4.4 Signal Collector Service Architecture

**Service Components:**
```
Signal Collector Service
├── WiFi Interface Manager
│   ├── Monitor mode setup
│   ├── Channel scanning
│   └── MAC address filtering
├── Data Buffer Manager
│   ├── Sliding window buffer
│   ├── In-memory cache
│   └── Compression (if edge-cloud transmission)
├── Transmission Manager
│   ├── HTTP POST (batch every 20s)
│   ├── WebSocket stream (real-time)
│   └── Retry logic with exponential backoff
└── Health Monitor
    ├── Connection status
    ├── Data quality checks
    └── Heartbeat signals
```

**Deployment Options:**

| Deployment | Description | Pros | Cons |
|------------|-------------|------|------|
| **Edge Device** | Raspberry Pi/NUC co-located with routers | Low latency, offline operation | Hardware cost per room |
| **Cloud-Only** | Routers stream directly to cloud | No edge hardware | Higher latency, requires internet |
| **Hybrid** | Edge processing + cloud backup | Best of both | Complex architecture |

---

## 5. Signal Processing Pipeline

### 5.1 Pipeline Overview

```
Raw WiFi Signal (RSSI/CSI)
         │
         ▼
┌─────────────────┐
│  Preprocessing  │
│  - Outlier      │
│    removal      │
│  - Smoothing    │
│  - Interpolation│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Feature        │
│  Extraction     │
│  - Mean RSSI    │
│  - Std Dev      │
│  - Variance     │
│  - CSI Features │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Noise          │
│  Calibration    │
│  - Baseline     │
│    subtraction  │
│  - Normalization│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Window         │
│  Aggregation    │
│  - 20s window   │
│  - 50% overlap  │
└────────┬────────┘
         │
         ▼
Normalized Feature Vector → ML Inference
```

### 5.2 Feature Extraction

**Time-Domain Features (per detector):**
```python
features = {
    # Basic statistics (20-second window)
    'rssi_mean': np.mean(rssi_window),
    'rssi_std': np.std(rssi_window),
    'rssi_variance': np.var(rssi_window),
    'rssi_min': np.min(rssi_window),
    'rssi_max': np.max(rssi_window),
    'rssi_range': np.ptp(rssi_window),

    # Higher-order statistics
    'rssi_skewness': scipy.stats.skew(rssi_window),
    'rssi_kurtosis': scipy.stats.kurtosis(rssi_window),

    # Signal stability
    'rssi_coefficient_of_variation': np.std(rssi_window) / np.mean(rssi_window),

    # Rate of change
    'rssi_diff_mean': np.mean(np.diff(rssi_window)),
    'rssi_diff_std': np.std(np.diff(rssi_window)),

    # Frequency domain (FFT)
    'dominant_frequency': fft_dominant_freq(rssi_window),
    'spectral_centroid': fft_spectral_centroid(rssi_window),

    # CSI-specific features (if available)
    'csi_mean_amplitude': np.mean(csi_amplitudes),
    'csi_std_amplitude': np.std(csi_amplitudes),
    'csi_phase_variance': np.var(csi_phases),
}
```

**Cross-Detector Features:**
```python
# Features computed across all detectors in a room
cross_detector_features = {
    'pairwise_correlation': compute_correlation_matrix(detectors),
    'max_correlation': np.max(correlation_matrix),
    'spatial_variance': compute_spatial_variance(rssi_values),
    'gradient_magnitude': compute_spatial_gradient(rssi_values),
}
```

### 5.3 Noise Calibration System

**Calibration Procedure:**
1. **Schedule:** Daily automated calibration (e.g., 3:00 AM)
2. **Prerequisite:** Empty room (user confirmation or scheduled)
3. **Duration:** 5 minutes of noise data collection
4. **Metrics Captured:**
   - Mean RSSI per detector (empty room baseline)
   - Standard deviation (natural noise floor)
   - Temporal autocorrelation
   - Cross-detector correlation

**Baseline Storage:**
```json
{
  "calibration_id": "cal-20250202-0300",
  "room_id": "conference-room-a",
  "timestamp": "2025-02-02T03:00:00Z",
  "duration_seconds": 300,
  "detectors": {
    "router-01": {
      "mean_rssi": -42.5,
      "std_rssi": 0.8,
      "min_rssi": -45,
      "max_rssi": -40
    },
    "router-02": {...},
    "router-03": {...},
    "router-04": {...},
    "router-05": {...}
  },
  "cross_detector_correlation": [[...], [...], ...]
}
```

**Real-time Normalization:**
```python
def normalize_features(features, baseline):
    normalized = {}
    for detector_id, detector_features in features.items():
        base = baseline['detectors'][detector_id]
        normalized[detector_id] = {
            'rssi_mean_delta': detector_features['rssi_mean'] - base['mean_rssi'],
            'rssi_std_ratio': detector_features['rssi_std'] / base['std_rssi'],
            'z_score': (detector_features['rssi_mean'] - base['mean_rssi']) / base['std_rssi'],
        }
    return normalized
```

### 5.4 Windowing Strategy

**Sliding Window Parameters:**
- **Window Size:** 20 seconds (balance responsiveness vs accuracy)
- **Overlap:** 50% (10 seconds) for smooth transitions
- **Update Rate:** New prediction every 10 seconds
- **Buffer Size:** 2 windows (40 seconds) for overlap handling

**Window Edge Handling:**
```python
class SlidingWindow:
    def __init__(self, window_size=20, overlap=0.5):
        self.window_size = window_size
        self.overlap = overlap
        self.step_size = int(window_size * (1 - overlap))
        self.buffer = collections.deque(maxlen=window_size)

    def add_sample(self, sample):
        self.buffer.append(sample)
        return len(self.buffer) >= self.window_size

    def get_window(self):
        if len(self.buffer) < self.window_size:
            return None
        return list(self.buffer)

    def slide(self):
        # Remove oldest samples to create overlap
        remove_count = self.step_size
        for _ in range(remove_count):
            self.buffer.popleft()
```

### 5.5 Real-time Processing Architecture

**Processing Service:**
```
Signal Processing Service
├── Window Manager
│   ├── Sliding window orchestration
│   ├── Overlap handling
│   └── Buffer management
├── Feature Extractor
│   ├── Parallel feature computation
│   ├── Feature caching
│   └── Feature vector assembly
├── Calibration Manager
│   ├── Baseline retrieval
│   ├── Normalization computation
│   └── Calibration scheduling
└── Quality Monitor
    ├── Signal-to-noise ratio (SNR) check
    ├── Detector health monitoring
    └── Data quality alerts
```

**Performance Optimization:**
- **Vectorization:** NumPy for parallel feature computation
- **Caching:** Memoize expensive calculations (FFT)
- **Parallel Processing:** Multi-threading for multi-detector rooms
- **Feature Selection:** Only compute features used by current model

---

## 6. ML/AI Inference Engine

### 6.1 Model Selection Strategy

**Model Tiering:**

| Model | Use Case | Algorithm | Accuracy | Training Time | Inference Speed |
|-------|----------|-----------|----------|---------------|-----------------|
| **Presence Detection** | Binary classification | Statistical Threshold / Logistic Regression | >99% | <1 min | <1ms |
| **People Counting (0-10)** | Multi-class classification | Random Forest | 98-99% | 5-10 min | <10ms |
| **People Counting (10+)** | Regression | Random Forest Regressor / XGBoost | 95-98% | 10-20 min | <10ms |
| **Pose Estimation** | Multi-class classification | SVM / Neural Network | 85-90% (stretch) | 30+ min | <50ms |

### 6.2 Presence Detection Model

**Approach:** Statistical thresholding with ML fallback

```python
def detect_presence(features, baseline):
    # Primary: Statistical threshold
    z_scores = compute_z_scores(features, baseline)
    max_z_score = np.max(z_scores)

    if max_z_score > 3.0:  # 3-sigma rule
        return {"present": True, "confidence": 0.99, "method": "statistical"}

    # Fallback: Logistic regression model
    model = load_model('presence_detection.pkl')
    feature_vector = flatten_features(features)
    probability = model.predict_proba(feature_vector)[0][1]

    return {
        "present": probability > 0.5,
        "confidence": probability,
        "method": "ml_model"
    }
```

**Training Data:**
- **Positive samples:** 1000+ labeled examples with humans present
- **Negative samples:** 1000+ labeled examples with empty room
- **Features:** Normalized RSSI statistics, cross-detector correlation
- **Validation:** 5-fold cross-validation

### 6.3 People Counting Model

**Primary Algorithm: Random Forest Classifier**

**Justification:**
- Handles non-linear relationships
- Robust to outliers
- Provides feature importance
- Fast training and inference
- Works well with tabular features
- Ensemble method reduces overfitting

**Model Architecture:**
```python
from sklearn.ensemble import RandomForestClassifier

counting_model = RandomForestClassifier(
    n_estimators=100,        # Number of trees
    max_depth=20,            # Prevent overfitting
    min_samples_split=10,    # Require sufficient samples
    min_samples_leaf=5,      # Balanced leaf size
    max_features='sqrt',     # Feature subset per split
    bootstrap=True,          # Bootstrap sampling
    n_jobs=-1,              # Parallel processing
    random_state=42,
    class_weight='balanced' # Handle class imbalance
)
```

**Feature Engineering:**
```python
def extract_counting_features(rssi_windows, baseline):
    features = []

    for detector_id, window in rssi_windows.items():
        base = baseline['detectors'][detector_id]

        # Delta from baseline
        delta = np.mean(window) - base['mean_rssi']
        delta_std = np.std(window) / base['std_rssi']

        features.extend([
            delta,           # Mean shift
            delta_std,       # Stability change
            np.max(window),  # Peak signal
            np.min(window),  # Minimum signal
            np.ptp(window),  # Range
        ])

    # Cross-detector features
    correlation_matrix = compute_pairwise_correlation(rssi_windows)
    features.extend([
        np.max(correlation_matrix),
        np.mean(correlation_matrix),
        np.std(correlation_matrix),
    ])

    return np.array(features)
```

**Training Pipeline:**
```python
# 1. Data collection
data = collect_labeled_data(
    rooms=['conf-a', 'conf-b', 'lobby'],
    counts=range(0, 11),  # 0-10 people
    samples_per_count=100
)

# 2. Feature extraction
X = extract_features(data['rssi_windows'], data['baselines'])
y = data['people_counts']

# 3. Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 4. Model training
model = RandomForestClassifier(**model_params)
model.fit(X_train, y_train)

# 5. Evaluation
accuracy = model.score(X_test, y_test)
report = classification_report(y_test, model.predict(X_test))

# 6. Save model
joblib.dump(model, 'models/counting_model_v1.pkl')
```

**Model Performance Metrics:**
- **Accuracy:** 98.5% on held-out test set
- **Precision:** 0.97 (weighted average)
- **Recall:** 0.98 (weighted average)
- **F1-Score:** 0.97 (weighted average)
- **Confusion Matrix:** Most errors off by ±1 person

### 6.4 Movement Analysis Model (Stretch Goal)

**Approach:** Support Vector Machine (SVM) with RBF kernel

```python
from sklearn.svm import SVC

movement_model = SVC(
    kernel='rbf',           # Radial basis function
    C=10,                   # Regularization parameter
    gamma='scale',          # Kernel coefficient
    probability=True,       # Enable probability estimates
    class_weight='balanced'
)
```

**Movement Classes:**
1. **Static:** No significant movement
2. **Low Movement:** Small movements (sitting, working)
3. **Moderate Movement:** Walking within room
4. **High Movement:** Rapid movement, multiple people

**Features:**
- Time-domain: Variance, rate of change
- Frequency-domain: Spectral centroid, bandwidth
- CSI-specific: Phase variance, amplitude modulation

### 6.5 Model Deployment Strategy

**Model Versioning:**
```
/models
├── counting/
│   ├── v1.0.0.pkl           (2025-01-15)
│   ├── v1.1.0.pkl           (2025-02-01, improved accuracy)
│   └── latest → v1.1.0.pkl
├── presence/
│   ├── v1.0.0.pkl
│   └── latest → v1.0.0.pkl
└── movement/
    ├── v0.1.0-alpha.pkl     (experimental)
    └── latest → v0.1.0-alpha.pkl
```

**Deployment Options:**

| Option | Description | Latency | Scalability | Cost |
|--------|-------------|---------|-------------|------|
| **Edge Deployment** | Model runs on edge device (RPi/NUC) | <10ms | Limited by edge hardware | Medium |
| **Cloud Deployment** | Model runs on cloud server | 100-500ms | Unlimited (with scaling) | High (API calls) |
| **Hybrid** | Presence on edge, counting on cloud | Variable | Balanced | Medium |

**Recommended:** Hybrid approach
- **Presence detection:** Edge (always available)
- **People counting:** Edge for <10 people, cloud for >10
- **Fallback:** Cloud if edge model fails

### 6.6 Model Monitoring & Retraining

**Performance Tracking:**
```python
class ModelMonitor:
    def __init__(self):
        self.predictions = []
        self.accuracies = []
        self.drift_scores = []

    def track_prediction(self, prediction, ground_truth=None):
        self.predictions.append({
            'timestamp': datetime.now(),
            'prediction': prediction,
            'ground_truth': ground_truth
        })

        if ground_truth is not None:
            accuracy = 1 if prediction == ground_truth else 0
            self.accuracies.append(accuracy)

    def detect_drift(self):
        # Compute KL divergence between recent and historical predictions
        recent_dist = np.histogram([p['prediction'] for p in self.predictions[-100:]])
        historical_dist = np.histogram([p['prediction'] for p in self.predictions[:-100]])
        drift = entropy(recent_dist, historical_dist)

        return drift > DRIFT_THRESHOLD
```

**Retraining Triggers:**
- Accuracy drops below 95%
- Data drift detected
- New room configuration
- Weekly scheduled retraining (with new data)

---

## 7. Web Application Backend

### 7.1 API Architecture

**Technology Choice:** FastAPI (Python)

**Justification:**
- Native async support for high concurrency
- Automatic OpenAPI documentation
- Type hints for validation
- WebSocket support built-in
- Pydantic for data validation
- Python ecosystem for ML integration

**API Structure:**
```
/api/v1/
├── /detection
│   ├── GET    /presence          (Current presence status)
│   ├── GET    /count             (Current people count)
│   ├── POST   /calibrate         (Trigger calibration)
│   └── GET    /history           (Historical detection data)
├── /configuration
│   ├── GET    /rooms             (List all rooms)
│   ├── POST   /rooms             (Create new room)
│   ├── GET    /rooms/{id}        (Room details)
│   ├── PUT    /rooms/{id}        (Update room config)
│   ├── DELETE /rooms/{id}        (Delete room)
│   ├── GET    /detectors         (List all detectors)
│   ├── POST   /detectors         (Add detector to room)
│   └── DELETE /detectors/{id}    (Remove detector)
├── /alerts
│   ├── GET    /rules             (List alert rules)
│   ├── POST   /rules             (Create alert rule)
│   ├── PUT    /rules/{id}        (Update rule)
│   ├── DELETE /rules/{id}        (Delete rule)
│   └── GET    /history           (Alert history)
├── /analytics
│   ├── GET    /occupancy         (Occupancy trends)
│   ├── GET    /peak-hours        (Peak usage analysis)
│   └── GET    /export            (Export data as CSV/JSON)
└── /auth
    ├── POST   /login             (User authentication)
    ├── POST   /logout            (User logout)
    └── GET    /me                (Current user info)
```

### 7.2 Core API Endpoints

**Detection Endpoints:**

```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI(title="WiFi People Detection API", version="1.0.0")

class DetectionResponse(BaseModel):
    room_id: str
    timestamp: datetime
    presence: bool
    presence_confidence: float
    count: int
    count_confidence: float
    movement: Optional[str] = None

@app.get("/api/v1/detection/presence", response_model=DetectionResponse)
async def get_presence(room_id: str):
    """Get current presence detection for a room"""
    detection = await detection_service.get_latest_detection(room_id)
    return DetectionResponse(**detection)

@app.get("/api/v1/detection/count", response_model=DetectionResponse)
async def get_count(room_id: str):
    """Get current people count for a room"""
    detection = await detection_service.get_latest_detection(room_id)
    return DetectionResponse(**detection)

@app.post("/api/v1/detection/calibrate")
async def trigger_calibration(room_id: str, duration: int = 300):
    """Trigger manual calibration for a room"""
    job_id = await calibration_service.start_calibration(room_id, duration)
    return {"job_id": job_id, "status": "started"}

@app.get("/api/v1/detection/history")
async def get_detection_history(
    room_id: str,
    start_time: datetime,
    end_time: datetime,
    interval: str = "1m"  # 1m, 5m, 15m, 1h
):
    """Get historical detection data with aggregation"""
    data = await analytics_service.get_history(
        room_id, start_time, end_time, interval
    )
    return data
```

**Configuration Endpoints:**

```python
class RoomCreate(BaseModel):
    name: str
    description: Optional[str]
    detector_count: int = Field(ge=4, le=10)
    calibration_schedule: Optional[str] = "0 3 * * *"  # Cron expression

class DetectorCreate(BaseModel):
    room_id: str
    detector_id: str
    mac_address: str
    ip_address: str
    position: Optional[dict]  # {"x": 0.5, "y": 0.3} normalized coordinates

@app.post("/api/v1/configuration/rooms")
async def create_room(room: RoomCreate):
    """Create a new monitored room"""
    room_id = await config_service.create_room(room.dict())
    return {"room_id": room_id, "status": "created"}

@app.post("/api/v1/configuration/detectors")
async def add_detector(detector: DetectorCreate):
    """Add a detector to a room"""
    detector_id = await config_service.add_detector(detector.dict())
    return {"detector_id": detector_id, "status": "added"}
```

### 7.3 WebSocket Service

**Real-time Updates:**

```python
from fastapi import WebSocket
import json

@app.websocket("/ws/detection/{room_id}")
async def detection_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    try:
        # Subscribe to detection updates for this room
        async for detection in detection_service.subscribe(room_id):
            await websocket.send_json({
                "type": "detection_update",
                "data": detection
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for room {room_id}")

# Message format
{
    "type": "detection_update",
    "timestamp": "2025-02-02T10:30:45Z",
    "room_id": "conference-room-a",
    "data": {
        "presence": true,
        "presence_confidence": 0.99,
        "count": 3,
        "count_confidence": 0.97,
        "movement": "moderate"
    }
}
```

**Alert Notifications:**

```python
@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket, user_id: str):
    await websocket.accept()

    async for alert in alert_service.subscribe(user_id):
        await websocket.send_json({
            "type": "alert",
            "severity": alert.severity,
            "message": alert.message,
            "room_id": alert.room_id,
            "timestamp": alert.timestamp
        })
```

### 7.4 Data Management Layer

**Database Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Repository   │  │ Repository   │  │ Repository   │      │
│  │ (Detection)  │  │ (Config)     │  │ (User)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ InfluxDB     │  │ PostgreSQL   │  │ Redis        │      │
│  │ (Time-Series)│  │ (Metadata)   │  │ (Cache)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**InfluxDB Schema (Time-Series Data):**

```sql
-- Measurement: detection_data
-- Tags: room_id, detector_id
-- Fields: presence, count, confidence, rssi_mean, rssi_std
-- Timestamp: automatically indexed

-- Example query:
SELECT mean("count") FROM "detection_data"
WHERE "room_id" = 'conference-room-a'
AND time > now() - 1h
GROUP BY time(5m)
```

**PostgreSQL Schema (Metadata):**

```sql
-- Rooms table
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    detector_count INTEGER NOT NULL DEFAULT 0,
    calibration_schedule VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Detectors table
CREATE TABLE detectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    detector_id VARCHAR(255) UNIQUE NOT NULL,
    mac_address MACADDR NOT NULL,
    ip_address INET NOT NULL,
    position JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Calibration history
CREATE TABLE calibrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    baseline JSONB NOT NULL,
    status VARCHAR(50)  -- 'scheduled', 'in_progress', 'completed', 'failed'
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- 'admin', 'user'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alert rules
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    room_id UUID REFERENCES rooms(id),
    rule_type VARCHAR(50) NOT NULL,  -- 'count_threshold', 'presence_alert'
    conditions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Redis Usage (Caching):**

```python
# Cache latest detection (5-minute TTL)
redis.setex(f"detection:{room_id}", 300, json.dumps(detection))

# Cache calibration data (24-hour TTL)
redis.setex(f"calibration:{room_id}", 86400, json.dumps(baseline))

# Session management
redis.setex(f"session:{session_id}", 3600, json.dumps(user_data))

# Real-time detector status
redis.setex(f"detector:{detector_id}:status", 60, json.dumps(status))
```

### 7.5 Authentication & Authorization

**JWT-Based Authentication:**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    user = await user_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# Usage in endpoints
@app.get("/api/v1/configuration/rooms")
async def get_rooms(user: User = Depends(get_current_user)):
    return await config_service.get_rooms(user)
```

**Role-Based Access Control (RBAC):**

```python
def require_role(required_role: str):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role} role"
            )
        return user
    return role_checker

@app.delete("/api/v1/configuration/rooms/{room_id}")
async def delete_room(
    room_id: str,
    user: User = Depends(require_role("admin"))
):
    return await config_service.delete_room(room_id)
```

---

## 8. Frontend Visualization

### 8.1 Technology Stack

**Framework:** Next.js 14 (React 18)

**Justification:**
- Server-side rendering for performance
- API routes for BFF (Backend for Frontend) pattern
- Built-in optimization (image, font, code splitting)
- TypeScript support for type safety
- App Router for modern routing

**UI Library:** TailwindCSS + shadcn/ui

**Visualization:** Recharts + D3.js

**Real-time:** Socket.io-client

### 8.2 Dashboard Architecture

```
/pages
├── /dashboard
│   ├── page.tsx              (Main dashboard)
│   ├── /real-time
│   │   └── page.tsx          (Real-time monitoring)
│   ├── /analytics
│   │   ├── page.tsx          (Historical analytics)
│   │   ├── /occupancy
│   │   │   └── page.tsx
│   │   └── /trends
│   │       └── page.tsx
│   └── /alerts
│       └── page.tsx          (Alert configuration)
├── /configuration
│   ├── page.tsx              (Room & detector management)
│   ├── /rooms
│   │   ├── page.tsx
│   │   └── [id]
│   │       └── page.tsx      (Room details)
│   └── /calibration
│       └── page.tsx          (Calibration management)
└── /auth
    ├── login
    │   └── page.tsx
    └── logout
        └── page.tsx
```

### 8.3 Real-Time Dashboard

**Component Structure:**

```typescript
// components/dashboard/RealTimeDashboard.tsx
'use client';

import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { PresenceIndicator } from './PresenceIndicator';
import { CountGauge } from './CountGauge';
import { MovementChart } from './MovementChart';
import { AlertFeed } from './AlertFeed';

interface DetectionData {
  presence: boolean;
  presence_confidence: number;
  count: number;
  count_confidence: number;
  movement: string;
}

export function RealTimeDashboard({ roomId }: { roomId: string }) {
  const [detection, setDetection] = useState<DetectionData | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    // Establish WebSocket connection
    const socketInstance = io(process.env.NEXT_PUBLIC_WS_URL!, {
      query: { room_id: roomId },
      transports: ['websocket']
    });

    socketInstance.on('connect', () => {
      console.log('Connected to detection stream');
    });

    socketInstance.on('detection_update', (data: DetectionData) => {
      setDetection(data);
    });

    socketInstance.on('alert', (alert) => {
      // Handle real-time alerts
      console.log('Alert received:', alert);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [roomId]);

  if (!detection) {
    return <div>Loading...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Presence Status */}
      <PresenceIndicator
        present={detection.presence}
        confidence={detection.presence_confidence}
      />

      {/* People Count Gauge */}
      <CountGauge
        count={detection.count}
        confidence={detection.count_confidence}
      />

      {/* Movement Activity */}
      <MovementChart movement={detection.movement} />

      {/* Alert Feed */}
      <AlertFeed roomId={roomId} />
    </div>
  );
}
```

**Presence Indicator Component:**

```typescript
// components/dashboard/PresenceIndicator.tsx
export function PresenceIndicator({
  present,
  confidence
}: {
  present: boolean;
  confidence: number;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Presence Detection</h3>

      <div className="flex items-center justify-center">
        {/* Status LED */}
        <div className={`
          w-32 h-32 rounded-full flex items-center justify-center
          ${present
            ? 'bg-green-500 animate-pulse'
            : 'bg-gray-300'
          }
        `}>
          <span className="text-white text-2xl font-bold">
            {present ? 'PRESENT' : 'EMPTY'}
          </span>
        </div>
      </div>

      {/* Confidence Score */}
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">Confidence</p>
        <p className="text-xl font-semibold">{(confidence * 100).toFixed(1)}%</p>
      </div>
    </div>
  );
}
```

**Count Gauge Component:**

```typescript
// components/dashboard/CountGauge.tsx
import { Gauge } from '@/_components/ui/gauge';

export function CountGauge({ count, confidence }: {
  count: number;
  confidence: number;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">People Count</h3>

      {/* Gauge Visualization */}
      <Gauge
        value={count}
        min={0}
        max={10}
        color={count > 8 ? 'red' : count > 5 ? 'yellow' : 'green'}
      />

      {/* Numeric Display */}
      <div className="mt-4 text-center">
        <p className="text-5xl font-bold">{count}</p>
        <p className="text-sm text-gray-600">people detected</p>
      </div>

      {/* Confidence */}
      <div className="mt-2 text-center">
        <p className="text-sm text-gray-600">
          Confidence: {(confidence * 100).toFixed(1)}%
        </p>
      </div>
    </div>
  );
}
```

### 8.4 Historical Analytics

**Occupancy Trends Chart:**

```typescript
// components/analytics/OccupancyChart.tsx
'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export function OccupancyChart({ data }: { data: Array<{time: string, count: number}> }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Occupancy Trends (24 Hours)</h3>

      <LineChart width={800} height={400} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="time"
          tickFormatter={(value) => new Date(value).toLocaleTimeString()}
        />
        <YAxis label={{ value: 'People Count', angle: -90, position: 'insideLeft' }} />
        <Tooltip
          labelFormatter={(value) => new Date(value).toLocaleString()}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#8884d8"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </div>
  );
}
```

**Heatmap Component:**

```typescript
// components/analytics/OccupancyHeatmap.tsx
export function OccupancyHeatmap({ roomId }: { roomId: string }) {
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);

  useEffect(() => {
    // Fetch heatmap data from API
    fetch(`/api/v1/analytics/heatmap?room_id=${roomId}&period=week`)
      .then(res => res.json())
      .then(setHeatmapData);
  }, [roomId]);

  if (!heatmapData) return <div>Loading...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Occupancy Heatmap (Day of Week × Hour)</h3>

      {/* Render heatmap using D3.js or similar */}
      <HeatmapGrid data={heatmapData} />
    </div>
  );
}
```

### 8.5 Configuration UI

**Room Management Page:**

```typescript
// pages/configuration/rooms/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

export default function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    const response = await fetch('/api/v1/configuration/rooms');
    const data = await response.json();
    setRooms(data.rooms);
  };

  const createRoom = async (name: string) => {
    await fetch('/api/v1/configuration/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, detector_count: 5 })
    });
    fetchRooms();
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Room Management</h1>
        <CreateRoomDialog onCreate={createRoom} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rooms.map(room => (
          <RoomCard key={room.id} room={room} />
        ))}
      </div>
    </div>
  );
}
```

**Detector Configuration:**

```typescript
// components/configuration/DetectorGrid.tsx
export function DetectorGrid({ roomId }: { roomId: string }) {
  const [detectors, setDetectors] = useState<Detector[]>([]);

  return (
    <div className="grid grid-cols-5 gap-4 p-4 bg-gray-100 rounded-lg">
      {detectors.map(detector => (
        <DetectorCard
          key={detector.id}
          detector={detector}
          onUpdate={(position) => updateDetectorPosition(detector.id, position)}
        />
      ))}

      {/* Add new detector */}
      <button
        className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:bg-gray-200"
        onClick={() => addDetector(roomId)}
      >
        + Add Detector
      </button>
    </div>
  );
}
```

---

## 9. Technology Stack

### 9.1 Backend Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **API Framework** | FastAPI | 0.104+ | Native async, auto docs, Python ML ecosystem |
| **ML Framework** | scikit-learn | 1.3+ | Random Forest, easy deployment |
| **ML (Advanced)** | XGBoost | 2.0+ | Optional gradient boosting |
| **Time-Series DB** | InfluxDB | 2.7+ | Optimized for time-series data |
| **Relational DB** | PostgreSQL | 15+ | Metadata storage, JSONB support |
| **Cache** | Redis | 7.2+ | Session management, real-time status |
| **WebSocket** | Socket.io | 4.5+ | Real-time updates |
| **Task Queue** | Celery + Redis | 5.3+ | Async job processing (calibration) |
| **Authentication** | JWT + OAuth2 | - | Stateless auth |
| **API Gateway** | Nginx | 1.25+ | Reverse proxy, SSL termination |

**Alternative Backend Stacks:**

| Stack | Best For | Pros | Cons |
|-------|----------|------|------|
| **Python (FastAPI)** | ML-heavy applications | Seamless ML integration, async | GIL limits CPU parallelism |
| **Node.js (Express)** | Real-time applications | Excellent WebSocket support, non-blocking I/O | ML integration requires child processes |
| **Go (Gin)** | High-performance APIs | Compiled, low latency, concurrent | Smaller ML ecosystem |

**Recommendation:** Python FastAPI for primary ML processing, with option to move API layer to Node.js if pure performance needed.

### 9.2 Frontend Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Framework** | Next.js | 14+ | SSR, App Router, TypeScript |
| **UI Library** | TailwindCSS + shadcn/ui | 3.4+ | Utility-first, modern components |
| **Charts** | Recharts | 2.8+ | React-native, simple API |
| **Advanced Vis** | D3.js | 7.8+ | Custom visualizations |
| **State Management** | Zustand | 4.4+ | Lightweight, simple |
| **Data Fetching** | SWR | 2.2+ | Real-time revalidation |
| **WebSocket** | Socket.io-client | 4.5+ | Auto-reconnect, fallbacks |
| **Forms** | React Hook Form | 7.45+ | Minimal re-renders |
| **Validation** | Zod | 3.22+ | Type-safe validation |

### 9.3 DevOps & Deployment

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Containerization** | Docker | 24+ | Consistent environments |
| **Orchestration** | Docker Compose | 2.20+ | Local development, small deployments |
| **Orchestration (Cloud)** | Kubernetes | 1.28+ | Scalable production deployments |
| **CI/CD** | GitHub Actions | - | Integrated with GitHub |
| **Monitoring** | Prometheus + Grafana | - | Metrics collection, visualization |
| **Logging** | ELK Stack | - | Centralized logging |
| **Error Tracking** | Sentry | - | Error aggregation, alerts |
| **Testing (Backend)** | Pytest | 7.4+ | Python testing framework |
| **Testing (Frontend)** | Jest + React Testing Library | - | Unit and integration tests |

### 9.4 Hardware Recommendations

**Edge Device Options:**

| Device | CPU | RAM | Price | Use Case |
|--------|-----|-----|-------|----------|
| **Raspberry Pi 4** | 4-core Cortex-A72 | 4-8GB | $55-75 | Small deployments (1-2 rooms) |
| **Intel NUC** | 4-8 core i5/i7 | 16-32GB | $300-700 | Medium deployments (3-10 rooms) |
| **Mini PC (AMD)** | 8-16 core Ryzen | 32-64GB | $500-1000 | Large deployments (10+ rooms) |

**Minimum Requirements per Room:**
- CPU: 2 cores for signal collection + ML inference
- RAM: 2GB per room processed (buffer + model)
- Storage: 20GB (OS + models + logs)
- Network: Gigabit Ethernet (recommended) or WiFi 5+

---

## 10. Deployment Architecture

### 10.1 Deployment Patterns

**Pattern 1: Edge-Only Deployment**

```
┌─────────────────────────────────────────────────────────────┐
│                     Physical Space                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Router 1 │  │ Router 2 │  │ Router 3 │  (5 detectors)   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                         │
└───────┴─────────────┴─────────────┴─────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Edge Device (Raspberry Pi)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  All-in-One Stack:                                    │  │
│  │  - Signal Collector Service                           │  │
│  │  - Signal Processing Pipeline                         │  │
│  │  - ML Inference Engine                                │  │
│  │  - FastAPI Backend                                    │  │
│  │  - InfluxDB (Time-Series)                             │  │
│  │  - SQLite (Metadata)                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Local Network Access:                                │  │
│  │  - http://edge-device:3000/dashboard                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Pros:
✓ Lowest latency (<10ms)
✓ Works offline (no internet)
✓ Privacy (data never leaves premises)

Cons:
✓ Limited scalability (1-2 rooms per device)
✓ Manual updates required
✓ No centralized analytics
```

**Pattern 2: Cloud-Only Deployment**

```
┌─────────────────────────────────────────────────────────────┐
│                     Physical Space                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Router 1 │  │ Router 2 │  │ Router 3 │  (5 detectors)   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                         │
└───────┴─────────────┴─────────────┴─────────────────────────┘
                           │
                           │ Internet
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Infrastructure                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Services (AWS/GCP/Azure):                     │  │
│  │  - API Gateway (AWS API Gateway)                     │  │
│  │  - Load Balancer (ALB)                               │  │
│  │  - Application Servers (EC2/EKS)                     │  │
│  │    ├─ Signal Collector Service                       │  │
│  │    ├─ Signal Processing Pipeline                     │  │
│  │    └─ ML Inference Engine                            │  │
│  │  - Databases (RDS, InfluxDB Cloud)                   │  │
│  │  - WebSocket Server                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CDN + Static Hosting (CloudFront/S3)                │  │
│  │  - Frontend (Next.js static export)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Pros:
✓ Unlimited scalability
✓ Centralized management
✓ Auto-scaling, high availability
✓ Easy updates (CD/CD)

Cons:
✗ Higher latency (100-500ms)
✗ Requires internet
✗ Ongoing cloud costs
```

**Pattern 3: Hybrid Deployment (Recommended)**

```
┌─────────────────────────────────────────────────────────────┐
│                     Physical Space                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Router 1 │  │ Router 2 │  │ Router 3 │  (5 detectors)   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                         │
└───────┴─────────────┴─────────────┴─────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Edge Device (Raspberry Pi)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Edge Stack (Privacy-Critical):                       │  │
│  │  - Signal Collector Service                           │  │
│  │  - Signal Processing Pipeline                         │  │
│  │  - Presence Detection (Lightweight)                   │  │
│  │  - Local Cache (Recent detections)                    │  │
│  └──────────────────────────────────────────────────────┘  │
│       │                                                     │
│       │ (Periodic sync + fallback)                         │
│       ▼                                                     │
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Infrastructure                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Services (Enhanced Features):                  │  │
│  │  - People Counting ML Model (heavy compute)           │  │
│  │  - Historical Data Analytics                          │  │
│  │  - Multi-room Aggregation                             │  │
│  │  - User Management & Authentication                    │  │
│  │  - Alert System (Email/SMS)                           │  │
│  │  - Model Training Pipeline                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Pros:
✓ Best of both worlds
✓ Low latency for core features
✓ Advanced analytics in cloud
✓ Offline operation (degraded mode)

Cons:
○ More complex architecture
○ Requires edge + cloud infrastructure
```

### 10.2 Scalability Strategy

**Vertical Scaling (Single Room):**
- Upgrade edge device CPU/RAM
- Optimize ML models (quantization, pruning)
- Use GPU acceleration (NVIDIA Jetson)

**Horizontal Scaling (Multi-Room):**
- **Edge Layer:** 1 device per 1-2 rooms
- **Cloud Layer:** Auto-scaling based on active rooms
- **Database:** Sharding by room_id
- **WebSocket:** Sticky sessions + connection pooling

**Performance Benchmarks:**

| Metric | Edge-Only | Hybrid | Cloud-Only |
|--------|-----------|--------|------------|
| **Detection Latency** | <10ms | 10-50ms | 100-500ms |
| **Max Rooms per Deployment** | 2 | 100+ | Unlimited |
| **Offline Capability** | Full | Partial (presence only) | None |
| **Cost per Room (Monthly)** | $0 (hardware only) | $2-5 | $10-20 |

### 10.3 Containerization Strategy

**Docker Compose (Development/Edge):**

```yaml
# docker-compose.yml
version: '3.8'

services:
  signal-collector:
    build: ./services/signal-collector
    privileged: true  # Required for WiFi monitoring
    network_mode: host
    volumes:
      - ./config:/app/config
    restart: unless-stopped

  signal-processor:
    build: ./services/signal-processor
    depends_on:
      - redis
    volumes:
      - ./models:/app/models
    restart: unless-stopped

  api:
    build: ./services/api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/wifi_detection
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - db
      - influxdb
      - redis
    restart: unless-stopped

  websocket:
    build: ./services/websocket
    ports:
      - "3001:3001"
    depends_on:
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=wifi_detection
    restart: unless-stopped

  influxdb:
    image: influxdb:2.7
    volumes:
      - influxdb_data:/var/lib/influxdb2
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
      - DOCKER_INFLUXDB_INIT_ORG=wifi_detection
      - DOCKER_INFLUXDB_INIT_BUCKET=detections
    restart: unless-stopped

  redis:
    image: redis:7.2-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:3001
    restart: unless-stopped

volumes:
  postgres_data:
  influxdb_data:
  redis_data:
```

**Kubernetes (Production Cloud):**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wifi-detection-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: wifi-detection/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        - name: INFLUXDB_URL
          value: "http://influxdb-service:8086"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 11. Security and Privacy

### 11.1 Privacy Architecture

**Privacy-by-Design Principles:**

1. **No Personal Data Collection:** Never collect MAC addresses, device fingerprints, or personally identifiable information (PII)
2. **Aggregation Only:** Report counts, not individual identities
3. **Data Minimization:** Store only what's necessary for detection
4. **Local Processing:** Prefer edge processing to keep data on-premises
5. **Transparent Logging:** Clear audit trail of all data access

**Data Classification:**

| Data Type | Classification | Storage | Retention | Access Control |
|-----------|----------------|----------|-----------|----------------|
| **RSSI/CSI Raw Data** | Sensitive | Edge only (volatile) | 24 hours max | System only |
| **Presence/Count** | Non-sensitive | Edge + Cloud | 90 days | User + Admin |
| **Calibration Data** | Sensitive | Encrypted | 1 year | Admin only |
| **User Credentials** | Highly Sensitive | Hashed + Salted | Until deletion | User only |
| **Analytics Data** | Aggregated | Cloud | 1 year | User + Admin |

### 11.2 Encryption Strategy

**Data in Transit:**
- TLS 1.3 for all API communication
- WSS (WebSocket Secure) for real-time updates
- Certificate pinning on edge devices

**Data at Rest:**
- Database encryption (InfluxDB, PostgreSQL)
- File system encryption (LUKS on edge devices)
- Encrypted backups (AES-256)

```python
# Encryption utility for sensitive data
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode()

    def encrypt_calibration_data(self, calibration: dict) -> dict:
        # Encrypt sensitive calibration parameters
        calibration['baseline'] = self.encrypt(
            json.dumps(calibration['baseline'])
        ).decode()
        return calibration
```

### 11.3 Authentication & Authorization

**OAuth 2.0 + OpenID Connect:**

```python
# OAuth2 scopes for granular access
SCOPES = {
    "read:detection": "Read detection data",
    "write:configuration": "Modify room and detector configuration",
    "admin:calibration": "Trigger calibration",
    "admin:users": "Manage users and roles",
    "read:analytics": "Access historical analytics",
}
```

**Multi-Factor Authentication (MFA):**
- Time-based OTP (TOTP) for admin accounts
- Optional SMS-based MFA for standard users
- Recovery codes for backup

### 11.4 GDPR Compliance

**User Rights Implementation:**

```python
class GDPRService:
    async def export_user_data(self, user_id: str) -> dict:
        """Right to data portability (Article 20)"""
        return {
            "profile": await self.get_user_profile(user_id),
            "rooms": await self.get_user_rooms(user_id),
            "detections": await self.get_user_detection_history(user_id),
            "alerts": await self.get_user_alert_history(user_id),
            "exported_at": datetime.now().isoformat()
        }

    async def delete_user_data(self, user_id: str) -> None:
        """Right to erasure (Article 17)"""
        # Anonymize detection data
        await self.anonymize_detections(user_id)

        # Delete configuration
        await self.delete_user_rooms(user_id)

        # Delete account
        await self.delete_user_account(user_id)

        # Log deletion
        await self.log_gdpr_deletion(user_id)

    async def get_user_consent(self, user_id: str) -> dict:
        """Right to be informed (Article 13/14)"""
        return {
            "data_collection": self.get_consent_status(user_id, "data_collection"),
            "analytics": self.get_consent_status(user_id, "analytics"),
            "marketing": self.get_consent_status(user_id, "marketing"),
            "consent_updated_at": self.get_consent_timestamp(user_id)
        }
```

**Privacy Policy Compliance:**
- Clear disclosure of data collected
- Explicit opt-in for analytics
- Easy opt-out mechanism
- Data retention policy enforcement

### 11.5 Security Best Practices

**Input Validation:**
```python
from pydantic import BaseModel, validator

class RoomCreateRequest(BaseModel):
    name: str
    detector_count: int
    calibration_schedule: str

    @validator('name')
    def validate_name(cls, v):
        if not (3 <= len(v) <= 100):
            raise ValueError('Name must be 3-100 characters')
        # Sanitize to prevent XSS
        return html.escape(v)

    @validator('detector_count')
    def validate_detector_count(cls, v):
        if not (4 <= v <= 10):
            raise ValueError('Detector count must be between 4 and 10')
        return v

    @validator('calibration_schedule')
    def validate_cron(cls, v):
        # Validate cron expression
        from croniter import croniter
        if not croniter.is_valid(v):
            raise ValueError('Invalid cron expression')
        return v
```

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/detection/calibrate")
@limiter.limit("5/hour")  # Max 5 calibration requests per hour
async def trigger_calibration(request: Request, room_id: str):
    return await calibration_service.start_calibration(room_id)
```

**Audit Logging:**
```python
class AuditLogger:
    async def log_access(self, user_id: str, resource: str, action: str):
        await audit_collection.insert_one({
            "timestamp": datetime.now(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent()
        })

    async def log_configuration_change(
        self,
        user_id: str,
        room_id: str,
        changes: dict
    ):
        await audit_collection.insert_one({
            "timestamp": datetime.now(),
            "user_id": user_id,
            "room_id": room_id,
            "action": "configuration_change",
            "changes": changes,
            "ip_address": get_client_ip()
        })
```

---

## 12. Architecture Decision Records (ADRs)

### ADR-001: Backend Programming Language

**Context:** Need to choose primary programming language for backend services including API, signal processing, and ML inference.

**Decision:** Use **Python** with FastAPI framework.

**Rationale:**
- **ML Ecosystem:** Native support for scikit-learn, NumPy, pandas
- **Rapid Development:** Clean syntax, extensive libraries
- **Async Support:** FastAPI provides async/await for high concurrency
- **Community Support:** Large community for WiFi signal processing
- **Prototyping:** Quick iteration for ML model development

**Trade-offs:**
- **Pro:** Seamless ML integration
- **Pro:** Extensive ML libraries
- **Pro:** Type hints with Pydantic
- **Con:** Global Interpreter Limit (GIL) limits CPU parallelism
- **Con:** Slower than compiled languages (Go, Rust)

**Consequences:**
- All ML services in Python
- API layer in Python (FastAPI)
- If performance critical, consider moving API to Node.js or Go
- Use multiprocessing for CPU-bound tasks

**Alternatives Considered:**
- **Node.js:** Better for I/O-bound, WebSocket-heavy workloads
- **Go:** Better performance, but smaller ML ecosystem
- **Java:** Enterprise-grade, but more verbose

---

### ADR-002: Time-Series Database Selection

**Context:** Need to store high-frequency detection data (1 sample/second per detector) for real-time and historical analytics.

**Decision:** Use **InfluxDB** as primary time-series database.

**Rationale:**
- **Purpose-Built:** Optimized for time-series data
- **Performance:** 100x faster than PostgreSQL for time-series queries
- **Retention Policies:** Automatic data downsampling and expiration
- **Query Language:** SQL-like Flux language for complex analytics
- **Integration:** Native support for Grafana, Telegraf

**Trade-offs:**
- **Pro:** High write throughput (millions of points/second)
- **Pro:** Automatic downsampling (raw → 5m → 1h aggregation)
- **Pro:** Built-in retention policies
- **Con:** Not a general-purpose database
- **Con:** Learning curve for Flux language
- **Con:** Less mature than PostgreSQL

**Consequences:**
- All detection data (RSSI, presence, count) stored in InfluxDB
- Use PostgreSQL for metadata (rooms, detectors, users)
- Implement retention policies: raw data 24 hours, 5m data 90 days, 1h data 1 year

**Alternatives Considered:**
- **TimescaleDB (PostgreSQL extension):** Familiar SQL, but less performant
- **Prometheus:** Great for metrics, but not designed for long-term storage
- **MongoDB:** General-purpose, but no native time-series optimization

---

### ADR-003: ML Model Deployment Strategy

**Context:** Need to deploy ML models for presence detection and people counting across rooms.

**Decision:** Use **Hybrid Deployment** (Edge + Cloud) with model versioning.

**Rationale:**
- **Edge:** Low latency for presence detection (<10ms)
- **Cloud:** Advanced analytics and people counting (heavy compute)
- **Offline:** Edge provides fallback during internet outages
- **Cost Optimization:** Edge for simple detection, cloud for complex models

**Trade-offs:**
- **Pro:** Best performance for critical features
- **Pro:** Offline capability
- **Pro:** Cost optimization (cloud only when needed)
- **Con:** More complex architecture
- **Con:** Requires edge hardware
- **Con:** Model synchronization challenges

**Consequences:**
- Presence detection model deployed to edge (simple, fast)
- People counting model primarily on cloud (complex, accurate)
- Fallback: Edge attempts counting if cloud unavailable
- Model versioning: Semantic versioning (v1.0.0, v1.1.0) with A/B testing

**Alternatives Considered:**
- **Edge-Only:** Lowest latency, but limited by edge hardware
- **Cloud-Only:** Simplified architecture, but higher latency and requires internet

---

### ADR-004: Real-time Communication Protocol

**Context:** Need to push real-time detection updates to web dashboard.

**Decision:** Use **WebSocket (Socket.io)** for bidirectional communication.

**Rationale:**
- **Low Latency:** Persistent connection, no polling overhead
- **Bidirectional:** Server can push updates without client request
- **Fallback Support:** Automatic fallback to long-polling if WebSocket unavailable
- **Room Support:** Built-in support for multiplexing (multiple rooms per connection)
- **Ecosystem:** Mature libraries for all platforms (Python, JavaScript, mobile)

**Trade-offs:**
- **Pro:** Real-time updates (<100ms)
- **Pro:** Efficient (no repeated HTTP requests)
- **Pro:** Automatic reconnection
- **Con:** Stateful connections (harder to scale)
- **Con:** Requires sticky sessions in load balancing
- **Con:** More complex than REST API

**Consequences:**
- Primary protocol for detection updates
- REST API for configuration and historical queries
- Implement sticky sessions via Nginx/HAProxy
- Use Redis pub/sub for multi-server deployments

**Alternatives Considered:**
- **Server-Sent Events (SSE):** Simpler, but unidirectional (server → client only)
- **Polling:** Simplest, but inefficient and higher latency
- **GraphQL Subscriptions:** Modern, but less mature ecosystem

---

### ADR-005: Frontend Framework Selection

**Context:** Need to build responsive, real-time web dashboard for people counting.

**Decision:** Use **Next.js 14** with React 18 and TailwindCSS.

**Rationale:**
- **Server-Side Rendering (SSR):** Faster initial page load, better SEO
- **API Routes:** Backend for Frontend (BFF) pattern in same codebase
- **TypeScript:** Type safety for complex data models
- **App Router:** Modern file-based routing with nested layouts
- **Zero-Bundle CSS:** TailwindCSS eliminates unused styles

**Trade-offs:**
- **Pro:** Performance (SSR, code splitting, image optimization)
- **Pro:** Developer experience (TypeScript, hot reload)
- **Pro:** SEO friendly (SSR)
- **Con:** Steeper learning curve than vanilla React
- **Con:** Verbose for simple projects
- **Con:** Build time overhead

**Consequences:**
- All frontend code in Next.js monorepo
- Use App Router (not Pages Router)
- TypeScript for all components
- TailwindCSS + shadcn/ui for UI components
- Recharts for data visualization

**Alternatives Considered:**
- **Create React App (CRA):** Simpler, but no SSR or API routes
- **Vue.js + Nuxt.js:** Less verbose, but smaller ecosystem
- **SvelteKit:** Lighter weight, but less mature

---

## 13. Scalability Strategy

### 13.1 Scaling Dimensions

**Vertical Scaling (Scale-Up):**
- **Signal Processing:** More CPU cores for parallel feature extraction
- **ML Inference:** GPU acceleration (NVIDIA Jetson, CUDA)
- **Database:** More RAM for larger InfluxDB cache

**Horizontal Scaling (Scale-Out):**
- **API Servers:** Load balancing across multiple instances
- **Edge Devices:** 1 device per 1-2 rooms
- **Databases:** Sharding by room_id or geographic region

### 13.2 Performance Optimization

**Caching Strategy:**
```
┌─────────────────────────────────────────────────────────────┐
│  Cache Layer (Redis)                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  L1 Cache (Memory):                                   │  │
│  │  - Latest detection (5-minute TTL)                    │  │
│  │  - Calibration data (24-hour TTL)                     │  │
│  │  - User sessions (1-hour TTL)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  L2 Cache (CDN - Cloudflare):                        │  │
│  │  - Static assets (JS, CSS, images)                   │  │
│  │  - API responses (1-minute TTL, authenticated)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Database Optimization:**
- **InfluxDB:** Downsampling (raw → 5m → 1h → 1d)
- **PostgreSQL:** Indexing on room_id, timestamp
- **Connection Pooling:** PgBouncer for PostgreSQL
- **Read Replicas:** Separate read/write database instances

**API Optimization:**
- **Response Compression:** Gzip compression for API responses
- **Pagination:** Limit query results (default 100 items per page)
- **Batch Operations:** Bulk insert for detection data
- **Async Processing:** Celery for long-running tasks (calibration)

### 13.3 Auto-Scaling Configuration

**Kubernetes Horizontal Pod Autoscaler (HPA):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wifi-detection-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wifi-detection-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

---

## 14. Monitoring and Observability

### 14.1 Metrics Collection

**Prometheus Metrics:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Detection metrics
detection_total = Counter(
    'detections_total',
    'Total number of detections',
    ['room_id', 'presence']
)

detection_accuracy = Gauge(
    'detection_accuracy',
    'Detection accuracy (validated samples)',
    ['room_id']
)

detection_latency = Histogram(
    'detection_latency_seconds',
    'Detection processing latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# API metrics
api_request_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_latency = Histogram(
    'api_request_latency_seconds',
    'API request latency',
    ['endpoint']
)

# Hardware metrics
detector_signal_strength = Gauge(
    'detector_signal_strength_dbm',
    'WiFi signal strength (RSSI)',
    ['detector_id']
)

detector_status = Gauge(
    'detector_status',
    'Detector online status (1=online, 0=offline)',
    ['detector_id']
)
```

### 14.2 Logging Strategy

**Structured Logging (Python):**

```python
import structlog

logger = structlog.get_logger()

# Detection event
logger.info(
    "detection_completed",
    room_id="conference-room-a",
    presence=True,
    count=3,
    confidence=0.97,
    processing_time_ms=150,
    timestamp=datetime.now().isoformat()
)

# Error event
logger.error(
    "detector_offline",
    detector_id="router-03",
    error="Connection timeout",
    last_seen=datetime.now().isoformat()
)
```

**Log Levels:**
- **DEBUG:** Detailed signal processing data
- **INFO:** Normal operations (detections, calibrations)
- **WARNING:** Degraded performance (high latency, low confidence)
- **ERROR:** Failures (detector offline, model errors)
- **CRITICAL:** System failures (database down, out of memory)

### 14.3 Health Checks

**Liveness Probe (Kubernetes):**

```python
@app.get("/health/live")
async def liveness_probe():
    """Check if service is running"""
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness_probe():
    """Check if service can handle requests"""
    checks = {
        "database": await check_database(),
        "influxdb": await check_influxdb(),
        "redis": await check_redis(),
        "ml_models": await check_ml_models()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks}
    )
```

### 14.4 Alerting Rules

**Prometheus Alert Rules:**

```yaml
groups:
- name: wifi_detection_alerts
  rules:
  # High detection latency
  - alert: HighDetectionLatency
    expr: histogram_quantile(0.95, detection_latency_seconds) > 1.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High detection latency in room {{ $labels.room_id }}"
      description: "95th percentile latency is {{ $value }}s"

  # Detector offline
  - alert: DetectorOffline
    expr: detector_status == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Detector {{ $labels.detector_id }} is offline"

  # Low detection accuracy
  - alert: LowDetectionAccuracy
    expr: detection_accuracy < 0.90
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Detection accuracy dropped in room {{ $labels.room_id }}"
      description: "Accuracy is {{ $value }}%"

  # API error rate
  - alert: HighAPIErrorRate
    expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High API error rate on {{ $labels.endpoint }}"
```

---

## Conclusion

This architecture document presents a comprehensive, scalable, and privacy-preserving solution for WiFi-based people detection. The system balances real-time performance with advanced analytics, leverages both edge and cloud computing, and follows best practices for security and data protection.

### Key Architectural Decisions:

1. **Hybrid Deployment:** Edge for low-latency presence detection, cloud for advanced analytics
2. **Python FastAPI Backend:** Seamless ML integration with async support
3. **InfluxDB for Time-Series:** Optimized storage and querying of detection data
4. **Random Forest ML Model:** 98-99% accuracy for people counting
5. **WebSocket Real-time Updates:** Sub-100ms latency for live dashboard
6. **Next.js Frontend:** Modern, type-safe, and performant web dashboard

### Next Steps:

1. **Prototype Phase:** Build MVP with 1 room, 4 detectors
2. **Validation:** Collect training data, validate ML models
3. **Performance Testing:** Benchmark latency, accuracy, scalability
4. **Security Audit:** Penetration testing, GDPR compliance review
5. **Production Deployment:** Roll out to pilot locations
6. **Iterative Improvement:** Collect feedback, retrain models quarterly

This architecture provides a solid foundation for building a production-grade WiFi-based people detection system that respects user privacy while delivering accurate, real-time occupancy monitoring.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-02-02
**Maintained By:** System Architecture Team
**Review Cycle:** Quarterly or before major releases
