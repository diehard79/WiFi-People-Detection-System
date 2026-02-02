# ADR-006: Server-Based Deployment Architecture

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection System Deployment Strategy
**Decision:** Server-Based Deployment with Optional Cloud Enhancement

---

## MAJOR REVISION NOTICE - Version 2.0

**Date:** 2025-02-02
**Author:** Technical Architect
**Changes:**
- **CRITICAL ARCHITECTURE CHANGE:** System is now SERVER-BASED, not edge-based
- Removed all Raspberry Pi/edge device content
- Simplified architecture: All processing runs on user's server
- ML training occurs locally on server (not edge, not cloud)
- Only model weights uploaded to cloud (not training data)
- Removed Docker requirements (uses local Python environment)
- Added specific WiFi router hardware recommendations
- Much simpler deployment and maintenance

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version (Hybrid Edge + Cloud) | Technical Architect |
| 2.0 | 2025-02-02 | **MAJOR REVISION:** Server-based architecture (remove edge devices) | Technical Architect |

---

## Context

The deployment architecture must balance competing requirements:
- **Latency:** <25 seconds end-to-end for real-time detection
- **Reliability:** 99.5% uptime, simple maintenance
- **Scalability:** Support 1-100+ rooms
- **Cost:** Minimize ongoing operational expenses
- **Privacy:** GDPR compliance, data minimization
- **Simplicity:** Easy deployment and maintenance

**Deployment Options:**
1. **Server-Only:** All processing on user's server
2. **Cloud-Only:** All processing in cloud
3. **Hybrid:** Server processing + optional cloud enhancement

---

## Decision

**Selected Architecture: Server-Based Deployment with Optional Cloud Enhancement**

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PHYSICAL SPACE                          │
│  4-5 WiFi Routers (Specific Models) → WiFi Signal Space      │
└────────────────────┬────────────────────────────────────────┘
                     │ WiFi Network
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  YOUR SERVER (On-Premises)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ALL SERVICES (Local Python Environment):              │  │
│  │  ✓ Signal Collector Service                          │  │
│  │  ✓ Signal Processing Pipeline                        │  │
│  │  ✓ ML Model Training (Train locally)                  │  │
│  │  ✓ ML Inference Engine (Presence + Counting)          │  │
│  │  ✓ Model Weights Export (to cloud for distribution)   │  │
│  │  ✓ Web Application (FastAPI Backend)                  │  │
│  │  ✓ Database (InfluxDB + PostgreSQL)                   │  │
│  │  ✓ WebSocket Server (Real-time updates)               │  │
│  │  ✓ Calibration Manager (Automated daily)              │  │
│  │  ✓ User Dashboard (Next.js Frontend)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│       │                                                     │
│       │ Model Weights Only (No training data)              │
│       ▼                                                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Internet (Optional)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD (Optional)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OPTIONAL CLOUD SERVICES (For multi-room deployments): │  │
│  │  ✓ Centralized Analytics                              │  │
│  │  ✓ Multi-Room Aggregation                             │  │
│  │  ✓ Model Weights Distribution                         │  │
│  │  ✓ Global Monitoring Dashboard                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Performance Comparison

**Latency Breakdown:**

| Operation | Server-Only | Server + Cloud | Cloud-Only |
|-----------|-------------|----------------|------------|
| **Signal Collection** | 5ms | 5ms | 5ms |
| **Signal Processing** | 15ms | 15ms | 15ms |
| **ML Inference** | 8ms | 8ms | 8ms |
| **Network Transmission** | 0ms | 50ms (optional) | 150ms |
| **Cloud Processing** | N/A | 0ms (or 50ms) | 100ms |
| **Database Write** | 5ms (local) | 5ms (local) + 50ms (cloud) | 100ms (cloud) |
| **TOTAL** | **33ms** ✅ | **38ms** (local) / **133ms** (cloud) | **378ms** ❌ |

**Conclusion:** Server-based approach easily meets <25s requirement.

### Cost Analysis

**Monthly Costs (100 rooms):**

