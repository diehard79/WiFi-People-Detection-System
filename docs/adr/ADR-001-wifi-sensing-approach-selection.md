# ADR-001: WiFi Sensing Approach Selection

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection Web Application
**Decision:** RSSI-Based Detection with Machine Learning Enhancement

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version | Technical Architect |
| 1.1 | 2025-02-02 | Clarified sampling rate configuration (Critical Issue #1 fix) | Technical Architect |

---

---

## Context

We need to select a WiFi-based sensing approach for detecting human presence and counting individuals in indoor spaces. Three primary technical approaches are available:

1. **RSSI (Received Signal Strength Indicator)** - Standard signal strength measurements from commercial WiFi routers
2. **CSI (Channel State Information)** - Fine-grained phase and amplitude data requiring specialized hardware
3. **DensePose Neural Networks** - Deep learning approach for pose estimation using WiFi signals

The decision must balance accuracy requirements, hardware cost, implementation complexity, and deployment feasibility for a web application.

---

## Decision

**Selected Approach: RSSI-Based Detection with Machine Learning Enhancement**

We will use RSSI standard deviation analysis combined with Random Forest machine learning models for:
- Presence detection (>99% accuracy)
- People counting (98-99% accuracy for 1-5 people)
- Real-time processing with 20-second sliding windows

### Key Implementation Parameters

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **Hardware** | 4-5 standard WiFi routers | Research shows 98%+ accuracy with this configuration |
| **Sampling Rate** | 1 Hz (default), Configurable 0.5-2 Hz | Balances data volume with detection responsiveness; 1 Hz is target rate for optimal accuracy-performance tradeoff |
| **Window Size** | 20 seconds | Optimal for capturing human movement patterns |
| **Calibration** | Daily automated (5 min) | Compensates for environmental drift |
| **ML Algorithm** | Random Forest | Proven 98-99% accuracy on RSSI features |
| **Features** | Mean, std dev, variance, FFT | Captures signal variability patterns |

**Sampling Rate Configuration:**

The system supports configurable sampling rates to accommodate different deployment scenarios:

- **Edge-Only Mode:** 1 Hz (default) - Power-efficient, sufficient for presence detection
- **Cloud-Enhanced Mode:** 1.5-2 Hz - Higher accuracy for people counting (requires stable internet)
- **Power-Constrained:** 0.5 Hz - Extended battery life (accepts 2-3% accuracy reduction)
- **High-Accuracy Mode:** 2 Hz - Maximum accuracy for critical spaces (conference rooms, security areas)

**Rate Selection Guidelines:**
```python
# Automatic rate selection based on deployment mode
if deployment_mode == "edge_only":
    sampling_rate = 1.0  # Hz
elif deployment_mode == "cloud_enhanced":
    sampling_rate = 1.5  # Hz (balances accuracy with bandwidth)
elif deployment_mode == "power_constrained":
    sampling_rate = 0.5  # Hz (battery-powered edge devices)
elif deployment_mode == "high_accuracy":
    sampling_rate = 2.0  # Hz (critical security areas)
```

---

## Rationale

### Accuracy Capabilities

**RSSI-Based Systems:**
- **Presence Detection:** 98-99% accuracy with 4-5 detectors
- **People Counting:** 98%+ for 1-5 people, 95%+ for 6-10 people
- **Latency:** 1-3 seconds for real-time detection
- **Proven Results:** Validated in peer-reviewed research ([arXiv:2308.06773](https://arxiv.org/html/2308.06773v2))

**CSI-Based Systems:**
- **Accuracy:** 98-99%+ (slightly better than RSSI)
- **Complexity:** Requires specialized hardware (Intel 5300, Atheros cards)
- **Cost:** $500-2000 for complete CSI system vs. $200-1000 for RSSI

**DensePose WiFi:**
- **Accuracy:** 70-85% (significant limitations)
- **Limitations:** Hallucinations with unusual poses, struggles with 3+ people
- **Status:** Not production-ready (research only)

### Hardware Availability

**RSSI Advantages:**
- Works with standard 802.11n/ac/ax routers (TP-Link, Netgear, etc.)
- No firmware modifications required
- Commercial off-the-shelf hardware
- Easy procurement and replacement

### Recommended WiFi Routers

Based on research and testing, the following routers are recommended for server-based deployment:

| Model | Standard | MIMO | Antennas | Approx. Price | Notes |
|-------|----------|------|----------|--------------|-------|
| **TP-Link Archer A6** | AC1200 | 2x2 | 3 Fixed | $60 | **Best value**, tested |
| **TP-Link Archer A7** | AC1750 | 3x3 | 3 Fixed | $85 | Better performance |
| **Netgear WNR2020** | N300 | 2x2 | 2 Fixed | $45 | Budget option |
| **ASUS RT-AC66U** | AC1750 | 3x3 | 3 External | $120 | Best range, external antennas |

**Minimum Requirements for Other Models:**
- IEEE 802.11n or 802.11ac compatible
- MIMO 2x2 or better
- Removable or adjustable antennas preferred
- TX power: ≥20 dBm

**Router Procurement:**
- Commercial off-the-shelf (COTS) routers
- No firmware modifications required
- Standard WiFi protocols (no proprietary hardware)
- Easy replacement and expansion
- Connect to your server via standard WiFi network

**CSI Limitations:**
- Intel 5300 CSI Tool: Requires specific outdated WiFi cards
- Atheros CSI Tool: Limited card compatibility
- ESP32-based: Lower cost but still specialized
- Most commercial routers NOT compatible with CSI extraction

**DensePose Limitations:**
- Requires two TP-Link routers with custom firmware
- Needs GPU for inference (GeForce GTX 1080 or better)
- Extensive training data collection required

### Implementation Complexity

**RSSI Implementation:**
```python
# Simple data collection
rssi = get_signal_strength(mac_address)
features = [mean(rssi), std(rssi), var(rssi)]
prediction = model.predict(features)
```

**CSI Implementation:**
- Requires custom firmware installation
- Complex phase and amplitude processing
- Specialized driver configuration
- Linux environment typically required

**DensePose Implementation:**
- Deep neural network training (days to weeks)
- Camera + WiFi paired data collection
- Significant computational resources
- Ongoing model refinement required

### Cost Analysis

**Per-Room Hardware Costs:**

| Approach | Hardware | Quantity | Unit Cost | Total Cost |
|----------|----------|----------|-----------|------------|
| **RSSI** | Standard WiFi Routers | 4-5 | $50-100 | $200-500 |
| **CSI** | Intel 5300 Cards | 4-5 | $150-300 | $600-1500 |
| **CSI** | ESP32 Devices | 4-5 | $10-30 | $40-150 |
| **DensePose** | TP-Link Routers + GPU | 2 + 1 | $100 + $500 | $700+ |

**Development Costs:**
- RSSI: 2-3 months (simple integration)
- CSI: 4-6 months (hardware setup + firmware)
- DensePose: 8-12 months (research project)

---

## Consequences

### Positive Consequences

**Feasibility:**
- ✅ Highest feasibility for web app implementation
- ✅ Standard hardware readily available
- ✅ Lower deployment barriers
- ✅ Faster time-to-market (2-3 month MVP)

**Cost-Effectiveness:**
- ✅ 4-5x lower hardware costs than CSI
- ✅ No specialized hardware procurement
- ✅ Easier to scale across multiple locations
- ✅ Replacement hardware available locally

**Privacy:**
- ✅ More privacy-preserving than cameras
- ✅ No visual data collected
- ✅ Aggregated counting only (no individual identification)
- ✅ Easier GDPR compliance

**Maintainability:**
- ✅ Simpler calibration requirements
- ✅ Easier troubleshooting with standard tools
- ✅ Larger community of RSSI-based sensing research
- ✅ Transferable knowledge across hardware vendors

**Performance:**
- ✅ Meets accuracy requirements (98-99%)
- ✅ Real-time processing capable (<3 seconds)
- ✅ Proven in peer-reviewed research
- ✅ Suitable for target use cases (1-10 people)

### Negative Consequences

**Accuracy Limitations:**
- ❌ More susceptible to multipath interference than CSI
- ❌ Accuracy degrades with 6+ people
- ❌ Environmental changes affect performance
- ❌ Daily calibration required (vs. weekly for CSI)

**Environmental Sensitivity:**
- ❌ Affected by temperature/humidity changes
- ❌ Other WiFi networks cause interference
- ❌ Metal obstacles block signals
- ❌ Requires per-location calibration

**Feature Limitations:**
- ❌ Cannot achieve pose estimation (unlike DensePose)
- ❌ Limited activity recognition capabilities
- ❌ Less precise localization
- ❌ Cannot identify individuals

**Calibration Burden:**
- ❌ Daily automated calibration required
- ❌ Environmental drift affects baseline
- ❌ Per-environment training not transferable
- ❌ Setup optimization requires expertise

---

## Trade-offs Summary

| Aspect | RSSI (Selected) | CSI | DensePose |
|--------|----------------|-----|-----------|
| **Accuracy** | 98-99% ✅ | 98-99%+ ✅ | 70-85% ❌ |
| **Hardware Cost** | $200-500 ✅ | $600-1500 ❌ | $700+ ❌ |
| **Implementation** | 2-3 months ✅ | 4-6 months ❌ | 8-12 months ❌ |
| **Complexity** | Low ✅ | High ❌ | Very High ❌ |
| **Scalability** | High ✅ | Medium ⚠️ | Low ❌ |
| **Privacy** | High ✅ | High ✅ | Medium ⚠️ |
| **Calibration** | Daily ❌ | Weekly ✅ | Extensive ❌ |
| **Pose Estimation** | No ❌ | No ❌ | Yes ✅ |

---

## Alternatives Considered

### Alternative 1: CSI-Based Detection

**Why Not Selected:**
- Hardware complexity too high for MVP
- Specialized hardware procurement challenges
- Firmware modifications required
- Longer development timeline (4-6 months)
- Limited hardware compatibility

**When to Reconsider:**
- If RSSI accuracy insufficient in production
- If budget allows specialized hardware
- If fine-grained activity recognition needed
- For enterprise deployments with IT support

### Alternative 2: DensePose WiFi

**Why Not Selected:**
- Significant accuracy limitations (70-85%)
- Hallucination issues with unusual poses
- Struggles with 3+ people
- Not production-ready
- Research-only status

**When to Reconsider:**
- For research projects or proof-of-concepts
- If pose estimation becomes critical requirement
- If accuracy limitations acceptable
- If extensive training resources available

### Alternative 3: Hybrid Approach (RSSI + CSI)

**Potential Future Strategy:**
- Start with RSSI for MVP
- Add CSI for high-priority rooms
- Use RSSI for presence detection
- Use CSI for people counting in critical areas

**Benefits:**
- Balance cost and accuracy
- Phased deployment possible
- Redundancy through multiple methods

---

## Implementation Plan

### Phase 1: MVP (Months 1-3)
- Set up server with Python environment
- Deploy 4-5 standard WiFi routers (see recommendations above)
- Configure network (routers → server)
- Implement RSSI data collection (1 Hz)
- Train Random Forest model on RSSI features (local server training)
- Achieve 98%+ accuracy for 1-5 people
- Build web dashboard with real-time updates

### Phase 2: Optimization (Months 4-6)
- Implement automated daily calibration
- Optimize detector placement
- Add environmental compensation algorithms
- Improve accuracy for 6-10 people
- Add multi-room support

### Phase 3: Enhancement (Months 7-12)
- Consider CSI integration for high-accuracy requirements
- Explore advanced ML models (Gradient Boosting)
- Add activity recognition capabilities
- Deploy to additional locations

---

## Success Criteria

- **Presence Detection:** >99% accuracy
- **People Counting (1-5):** >98% accuracy
- **People Counting (6-10):** >95% accuracy
- **Detection Latency:** <3 seconds
- **Hardware Cost:** <$500 per room
- **Calibration:** Fully automated daily
- **Uptime:** >99% availability

---

## References

1. [Detection of Presence and Number of Persons by a Wi-Fi Signal](https://arxiv.org/html/2308.06773v2) - Primary RSSI research
2. [WiFi-Based Human Sensing With Deep Learning](https://ieeexplore.ieee.org/iel8/8782661/10362961/10552143.pdf) - IEEE survey
3. [DensePose From WiFi](https://arxiv.org/abs/2301.00250) - CMU DensePose research
4. System Architecture Document: `/docs/architecture/SYSTEM_ARCHITECTURE.md`
5. Research Synthesis: `/docs/research-synthesis-wifi-human-detection.md`

---

**Document End**

*This ADR will be reviewed quarterly or if accuracy requirements are not met in production.*
