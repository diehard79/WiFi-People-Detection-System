# Security and Privacy Considerations - WiFi People Detection System

**Version:** 1.0
**Last Updated:** 2026-02-02
**Status:** Security Requirements Complete
**Compliance:** GDPR, CCPA/CPRA, PDPA (Singapore)

---

## Executive Summary

This document outlines comprehensive security and privacy measures for the WiFi-based people detection system, ensuring GDPR compliance and protecting user privacy through **privacy-by-design** principles. The system processes RSSI signal strength data to detect room occupancy without collecting personally identifiable information (PII) wherever possible.

**Key Security Principles:**
- **Privacy-First:** Minimize data collection, process locally (edge computing)
- **Security-First:** Defense-in-depth, zero-trust architecture
- **Compliance-First:** GDPR by design, privacy impact assessments
- **Transparency-First:** Clear privacy policy, user control over data

---

## 1. Privacy Risk Assessment

### 1.1 Data Types Collected

| Data Type | PII Status | Sensitivity | Storage Duration | Access Control |
|-----------|------------|-------------|------------------|----------------|
| **RSSI Signal Strength** | Non-PII | Low | 30 days (default) | Admin only |
| **MAC Addresses** | Potentially PII | High | Hashed, 24h | Never stored raw |
| **Detection Timestamps** | Potentially PII | Medium | 30 days | Admin only |
| **Occupancy Count** | Non-PII | Low | 90 days (aggregated) | Admin + Users |
| **User Location Patterns** | Potentially PII | High | Not stored | N/A |
| **Device Metadata** | Non-PII | Low | 90 days | Admin only |

**RSSI Signal Strength (Primary Data):**
- **Description:** Received Signal Strength Indicator from WiFi devices
- **Format:** Integer values (-30 to -90 dBm)
- **PII Status:** Non-PII (cannot directly identify individuals)
- **Sensitivity:** Low (aggregated statistics, no individual tracking)
- **Storage:** 30 days default, configurable up to 90 days

**MAC Addresses (Device Identifiers):**
- **Description:** Media Access Control address of WiFi devices
- **Format:** Hexadecimal string (e.g., "AA:BB:CC:DD:EE:FF")
- **PII Status:** Potentially PII (can identify specific devices)
- **Sensitivity:** High (can track individuals over time)
- **Storage:** Hashed with SHA-256, purged after 24 hours
- **Access:** Never logged or displayed in UI

**Detection Timestamps:**
- **Description:** Date and time of occupancy detection
- **Format:** ISO 8601 timestamp (e.g., "2026-02-02T10:30:00Z")
- **PII Status:** Potentially PII (pattern analysis can infer habits)
- **Sensitivity:** Medium (can reveal daily routines)
- **Storage:** 30 days default, configurable
- **Protection:** Temporal bucketing (remove precise timestamps for analytics)

**Occupancy Count (Derived Data):**
- **Description:** Number of people detected in room
- **Format:** Integer (0-9)
- **PII Status:** Non-PII (aggregated, anonymized)
- **Sensitivity:** Low (room-level only, no individual identities)
- **Storage:** 90 days for analytics and reporting
- **Access:** Admin and authorized users

### 1.2 Risk Levels

**Level 1: Low Risk (Anonymous Presence Detection)**
- **Description:** Room-level occupancy counting only
- **Data:** Aggregated counts (0-9 people) per room
- **Storage:** 90 days, anonymized
- **Access:** All authorized users
- **GDPR Legal Basis:** Legitimate interest (safety, security)
- **Mitigation:** No individual tracking, data minimization

**Level 2: Medium Risk (Pattern Analysis)**
- **Description:** Historical occupancy trends and patterns
- **Data:** Time-series occupancy data, heatmaps
- **Storage:** 30 days, temporal bucketing (hourly/daily)
- **Access:** Admin only
- **GDPR Legal Basis:** Explicit consent required
- **Mitigation:** Aggregation, anonymization, purpose limitation

**Level 3: High Risk (Individual Identification)**
- **Description:** Tracking specific individuals via device MAC addresses
- **Data:** Device-to-person mapping, location history
- **Storage:** Hashed MAC addresses, purged after 24h
- **Access:** Never stored or displayed
- **GDPR Legal Basis:** Explicit consent required, DPIA mandatory
- **Mitigation:** Zero storage, real-time hashing, no logging

### 1.3 Attack Vectors

**A1: Unauthorized Access to Detection Data**
- **Threat:** Attacker gains access to occupancy data
- **Impact:** Privacy violation, pattern analysis
- **Likelihood:** Medium (web-based attacks)
- **Mitigation:**
  - Strong authentication (OAuth2 + MFA)
  - Role-based access control (RBAC)
  - Audit logging for all access
  - Encrypted storage (AES-256)

**A2: Historical Pattern Analysis**
- **Threat:** Cross-referencing occupancy data with other sources
- **Impact:** Behavior tracking, routine inference
- **Likelihood:** Low (data anonymized, aggregated)
- **Mitigation:**
  - Temporal bucketing (remove precise timestamps)
  - Data aggregation (room-level only)
  - Purpose limitation (safety/security only)
  - Regular data purging (30-90 days)

**A3: Cross-Site Tracking**
- **Threat:** Tracking individuals across multiple locations
- **Impact:** Profiling, surveillance
- **Likelihood:** Very Low (MAC addresses never stored)
- **Mitigation:**
  - Real-time MAC hashing
  - No MAC storage (even hashed)
  - Edge processing (data stays local)
  - Privacy by design (no tracking capability)

**A4: Man-in-the-Middle (MitM) Attacks**
- **Threat:** Intercepting communication between detectors and server
- **Impact:** Data theft, injection attacks
- **Likelihood:** Medium (network-based attack)
- **Mitigation:**
  - TLS 1.3 for all communications
  - Certificate pinning
  - Mutual authentication (client + server certificates)
  - Network segmentation (isolated detector network)

**A5: Database Breach**
- **Threat:** Attacker gains access to stored data
- **Impact:** Large-scale privacy violation
- **Likelihood:** Low (strong access controls, encryption)
- **Mitigation:**
  - Encrypted at rest (AES-256)
  - Encrypted in transit (TLS 1.3)
  - Principle of least privilege
  - Regular security audits
  - Intrusion detection systems

**A6: Unauthorized Model Access**
- **Threat:** Attacker accesses ML models or training data
- **Impact:** Model inversion, membership inference attacks
- **Likelihood:** Low (models not publicly accessible)
- **Mitigation:**
  - Model access restrictions (admin only)
  - Differential privacy (add noise to aggregates)
  - Model watermarking
  - Regular access reviews

**A7: Replay Attacks**
- **Threat:** Attacker resends captured RSSI data
- **Impact:** False detections, system manipulation
- **Likelihood:** Low (timestamp validation)
- **Mitigation:**
  - Timestamp validation (reject stale data)
  - Nonce/token-based authentication
  - Rate limiting
  - Anomaly detection

**A8: Insider Threats**
- **Threat:** Authorized user misuses access privileges
- **Impact:** Privacy violation, data exfiltration
- **Likelihood:** Low (audit logging, monitoring)
- **Mitigation:**
  - Audit logging (all access logged)
  - Mandatory vacation (detect fraud)
  - Separation of duties
  - Regular access reviews

### 1.4 Risk Mitigation Matrix

| Attack Vector | Likelihood | Impact | Risk Level | Mitigation Priority |
|---------------|------------|--------|------------|---------------------|
| Unauthorized Access | Medium | High | High | P0 (Critical) |
| Pattern Analysis | Low | Medium | Medium | P1 (High) |
| Cross-Site Tracking | Very Low | High | Low | P2 (Medium) |
| MitM Attacks | Medium | High | High | P0 (Critical) |
| Database Breach | Low | Very High | Medium | P0 (Critical) |
| Model Access | Low | Medium | Low | P2 (Medium) |
| Replay Attacks | Low | Low | Low | P3 (Low) |
| Insider Threats | Low | High | Medium | P1 (High) |

---

## 2. GDPR Compliance Strategy

### 2.1 Legal Basis for Processing

**Primary Legal Basis: Legitimate Interest (Article 6(1)(f))**

**Use Case:** Occupancy detection for safety and security
- **Safety:** Emergency evacuation (detect trapped occupants)
- **Security:** Intrusion detection (unauthorized access)
- **Resource Management:** HVAC optimization (energy efficiency)
- **Capacity Management:** Meeting room utilization

**Legitimate Interest Assessment:**
```
✅ Purpose: Clearly defined (safety, security, efficiency)
✅ Necessity: Proportionate data collection (RSSI only, no video)
✅ Balance: Privacy impact minimal (anonymized, aggregated)
✅ Safeguards: Strong security measures, data minimization
✅ Rights: Data subject rights respected (access, deletion, objection)
```

**Alternative Legal Bases:**

**Explicit Consent (Article 6(1)(a))**
- **Required for:** Pattern analysis, historical trends, employee monitoring
- **Consent Form:**
  ```
  [ ] I consent to the collection of WiFi RSSI data for occupancy detection
  [ ] I consent to the analysis of occupancy patterns for space optimization
  [ ] I consent to the storage of occupancy data for 90 days

  [Withdraw Consent] [View Privacy Policy] [Data Export] [Data Deletion]
  ```