| Cost Component | Server-Only | Server + Optional Cloud | Cloud-Only |
|----------------|-------------|-------------------------|------------|
| **Server Hardware** | $1,000-2,000 (one-time) ✅ | $1,000-2,000 (one-time) ✅ | $0 ❌ |
| **WiFi Routers** | $200-500/room (one-time) ✅ | $200-500/room (one-time) ✅ | $200-500/room (one-time) ✅ |
| **Cloud Compute** | $0 ✅ | $2-3 ✅ | $10-15 ❌ |
| **Cloud Storage** | $0 ✅ | $1-2 ✅ | $5-8 ❌ |
| **Network Bandwidth** | $0 ✅ | $0.50 ✅ | $5-10 ❌ |
| **Maintenance** | Low (server only) ✅ | Low ⚠️ | Low (cloud) ✅ |
| **TOTAL/MONTH** | **$0** ✅ | **$4-6** ⚠️ | **$20-33** ❌ |

**Annual Cost Comparison (100 Rooms):**
- **Server-Only:** $22,000 (server + routers, one-time)
- **Server + Cloud:** $22,000 + $5,000/year = $27,000 first year, $5,000/year thereafter
- **Cloud-Only:** $22,000 + $30,000/year = $52,000/year

**ROI:** Server-based pays for itself immediately vs. cloud-only (no ongoing compute costs).

### Simplicity & Maintenance

**Deployment Complexity:**

| Aspect | Server-Based | Edge-Based | Cloud-Only |
|--------|--------------|------------|------------|
| **Hardware** | 1 server + routers | Multiple edge devices + routers | Routers only |
| **Software** | Single installation | Multiple installations | Cloud setup |
| **Updates** | Single update ✅ | Per-device updates ❌ | Cloud updates ✅ |
| **Maintenance** | One location ✅ | Multiple locations ❌ | Cloud provider ✅ |
| **Troubleshooting** | Centralized ✅ | Distributed ❌ | Centralized ✅ |
| **Complexity** | **LOW** ✅ | **HIGH** ❌ | MEDIUM ⚠️ |

**Server-Based Benefits:**
- ✅ Single point of deployment
- ✅ Centralized monitoring and maintenance
- ✅ Easier debugging and troubleshooting
- ✅ Simpler backup and disaster recovery
- ✅ No distributed systems complexity
- ✅ Faster development and iteration

---

## Consequences

### Positive Consequences

**Simplicity:**
- ✅ **MAJOR:** Dramatically simpler architecture (no edge devices)
- ✅ Single deployment target (server)
- ✅ Easier development and testing
- ✅ Faster time-to-market
- ✅ Lower operational complexity

**Cost:**
- ✅ No edge device hardware costs ($75-150/room)
- ✅ No ongoing cloud compute costs (server-based)
- ✅ Predictable costs (hardware + minimal cloud)
- ✅ No bandwidth costs (minimal data transfer)
- ✅ Lower total cost of ownership

**Privacy:**
- ✅ Data stays on your server (not edge, not cloud)
- ✅ GDPR compliant architecture
- ✅ User-controlled data sharing
- ✅ No third-party data transmission required

**Reliability:**
- ✅ Single point of maintenance
- ✅ Easier to achieve 99.9% uptime
- ✅ No network dependency for core functionality
- ✅ Simplified backup and recovery

**Development:**
- ✅ No resource constraints (server vs edge)
- ✅ Standard Python environment (no Docker needed)
- ✅ Easier debugging and profiling
- ✅ Faster ML model training (server resources)
- ✅ Simpler CI/CD pipeline

**Flexibility:**
- ✅ Easy to add more rooms (just add routers)
- ✅ Scale up server resources as needed
- ✅ Mix server-only and server+cloud deployments
- ✅ Easy to add cloud features later

### Negative Consequences

**Centralization:**
- ❌ Single point of failure (server)
- ❌ Requires reliable server hardware
- ❌ Network connectivity required (routers → server)

