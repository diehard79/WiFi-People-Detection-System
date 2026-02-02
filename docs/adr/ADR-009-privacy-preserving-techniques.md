# ADR-009: Privacy-Preserving Techniques

**Status:** Accepted
**Date:** 2025-02-02
**Context:** GDPR Compliance and User Privacy Protection
**Decision:** Server-Based Processing with Data Minimization and Anonymization

---

## MAJOR REVISION NOTICE - Version 2.0

**Date:** 2025-02-02
**Author:** Technical Architect
**Changes:**
- **ARCHITECTURE UPDATE:** System is now server-based (not edge-based)
- Changed "Edge Processing" to "Server Processing" throughout
- Updated data flow: WiFi Routers → Your Server → Processing
- Clarified that all data stays on your server (not edge devices, not cloud)
- Removed edge device-specific content
- Emphasized server-based privacy benefits

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version (Edge-First Processing) | Technical Architect |
| 2.0 | 2025-02-02 | Server-based architecture: Update to Server Processing | Technical Architect |

---

## Context

WiFi-based people detection raises privacy concerns:
- **GDPR Compliance:** Required for EU deployments
- **User Trust:** Critical for adoption
- **Data Sensitivity:** WiFi signals can reveal movement patterns
- **Regulatory Risk:** Fines up to €20M or 4% of global revenue

**Privacy Challenges:**
- MAC addresses considered personal data (GDPR)
- RSSI/CSI data can identify individuals
- Movement patterns reveal behavior
- Historical data creates surveillance risk

---

## Decision

**Selected Strategy: Privacy-by-Design with Server-Based Processing**

### Core Privacy Principles

```
┌─────────────────────────────────────────────────────────────┐
│                  PRIVACY ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DATA MINIMIZATION                                         │
│  ├─ Collect minimum necessary data                           │
│  ├─ Aggregate immediately (no raw data storage)              │
│  └─ Discard raw RSSI after 24 hours                         │
│                                                               │
│  2. SERVER-BASED PROCESSING                                   │
│  ├─ Process data on your server (on-premises)                │
│  ├─ Only transmit model weights to cloud (not training data) │
│  └─ User controls data sharing                              │
│                                                               │
│  3. ANONYMIZATION                                             │
│  ├─ Hash MAC addresses (one-way)                            │
│  ├─ Strip device fingerprints                               │
│  ├─ Aggregate counts (no individual tracking)               │
│  └─ Differential privacy (add noise)                         │
│                                                               │
│  4. TRANSPARENCY                                             │
│  ├─ Clear privacy policy                                    │
│  ├─ Explicit consent required                               │
│  ├─ Data access logs                                        │
│  └─ User control panel                                      │
│                                                               │
│  5. RETENTION LIMITS                                          │
│  ├─ Raw data: 24 hours maximum                              │
│  ├─ Aggregates: 90 days default                             │
│  ├─ User-configurable retention                             │
│  └─ Automatic deletion                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### GDPR Compliance Analysis

**Personal Data Definition (GDPR Article 4):**
> "Personal data means any information relating to an identified or identifiable natural person."

**WiFi Data Considered Personal:**
- **MAC Addresses:** Directly identify devices → Personal Data ✅
- **RSSI Values:** Can identify individuals via device fingerprinting → Personal Data ✅
- **Presence/Count:** Aggregated, non-identifying → Not Personal Data (if anonymized) ✅

**Compliance Strategy:**

| Data Type | Classification | Storage | Retention | Access Control |
|-----------|----------------|----------|-----------|----------------|
| **Raw RSSI/CSI** | Personal Data | Server only | 24 hours | System only |
| **MAC Addresses** | Personal Data | Hashed | 24 hours | System only |
| **Presence (Binary)** | Aggregated | Server + Cloud (optional) | 90 days | User + Admin |
| **People Count** | Aggregated | Server + Cloud (optional) | 90 days | User + Admin |
| **Calibration Data** | Sensitive | Encrypted | 1 year | Admin only |

### Server-Based Processing Benefits

**Privacy Advantages:**
- ✅ Data never leaves your server (user control)
- ✅ No third-party data transmission required
- ✅ GDPR Article 25 compliance (data protection by design)
- ✅ User can verify data handling (on-premises access)
- ✅ Training data stays local (only model weights shared)

**Technical Advantages:**
- ✅ Lower latency (<50ms vs. 200ms cloud)
- ✅ Works without internet (not dependent on cloud)
- ✅ Reduced bandwidth costs (no data transfer to cloud)
- ✅ Compliance with data sovereignty laws
- ✅ Simpler architecture (no edge devices to manage)

**Deployment Simplicity:**
- ✅ Single point of maintenance (your server)
- ✅ Easier to audit and verify
- ✅ No distributed systems complexity
- ✅ Centralized data management

### Anonymization Techniques

**1. MAC Address Hashing:**
```python
import hashlib