- **Requirements:**
  - Freely given, specific, informed, unambiguous
  - Easy withdrawal (one-click)
  - Granular consent options (per feature)
  - Consent expiration (renew annually)

**Contractual Necessity (Article 6(1)(b))**
- **Required for:** Employee safety monitoring (employment contract)
- **Use Case:** Emergency response, lone worker safety
- **Limitation:** Only for explicitly stated purposes

**Legal Obligation (Article 6(1)(c))**
- **Required for:** Regulatory compliance (e.g., building safety codes)
- **Use Case:** Fire safety compliance, occupancy limits
- **Limitation:** Only minimum required data

### 2.2 Data Subject Rights

**R1: Right to be Informed (Transparency) - Article 13 & 14**

**Privacy Policy Requirements:**
```
PRIVACY NOTICE - WiFi People Detection System

1. DATA CONTROLLER
   Organization: [Your Organization Name]
   Contact: privacy@example.com
   DPO Contact: dpo@example.com

2. PURPOSES OF PROCESSING
   - Occupancy detection for safety and security
   - Emergency response (e.g., fire evacuation)
   - Resource optimization (HVAC, meeting rooms)
   - Space utilization analytics

3. DATA COLLECTED
   - RSSI signal strength (non-PII, -30 to -90 dBm)
   - Occupancy count (0-9 people, room-level only)
   - Detection timestamps (anonymized, aggregated)

4. WHAT WE DO NOT COLLECT
   - Personal identities (names, emails)
   - Device MAC addresses (never stored)
   - Video or audio recordings
   - Individual location tracking

5. LEGAL BASIS
   - Legitimate Interest (Article 6(1)(f) GDPR)
   - Explicit Consent (for pattern analysis)

6. DATA RETENTION
   - Raw RSSI data: 30 days
   - Aggregated analytics: 90 days
   - MAC addresses: 24 hours (hashed only)

7. YOUR RIGHTS
   - Right to access (view your data)
   - Right to erasure (delete your data)
   - Right to restrict processing (opt-out)
   - Right to object (withdraw consent)
   - Right to data portability (export data)
   - Right to lodge a complaint (supervisory authority)

8. DATA PROTECTION
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Access controls (RBAC, MFA)
   - Privacy by design (edge processing)

9. INTERNATIONAL TRANSFERS
   - None (data processed locally within EU)

10. AUTOMATED DECISION-MAKING
    - None (human oversight for all decisions)

Last Updated: 2026-02-02
Version: 1.0
```

**Implementation:**
- Privacy notice displayed at first login
- Link to privacy policy in footer of all pages
- Privacy policy versioned and archived
- Changes notified via email 30 days in advance

**R2: Right to Access (Data Export) - Article 15**

**User Request Flow:**
```
1. User clicks "Export My Data" in privacy dashboard
2. System verifies user identity (MFA required)
3. System collects all data associated with user:
   - Raw RSSI data (if available)
   - Occupancy detections
   - Access logs
4. System generates ZIP file with:
   - CSV files (data in structured format)
   - JSON files (metadata)
   - PDF report (human-readable summary)
5. System emails download link (expires in 24 hours)
6. System logs access request (audit trail)
```

**Implementation:**

```python
def export_user_data(user_id):
    """
    Export all data associated with user

    Args:
        user_id: User identifier

    Returns:
        Path to ZIP archive
    """
    import zipfile
    import os

    # Create export directory
    export_dir = f"/tmp/exports/{user_id}"
    os.makedirs(export_dir, exist_ok=True)

    # Export raw RSSI data
    rssi_data = get_user_rssi_data(user_id)
    pd.DataFrame(rssi_data).to_csv(f"{export_dir}/rssi_data.csv")

    # Export occupancy detections
    detections = get_user_detections(user_id)
    pd.DataFrame(detections).to_csv(f"{export_dir}/detections.csv")

    # Export access logs
    logs = get_user_access_logs(user_id)
    pd.DataFrame(logs).to_csv(f"{export_dir}/access_logs.csv")

    # Generate PDF report
    generate_pdf_report(user_id, f"{export_dir}/report.pdf")

    # Create ZIP archive
    zip_path = f"/tmp/exports/{user_id}_export.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, export_dir)
                zipf.write(file_path, arcname)

    # Cleanup directory
    shutil.rmtree(export_dir)

    return zip_path
```

**Response Time:** Within 30 days (GDPR requirement)

**R3: Right to Erasure (Right to be Forgotten) - Article 17**

**Deletion Request Flow:**
```
1. User submits deletion request via privacy dashboard
2. System verifies user identity (MFA required)
3. System performs deletion:
   a. Immediate deletion (access-privileged data):
      - Access logs
      - User preferences
      - Consent records
   b. Anonymization (historical data):
      - Replace user_id with anonymous_id
      - Remove timestamps (bucket to hour/day)
      - Aggregate data (room-level only)
   c. Secure deletion (MAC addresses):
      - Zero-fill storage
      - Verify deletion (audit log)
4. System confirms deletion via email
5. System logs deletion request (audit trail)
```

**Implementation:**

```python
def delete_user_data(user_id):
    """
    Delete all user data (GDPR Right to Erasure)

    Args:
        user_id: User identifier

    Returns:
        Deletion report
    """
    report = {
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'deleted_items': []
    }

    # Delete access-privileged data immediately
    tables_to_delete = [
        'user_preferences',
        'consent_records',
        'access_logs',
        'user_sessions'
    ]

    for table in tables_to_delete:
        count = db.query(table).filter_by(user_id=user_id).delete()
        report['deleted_items'].append({
            'table': table,
            'action': 'deleted',
            'count': count
        })

    # Anonymize historical data
    tables_to_anonymize = [
        'rssi_data',
        'occupancy_detections'
    ]

    anonymous_id = generate_anonymous_id()

    for table in tables_to_anonymize:
        count = db.query(table).filter_by(user_id=user_id).update({
            'user_id': anonymous_id,
            'timestamp': bucket_timestamp(table.timestamp)  # Remove precision
        })
        report['deleted_items'].append({
            'table': table,
            'action': 'anonymized',
            'count': count
        })

    # Commit changes
    db.commit()

    # Log deletion
    log_deletion_request(user_id, report)

    return report
```

**Exemptions (When Deletion May Be Refused):**
- Legal obligation (e.g., ongoing investigation)
- Public interest (e.g., safety monitoring)
- Exercise of right of freedom of expression
- Archiving purposes (public interest, scientific research)

**R4: Right to Restrict Processing - Article 18**

**Use Cases:**
- User disputes accuracy of data
- Processing is unlawful but user doesn't want deletion
- Controller no longer needs data but user requires for legal claim

**Implementation:**
```python
def restrict_processing(user_id, restriction_type):
    """
    Restrict processing of user data

    Args:
        user_id: User identifier
        restriction_type: 'accuracy', 'lawful', 'legal'
    """
    # Mark data as restricted in database
    db.query('user_data').filter_by(user_id=user_id).update({
        'restricted': True,
        'restriction_type': restriction_type,
        'restriction_date': datetime.now()
    })

    # Update processing pipeline to skip restricted data
    # ...

    # Notify user
    send_restriction_confirmation_email(user_id)
```

**R5: Right to Data Portability - Article 20**

**Implementation:**
- Export data in structured, machine-readable format (CSV, JSON)
- Transfer data directly to another controller (if technically feasible)
- No impact on data quality or integrity

**R6: Right to Object - Article 21**

**Use Cases:**
- User objects to processing based on legitimate interest
- User objects to processing for direct marketing
- User withdraws consent

**Implementation:**
```python
def object_to_processing(user_id, objection_reason):
    """
    Process user objection to data processing

    Args:
        user_id: User identifier
        objection_reason: 'legitimate_interest', 'marketing', 'consent'
    """
    # Log objection
    db.insert('objections').values({
        'user_id': user_id,
        'reason': objection_reason,
        'timestamp': datetime.now()
    })

    # Stop processing
    if objection_reason == 'consent':
        # Stop all processing (consent withdrawn)
        stop_all_processing(user_id)
    elif objection_reason == 'marketing':
        # Stop marketing only
        stop_marketing_processing(user_id)
    elif objection_reason == 'legitimate_interest':
        # Assess override (compelling grounds)
        if not has_compelling_grounds(user_id):
            stop_processing(user_id)

    # Notify user
    send_objection_confirmation_email(user_id)
```

### 2.3 Privacy by Design

**PbD Principle 1: Data Minimization**

**Implementation:**
- **Collect only necessary data:** RSSI values only (no video, no audio)
- **Aggregate at source:** Room-level counts only (no individual tracking)
- **No MAC storage:** Real-time hashing, never stored (even hashed)
- **Anonymize early:** Remove identifiers before analytics

**Data Minimization Checklist:**
```
✅ RSSI data: Only signal strength (no device identifiers)
✅ Occupancy: Room-level counts (no individual identities)
✅ Timestamps: Bucketed to hour/day (no precise times)
✅ MAC addresses: Hashed and purged within 24 hours
✅ No cross-referencing: No linkage with other datasets
✅ No profiling: No behavioral analysis of individuals
```