**Scalability:**
- ❌ Server resource limits (CPU, RAM, storage)
- ❌ May need server upgrades for large deployments
- ❌ Network bandwidth considerations

**Deployment:**
- ❌ Requires server setup and configuration
- ❌ Network configuration required (routers → server)
- ❌ Power and cooling for server

**Mitigation Strategies:**
```python
# 1. Redundancy (backup server)
# Use primary server with hot standby
PRIMARY_SERVER = "192.168.1.100"
BACKUP_SERVER = "192.168.1.101"

# 2. Health monitoring
async def monitor_server_health():
    while True:
        if not await check_server_health():
            await send_alert("Server health degraded")
            await failover_to_backup()
        await asyncio.sleep(60)

# 3. Resource scaling
# Monitor server resources and scale up if needed
if cpu_usage > 80% or memory_usage > 80%:
    send_alert("Server resources running high, consider upgrade")
```

---

## Deployment Scenarios

### Scenario 1: Small Deployment (1-5 Rooms)

**Recommended:** Server-Only

**Architecture:**
```
Your Server:
├─ Signal Collector Service (5 detectors)
├─ Signal Processing Pipeline
├─ Presence Detection Model
├─ People Counting Model
└─ Web Dashboard (http://your-server:3000)

Hardware:
├─ Server: Mini PC or workstation ($500-1000)
└─ WiFi Routers: 4-5 per room ($200-500/room)
```

**Hardware Cost:** $1,500-3,500 (server + routers)
**Monthly Cost:** $0
**Maintenance:** Software updates as needed

**When to Add Cloud:**
- Need remote monitoring
- Need multi-location aggregation
- Need centralized analytics

### Scenario 2: Medium Deployment (6-50 Rooms)

**Recommended:** Server + Optional Cloud

**Architecture:**
```
Your Server:
├─ Signal Collection (30-250 detectors)
├─ Signal Processing
├─ Presence Detection
├─ People Counting
├─ ML Model Training (local)
├─ Web Dashboard
└─ Cloud Sync (optional)

Optional Cloud:
├─ Aggregation Service
├─ Analytics Engine
├─ User Management
└─ Global Dashboard
```

**Hardware Cost:** $1,000-2,000 (server) + $200-500/room (routers)
**Monthly Cost:** $0 (server-only) or $4-6/room (with cloud)
**Maintenance:** Regular software updates

### Scenario 3: Large Deployment (50+ Rooms)

**Recommended:** Server + Cloud Enhancement

**Architecture:**
```
Your Server (or multiple servers):
└─ Same as medium deployment (may scale to 2-3 servers)

Cloud Layer (Optional):
├─ Centralized Analytics
├─ Multi-Room Aggregation
├─ Model Weights Distribution
└─ Global Monitoring Dashboard
```

**Hardware Cost:** $2,000-5,000 (servers) + $200-500/room (routers)
**Monthly Cost:** $4-8/room (optional cloud)
**Maintenance:** Continuous monitoring, DevOps team

---

## Technology Stack

### Server Hardware

**Recommended Server Configurations:**

| Rooms | CPU | RAM | Storage | Approx. Cost |
|-------|-----|-----|---------|--------------|
| **1-10** | 4 cores | 8GB | 256GB SSD | $500-1,000 |
| **11-50** | 8 cores | 16GB | 512GB SSD | $1,000-2,000 |
| **51-100** | 16 cores | 32GB | 1TB SSD | $2,000-3,500 |
| **100+** | 32 cores | 64GB | 2TB SSD | $3,500-5,000 |

**OS:** Linux (Ubuntu 22.04 LTS or 24.04 LTS recommended)

**Software Stack:**
```yaml
Server Stack:
  os: Ubuntu 22.04/24.04 LTS
  runtime: Python 3.11+ (local environment)
  services:
    - signal-collector
    - signal-processor
    - ml-inference (scikit-learn)
    - ml-training (local, scikit-learn)
    - api-server (FastAPI)
    - database: InfluxDB (time-series) + PostgreSQL (metadata)
    - web-dashboard: Next.js (frontend)
    - websocket-server (real-time updates)
```