def hash_mac_address(mac_address: str, salt: str) -> str:
    """One-way hash of MAC address"""
    # Use device-specific salt (prevents rainbow table attacks)
    salted = f"{mac_address}{salt}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    return hashed

# Example:
# Input:  AA:BB:CC:DD:EE:FF
# Output: 7a9b8c6d5e4f3a2b1c0d9e8f7a6b5c4d (non-reversible)
# Benefit: Cannot reverse-hash to obtain original MAC
```

**2. Differential Privacy (Add Noise):**
```python
import numpy as np

def add_laplace_noise(count: int, epsilon: float = 1.0) -> int:
    """Add noise to count for privacy (differential privacy)"""
    sensitivity = 1  # Maximum change from one person
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    noisy_count = max(0, int(round(count + noise)))
    return noisy_count

# Example:
# True count: 3 people
# Noisy count: 2, 3, or 4 people (varies)
# Benefit: Cannot determine individual presence from aggregate
```

**3. Temporal Aggregation:**
```python
def aggregate_counts(counts: list[int], window_minutes: int = 5):
    """Aggregate counts over time window (loses precision)"""
    # Instead of storing every second, store 5-minute averages
    aggregated = []
    for i in range(0, len(counts), window_minutes * 60):
        window = counts[i:i + window_minutes * 60]
        aggregated.append(int(round(np.mean(window))))
    return aggregated

# Example:
# Raw data:    [3, 3, 3, 3, 3, 4, 4, 4, ...] (per second)
# Aggregated:  [3, 4, ...] (per 5 minutes)
# Benefit: Loses individual movement patterns
```

### Data Flow Comparison

**Privacy-Preserving Flow (Selected - Server-Based):**
```
WiFi Routers → Your Server (Processing)
    ├─ RSSI Collection (1 Hz)
    ├─ Feature Extraction (Mean, Std Dev)
    ├─ ML Inference (Presence + Count)
    ├─ ML Training (Local, on server)
    ├─ Aggregation (5-minute windows)
    ├─ Anonymization (Hash MAC, add noise)
    └─ Storage
        ├─ Raw RSSI: 24 hours (server only)
        ├─ Aggregates: 90 days (server + optional cloud)
        └─ Model Weights: Export to cloud (optional)
```

**Non-Privacy-Preserving Flow (Avoid):**
```
WiFi Routers → Cloud Processing
    ├─ Raw RSSI transmitted to cloud ❌
    ├─ MAC addresses stored ❌
    ├─ Individual tracking possible ❌
    └─ GDPR violation risk ❌
```

---

## Consequences

### Positive Consequences

**GDPR Compliance:**
- ✅ Article 25: Data protection by design and by default
- ✅ Article 32: Security of processing (server-based)
- ✅ Article 5: Data minimization (aggregate only)
- ✅ Reduced regulatory risk

**User Trust:**
- ✅ Transparent data handling
- ✅ User control over data sharing
- ✅ No surveillance concerns (aggregates only)
- ✅ Easier adoption (privacy-first messaging)
- ✅ User can inspect server (on-premises)

**Legal:**
- ✅ Compliance with EU data laws
- ✅ Avoid fines (€20M or 4% of revenue)
- ✅ Future-proof for stricter regulations
- ✅ Data sovereignty (data stays in country)

**Technical:**
- ✅ Lower latency (server processing)
- ✅ Reduced bandwidth (no raw data transmission)
- ✅ Works without internet (no cloud dependency)
- ✅ Simplified compliance (fewer data transfers)
- ✅ Single point of maintenance

**Simplicity:**
- ✅ No edge devices to manage
- ✅ Centralized data processing
- ✅ Easier to audit and verify
- ✅ Simpler architecture

### Negative Consequences

**Feature Limitations:**
- ❌ Cannot identify individuals (by design)
- ❌ Cannot track individual movement patterns
- ❌ No device-specific analytics
- ❌ Limited debugging (no raw data in cloud if used)

**Operational Considerations:**
- ❌ Server maintenance required
- ❌ Data verification centralized
- ❌ Server resource requirements
- ❌ Network connectivity required (routers → server)

**Development Complexity:**
- ❌ Anonymization algorithms required
- ❌ Privacy auditing needed
- ❌ User consent management
- ❌ Data retention automation

**Mitigation Strategies:**
```python
# 1. Privacy-Preserving Debugging (Opt-in)
if user.has_consent("debugging"):
    # Temporarily store anonymized raw data for troubleshooting
    store_anonymized_rssi(rssi_data, retention_hours=1)