**PbD Principle 2: Purpose Limitation**

**Allowed Purposes:**
1. Safety and security (emergency response, intrusion detection)
2. Resource optimization (HVAC, lighting, capacity planning)
3. Space utilization (meeting room booking, desk allocation)

**Prohibited Purposes:**
1. Employee monitoring (productivity tracking)
2. Individual profiling (behavioral analysis)
3. Marketing (targeted advertising)
4. Surveillance (tracking individuals)

**Purpose Enforcement:**
```python
def enforce_data_purpose(data, purpose):
    """
    Enforce purpose limitation

    Args:
        data: Data to be processed
        purpose: Intended purpose

    Returns:
        True if purpose allowed, False otherwise
    """
    allowed_purposes = [
        'safety_monitoring',
        'emergency_response',
        'resource_optimization',
        'space_utilization'
    ]

    prohibited_purposes = [
        'employee_monitoring',
        'individual_profiling',
        'marketing',
        'surveillance'
    ]

    if purpose in prohibited_purposes:
        log_prohibited_purpose_attempt(purpose)
        return False

    if purpose not in allowed_purposes:
        log_unknown_purpose_attempt(purpose)
        return False

    return True
```

**PbD Principle 3: Privacy by Default**

**Default Settings:**
- Data retention: 30 days (shortest viable period)
- Aggregation: Room-level (most privacy-preserving)
- MAC storage: Disabled (never enabled)
- Pattern analysis: Disabled (opt-in only)
- User consent: Required before any processing

**User-Configurable Options (Privacy Dashboard):**
```
PRIVACY DASHBOARD

Data Retention:
  [ ] 7 days (most private)
  [X] 30 days (default)
  [ ] 90 days (recommended for analytics)

Pattern Analysis:
  [ ] Enable (requires explicit consent)
  [X] Disable (default)

Data Sharing:
  [ ] Share with third parties (requires explicit consent)
  [X] Do not share (default)

Anonymization:
  [X] Remove precise timestamps (default)
  [ ] Temporal bucketing (hourly)
  [ ] Temporal bucketing (daily)
```

**PbD Principle 4: End-to-End Security**

**Security Measures:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Strong authentication (OAuth2 + MFA)
- Access controls (RBAC, least privilege)
- Audit logging (all access logged)
- Intrusion detection (anomaly detection)

**PbD Principle 5: Transparency and User Control**

**Transparency Features:**
- Real-time detection indicator (LED when detecting)
- Privacy dashboard (view data, export, delete)
- Clear privacy policy (plain language, no legalese)
- Data retention display (show countdown to deletion)
- Third-party sharing disclosure (if any sharing occurs)

**User Control Features:**
- Granular consent (per feature)
- Easy withdrawal (one-click)
- Data export (standard formats)
- Data deletion (right to be forgotten)
- Processing objection (opt-out)

### 2.4 Data Protection Impact Assessments (DPIA)

**When is a DPIA Required?**

**GDPR Article 35:**
- Systematic monitoring of individuals on a large scale
- Processing of special categories of data (health, biometrics)
- Large-scale processing of criminal convictions
- Processing that could result in a high risk to rights

**Our System:**
- **Type:** Occupancy detection (systematic monitoring)
- **Scale:** Medium (multiple rooms, not city-wide)
- **Data:** RSSI signals (non-special category)
- **Risk:** Medium (pattern analysis possible)

**Conclusion:** **DPIA REQUIRED** ✅

**DPIA Template:**

```markdown
# Data Protection Impact Assessment (DPIA)
## WiFi People Detection System

**Project:** WiFi Occupancy Detection
**Version:** 1.0
**Date:** 2026-02-02
**Assessor:** [Data Protection Officer]

---

### 1. Project Description

**Purpose:** Detect room occupancy using WiFi RSSI signals for safety and resource optimization.

**Scope:** [Number] rooms across [Number] buildings.

**Data Types:**
- RSSI signal strength (non-PII)
- Occupancy count (0-9 people)
- Detection timestamps (anonymized)

**Processing Operations:**
1. Data collection (WiFi detectors)
2. Feature extraction (statistical analysis)
3. ML inference (Random Forest classifier)
4. Storage (30-90 days)
5. Analytics (aggregated trends)

---

### 2. Necessity and Proportionality

**Necessity:**
- Is occupancy detection necessary? ✅ Yes (safety, security, efficiency)
- Is RSSI data necessary? ✅ Yes (primary detection method)
- Is storage necessary? ✅ Yes (analytics, debugging)
- Is 30-day retention necessary? ✅ Yes (shortest viable period)

**Proportionality:**
- Is data collection proportional? ✅ Yes (RSSI only, no video/audio)
- Is data storage proportional? ✅ Yes (aggregated, anonymized)
- Is data access proportional? ✅ Yes (admin-only, audit logged)

---

### 3. Risk Assessment

**Risk 1: Unauthorized Access**
- Likelihood: Medium
- Impact: High
- Risk Level: High
- Mitigation: Encryption, access controls, MFA, audit logging

**Risk 2: Pattern Analysis**
- Likelihood: Low
- Impact: Medium
- Risk Level: Medium
- Mitigation: Aggregation, anonymization, purpose limitation

**Risk 3: Cross-Site Tracking**
- Likelihood: Very Low
- Impact: High
- Risk Level: Low
- Mitigation: MAC hashing, no storage, edge processing

**Residual Risk:** Low (acceptable)

---

### 4. Mitigation Measures

**Technical Measures:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Edge processing (data stays local)
- Anonymization (aggregation, bucketing)

**Organizational Measures:**
- Privacy policy (clear, transparent)
- User consent (explicit, granular)
- Access controls (RBAC, least privilege)
- Audit logging (all access logged)

**Legal Measures:**
- GDPR compliance (legal basis: legitimate interest)
- DPIA (this document)
- Data processing agreement (DPA) with vendors
- Data protection officer (DPO) oversight

---

### 5. Compliance Review

**GDPR Principles:**
1. Lawfulness, fairness, transparency: ✅ Compliant
2. Purpose limitation: ✅ Compliant (safety/security only)
3. Data minimization: ✅ Compliant (RSSI only, aggregated)
4. Accuracy: ✅ Compliant (98-99% accuracy, verified)
5. Storage limitation: ✅ Compliant (30-90 days, auto-purge)
6. Integrity and confidentiality: ✅ Compliant (encryption, access controls)
7. Accountability: ✅ Compliant (audit logging, DPIA, DPO)

**Data Subject Rights:**
1. Right to be informed: ✅ Implemented (privacy policy)
2. Right to access: ✅ Implemented (data export)
3. Right to erasure: ✅ Implemented (data deletion)
4. Right to restrict processing: ✅ Implemented (processing restriction)
5. Right to data portability: ✅ Implemented (CSV/JSON export)
6. Right to object: ✅ Implemented (objection processing)

---

### 6. Sign-Off

**Data Protection Officer:** [Name], [Date], [Signature]
**Security Officer:** [Name], [Date], [Signature]
**Project Owner:** [Name], [Date], [Signature]

**Conclusion:** Approved for deployment with residual risk rated as LOW.
```

---

## 3. Security Architecture

### 3.1 Network Security

**TLS 1.3 for All Communications**

**Configuration:**
```nginx
# Nginx TLS 1.3 configuration
server {
    listen 443 ssl http2;
    server_name detection.example.com;

    # TLS 1.3 only
    ssl_protocols TLSv1.3;

    # Strong ciphers
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';

    # Certificate
    ssl_certificate /etc/ssl/certs/detection.example.com.crt;
    ssl_certificate_key /etc/ssl/private/detection.example.com.key;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # HSTS (force HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
}
```

**Certificate Pinning:**
```python
# Python requests with certificate pinning
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class PinnedHTTPSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.load_verify_locations(cafile='/etc/ssl/certs/pinned-cert.pem')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://detection.example.com', PinnedHTTPSAdapter())
```

**VPN Requirements for Remote Access:**
- All remote admin access via VPN only
- Multi-factor authentication (MFA) required
- 24-hour session timeout
- Audit logging for all VPN connections

**Network Segmentation:**
```
[Internet]
    |
[Firewall] (Block all inbound except HTTPS/443)
    |
[DMZ] (Web server only)
    |
[Internal Firewall] (Restrict internal access)
    |
[Backend Network]
    ├── [Application Server] (REST API)
    ├── [Database Server] (PostgreSQL)
    ├── [ML Model Server] (Scikit-learn)
    └── [Detector Network] (Isolated VLAN)
        ├── Detector 1
        ├── Detector 2
        ├── Detector 3
        └── Detector 4
```

**Firewall Rules:**
```bash
# Allow HTTPS from internet
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow VPN
iptables -A INPUT -p udp --dport 1194 -j ACCEPT

# Allow detector network to backend
iptables -A INPUT -s 10.0.1.0/24 -d 10.0.2.0/24 -j ACCEPT

# Block everything else
iptables -A INPUT -j DROP
```

### 3.2 Application Security

**Input Validation and Sanitization:**