### WiFi Router Hardware

**Recommended WiFi Router Models:**

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

### Server Software Installation

**Local Python Environment Setup:**
```bash
# 1. Install Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# 2. Create virtual environment
python3.11 -m venv ~/wifi-detection-env
source ~/wifi-detection-env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install system dependencies
sudo apt install influxdb postgresql redis-server nginx

# 5. Configure services
# (See deployment guide for detailed setup)
```

**Key Dependencies:**
```txt
# requirements.txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
scikit-learn==1.3.0
numpy==1.26.0
pandas==2.1.0
scipy==1.11.0
influxdb-client==1.38.0
asyncpg==0.29.0
redis==5.0.0
celery==5.3.0
pydantic==2.5.0
websockets==12.0
```

### Resource Requirements

**Server Resource Utilization (Per 10 Rooms):**

| Component | CPU | RAM | Storage | Network |
|-----------|-----|-----|---------|---------|
| **Signal Collection** | 5% | 200MB | - | 1 Mbps |
| **Signal Processing** | 15% | 500MB | - | - |
| **ML Inference** | 10% | 100MB | 100MB | - |
| **Databases** | 5% | 1GB | 10GB | - |
| **Web Dashboard** | 5% | 200MB | 500MB | 10 Mbps |
| **OS + Overhead** | 10% | 1GB | 5GB | - |
| **TOTAL** | **50%** | **3GB** | **15.6GB** | **11 Mbps** |

**Scaling Guidance:**
- 1-10 rooms: 4-core CPU, 8GB RAM
- 11-50 rooms: 8-core CPU, 16GB RAM
- 51-100 rooms: 16-core CPU, 32GB RAM
- 100+ rooms: 32-core CPU, 64GB RAM (or multiple servers)

---

## Implementation Plan

### Phase 1: Server Setup (Week 1)

**Deliverables:**
1. Server hardware procurement or setup
2. OS installation (Ubuntu 22.04/24.04 LTS)
3. Python environment setup
4. Database installation (InfluxDB, PostgreSQL)
5. Network configuration (routers → server)

**Success Criteria:**
- Server running and accessible
- Python environment configured
- Databases operational
- Network connectivity verified

### Phase 2: Software Deployment (Weeks 2-4)

**Deliverables:**
1. Signal collection service deployment
2. Signal processing pipeline deployment
3. ML model training and deployment
4. Web application deployment
5. Automated calibration system

**Success Criteria:**
- All services running on server
- ML models trained and operational
- Real-time detection working
- Dashboard accessible

### Phase 3: Router Deployment (Weeks 5-6)

**Deliverables:**
1. WiFi router procurement
2. Router installation and configuration
3. Network optimization
4. Calibration and testing

**Success Criteria:**
- 4-5 routers deployed per room
- Network connectivity stable
- Detection accuracy >98%
- Calibration automated

### Phase 4: Optional Cloud Integration (Weeks 7-8)

**Deliverables:**
1. Cloud infrastructure setup (if desired)
2. Server-cloud sync service
3. Multi-room aggregation
4. Global monitoring dashboard

**Success Criteria:**
- Cloud sync operational
- Multi-room analytics working
- Model weights distribution functional

---

## Success Criteria

- **Latency:** <50ms for server-based detection
- **Availability:** 99.9% server uptime
- **Cost:** <$6/month per room (optional cloud costs only)
- **Scalability:** Support 1-1000+ rooms
- **Privacy:** All data stays on your server
- **Deployment:** Automated setup (<1 day for server)
- **Simplicity:** Single deployment target
- **Maintenance:** Centralized monitoring and updates

---

## References

1. [Server-Side Machine Learning Best Practices](https://aws.amazon.com/machine-learning/)
2. [Local Python Environment Management](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
3. System Architecture Document: `/docs/architecture/SYSTEM_ARCHITECTURE.md`

---

**Document End**

*This ADR reflects the simplified server-based architecture. All edge device content has been removed.*