# 2. Audit Logging (Compliance)
log_data_access(
    user_id=user.id,
    action="view_analytics",
    data_type="aggregates_only",
    timestamp=now()
)

# 3. User Control Panel
class PrivacySettings:
    def __init__(self, user):
        self.retention_days = user.privacy_retention  # 7, 30, 90 days
        self.share_analytics = user.privacy_share    # Enable cloud sync
        self.anonymization_level = user.privacy_noise # Epsilon for DP
```

---

## Implementation

### Server Privacy Configuration

**Data Retention Policy:**
```python
# server/config/privacy.py
PRIVACY_CONFIG = {
    "raw_rssi_retention_hours": 24,  # Auto-delete after 24h
    "aggregate_retention_days": 90,  # Default, user-configurable
    "mac_hash_salt": os.getenv("MAC_SALT"),  # Server-specific
    "differential_privacy_epsilon": 1.0,  # Privacy parameter
    "enable_cloud_sync": False,  # Opt-in only
}
```

**Automatic Data Deletion:**
```python
import asyncio
from datetime import datetime, timedelta

async def delete_old_data():
    """Background task: Delete raw RSSI data older than 24 hours"""
    while True:
        cutoff = datetime.now() - timedelta(hours=24)

        # Delete from server database
        await influxdb.delete(
            measurement="raw_rssi",
            predicate=f'time < "{cutoff.isoformat()}"'
        )

        # Log deletion (GDPR compliance)
        logger.info(f"Deleted raw RSSI data older than {cutoff}")

        await asyncio.sleep(3600)  # Run every hour

# Start on server startup
asyncio.create_task(delete_old_data())
```

### Optional Cloud Privacy Features

**User Consent Management:**
```python
class ConsentManager:
    async def record_consent(self, user_id: str, consent_type: str):
        """Record user consent (GDPR Article 7)"""
        await db.execute(
            """INSERT INTO consents (user_id, consent_type, granted_at)
               VALUES ($1, $2, NOW())""",
            user_id, consent_type
        )

    async def check_consent(self, user_id: str, consent_type: str) -> bool:
        """Check if user has granted consent"""
        result = await db.fetch_val(
            """SELECT COUNT(*) FROM consents
               WHERE user_id = $1 AND consent_type = $2
               AND revoked = FALSE""",
            user_id, consent_type
        )
        return result > 0

# Required consents
CONSENT_TYPES = [
    "data_collection",      # RSSI data collection
    "cloud_processing",      # Cloud analytics (optional)
    "anonymous_analytics",   # Aggregated analytics only
]
```

**Data Access Logs (GDPR Article 30):**
```python
async def log_data_access(user_id: str, action: str, data_type: str):
    """Log all data access (compliance monitoring)"""
    await db.execute(
        """INSERT INTO data_access_logs
           (user_id, action, data_type, timestamp, ip_address)
           VALUES ($1, $2, $3, NOW(), $4)""",
        user_id, action, data_type, get_client_ip()
    )