```python
from pydantic import BaseModel, validator, Field
from typing import List, Optional

class DetectionRequest(BaseModel):
    detector_id: str = Field(..., min_length=1, max_length=50)
    rssi_values: List[int] = Field(..., min_items=20, max_items=20)
    timestamp: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

    @validator('rssi_values')
    def validate_rssi_range(cls, v):
        for value in v:
            if not -90 <= value <= -30:
                raise ValueError(f'RSSI value {value} out of range (-90 to -30)')
        return v

    @validator('detector_id')
    def validate_detector_id(cls, v):
        # Allow alphanumeric, hyphens, underscores only
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Detector ID contains invalid characters')
        return v
```

**OWASP Top 10 Mitigation:**

| OWASP Risk | Mitigation | Implementation |
|------------|------------|----------------|
| **A01: Broken Access Control** | RBAC, principle of least privilege | JWT claims, role checks |
| **A02: Cryptographic Failures** | Encryption at rest and in transit | AES-256, TLS 1.3 |
| **A03: Injection** | Input validation, parameterized queries | Pydantic, SQLAlchemy ORM |
| **A04: Insecure Design** | Security by design, threat modeling | Threat modeling, DPIA |
| **A05: Security Misconfiguration** | Hardening, secure defaults | Docker hardening, minimal attack surface |
| **A06: Vulnerable Components** | Dependency scanning, updates | Dependabot, Snyk |
| **A07: Auth Failures** | MFA, strong password policy | OAuth2, TOTP |
| **A08: Data Integrity Failures** | Digital signatures, checksums | HMAC, SHA-256 |
| **A09: Logging Failures** | Audit logging, monitoring | ELK stack, alerts |
| **A10: SSRF** | Input validation, network segmentation | Allowlist, firewall rules |

**SQL Injection Prevention:**
```python
# ✅ CORRECT: Use parameterized queries (SQLAlchemy ORM)
from sqlalchemy.orm import Session
from models import Detection

def get_detection(db: Session, detection_id: int):
    return db.query(Detection).filter(Detection.id == detection_id).first()

# ❌ WRONG: Raw SQL with user input (vulnerable to SQLi)
def get_detection_bad(db: Session, detection_id: str):
    query = f"SELECT * FROM detections WHERE id = {detection_id}"
    return db.execute(query)
```

**XSS Protection:**
```python
# ✅ CORRECT: HTML escaping (Jinja2 template)
from jinja2 import Template

template = Template('Hello {{ name|e }}!')
rendered = template.render(name='<script>alert("XSS")</script>')

# ❌ WRONG: Unescaped user input (vulnerable to XSS)
def render_bad(name):
    return f'Hello {name}!'
```

**CSRF Protection:**
```python
from fastapi_csrf_protect import CsrfProtect

# Generate CSRF token
@csrf_protect.get_csrf_token
async def get_csrf_token(request: Request):
    return {'csrf_token': request.csrf_token}

# Validate CSRF token
@app.post("/api/detections")
@csrf_protect.protect
async def create_detection(request: Request, detection: Detection):
    # Process detection
    pass
```

### 3.3 Authentication & Authorization

**OAuth2 + OpenID Connect:**

```python
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/oauth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate OAuth2 token and extract user claims
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/detections")
async def get_detections(user_id: str = Depends(get_current_user)):
    """
    Protected endpoint: Requires valid OAuth2 token
    """
    return {"detections": get_user_detections(user_id)}
```

**Multi-Factor Authentication (MFA):**

```python
import pyotp

def enable_mfa(user_id: str):
    """
    Enable MFA for user
    """
    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Save to database
    db.query(User).filter_by(id=user_id).update({
        'mfa_secret': secret,
        'mfa_enabled': True
    })

    # Generate QR code URL
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=user_id,
        issuer_name="WiFi Detection System"
    )

    return {'qr_url': qr_url}

def verify_mfa(user_id: str, code: str):
    """
    Verify MFA code
    """
    user = db.query(User).filter_by(id=user_id).first()

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    return True
```

**Role-Based Access Control (RBAC):**

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    USER = "user"

class Permission(str, Enum):
    READ_DETECTIONS = "read:detections"
    WRITE_DETECTIONS = "write:detections"
    DELETE_DETECTIONS = "delete:detections"
    MANAGE_USERS = "manage:users"
    EXPORT_DATA = "export:data"
    CONFIGURE_SYSTEM = "configure:system"

# Role permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.READ_DETECTIONS,
        Permission.WRITE_DETECTIONS,
        Permission.DELETE_DETECTIONS,
        Permission.MANAGE_USERS,
        Permission.EXPORT_DATA,
        Permission.CONFIGURE_SYSTEM
    ],
    Role.OPERATOR: [
        Permission.READ_DETECTIONS,
        Permission.WRITE_DETECTIONS,
        Permission.EXPORT_DATA
    ],
    Role.VIEWER: [
        Permission.READ_DETECTIONS
    ],
    Role.USER: [
        Permission.READ_DETECTIONS
    ]
}

def require_permission(permission: Permission):
    """
    Decorator to require specific permission
    """
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
            if permission not in user_permissions:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

@app.delete("/api/detections/{detection_id}")
@require_permission(Permission.DELETE_DETECTIONS)
async def delete_detection(detection_id: int, current_user: User = Depends(get_current_user)):
    """
    Delete detection (requires DELETE_DETECTIONS permission)
    """
    # Delete detection
    pass
```

**JWT Token Management:**

```python
from datetime import datetime, timedelta
from jose import jwt

def create_access_token(user_id: str, role: Role):
    """
    Create JWT access token
    """
    payload = {
        "sub": user_id,
        "role": role.value,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=15),  # 15-minute expiration
        "type": "access"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def create_refresh_token(user_id: str):
    """
    Create JWT refresh token (longer-lived)
    """
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=7),  # 7-day expiration
        "type": "refresh"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def refresh_access_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        user = db.query(User).filter_by(id=user_id).first()

        # Generate new access token
        access_token = create_access_token(user_id, user.role)
        return {"access_token": access_token}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Session Management:**

```python
from fastapi import Request

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """
    Session management middleware
    """
    # Check for active session
    session_token = request.cookies.get("session_token")
    if session_token:
        # Validate session
        session = validate_session(session_token)
        if not session:
            # Invalid session, redirect to login
            return RedirectResponse(url="/login")

        # Check session expiration
        if session.expired:
            # Session expired, redirect to login
            return RedirectResponse(url="/login?expired=true")

        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()

    # Process request
    response = await call_next(request)
    return response
```

### 3.4 Data Encryption

**Encryption at Rest (AES-256):**

```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt plaintext data
        """
        encrypted_data = self.cipher.encrypt(data.encode())
        return encrypted_data.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        """
        decrypted_data = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_data.decode()

# Usage
encryption_service = EncryptionService(settings.ENCRYPTION_KEY)

# Encrypt sensitive data
encrypted_mac = encryption_service.encrypt(mac_address)

# Decrypt sensitive data
mac_address = encryption_service.decrypt(encrypted_mac)
```

**Database Encryption (PostgreSQL):**

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create table with encrypted column
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    detector_id VARCHAR(50) NOT NULL,
    rssi_data BYTEA,  -- Encrypted RSSI data
    timestamp TIMESTAMP NOT NULL
);

-- Encrypt data before insert
INSERT INTO detections (detector_id, rssi_data, timestamp)
VALUES (
    'detector_1',
    pgp_sym_encrypt('[-45, -50, -48, ...]', 'encryption_key'),
    NOW()
);

-- Decrypt data when reading
SELECT
    detector_id,
    pgp_sym_decrypt(rssi_data::bytea, 'encryption_key') AS rssi_values,
    timestamp
FROM detections;
```

**Encryption in Transit (TLS 1.3):**

```python
# FastAPI with HTTPS
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "HTTPS enabled"}

# Run with HTTPS
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/etc/ssl/private/detection.example.com.key",
        ssl_certfile="/etc/ssl/certs/detection.example.com.crt"
    )
```

**Key Management Strategy:**

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import os

class KeyManager:
    def __init__(self):
        self.keys = {}

    def generate_key(self, key_id: str) -> bytes:
        """
        Generate encryption key using PBKDF2
        """
        salt = os.urandom(16)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(key_id.encode())
        self.keys[key_id] = key
        return key

    def rotate_key(self, key_id: str):
        """
        Rotate encryption key
        """
        old_key = self.keys.get(key_id)
        new_key = self.generate_key(key_id)

        # Re-encrypt all data with new key
        # ...

        # Delete old key
        del old_key

        return new_key

# Key rotation schedule
# - Master key: Rotate annually
# - Data encryption keys: Rotate every 90 days
# - Session keys: Rotate daily
```

**Key Rotation Policies:**

| Key Type | Rotation Frequency | Trigger | Retention |
|----------|-------------------|---------|-----------|
| Master Key | Annually | Schedule | Previous 1 key kept |
| Data Encryption Key | Quarterly | Schedule | Previous 3 keys kept |
| Session Key | Daily | Automatic | Deleted after session |
| API Key | Monthly | Manual | Previous 12 keys kept |

### 3.5 API Security

