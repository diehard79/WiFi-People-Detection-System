# SPARC Methodology for WiFi-Based People Detection

**Version:** 1.0.0
**Date:** 2025-02-02
**Project:** WiFi-Based People Detection Web Application
**Status:** Active Development Methodology

---

## Table of Contents

1. [Introduction to SPARC](#1-introduction-to-sparc)
2. [Phase 1: Specification](#2-phase-1-specification)
3. [Phase 2: Pseudocode](#3-phase-2-pseudocode)
4. [Phase 3: Architecture](#4-phase-3-architecture)
5. [Phase 4: Refinement (TDD Approach)](#5-phase-4-refinement-tdd-approach)
6. [Phase 5: Completion](#6-phase-5-completion)
7. [SPARC Implementation Roadmap](#7-sparc-implementation-roadmap)
8. [Success Criteria](#8-success-criteria)
9. [Tools and Automation](#9-tools-and-automation)

---

## 1. Introduction to SPARC

### 1.1 What is SPARC?

**SPARC** is a systematic development methodology for building robust, test-driven software applications through five distinct phases:

```
┌─────────────────────────────────────────────────────────────┐
│                    SPARC METHODOLOGY                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  S ────────────────────────────────────────────────────┐   │
│  │ SPECIFICATION                                         │   │
│  │ Define requirements, constraints, and success criteria │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  P ────────────────────────────────────────────────────┐   │
│  │ PSEUDOCODE                                            │   │
│  │ Design algorithms and data flows in pseudocode        │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  A ────────────────────────────────────────────────────┐   │
│  │ ARCHITECTURE                                           │   │
│  │ Design system architecture and component interactions │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  R ────────────────────────────────────────────────────┐   │
│  │ REFINEMENT (TDD)                                      │   │
│  │ Test-driven implementation and code refinement        │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  C ────────────────────────────────────────────────────┐   │
│  │ COMPLETION                                            │   │
│  │ Integration, testing, deployment, and documentation  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Why SPARC for This Project?

**Benefits for WiFi-Based People Detection:**

1. **Structured Development:** Prevents "jump to coding" without proper planning
2. **Quality Focus:** Test-driven approach ensures 98-99% accuracy targets are met
3. **Documentation-First:** All decisions documented before implementation
4. **Risk Mitigation:** Architecture phase identifies technical risks early
5. **Maintainability:** Refinement phase produces clean, testable code

**Project-Specific Advantages:**

| Phase | WiFi Detection Application Benefit |
|-------|----------------------------------|
| **Specification** | Clear accuracy requirements (98-99%), privacy (GDPR), performance (<25s) |
| **Pseudocode** | Algorithm design for signal processing, ML inference, calibration |
| **Architecture** | Hybrid edge-cloud architecture, component interactions |
| **Refinement** | Test ML models with real RSSI data, validate accuracy |
| **Completion** | Multi-detector coordination, edge-cloud sync, user acceptance |

### 1.3 SPARC vs. Traditional Development

| Aspect | Traditional | SPARC |
|--------|-------------|-------|
| **Planning** | Minimal or ad-hoc | Structured specification phase |
| **Algorithm Design** | Jump to coding | Pseudocode-first approach |
| **Architecture** | Emerges during coding | Explicit architecture phase |
| **Testing** | After implementation | Test-driven (before implementation) |
| **Documentation** | After completion | Throughout all phases |
| **Risk Detection** | Late (during testing) | Early (architecture phase) |

---

## 2. Phase 1: Specification

### 2.1 Objectives

The Specification phase defines **what** we are building, **why** we are building it, and **how we will measure success**.

### 2.2 Requirements Gathering Approach

**Stakeholder Identification:**
```
┌─────────────────────────────────────────────────────────────┐
│                      STAKEHOLDERS                            │
├─────────────────────────────────────────────────────────────┤
│  Primary Users:                                              │
│  - Facility managers (need occupancy monitoring)             │
│  - Building owners (need space utilization analytics)         │
│  - Security personnel (need presence detection)              │
│                                                               │
│  Secondary Users:                                            │
│  - Employees (being monitored, need privacy assurance)        │
│  - IT administrators (deploy and maintain system)             │
│                                                               │
│  Technical Stakeholders:                                     │
│  - Data scientists (ML model development)                    │
│  - Hardware engineers (WiFi detector setup)                  │
│  - Software developers (application development)              │
│                                                               │
│  Regulatory Stakeholders:                                    │
│  - GDPR compliance officers (privacy assurance)              │
│  - Security auditors (data protection verification)           │
└─────────────────────────────────────────────────────────────┘
```

**Requirements Sources:**
- **Research Synthesis:** `/docs/research-synthesis-wifi-human-detection.md`
- **Architecture Document:** `/docs/architecture/SYSTEM_ARCHITECTURE.md`
- **Stakeholder Interviews:** User needs, pain points
- **Technical Constraints:** Hardware, budget, timeline
- **Regulatory Requirements:** GDPR, data protection laws

### 2.3 Functional Requirements

**Core Capabilities:**

```
FR-001: PRESENCE DETECTION
  Description: System shall detect human presence in a monitored space
  Input: RSSI data from 4-5 WiFi detectors
  Output: Binary presence indication (present/absent)
  Accuracy: >99% detection accuracy
  Latency: <25 seconds end-to-end
  Priority: Critical

FR-002: PEOPLE COUNTING
  Description: System shall estimate the number of individuals in a space
  Input: RSSI features from detectors
  Output: Integer count (0-10 people)
  Accuracy: >98% for 1-5 people, >95% for 6-10 people
  Latency: <25 seconds end-to-end
  Priority: Critical

FR-003: REAL-TIME MONITORING
  Description: System shall provide real-time dashboard updates
  Input: Detection results from ML models
  Output: WebSocket stream to frontend
  Update Rate: Every 10 seconds (new window)
  Priority: High

FR-004: MULTI-ROOM SUPPORT
  Description: System shall monitor multiple rooms independently
  Input: N rooms × 4-5 detectors each
  Output: Per-room detection results
  Scalability: Support 100+ concurrent rooms
  Priority: High

FR-005: CALIBRATION MANAGEMENT
  Description: System shall perform automated daily calibration
  Input: Empty room RSSI data (5 minutes)
  Output: Baseline statistics stored in database
  Frequency: Daily at 3:00 AM (configurable)
  Priority: High

FR-006: HISTORICAL ANALYTICS
  Description: System shall store and analyze historical detection data
  Input: Time-series detection results
  Output: Trends, heatmaps, peak usage reports
  Retention: 90 days (configurable)
  Priority: Medium

FR-007: ALERT SYSTEM
  Description: System shall generate alerts based on configurable rules
  Input: Detection results + user-defined thresholds
  Output: Email, SMS, webhook notifications
  Priority: Medium

FR-008: USER AUTHENTICATION
  Description: System shall authenticate and authorize users
  Input: User credentials (email/password)
  Output: JWT tokens, role-based access control
  Roles: Admin, Standard User, Read-Only
  Priority: High
```

### 2.4 Non-Functional Requirements

**Quality Attributes:**

```
NFR-001: ACCURACY
  Target: >98% presence detection, >98% people counting (1-5 people)
  Measurement: Validated against ground truth (manual counts)
  Priority: Critical

NFR-002: PERFORMANCE
  Detection Latency: <25 seconds end-to-end
  API Response Time: P95 <100ms
  WebSocket Latency: <50ms message delivery
  Page Load Time: <2 seconds initial page load
  Priority: High

NFR-003: SCALABILITY
  Concurrent Rooms: Support 100+ concurrent rooms
  Concurrent Users: Support 1000+ concurrent dashboard users
  Throughput: 1000+ detection predictions per second
  Priority: High

NFR-004: RELIABILITY
  Uptime: 99.5% availability target
  Mean Time Between Failures (MTBF): >720 hours (30 days)
  Mean Time To Recovery (MTTR): <1 hour
  Data Loss: <0.1% (graceful degradation)
  Priority: Critical

NFR-005: SECURITY
  Authentication: JWT-based with role-based access control
  Encryption: TLS 1.3 for data in transit, AES-256 for data at rest
  Privacy: GDPR compliant, edge-first processing
  Audit Logging: All data access logged
  Priority: Critical

NFR-006: MAINTAINABILITY
  Code Coverage: >90% for critical paths (ML inference, signal processing)
  Documentation: All APIs documented with OpenAPI/Swagger
  Onboarding: <2 days for new developers
  Deployment: Automated CI/CD pipeline
  Priority: Medium

NFR-007: USABILITY
  Mobile Support: Responsive design (iOS Safari, Android Chrome)
  Accessibility: WCAG 2.1 AA compliance
  Browser Support: Latest 2 versions of Chrome, Firefox, Safari, Edge
  Language: English (future: multi-language support)
  Priority: Medium
```

### 2.5 Constraints

**Technical Constraints:**

```
TC-001: HARDWARE LIMITATIONS
  WiFi Routers: Standard 802.11n/ac/ax routers only
  Detectors per Room: 4-5 minimum for 98%+ accuracy
  Edge Device: Raspberry Pi 4 (4GB RAM) or equivalent
  Network: Gigabit Ethernet recommended, WiFi 5+ acceptable

TC-002: ML MODEL CONSTRAINTS
  Framework: scikit-learn (Random Forest) for primary model
  Training Data: 1000-5000 labeled samples per room
  Inference Time: <10ms per prediction (edge device)
  Model Size: <3MB (for edge deployment)

TC-003: CALIBRATION REQUIREMENTS
  Frequency: Daily calibration required
  Duration: 5 minutes empty room data collection
  Timing: Default 3:00 AM (configurable)
  Prerequisite: Empty room (no people present)

TC-004: PRIVACY CONSTRAINTS
  Data Minimization: Only aggregate counts transmitted to cloud
  Retention: Raw RSSI data <24 hours, aggregates <90 days
  Anonymization: MAC addresses hashed before storage
  Consent: Explicit user consent required for data collection
```

**Business Constraints:**

```
BC-001: BUDGET
  Hardware Cost: <$500 per room (one-time)
  Operational Cost: <$6/month per room (cloud services)
  Development Timeline: 6 months to MVP

BC-002: TIMELINE
  Phase 1 (Specification): 2 weeks
  Phase 2 (Pseudocode): 2 weeks
  Phase 3 (Architecture): 3 weeks
  Phase 4 (Refinement): 8 weeks
  Phase 5 (Completion): 4 weeks

BC-003: REGULATORY
  GDPR Compliance: Required for EU deployments
  Data Protection: Privacy-by-design approach mandatory
  Audit Trail: All data access logged and retained
```

### 2.6 Acceptance Criteria

**Definition of Done (per feature):**

```
AC-001: PRESENCE DETECTION
  ✓ Detects presence with >99% accuracy (100 test samples)
  ✓ Returns result within 25 seconds of signal collection
  ✓ Handles detector failure (graceful degradation)
  ✓ Documented API with examples
  ✓ Unit tests (90%+ coverage)
  ✓ Integration tests (end-to-end detection flow)

AC-002: PEOPLE COUNTING
  ✓ Counts people with >98% accuracy for 1-5 people (100 test samples)
  ✓ Counts people with >95% accuracy for 6-10 people (100 test samples)
  ✓ Returns result within 25 seconds of signal collection
  ✓ Calibration data properly applied
  ✓ Documented API with examples
  ✓ Unit tests (90%+ coverage)
  ✓ Model performance validated

AC-003: REAL-TIME DASHBOARD
  ✓ Updates within 1 second of detection result
  ✓ Shows presence indicator (green/red)
  ✓ Shows people count gauge
  ✓ Shows confidence percentage
  ✓ Mobile responsive (tested on iOS, Android)
  ✓ Accessibility audit passed (WCAG 2.1 AA)
```

---

## 3. Phase 2: Pseudocode

### 3.1 Objectives

The Pseudocode phase designs **how** the system will work through algorithm design and data flow specification, without implementation details.

### 3.2 Signal Processing Pseudocode

**RSSI Data Collection:**
```
ALGORITHM: Collect RSSI Data
INPUT: detector_id (string), sampling_rate (Hz), duration (seconds)
OUTPUT: rssi_samples (list of floats)

BEGIN
  INITIALIZE empty list rssi_samples
  INITIALIZE start_time = current_timestamp()

  WHILE current_timestamp() - start_time < duration DO
    rssi = GET_SIGNAL_STRENGTH(detector_id)
    APPEND rssi TO rssi_samples
    sleep(1 / sampling_rate)  // Wait for next sample
  END WHILE

  RETURN rssi_samples
END
```

**Sliding Window Processing:**
```
ALGORITHM: Sliding Window Processing
INPUT: rssi_stream (continuous), window_size (seconds), overlap (percentage)
OUTPUT: window_features (continuous stream)

BEGIN
  INITIALIZE buffer = empty deque
  INITIALIZE step_size = window_size * (1 - overlap)

  FOR EACH rssi_value IN rssi_stream DO
    APPEND rssi_value TO buffer

    IF buffer.size >= window_size * sampling_rate THEN
      window = CONVERT buffer TO list
      features = EXTRACT_FEATURES(window)
      SEND features TO processing_queue

      REMOVE oldest step_size elements FROM buffer
    END IF
  END FOR

  RETURN window_features
END
```

**Feature Extraction:**
```
ALGORITHM: Extract RSSI Features
INPUT: rssi_window (list of floats)
OUTPUT: features (dictionary)

BEGIN
  INITIALIZE features = {}

  // Basic Statistics
  features['mean'] = MEAN(rssi_window)
  features['std'] = STANDARD_DEVIATION(rssi_window)
  features['variance'] = VARIANCE(rssi_window)
  features['min'] = MIN(rssi_window)
  features['max'] = MAX(rssi_window)
  features['range'] = features['max'] - features['min']

  // Higher-Order Statistics
  features['skewness'] = SKEWNESS(rssi_window)
  features['kurtosis'] = KURTOSIS(rssi_window)
  features['coefficient_of_variation'] = features['std'] / features['mean']

  // Rate of Change
  differences = DIFF(rssi_window)  // First-order difference
  features['diff_mean'] = MEAN(differences)
  features['diff_std'] = STANDARD_DEVIATION(differences)

  // Frequency Domain
  fft_result = FFT(rssi_window)
  features['dominant_frequency'] = ARGMAX(ABS(fft_result))
  features['spectral_centroid'] = SPECTRAL_CENTROID(fft_result)

  RETURN features
END
```

### 3.3 ML Inference Pseudocode

**Presence Detection:**
```
ALGORITHM: Detect Presence
INPUT: features (dictionary), baseline (dictionary)
OUTPUT: presence (boolean), confidence (float)

BEGIN
  // Method 1: Statistical Threshold (3-sigma rule)
  z_score = (features['mean'] - baseline['mean_rssi']) / baseline['std_rssi']

  IF z_score > 3.0 THEN
    RETURN (presence=True, confidence=0.99)
  END IF

  // Method 2: Machine Learning Model (Fallback)
  feature_vector = FLATTEN(features)
  probability = presence_model.PREDICT_PROBABILITY(feature_vector)

  IF probability > 0.5 THEN
    RETURN (presence=True, confidence=probability)
  ELSE
    RETURN (presence=False, confidence=1-probability)
  END IF
END
```

**People Counting:**
```
ALGORITHM: Count People
INPUT: features (list of dictionaries, one per detector), baseline (dictionary)
OUTPUT: count (integer), confidence (float)

BEGIN
  // Normalize Features
  normalized_features = []
  FOR EACH detector_features IN features DO
    detector_id = detector_features['detector_id']
    base = baseline[detector_id]

    normalized = []
    APPEND (detector_features['mean'] - base['mean_rssi']) TO normalized
    APPEND (detector_features['std'] / base['std_rssi']) TO normalized
    APPEND detector_features['max'] TO normalized
    APPEND detector_features['min'] TO normalized
    APPEND detector_features['variance'] TO normalized

    EXTEND normalized_features WITH normalized
  END FOR

  // Cross-Detector Features
  correlation_matrix = COMPUTE_CORRELATION(features)
  APPEND MAX(correlation_matrix) TO normalized_features
  APPEND MEAN(correlation_matrix) TO normalized_features
  APPEND STD(correlation_matrix) TO normalized_features

  // ML Prediction
  feature_vector = ARRAY(normalized_features)
  count = counting_model.PREDICT(feature_vector)
  probabilities = counting_model.PREDICT_PROBABILITY(feature_vector)
  confidence = MAX(probabilities)

  RETURN (count, confidence)
END
```

### 3.4 Calibration Pseudocode

**Automated Calibration:**
```
ALGORITHM: Daily Calibration
INPUT: room_id (string), duration (minutes)
OUTPUT: baseline (dictionary)

BEGIN
  // Step 1: Notify Users
  BROADCAST message="Calibration starting in 15 minutes"
  WAIT 15 minutes

  // Step 2: Collect Noise Data
  INITIALIZE samples_per_detector = empty dictionary

  start_time = current_timestamp()
  end_time = start_time + duration_minutes * 60

  WHILE current_timestamp() < end_time DO
    FOR EACH detector_id IN GET_DETECTORS(room_id) DO
      rssi = GET_SIGNAL_STRENGTH(detector_id)

      IF detector_id NOT IN samples_per_detector THEN
        INITIALIZE samples_per_detector[detector_id] = empty list
      END IF

      APPEND rssi TO samples_per_detector[detector_id]
    END FOR

    sleep(1)  // 1 Hz sampling
  END WHILE

  // Step 3: Compute Baseline Statistics
  INITIALIZE baseline = empty dictionary

  FOR EACH detector_id, samples IN samples_per_detector DO
    baseline[detector_id] = {
      'mean_rssi': MEAN(samples),
      'std_rssi': STD(samples),
      'min_rssi': MIN(samples),
      'max_rssi': MAX(samples),
      'variance': VARIANCE(samples),
      'sample_count': LENGTH(samples)
    }
  END FOR

  // Step 4: Quality Checks
  FOR EACH detector_id, baseline_stats IN baseline DO
    snr = CALCULATE_SNR(samples_per_detector[detector_id])
    outliers = DETECT_OUTLIERS(samples_per_detector[detector_id])

    IF snr < 15 OR LENGTH(outliers) / LENGTH(samples) > 0.05 THEN
      LOG warning="Low quality calibration data for " + detector_id
      RETURN failure="Calibration quality check failed"
    END IF
  END FOR

  // Step 5: Store Baseline
  STORE baseline IN DATABASE WITH room_id

  // Step 6: Notify Completion
  BROADCAST message="Calibration complete"
  RETURN baseline
END
```

### 3.5 Data Flow Pseudocode

**End-to-End Detection Flow:**
```
ALGORITHM: Real-Time Detection Pipeline
INPUT: room_id (string)
OUTPUT: detection_results (continuous)

BEGIN
  // Initialize Components
  detectors = GET_DETECTORS(room_id)
  baseline = GET_LATEST_BASELINE(room_id)
  buffer = SLIDING_WINDOW_BUFFER(size=20_seconds, overlap=50%)

  // Main Loop
  WHILE system_running DO
    // Collect RSSI from all detectors
    FOR EACH detector IN detectors DO
      rssi = GET_SIGNAL_STRENGTH(detector.id)
      buffer.ADD(detector.id, rssi)
    END FOR

    // Check if window is ready
    IF buffer.IS_READY() THEN
      // Extract window data
      rssi_windows = buffer.GET_WINDOWS()

      // Extract features
      features = EXTRACT_FEATURES(rssi_windows)

      // Normalize using baseline
      normalized_features = NORMALIZE(features, baseline)

      // Detect presence
      presence, presence_conf = DETECT_PRESENCE(normalized_features, baseline)

      IF presence IS True THEN
        // Count people
        count, count_conf = COUNT_PEOPLE(normalized_features, baseline)
      ELSE
        count = 0
        count_conf = 0.99
      END IF

      // Create detection result
      result = {
        'room_id': room_id,
        'timestamp': CURRENT_TIMESTAMP(),
        'presence': presence,
        'presence_confidence': presence_conf,
        'count': count,
        'count_confidence': count_conf,
        'features': features
      }

      // Store result
      STORE result IN DATABASE

      // Push to dashboard
      WEBSOCKET_EMIT(result)

      // Slide window
      buffer.SLIDE()
    END IF

    sleep(1)  // 1 Hz processing
  END WHILE
END
```

---

## 4. Phase 3: Architecture

### 4.1 Objectives

The Architecture phase defines **system structure**, **component interactions**, and **technology choices**. This phase is **already documented** in:

**Reference:** `/docs/architecture/SYSTEM_ARCHITECTURE.md`

### 4.2 Key Architectural Decisions

**Architecture Decision Records (ADRs):**

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | RSSI-based detection with ML enhancement | Accepted |
| ADR-002 | Python with FastAPI backend | Accepted |
| ADR-003 | InfluxDB for time-series data | Accepted |
| ADR-004 | scikit-learn Random Forest models | Accepted |
| ADR-005 | WebSocket (Socket.io) for real-time updates | Accepted |
| ADR-006 | Hybrid deployment (edge + cloud) | Accepted |
| ADR-007 | Next.js 14 with TypeScript frontend | Accepted |
| ADR-008 | JWT-based authentication | Accepted |
| ADR-009 | Edge-first processing for privacy | Accepted |
| ADR-010 | Automated daily calibration | Accepted |

### 4.3 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    HIGH-LEVEL ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  PHYSICAL LAYER (WiFi Routers)                       │  │
│  │  4-5 standard 802.11n/ac/ax routers per room          │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│                      ▼                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  EDGE LAYER (Raspberry Pi 4)                          │  │
│  │  - Signal Collector Service                           │  │
│  │  - Signal Processing Pipeline                         │  │
│  │  - ML Inference Engine (scikit-learn)                │  │
│  │  - Calibration Manager                                │  │
│  │  - Local Database (InfluxDB, SQLite)                  │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │ (Optional Sync)                       │
│                      ▼                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CLOUD LAYER (AWS/GCP/Azure)                          │  │
│  │  - Enhanced Analytics                                 │  │
│  │  - Multi-Room Aggregation                             │  │
│  │  - User Management (PostgreSQL)                       │  │
│  │  - Global Monitoring                                  │  │
│  │  - Model Training Pipeline                            │  │
│  └───────────────────┬───────────────────────────────────┘  │
│                      │                                       │
│                      ▼                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  FRONTEND LAYER (Next.js 14)                          │  │
│  │  - Real-Time Dashboard                                │  │
│  │  - Historical Analytics                               │  │
│  │  - Configuration Panel                                 │  │
│  │  - Alert Management                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Component Interactions

**Detection Flow (Real-Time):**
```
WiFi Routers → Signal Collector → Buffer (20s window) → Feature Extractor
→ ML Inference → Database Store → WebSocket → Frontend Dashboard
```

**Calibration Flow (Daily):**
```
Scheduler → Notification → Collect RSSI (5 min) → Compute Baseline
→ Quality Check → Store Baseline → Notification Complete
```

---

## 5. Phase 4: Refinement (TDD Approach)

### 5.1 Objectives

The Refinement phase implements the system **test-first**, ensuring all components meet specifications before deployment.

### 5.2 Test Strategy

**Test Pyramid:**

```
                  ┌─────────────────┐
                  │   E2E Tests     │  ← 10% (Critical paths)
                  │   (Playwright)  │
                  ├─────────────────┤
                  │ Integration     │  ← 30% (API, Database)
                  │   Tests         │
                  ├─────────────────┤
                  │   Unit Tests    │  ← 60% (Business logic)
                  │   (Pytest)      │
                  └─────────────────┘
```

### 5.3 Unit Tests

**Signal Processing Tests:**
```python
# tests/test_signal_processing.py
import pytest
import numpy as np
from signal_processing import extract_features, normalize_features

def test_extract_features_basic_statistics():
    """Test feature extraction with known data"""
    rssi_window = [-45, -46, -44, -45, -47, -45, -46, -44, -45, -46]
    features = extract_features(rssi_window)

    assert features['mean'] == pytest.approx(-45.3, abs=0.1)
    assert features['std'] == pytest.approx(0.95, abs=0.1)
    assert features['min'] == -47
    assert features['max'] == -44

def test_normalize_features():
    """Test feature normalization using baseline"""
    features = {'mean': -40.0, 'std': 2.0}
    baseline = {'mean_rssi': -42.0, 'std_rssi': 1.5}

    normalized = normalize_features(features, baseline)

    assert normalized['mean_delta'] == 2.0  # -40 - (-42)
    assert normalized['std_ratio'] == pytest.approx(1.33, abs=0.01)  # 2.0 / 1.5
```

**ML Model Tests:**
```python
# tests/test_ml_models.py
import pytest
import joblib
import numpy as np

def test_presence_detection_accuracy():
    """Test presence detection model accuracy"""
    model = joblib.load('models/presence_detection.pkl')

    # Load test dataset
    X_test, y_test = load_test_data('presence')

    # Predict
    y_pred = model.predict(X_test)

    # Assert >99% accuracy
    accuracy = np.mean(y_pred == y_test)
    assert accuracy > 0.99

def test_people_counting_accuracy():
    """Test people counting model accuracy"""
    model = joblib.load('models/counting_model.pkl')

    # Load test dataset (1-5 people)
    X_test, y_test = load_test_data('counting_1_5')

    # Predict
    y_pred = model.predict(X_test)

    # Assert >98% accuracy
    accuracy = np.mean(y_pred == y_test)
    assert accuracy > 0.98
```

### 5.4 Integration Tests

**API Tests:**
```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_detection_presence_endpoint():
    """Test GET /api/v1/detection/presence"""
    response = client.get("/api/v1/detection/presence?room_id=conf-a")

    assert response.status_code == 200
    data = response.json()
    assert 'presence' in data
    assert 'presence_confidence' in data
    assert isinstance(data['presence'], bool)
    assert 0 <= data['presence_confidence'] <= 1

def test_detection_count_endpoint():
    """Test GET /api/v1/detection/count"""
    response = client.get("/api/v1/detection/count?room_id=conf-a")

    assert response.status_code == 200
    data = response.json()
    assert 'count' in data
    assert 'count_confidence' in data
    assert 0 <= data['count'] <= 10
```

**Database Tests:**
```python
# tests/test_database_integration.py
import pytest
from database import get_database

@pytest.mark.asyncio
async def test_store_detection():
    """Test storing detection result in database"""
    db = get_database()

    detection = {
        'room_id': 'test-room',
        'timestamp': '2025-02-02T10:00:00Z',
        'presence': True,
        'count': 3
    }

    await db.store_detection(detection)

    # Retrieve and verify
    retrieved = await db.get_latest_detection('test-room')
    assert retrieved['count'] == 3
    assert retrieved['presence'] is True
```

### 5.5 End-to-End Tests

**E2E Test with Playwright:**
```typescript
// tests/e2e/detection.spec.ts
import { test, expect } from '@playwright/test';

test('real-time detection dashboard', async ({ page }) => {
  // Navigate to dashboard
  await page.goto('http://localhost:3000/dashboard/real-time?room_id=conf-a');

  // Wait for connection
  await page.waitForSelector('[data-testid="connection-status"][data-connected="true"]', {
    timeout: 5000
  });

  // Verify presence indicator is visible
  await expect(page.locator('[data-testid="presence-indicator"]')).toBeVisible();

  // Verify count gauge is visible
  await expect(page.locator('[data-testid="count-gauge"]')).toBeVisible();

  // Verify confidence is displayed
  await expect(page.locator('[data-testid="confidence-percentage"]')).toBeVisible();

  // Wait for at least one detection update
  await page.waitForSelector('[data-testid="detection-update"]', {
    timeout: 15000  // 15 seconds max
  });

  // Verify detection update contains expected fields
  const detection = await page.locator('[data-testid="detection-update"]').textContent();
  expect(detection).toContain('Presence:');
  expect(detection).toContain('Count:');
});
```

### 5.6 Test Coverage Requirements

**Coverage Targets:**
```
Component                  | Target Coverage
---------------------------|------------------
Signal Processing          | >95%
ML Inference               | >90%
API Endpoints              | >90%
Database Operations        | >85%
WebSocket Handlers         | >80%
Frontend Components        | >85%
```

**Quality Gates:**
- No commits without passing unit tests
- No merges without >90% coverage increase
- No deployment without passing E2E tests

---

## 6. Phase 5: Completion

### 6.1 Objectives

The Completion phase integrates all components, performs comprehensive testing, and prepares the system for production deployment.

### 6.2 Integration Testing Approach

**Hardware-Software Integration:**
```
Test Scenario 1: Single Room Detection
  Setup: 4 WiFi routers, 1 edge device, 1 room
  Procedure:
    1. Deploy hardware to room
    2. Configure detectors in system
    3. Run automated calibration
    4. Collect 100 labeled samples (0-5 people)
    5. Compare system predictions to ground truth
  Success Criteria:
    - Presence detection: >99% accuracy
    - People counting: >98% accuracy (1-5 people)
    - Latency: <25 seconds end-to-end

Test Scenario 2: Multi-Detector Coordination
  Setup: 5 detectors in single room
  Procedure:
    1. Verify all detectors collecting data
    2. Simulate detector failure (disconnect 1 detector)
    3. Verify graceful degradation
    4. Reconnect detector
    5. Verify automatic recovery
  Success Criteria:
    - System continues with 4 detectors
    - Accuracy drop <5% with 4 detectors
    - Automatic recovery within 1 minute
```

**Edge-Cloud Synchronization:**
```
Test Scenario 3: Cloud Sync Failure
  Setup: Edge device with cloud sync enabled
  Procedure:
    1. Disable internet connection
    2. Verify local operation continues
    3. Generate 10 detection results
    4. Re-enable internet connection
    5. Verify automatic sync
  Success Criteria:
    - Local operation: 100% uptime during outage
    - Data loss: 0% (all results synced)
    - Sync time: <1 minute after reconnection
```

### 6.3 User Acceptance Testing (UAT)

**UAT Checklist:**
```
UAT-001: Dashboard Usability
  [ ] Can view real-time detection results
  [ ] Can view historical analytics
  [ ] Can configure rooms and detectors
  [ ] Can trigger manual calibration
  [ ] Can set up alert rules
  [ ] Dashboard works on mobile devices

UAT-002: Accuracy Validation
  [ ] Presence detection matches ground truth (>99%)
  [ ] People counting matches ground truth (>98% for 1-5 people)
  [ ] Calibration improves accuracy
  [ ] No false positives in empty room

UAT-003: Performance Validation
  [ ] Dashboard loads in <2 seconds
  [ ] Detection updates appear within 1 second
  [ ] No lag or freezing with 100+ concurrent users

UAT-004: Privacy Validation
  [ ] Raw RSSI data never leaves edge device
  [ ] Can view and delete personal data
  [ ] Privacy policy is clear and accessible
  [ ] Consent is obtained before data collection
```

### 6.4 Documentation Requirements

**Required Documentation:**

```
1. User Documentation
   - Installation Guide (hardware setup)
   - User Manual (dashboard, configuration)
   - Troubleshooting Guide
   - FAQ

2. Developer Documentation
   - API Documentation (OpenAPI/Swagger)
   - Architecture Overview
   - Development Environment Setup
   - Contributing Guidelines

3. Operator Documentation
   - Deployment Guide (Docker, Kubernetes)
   - Monitoring Setup (Prometheus, Grafana)
   - Backup and Recovery Procedures
   - Security Hardening Guide

4. Compliance Documentation
   - Privacy Policy (GDPR compliant)
   - Data Protection Impact Assessment (DPIA)
   - Security Audit Report
   - Incident Response Plan
```

### 6.5 Deployment Checklist

**Pre-Deployment:**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage >90% for critical paths
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Backup strategy tested
- [ ] Monitoring configured
- [ ] Alert rules set up

**Deployment Steps:**
```
1. Provision infrastructure (edge devices, cloud resources)
2. Deploy backend services (API, WebSocket, ML models)
3. Deploy frontend (Next.js build, CDN)
4. Configure databases (InfluxDB, PostgreSQL)
5. Run smoke tests (health checks)
6. Perform calibration for each room
7. Verify detection accuracy (ground truth validation)
8. Train users (handover session)
9. Go-live with monitoring
```

---

## 7. SPARC Implementation Roadmap

### 7.1 Phase Timeline

| Phase | Duration | Deliverables | Dependencies |
|-------|----------|--------------|--------------|
| **Specification** | 2 weeks | Requirements document, ADRs 1-10 | Research synthesis |
| **Pseudocode** | 2 weeks | Algorithm pseudocode, data flow diagrams | Specification |
| **Architecture** | 3 weeks | System architecture document, ADRs signed off | Pseudocode |
| **Refinement** | 8 weeks | Tested code, 90%+ coverage | Architecture |
| **Completion** | 4 weeks | Integrated system, documentation | Refinement |

**Total: 19 weeks (~5 months)**

### 7.2 Milestones

```
M1: Requirements Complete (Week 2)
  ✓ All functional requirements documented
  ✓ All non-functional requirements defined
  ✓ All ADRs written and reviewed

M2: Algorithm Design Complete (Week 4)
  ✓ Signal processing pseudocode
  ✓ ML inference pseudocode
  ✓ Calibration pseudocode
  ✓ Data flow diagrams

M3: Architecture Approved (Week 7)
  ✓ System architecture document complete
  ✓ Technology stack selected
  ✓ Component interfaces defined

M4: Core Features Implemented (Week 11)
  ✓ Signal collection service
  ✓ Feature extraction pipeline
  ✓ ML inference engine
  ✓ Unit tests passing

M5: Real-Time Dashboard Working (Week 13)
  ✓ WebSocket communication
  ✓ Frontend components
  ✓ Integration tests passing

M6: Calibration System Working (Week 15)
  ✓ Automated calibration
  ✓ Manual calibration trigger
  ✓ Baseline storage and retrieval

M7: Integration Complete (Week 17)
  ✓ Hardware-software integration
  ✓ Edge-cloud synchronization
  ✓ End-to-end tests passing

M8: Production Ready (Week 19)
  ✓ Documentation complete
  ✓ Security audit passed
  ✓ Performance validated
  ✓ User acceptance testing complete
```

---

## 8. Success Criteria

### 8.1 Phase Completion Criteria

**Specification Phase:**
- [ ] All 8 functional requirements defined
- [ ] All 7 non-functional requirements specified
- [ ] All 10 ADRs written and reviewed
- [ ] Stakeholder sign-off obtained

**Pseudocode Phase:**
- [ ] Signal processing algorithm designed
- [ ] ML inference algorithm designed
- [ ] Calibration algorithm designed
- [ ] Data flow documented
- [ ] Peer review completed

**Architecture Phase:**
- [ ] System architecture document complete
- [ ] Component interfaces defined
- [ ] Technology stack selected
- [ ] Deployment architecture designed
- [ ] Security architecture documented
- [ ] Architecture review board approved

**Refinement Phase:**
- [ ] All core features implemented
- [ ] Unit test coverage >90%
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Code review approved

**Completion Phase:**
- [ ] End-to-end integration successful
- [ ] User acceptance testing passed
- [ ] Documentation complete
- [ ] Deployment verified
- [ ] Go-live approved

### 8.2 Quality Metrics

**Quality Gates:**
```
Gate 1: Code Quality
  - No critical linting issues
  - Code coverage >90% (critical paths)
  - No security vulnerabilities
  - Performance benchmarks met

Gate 2: Testing Quality
  - All unit tests passing
  - All integration tests passing
  - All E2E tests passing
  - Test maintenance <2 hours per week

Gate 3: Documentation Quality
  - All APIs documented
  - User documentation complete
  - Developer documentation up-to-date
  - Documentation review passed

Gate 4: Operational Readiness
  - Monitoring configured
  - Alerting tested
  - Backup strategy verified
  - Disaster recovery tested
```

---

## 9. Tools and Automation

### 9.1 SPARC Automation Tools

**Specification Tools:**
- **Requirements Management:** Markdown + Git version control
- **ADR Templates:** Custom Markdown templates
- **Diagramming:** Mermaid, Draw.io

**Pseudocode Tools:**
- **Pseudocode Editor:** Any text editor with syntax highlighting
- **Review Platform:** GitHub pull requests
- **Version Control:** Git

**Architecture Tools:**
- **Modeling:** C4 Model (diagrams)
- **Documentation:** Markdown, OpenAPI/Swagger
- ** Collaboration:** Miro, Lucidchart

**Refinement Tools:**
- **Testing:** Pytest (Python), Jest (TypeScript)
- **Coverage:** pytest-cov, istanbul
- **CI/CD:** GitHub Actions
- **Linting:** Ruff (Python), ESLint (TypeScript)

**Completion Tools:**
- **E2E Testing:** Playwright
- **Deployment:** Docker, Kubernetes
- **Monitoring:** Prometheus, Grafana
- **Documentation:** Docusaurus, MkDocs

### 9.2 Automation Commands

**SPARC CLI Commands:**
```bash
# Initialize SPARC project
npx sparcel init wifi-detection-app

# Start Specification phase
npx sparcel phase specification

# Generate ADR template
npx sparcel adr create "Backend Programming Language"

# Review ADR
npx sparcel adr review ADR-002

# Start Pseudocode phase
npx sparcel phase pseudocode

# Generate pseudocode template
npx sparcel pseudocode generate "signal_processing"

# Review pseudocode
npx sparcel pseudocode review signal_processing.pseudo

# Start Architecture phase
npx sparcel phase architecture

# Generate architecture diagram
npx sparcel architecture diagram "system_overview"

# Start Refinement phase
npx sparcel phase refinement

# Run tests
npx sparcel test --all

# Run coverage
npx sparcel coverage --threshold=90

# Start Completion phase
npx sparcel phase completion

# Generate deployment checklist
npx sparcel checklist generate
```

---

## Conclusion

The SPARC methodology provides a structured, test-driven approach to building the WiFi-based people detection system. By following the five phases—Specification, Pseudocode, Architecture, Refinement, and Completion—we ensure that:

1. **Requirements are clear** before implementation begins
2. **Algorithms are designed** before code is written
3. **Architecture is validated** before components are built
4. **Code is tested** before it's deployed
5. **System is production-ready** before go-live

This methodology minimizes risk, maximizes quality, and ensures delivery of a system that meets the 98-99% accuracy requirements, maintains privacy, and provides a reliable, scalable solution for WiFi-based people detection.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-02-02
**Maintained By:** Development Team
**Review Cycle:** Before each phase transition