# Usage
await log_data_access(
    user_id="user_123",
    action="view_analytics",
    data_type="aggregated_counts"
)
```

### Frontend Privacy Controls

**User Privacy Dashboard:**
```typescript
// app/privacy/page.tsx
export default function PrivacySettings() {
  const [consents, setConsents] = useState({
    dataCollection: false,
    cloudProcessing: false,
    anonymousAnalytics: true
  })

  const handleConsentChange = async (consentType: string, granted: boolean) => {
    await fetch('/api/v1/privacy/consent', {
      method: 'POST',
      body: JSON.stringify({ consent_type: consentType, granted })
    })
    setConsents(prev => ({ ...prev, [consentType]: granted }))
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Privacy Settings</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Data Collection Consent</h2>
        <p className="text-sm text-gray-600 mb-4">
          We collect WiFi RSSI data to detect people presence and count.
          Raw data is processed on your server and automatically deleted after 24 hours.
          Your data never leaves your server unless you opt-in to cloud features.
        </p>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={consents.dataCollection}
            onChange={(e) => handleConsentChange('data_collection', e.target.checked)}
            className="mr-2"
          />
          <span>I consent to WiFi signal data collection</span>
        </label>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Cloud Analytics (Optional)</h2>
        <p className="text-sm text-gray-600 mb-4">
          Enable cloud processing for advanced analytics and multi-room dashboards.
          Only anonymized aggregate data is transmitted to the cloud.
          No training data or raw RSSI data is ever sent to the cloud.
        </p>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={consents.cloudProcessing}
            onChange={(e) => handleConsentChange('cloud_processing', e.target.checked)}
            className="mr-2"
          />
          <span>I consent to cloud analytics (optional)</span>
        </label>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Data Retention</h2>
        <p className="text-sm text-gray-600 mb-4">
          Choose how long to retain aggregated detection data on your server.
        </p>
        <select
          className="border rounded px-3 py-2"
          onChange={(e) => updateRetention(parseInt(e.target.value))}
        >
          <option value="7">7 days</option>
          <option value="30">30 days</option>
          <option value="90" selected>90 days (default)</option>
        </select>
      </div>
    </div>
  )
}
```

---

## GDPR Compliance Checklist

### Article 6: Lawful Basis for Processing
- ✅ **Consent:** User opts in to data collection
- ✅ **Legitimate Interest:** Occupancy monitoring (if consent not required)
- ✅ **Contract:** Service requires data to function

### Article 7: Conditions for Consent
- ✅ **Explicit:** Clear consent request
- ✅ **Granular:** Separate consents for different data types
- ✅ **Revocable:** User can withdraw consent anytime
- ✅ **Verifiable:** Consent logged with timestamp

### Article 25: Data Protection by Design
- ✅ **Server Processing:** Data stays on user's server by default
- ✅ **Anonymization:** Hash MAC addresses, aggregate counts
- ✅ **Minimization:** Only collect necessary data

### Article 32: Security of Processing
- ✅ **Encryption:** Data encrypted at rest and in transit
- ✅ **Access Control:** Role-based permissions
- ✅ **Logging:** Audit trail for all data access

### User Rights (Articles 15-20)
- ✅ **Right to Access:** Export user data on request
- ✅ **Right to Rectification:** Update incorrect data
- ✅ **Right to Erasure:** Delete all data on request
- ✅ **Right to Portability:** Export data in machine-readable format
- ✅ **Right to Object:** Opt out of processing

---

## Success Criteria

- **GDPR Compliance:** Pass privacy impact assessment (DPIA)
- **Data Minimization:** No raw RSSI data transmitted to cloud
- **User Consent:** Explicit consent for all data collection
- **Data Retention:** Automatic deletion (raw <24h, aggregates <90 days)
- **Anonymization:** MAC addresses hashed, counts aggregated
- **Transparency:** Clear privacy policy, user control panel
- **Server Privacy:** All data stays on user's server by default

---

## References

1. [GDPR Full Text](https://gdpr-info.eu/)
2. [WiFi Tracking GDPR Guidance](https://www.aepd.es/guides/wi-fi-tracking-technologies-guidance-for-data-controllers.pdf)
3. [Differential Privacy](https://www.microsoft.com/en-us/research/publication/ differential-privacy-a-survey-of-results/)
4. System Architecture Document: `/docs/architecture/SYSTEM_ARCHITECTURE.md`

---

**Document End**

*This ADR reflects server-based privacy architecture. All edge device content has been removed.*