**Rate Limiting:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/detections")
@limiter.limit("10/minute")  # 10 requests per minute
async def get_detections(request: Request):
    """
    Rate-limited endpoint
    """
    return {"detections": []}
```

**API Key Management:**

```python
import secrets
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"

    key = Column(String(64), primary_key=True)
    user_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)

def generate_api_key(user_id: str, expires_days: int = 365):
    """
    Generate API key for user
    """
    key = secrets.token_urlsafe(32)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=expires_days)

    api_key = APIKey(
        key=key,
        user_id=user_id,
        created_at=created_at,
        expires_at=expires_at
    )

    db.add(api_key)
    db.commit()

    return key

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key
    """
    key_record = db.query(APIKey).filter_by(key=api_key).first()

    if not key_record:
        return False

    if key_record.expires_at < datetime.utcnow():
        return False

    # Update last used
    key_record.last_used = datetime.utcnow()
    db.commit()

    return True
```

**Request Signing (HMAC):**

```python
import hmac
import hashlib

def sign_request(request_body: str, secret_key: str) -> str:
    """
    Sign request with HMAC-SHA256
    """
    signature = hmac.new(
        secret_key.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_signature(request_body: str, signature: str, secret_key: str) -> bool:
    """
    Verify request signature
    """
    expected_signature = sign_request(request_body, secret_key)
    return hmac.compare_digest(expected_signature, signature)

# Usage
request_body = '{"detector_id": "1", "rssi": [-45, -50]}'
signature = sign_request(request_body, api_secret)

# Send request with signature
headers = {
    "X-Signature": signature,
    "Content-Type": "application/json"
}

# Verify on server side
if not verify_signature(request_body, headers["X-Signature"], api_secret):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

**CORS Policies:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific origin only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
    max_age=3600,
)
```

---

## 4. Data Protection Measures

### 4.1 Data Minimization

**Collect Only Necessary Data:**

| Data Type | Necessity | Collection Method | Minimization Technique |
|-----------|-----------|-------------------|------------------------|
| RSSI Signal Strength | ✅ Necessary | Detector → Server | Aggregate at source (room-level) |
| MAC Addresses | ⚠️ Optional | Real-time hashing | Hash and purge within 24h |
| Occupancy Count | ✅ Necessary | Derived from RSSI | Room-level only (0-9 people) |
| Timestamps | ⚠️ Optional | Detector → Server | Temporal bucketing (hourly/daily) |
| User IDs | ❌ Not necessary | Not collected | N/A |

**Implementation:**

```python
def collect_rssi_data(raw_rssi: List[int], detector_id: str):
    """
    Collect and minimize RSSI data at source

    Args:
        raw_rssi: Raw RSSI values (20 samples)
        detector_id: Detector identifier
    """
    # Validate RSSI range
    if not all(-90 <= value <= -30 for value in raw_rssi):
        raise ValueError("RSSI values out of range")

    # Compute statistics only (no raw data storage)
    rssi_stats = {
        'detector_id': detector_id,
        'mean': np.mean(raw_rssi),
        'std_dev': np.std(raw_rssi),
        'min': np.min(raw_rssi),
        'max': np.max(raw_rssi),
        'timestamp': datetime.utcnow().isoformat()
    }

    # Return aggregated data only
    return rssi_stats
```

**No MAC Address Storage:**

```python
def hash_mac_address(mac_address: str) -> str:
    """
    Hash MAC address with salt

    Args:
        mac_address: Raw MAC address (e.g., "AA:BB:CC:DD:EE:FF")

    Returns:
        Hashed MAC address (SHA-256)
    """
    import hashlib

    # Add salt (unique per deployment)
    salt = settings.MAC_SALT

    # Hash MAC address
    hashed_mac = hashlib.sha256((mac_address + salt).encode()).hexdigest()

    # Never store the hash (use only for real-time deduplication)
    return hashed_mac

# ✅ CORRECT: Use hash for real-time deduplication only
def deduplicate_devices(devices: List[str]) -> List[str]:
    """
    Deduplicate devices using hashed MAC addresses

    Note: Hashes are never stored, only used for comparison
    """
    seen_hashes = set()
    unique_devices = []

    for device in devices:
        hashed_mac = hash_mac_address(device)
        if hashed_mac not in seen_hashes:
            seen_hashes.add(hashed_mac)
            unique_devices.append(device)

    return unique_devices

# ❌ WRONG: Store hashed MAC addresses (still potentially identifiable)
def store_mac_address_wrong(mac_address: str):
    """
    DO NOT DO THIS: Storing hashed MAC is still PII
    """
    hashed_mac = hash_mac_address(mac_address)
    db.insert('devices').values(mac_hash=hashed_mac)  # WRONG!
```

### 4.2 Anonymization Techniques

**Technique 1: Aggregation (Room-Level Only)**

```python
def aggregate_detections(detections: List[Detection]) -> dict:
    """
    Aggregate detections to room-level only

    Args:
        detections: List of individual detections

    Returns:
        Aggregated room-level data
    """
    return {
        'room_id': detections[0].room_id,
        'occupancy_count': len(detections),  # Count only (no identities)
        'timestamp': datetime.utcnow().isoformat(),
        'detector_ids': [d.detector_id for d in detections]  # No MAC addresses
    }
```

**Technique 2: Temporal Bucketing (Remove Precise Timestamps)**

```python
def bucket_timestamp(timestamp: datetime, granularity: str = 'hour') -> datetime:
    """
    Remove precision from timestamp

    Args:
        timestamp: Precise timestamp
        granularity: 'hour', 'day', 'week'

    Returns:
        Bucketed timestamp (less precise)
    """
    if granularity == 'hour':
        return timestamp.replace(minute=0, second=0, microsecond=0)
    elif granularity == 'day':
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    elif granularity == 'week':
        # Start of week (Monday)
        days_since_monday = timestamp.weekday()
        return (timestamp - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

# Usage
precise_timestamp = datetime(2026, 2, 2, 10, 30, 45)
hourly_bucket = bucket_timestamp(precise_timestamp, granularity='hour')
# Result: 2026-02-02 10:00:00 (minutes/seconds removed)
```

**Technique 3: Differential Privacy (Add Noise to Aggregates)**

```python
import numpy as np

def add_laplace_noise(true_value: float, epsilon: float = 1.0, sensitivity: float = 1.0) -> float:
    """
    Add Laplace noise for differential privacy

    Args:
        true_value: True aggregate value
        epsilon: Privacy parameter (lower = more private)
        sensitivity: Maximum change in query from removing one individual

    Returns:
        Noisy value (differentially private)
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return true_value + noise

# Usage
true_occupancy = 5  # Actual count
private_occupancy = add_laplace_noise(true_occupancy, epsilon=0.1)
# Result: 5.2 (with noise added)
```

**Technique 4: k-Anonymity for Statistical Data**

```python
def achieve_k_anonymity(data: pd.DataFrame, k: int = 5, quasi_identifiers: List[str]) -> pd.DataFrame:
    """
    Achieve k-anonymity by grouping records

    Args:
        data: DataFrame with sensitive data
        k: Minimum group size
        quasi_identifiers: Columns that can identify individuals

    Returns:
        k-anonymized DataFrame
    """
    # Group by quasi-identifiers
    grouped = data.groupby(quasi_identifiers)

    # Filter out groups with less than k records
    anonymized = grouped.filter(lambda x: len(x) >= k)

    # Aggregate sensitive values within groups
    result = anonymized.groupby(quasi_identifiers).agg({
        'occupancy_count': 'mean',
        'timestamp': 'count'
    }).reset_index()

    return result
```

### 4.3 Access Controls

**Least Privilege Principle:**

```python
from enum import Enum

class AccessLevel(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

# Role-based access matrix
ACCESS_MATRIX = {
    "viewer": {
        "detections": AccessLevel.READ,
        "analytics": AccessLevel.READ,
        "settings": AccessLevel.NONE
    },
    "operator": {
        "detections": AccessLevel.WRITE,
        "analytics": AccessLevel.READ,
        "settings": AccessLevel.READ
    },
    "admin": {
        "detections": AccessLevel.ADMIN,
        "analytics": AccessLevel.ADMIN,
        "settings": AccessLevel.ADMIN
    }
}

def check_access(user_role: str, resource: str, required_access: AccessLevel) -> bool:
    """
    Check if user has required access level

    Args:
        user_role: User's role
        resource: Resource being accessed
        required_access: Required access level

    Returns:
        True if access granted, False otherwise
    """
    user_access = ACCESS_MATRIX.get(user_role, {}).get(resource, AccessLevel.NONE)

    # Compare access levels
    access_hierarchy = {
        AccessLevel.NONE: 0,
        AccessLevel.READ: 1,
        AccessLevel.WRITE: 2,
        AccessLevel.ADMIN: 3
    }

    return access_hierarchy[user_access] >= access_hierarchy[required_access]
```

**Audit Logging for All Access:**

```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource = Column(String(100), nullable=False)  # Table/endpoint
    resource_id = Column(String(50))  # ID of specific resource
    timestamp = Column(DateTime, nullable=False)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(255))
    success = Column(Integer, nullable=False)  # 1 = success, 0 = failure
    error_message = Column(Text)

def log_access(user_id: str, action: str, resource: str, resource_id: str = None,
               success: bool = True, error_message: str = None, request: Request = None):
    """
    Log access attempt

    Args:
        user_id: User ID
        action: Action performed (CREATE, READ, UPDATE, DELETE)
        resource: Resource accessed
        resource_id: Specific resource ID
        success: Whether access was successful
        error_message: Error message if failed
        request: FastAPI Request object
    """
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        timestamp=datetime.utcnow(),
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        success=int(success),
        error_message=error_message
    )

    db.add(log_entry)
    db.commit()
```

**Admin Approval for Exports:**

```python
from fastapi import BackgroundTasks

def request_data_export(user_id: str, export_reason: str):
    """
    Request data export (requires admin approval)

    Args:
        user_id: User requesting export
        export_reason: Reason for export
    """
    # Create export request
    export_request = DataExportRequest(
        user_id=user_id,
        reason=export_reason,
        status="pending_approval",
        created_at=datetime.utcnow()
    )

    db.add(export_request)
    db.commit()

    # Notify admins for approval
    notify_admins(export_request)

    return {"request_id": export_request.id}

def approve_export_request(request_id: str, admin_id: str):
    """
    Approve export request (admin only)

    Args:
        request_id: Export request ID
        admin_id: Admin user ID
    """
    # Get request
    request = db.query(DataExportRequest).filter_by(id=request_id).first()

    # Verify admin status
    if not is_admin(admin_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Approve request
    request.status = "approved"
    request.approved_by = admin_id
    request.approved_at = datetime.utcnow()

    db.commit()

    # Generate export in background
    generate_data_export(request_id)

    return {"message": "Export request approved"}
```

**Regular Access Reviews:**

```python
def schedule_access_review():
    """
    Schedule monthly access reviews
    """
    # Get all users with access
    users = db.query(User).filter(User.access_level != AccessLevel.NONE).all()

    for user in users:
        # Create review task
        review = AccessReview(
            user_id=user.id,
            current_role=user.role,
            review_date=datetime.utcnow() + timedelta(days=30),
            status="pending"
        )

        db.add(review)

    db.commit()

    # Notify reviewers
    notify_reviewers(users)
```

---

## 5. Operational Security

### 5.1 Secure Deployment

**Container Hardening:**

```dockerfile
# Dockerfile with security best practices
FROM python:3.9-slim as base

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port (HTTPS only)
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f https://localhost:8443/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8443", "--keyfile", "/etc/ssl/private/key.pem", "--certfile", "/etc/ssl/certs/cert.pem", "app:app"]
```

**Secrets Management (HashiCorp Vault):**

```python
import hvac

class VaultSecretsManager:
    def __init__(self, vault_url: str, token: str):
        self.client = hvac.Client(url=vault_url, token=token)

    def get_secret(self, path: str) -> dict:
        """
        Retrieve secret from Vault

        Args:
            path: Secret path in Vault

        Returns:
            Secret dictionary
        """
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']

    def create_secret(self, path: str, secret: dict):
        """
        Store secret in Vault

        Args:
            path: Secret path in Vault
            secret: Secret dictionary
        """
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret
        )

# Usage
vault = VaultSecretsManager(
    vault_url="https://vault.example.com",
    token=os.environ["VAULT_TOKEN"]
)

# Get database credentials
db_creds = vault.get_secret("secret/data/database")
db_url = f"postgresql://{db_creds['username']}:{db_creds['password']}@db.example.com/detection"

# Get encryption key
encryption_key = vault.get_secret("secret/data/encryption")['key']
```

**Immutable Infrastructure:**

```yaml
# Kubernetes deployment with immutable infrastructure
apiVersion: apps/v1
kind: Deployment
metadata:
  name: detection-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: detection-api
        version: "1.0.0"  # Immutable version tag
    spec:
      containers:
      - name: api
        image: registry.example.com/detection-api:1.0.0  # Immutable image tag
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
```

**Regular Security Updates:**

```bash
#!/bin/bash
# Automated security update script

# Update system packages
apt-get update && apt-get upgrade -y

# Update Python dependencies
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

# Scan for vulnerabilities
trivy image detection-api:latest

# Restart services if vulnerabilities found
if [ $? -ne 0 ]; then
    echo "Vulnerabilities found, rebuilding image..."
    docker build -t detection-api:latest .
    docker-compose up -d
fi
```

### 5.2 Monitoring & Logging

**Security Event Logging:**

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Rotate logs (10 MB max, keep 5 backup files)
handler = RotatingFileHandler(
    '/var/log/security.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)

# Format: timestamp | level | user_id | event | details
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(user_id)s | %(event)s | %(details)s'
)
handler.setFormatter(formatter)

security_logger.addHandler(handler)

# Log security events
def log_security_event(user_id: str, event: str, details: dict):
    """
    Log security event

    Args:
        user_id: User ID
        event: Event type (LOGIN_FAILED, PERMISSION_DENIED, etc.)
        details: Event details
    """
    security_logger.info(
        "",
        extra={
            "user_id": user_id,
            "event": event,
            "details": json.dumps(details)
        }
    )
```

**Intrusion Detection:**

```python
from sklearn.ensemble import IsolationForest
import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,  # Expected 10% anomalies
            random_state=42
        )

    def train(self, normal_traffic: np.ndarray):
        """
        Train on normal traffic patterns

        Args:
            normal_traffic: Feature matrix of normal traffic
        """
        self.model.fit(normal_traffic)

    def detect(self, traffic_sample: np.ndarray) -> bool:
        """
        Detect anomalous traffic

        Args:
            traffic_sample: Feature vector of current traffic

        Returns:
            True if anomalous, False otherwise
        """
        prediction = self.model.predict([traffic_sample])
        return prediction[0] == -1  # -1 = anomaly

# Usage
detector = AnomalyDetector()
normal_traffic = load_normal_traffic_data()
detector.train(normal_traffic)

# Monitor incoming traffic
current_traffic = extract_traffic_features(request)
if detector.detect(current_traffic):
    alert_security_team("Anomalous traffic detected")
```

**Anomaly Detection:**

```python
from datetime import datetime, timedelta

def detect_anomalies(metric: str, threshold: float = 3.0):
    """
    Detect anomalies using statistical process control

    Args:
        metric: Metric name (e.g., "cpu_usage", "memory_usage")
        threshold: Z-score threshold for anomaly
    """
    # Get last 100 data points
    data = get_metric_history(metric, limit=100)

    # Calculate mean and standard deviation
    mean = np.mean(data)
    std = np.std(data)

    # Get current value
    current_value = get_current_metric(metric)

    # Calculate Z-score
    z_score = (current_value - mean) / std

    # Check if anomalous
    if abs(z_score) > threshold:
        alert(f"Anomaly detected in {metric}: {current_value} (Z-score: {z_score:.2f})")
        return True

    return False
```

**Alert Thresholds:**

| Metric | Warning Threshold | Critical Threshold | Alert Type |
|--------|------------------|-------------------|------------|
| Failed Login Attempts | 5 per minute | 10 per minute | Email + SMS |
| CPU Usage | 80% | 95% | Email |
| Memory Usage | 80% | 95% | Email |
| Disk Usage | 80% | 95% | Email |
| API Latency (p95) | 1000ms | 5000ms | Email |
| Error Rate | 5% | 10% | Email + Pager |
| Intrusion Detection | N/A | 1 event | Email + Pager + Phone |

### 5.3 Incident Response

**Breach Notification Procedures:**

```python
class BreachNotifier:
    def __init__(self):
        self.recipients = {
            "dpo": "dpo@example.com",
            "security_team": "security@example.com",
            "management": "management@example.com"
        }

    def notify_breach(self, breach_details: dict):
        """
        Notify stakeholders of data breach

        Args:
            breach_details: Dictionary with breach information
        """
        # Send email to DPO
        send_email(
            to=self.recipients["dpo"],
            subject="URGENT: Data Breach Detected",
            body=f"""
            A data breach has been detected.

            Details:
            - Type: {breach_details['type']}
            - Scope: {breach_details['scope']}
            - Detected: {breach_details['detected_at']}
            - Affected Users: {breach_details['affected_users']}

            Immediate action required.
            """
        )

        # Send email to security team
        send_email(
            to=self.recipients["security_team"],
            subject="URGENT: Data Breach Response Required",
            body=f"See breach details above. Initiate incident response plan."
        )

        # Log breach
        log_security_event(
            user_id="system",
            event="DATA_BREACH",
            details=breach_details
        )
```

**GDPR 72-Hour Notification:**

```python
def notify_gdpr_breach(breach_details: dict):
    """
    Notify supervisory authority within 72 hours (GDPR Article 33)

    Args:
        breach_details: Dictionary with breach information
    """
    # Check if breach meets notification threshold
    if breach_details['risk_to_rights'] == 'high':
        # Notify supervisory authority (e.g., ICO in UK)
        notify_supervisory_authority(
            breach_type=breach_details['type'],
            affected_count=breach_details['affected_users'],
            breach_description=breach_details['description'],
            mitigation_measures=breach_details['mitigation'],
            contact_person="dpo@example.com"
        )

        # Notify affected data subjects (GDPR Article 34)
        notify_data_subjects(
            affected_users=breach_details['affected_users'],
            breach_description=breach_details['description'],
            likely_consequences=breach_details['consequences'],
            mitigation_measures=breach_details['mitigation'],
            contact_person="dpo@example.com"
        )
```

**Response Team Contacts:**

| Role | Name | Email | Phone | On-Call |
|------|------|-------|-------|---------|
| Data Protection Officer | [Name] | dpo@example.com | +1-555-0100 | 24/7 |
| Security Lead | [Name] | security@example.com | +1-555-0101 | 24/7 |
| Technical Lead | [Name] | tech@example.com | +1-555-0102 | Business hours |
| Legal Counsel | [Name] | legal@example.com | +1-555-0103 | Business hours |
| PR/Comms | [Name] | pr@example.com | +1-555-0104 | Business hours |

**Post-Incident Reviews:**

```markdown
# Post-Incident Review Template

**Incident ID:** INC-2026-001
**Date:** 2026-02-02
**Severity:** High
**Duration:** 4 hours (detection to resolution)

## Timeline
- 10:00 - Incident detected (alert triggered)
- 10:05 - Security team notified
- 10:15 - Incident response team assembled
- 10:30 - Root cause identified
- 11:00 - Mitigation implemented
- 12:00 - Service restored
- 14:00 - Post-incident review completed

## Root Cause
[Describe root cause]

## Impact Assessment
- Affected users: [Number]
- Data exposed: [Types]
- Service disruption: [Duration]

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]
3. [Lesson 3]

## Action Items
- [ ] [Action item 1] - Assigned to [Name] - Due [Date]
- [ ] [Action item 2] - Assigned to [Name] - Due [Date]

## Prevention Measures
1. [Prevention measure 1]
2. [Prevention measure 2]
```

---

## 6. Privacy-First Features

### 6.1 User Consent Management

**Granular Consent Options:**

```python
from sqlalchemy import Column, Boolean, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserConsent(Base):
    __tablename__ = "user_consent"

    user_id = Column(String(50), primary_key=True)
    occupancy_detection = Column(Boolean, default=False)  # Safety/security
    pattern_analysis = Column(Boolean, default=False)  # Space optimization
    data_sharing = Column(Boolean, default=False)  # Third-party sharing
    marketing = Column(Boolean, default=False)  # Marketing communications
    consent_date = Column(DateTime)
    withdrawn_date = Column(DateTime)

def update_consent(user_id: str, consent_type: str, consent_value: bool):
    """
    Update user consent

    Args:
        user_id: User ID
        consent_type: Type of consent (occupancy_detection, pattern_analysis, etc.)
        consent_value: True = consent given, False = consent withdrawn
    """
    user_consent = db.query(UserConsent).filter_by(user_id=user_id).first()

    if not user_consent:
        user_consent = UserConsent(user_id=user_id)
        db.add(user_consent)

    setattr(user_consent, consent_type, consent_value)

    if consent_value:
        user_consent.consent_date = datetime.utcnow()
        user_consent.withdrawn_date = None
    else:
        user_consent.withdrawn_date = datetime.utcnow()

    db.commit()
```

**Easy Withdrawal Mechanism:**

```html
<!-- Privacy Dashboard UI -->
<!DOCTYPE html>
<html>
<head>
    <title>Privacy Dashboard</title>
</head>
<body>
    <h1>Privacy Dashboard</h1>

    <h2>Your Consents</h2>

    <form id="consent-form">
        <label>
            <input type="checkbox" name="occupancy_detection" checked disabled>
            Occupancy Detection (required for safety/security)
        </label>
        <br><br>

        <label>
            <input type="checkbox" name="pattern_analysis">
            Pattern Analysis (space optimization)
        </label>
        <br><br>

        <label>
            <input type="checkbox" name="data_sharing">
            Data Sharing with Third Parties
        </label>
        <br><br>

        <label>
            <input type="checkbox" name="marketing">
            Marketing Communications
        </label>
        <br><br>

        <button type="submit">Update Consents</button>
        <button type="button" onclick="withdrawAll()">Withdraw All Consents</button>
    </form>

    <script>
        function withdrawAll() {
            if (confirm("Are you sure you want to withdraw all consents? This will disable all features.")) {
                document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = false;
                });
                document.getElementById('consent-form').submit();
            }
        }
    </script>
</body>
</html>
```

**Consent Expiration:**

```python
def check_consent_expiration(user_id: str):
    """
    Check if user consent has expired (1 year)

    Args:
        user_id: User ID

    Returns:
        True if consent expired, False otherwise
    """
    user_consent = db.query(UserConsent).filter_by(user_id=user_id).first()

    if not user_consent:
        return True

    # Check if consent is older than 1 year
    expiration_date = user_consent.consent_date + timedelta(days=365)

    if datetime.utcnow() > expiration_date:
        # Expire consent
        user_consent.occupancy_detection = False
        user_consent.pattern_analysis = False
        user_consent.data_sharing = False
        user_consent.marketing = False
        db.commit()

        # Notify user
        send_consent_renewal_email(user_id)

        return True

    return False
```

### 6.2 Privacy Dashboard

**Data Viewing Capability:**

```python
@app.get("/privacy/dashboard")
async def privacy_dashboard(user_id: str = Depends(get_current_user)):
    """
    Privacy dashboard for users to view their data
    """
    # Get user's data
    detections = get_user_detections(user_id)
    consent = get_user_consent(user_id)

    # Get data retention info
    data_retention = {
        'raw_rssi_data': days_until_purge(user_id, 'rssi_data', retention_days=30),
        'aggregated_analytics': days_until_purge(user_id, 'analytics', retention_days=90)
    }

    return {
        'user_id': user_id,
        'consent': consent,
        'data_retention': data_retention,
        'detections_count': len(detections),
        'last_detection': detections[-1].timestamp if detections else None
    }
```

**Export Functionality:**

```python
@app.post("/privacy/export")
async def export_user_data(user_id: str = Depends(get_current_user)):
    """
    Export user data (GDPR Right to Data Portability)
    """
    # Generate export
    export_path = export_user_data(user_id)

    # Create download link (expires in 24 hours)
    download_token = generate_download_token(user_id, export_path)
    download_link = f"https://example.com/privacy/download/{download_token}"

    # Send email with download link
    send_export_email(user_id, download_link)

    return {
        'status': 'success',
        'message': 'Export will be emailed to you within 24 hours'
    }
```

**Deletion Requests:**

```python
@app.post("/privacy/delete")
async def request_deletion(user_id: str = Depends(get_current_user)):
    """
    Request data deletion (GDPR Right to Erasure)
    """
    # Verify identity (MFA required)
    if not verify_mfa(user_id, mfa_code):
        raise HTTPException(status_code=401, detail="MFA verification required")

    # Schedule deletion (30-day grace period)
    deletion_request = DataDeletionRequest(
        user_id=user_id,
        requested_at=datetime.utcnow(),
        scheduled_for=datetime.utcnow() + timedelta(days=30),
        status='pending'
    )

    db.add(deletion_request)
    db.commit()

    # Send confirmation email
    send_deletion_confirmation_email(user_id, scheduled_for=deletion_request.scheduled_for)

    return {
        'status': 'success',
        'message': 'Your data will be deleted within 30 days. You can cancel this request anytime.'
    }
```

**Activity Logs Access:**

```python
@app.get("/privacy/activity-logs")
async def get_activity_logs(
    user_id: str = Depends(get_current_user),
    start_date: datetime,
    end_date: datetime
):
    """
    Get user's activity logs (data access, modifications, etc.)
    """
    # Get audit logs for user
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= start_date,
        AuditLog.timestamp <= end_date
    ).all()

    return {
        'logs': [
            {
                'timestamp': log.timestamp,
                'action': log.action,
                'resource': log.resource,
                'ip_address': log.ip_address
            }
            for log in logs
        ]
    }
```

### 6.3 Transparency Features

**Clear Privacy Policy:**

```markdown
# Privacy Policy

## Summary (Plain Language)
We use WiFi signals to detect how many people are in a room for safety and efficiency. We do not track individuals or collect personal information.

## What We Collect
- **WiFi signal strength** (RSSI): Measures how strong WiFi signals are (-30 to -90 dBm)
- **Occupancy count**: Number of people in a room (0-9, room-level only)
- **Timestamps**: When detections occurred (anonymized to hour/day for analytics)

## What We Don't Collect
- Personal identities (names, emails)
- Device identifiers (MAC addresses are never stored)
- Video or audio recordings
- Individual location tracking

## How We Use Your Data
1. **Safety & Security** (Legitimate Interest): Emergency response, intrusion detection
2. **Resource Optimization** (Legitimate Interest): HVAC control, capacity planning
3. **Space Utilization** (Explicit Consent Required): Meeting room analytics

## Your Rights
- Right to access (view your data)
- Right to erasure (delete your data)
- Right to restrict processing (opt-out)
- Right to object (withdraw consent)
- Right to data portability (export data)

## Data Retention
- Raw RSSI data: 30 days
- Aggregated analytics: 90 days
- Device identifiers: 24 hours (hashed only, never stored)

## Contact
Email: privacy@example.com
DPO: dpo@example.com

Last Updated: 2026-02-02
```

**Real-Time Detection Indicator:**

```python
# Hardware: LED on detector that lights up when detecting

# Software: Visual indicator in UI
@app.websocket("/ws/detections")
async def detection_updates(websocket: WebSocket):
    """
    Real-time detection updates via WebSocket
    """
    await websocket.accept()

    # Subscribe to detection stream
    async for detection in subscribe_to_detections():
        # Send detection to client
        await websocket.send_json({
            'room_id': detection.room_id,
            'occupancy_count': detection.count,
            'timestamp': detection.timestamp,
            'detecting': detection.count > 0  # LED indicator
        })
```

**Data Retention Display:**

```html
<!-- Privacy Dashboard UI -->
<h2>Your Data Retention</h2>

<table>
    <tr>
        <th>Data Type</th>
        <th>Retention Period</th>
        <th>Deletion Date</th>
    </tr>
    <tr>
        <td>Raw RSSI Data</td>
        <td>30 days</td>
        <td id="rssi-deletion-date">Calculating...</td>
    </tr>
    <tr>
        <td>Aggregated Analytics</td>
        <td>90 days</td>
        <td id="analytics-deletion-date">Calculating...</td>
    </tr>
</table>

<script>
    // Fetch deletion dates from API
    fetch('/api/privacy/deletion-dates')
        .then(response => response.json())
        .then(data => {
            document.getElementById('rssi-deletion-date').textContent = data.rssi_deletion_date;
            document.getElementById('analytics-deletion-date').textContent = data.analytics_deletion_date;
        });
</script>
```

**Third-Party Sharing Disclosure:**

```python
def check_data_sharing_consent(user_id: str) -> bool:
    """
    Check if user has consented to third-party data sharing

    Args:
        user_id: User ID

    Returns:
        True if consent given, False otherwise
    """
    user_consent = db.query(UserConsent).filter_by(user_id=user_id).first()

    if not user_consent or not user_consent.data_sharing:
        return False

    return True

@app.post("/analytics/share")
async def share_analytics_with_third_party(
    user_id: str = Depends(get_current_user),
    third_party: str
):
    """
    Share analytics with third party (requires explicit consent)
    """
    # Check consent
    if not check_data_sharing_consent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Third-party data sharing requires explicit consent"
        )

    # Log sharing
    log_security_event(
        user_id=user_id,
        event="DATA_SHARED_WITH_THIRD_PARTY",
        details={'third_party': third_party}
    )

    # Share aggregated data only (no individual data)
    aggregated_data = get_aggregated_analytics(user_id)
    send_to_third_party(third_party, aggregated_data)

    return {'status': 'success'}
```

---

## 7. Compliance Checklist

### 7.1 GDPR Compliance Items

**Article 5 - Principles:**
- ✅ Lawfulness, fairness, transparency: Privacy policy, legal basis (legitimate interest)
- ✅ Purpose limitation: Only for safety/security (not monitoring)
- ✅ Data minimization: RSSI only, aggregated, no MAC storage
- ✅ Accuracy: 98-99% accuracy, verified
- ✅ Storage limitation: 30-90 days, auto-purge
- ✅ Integrity and confidentiality: Encryption (AES-256, TLS 1.3)
- ✅ Accountability: Audit logging, DPIA, DPO oversight

**Article 6 - Lawfulness of Processing:**
- ✅ Legitimate interest (safety, security)
- ✅ Explicit consent (pattern analysis)
- ✅ Contractual necessity (employee safety)

**Article 7 - Conditions for Consent:**
- ✅ Freely given: No coercion, clear opt-out
- ✅ Specific: Granular consent per feature
- ✅ Informed: Clear privacy policy
- ✅ Unambiguous: Explicit checkbox, no pre-ticked boxes

**Article 12-23 - Data Subject Rights:**
- ✅ Right to be informed (Article 13 & 14): Privacy policy
- ✅ Right to access (Article 15): Data export
- ✅ Right to rectification (Article 16): N/A (data not modifiable)
- ✅ Right to erasure (Article 17): Data deletion
- ✅ Right to restrict processing (Article 18): Processing restriction
- ✅ Right to data portability (Article 20): CSV/JSON export
- ✅ Right to object (Article 21): Objection processing

**Article 24 - Responsibility of the Controller:**
- ✅ Technical and organizational measures: Encryption, access controls
- ✅ Data protection by design and by default: Privacy-first architecture

**Article 25 - Data Protection by Design and by Default:**
- ✅ Privacy by design: Edge processing, anonymization
- ✅ Privacy by default: 30-day retention, aggregation

**Article 32 - Security of Processing:**
- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.3)
- ✅ Access controls (RBAC, MFA)
- ✅ Audit logging (all access logged)

**Article 33 - Notification of a Personal Data Breach:**
- ✅ Notify supervisory authority within 72 hours
- ✅ Notify affected data subjects if high risk

**Article 35 - Data Protection Impact Assessment (DPIA):**
- ✅ DPIA completed (see Section 2.4)

**Article 37 - Designation of a Data Protection Officer (DPO):**
- ✅ DPO appointed (contact: dpo@example.com)

### 7.2 CCPA/CPRA Considerations (California)

**CCPA Rights:**
- ✅ Right to know: What data is collected (privacy policy)
- ✅ Right to delete: Data deletion (similar to GDPR)
- ✅ Right to opt-out: Sale of data (we don't sell data)
- ✅ Right to non-discrimination: No penalty for exercising rights

**CCPA Compliance:**
- ✅ "Do Not Sell My Personal Information" link (not applicable, no data sold)
- ✅ Data categories: RSSI (non-PII), occupancy count (non-PII)
- ✅ Data sources: WiFi detectors only
- ✅ Business purposes: Safety, security, resource optimization

### 7.3 PDPA Requirements (Singapore)

**PDPA Obligations:**
- ✅ Consent Obligation: Explicit consent for pattern analysis
- ✅ Notification Obligation: Privacy policy
- ✅ Access and Correction Obligation: Data export, correction
- ✅ Retention Obligation: 30-90 days, auto-purge
- ✅ Transfer Limitation Obligation: No international transfers
- ✅ Protection Obligation: Encryption, access controls

### 7.4 Industry-Specific Regulations

**Healthcare (HIPAA - if deployed in hospitals):**
- ⚠️ Not applicable to RSSI data alone
- ⚠️ If combined with patient data, HIPAA may apply
- ✅ Recommendation: Do not combine with patient identifiers

**Education (FERPA - if deployed in schools):**
- ⚠️ Not applicable to aggregate occupancy data
- ⚠️ If linked to student IDs, FERPA may apply
- ✅ Recommendation: Do not link to student records

**Government (FedRAMP - if deployed in government):**
- ✅ FedRAMP authorization required for cloud deployment
- ✅ Security assessment: Vulnerability scanning, penetration testing
- ✅ Continuous monitoring: Security logs, incident response

### 7.5 Security Audit Requirements

**External Penetration Testing:**
- **Frequency:** Annually (minimum) or after major changes
- **Scope:** All public-facing endpoints, APIs, web application
- **Methodology:** OWASP Top 10, CVE scanning
- **Reporting:** Executive summary + technical findings + remediation plan

**Internal Security Reviews:**
- **Frequency:** Quarterly
- **Scope:** Access controls, configuration review, code review
- **Methodology:** Security checklist, automated scanning
- **Reporting:** Internal memo + action items

**Vulnerability Scanning:**
- **Tools:** Nessus, OpenVAS, OWASP ZAP
- **Frequency:** Weekly automated scans
- **Scope:** Network, application, dependencies
- **Remediation:** Critical (within 24 hours), High (within 7 days), Medium (within 30 days)

**Dependency Scanning:**
- **Tools:** Snyk, Dependabot, npm audit
- **Frequency:** Weekly automated scans
- **Scope:** All Python/Node.js dependencies
- **Remediation:** Automatic updates for low-risk, manual for high-risk

---

## Appendix A: Security Policies

### Password Policy

- Minimum length: 12 characters
- Complexity: Uppercase, lowercase, numbers, special characters
- Expiration: 90 days
- History: Last 10 passwords cannot be reused
- Lockout: 5 failed attempts, 15-minute lockout

### Access Control Policy

- Principle of least privilege
- Role-based access control (RBAC)
- Mandatory access reviews (quarterly)
- Separation of duties (no single person has all access)
- Emergency access procedures (break-glass)

### Incident Response Policy

- Detection: Automated monitoring + human review
- Containment: Isolate affected systems
- Eradication: Remove root cause
- Recovery: Restore from backups
- Post-incident review: Lessons learned + improvements

### Data Retention Policy

- Raw RSSI data: 30 days
- Aggregated analytics: 90 days
- Access logs: 365 days
- Audit logs: 7 years (legal requirement)
- Backup retention: 90 days

---

**Document End**
**Next Steps:**
1. Review and approve security and privacy requirements
2. Conduct DPIA (if not already done)
3. Implement security measures (encryption, access controls)
4. Create privacy dashboard UI
5. Draft GDPR-compliant privacy policy
