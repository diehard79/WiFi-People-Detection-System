# ADR-010: Calibration Strategy Selection

**Status:** Accepted
**Date:** 2025-02-02
**Context:** RSSI Baseline Calibration for Accurate Detection
**Decision:** Automated Daily Calibration with Manual Override

---

## Context

RSSI-based detection requires calibration due to:
- **Environmental Drift:** Temperature, humidity, WiFi interference
- **Signal Variability:** Router power fluctuations, obstacles
- **Baseline Shifts:** New devices, furniture rearrangement
- **Accuracy Impact:** Uncalibrated systems drop to 60-70% accuracy

**Calibration Challenges:**
- Requires empty room (no people present)
- Takes 5-15 minutes to collect sufficient data
- Affects real-time accuracy
- User inconvenience during calibration

---

## Decision

**Selected Strategy: Automated Daily Calibration with User Control**

### Calibration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  CALIBRATION SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. SCHEDULER (Cron)                                          │
│  ├─ Default: Daily at 3:00 AM (configurable)                │
│  ├─ Requires empty room confirmation                        │
│  └─ Skips if room occupied                                  │
│                                                               │
│  2. CALIBRATION MANAGER                                      │
│  ├─ RSSI data collection (5 minutes)                        │
│  ├─ Statistical baseline computation                        │
│  │   ├─ Mean RSSI per detector                              │
│  │   ├─ Standard deviation (noise floor)                    │
│  │   ├─ Cross-detector correlation                          │
│  │   └─ Environmental factors                              │
│  ├─ Baseline storage (database)                             │
│  └─ Validation (quality checks)                             │
│                                                               │
│  3. QUALITY VALIDATION                                       │
│  ├─ Signal-to-noise ratio check                             │
│  ├─ Outlier detection                                       │
│  ├─ Consistency verification                                │
│  └─ Fallback to previous baseline if invalid                │
│                                                               │
│  4. USER INTERFACE                                           │
│  ├─ Schedule configuration                                   │
│  ├─ Manual calibration trigger                              │
│  ├─ Progress notification                                   │
│  └─ Calibration history                                     │
│                                                               │
│  5. NOTIFICATION SYSTEM                                      │
│  ├─ Pre-calibration reminder (15 min before)               │
│  ├─ In-progress updates                                     │
│  ├─ Completion confirmation                                 │
│  └─ Failure alerts                                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Calibration Frequency Analysis

**Research Findings ([arXiv:2308.06773](https://arxiv.org/html/2308.06773v2)):**

> "Daily calibration is required for RSSI-based systems to maintain 98%+ accuracy. Environmental drift causes baseline to shift 5-10% per day."

**Accuracy vs. Calibration Frequency:**

| Frequency | Accuracy | User Disruption | Data Volume | Complexity |
|-----------|----------|-----------------|-------------|------------|
| **Hourly** | 99%+ ✅ | Very High ❌ | High ❌ | Medium ⚠️ |
| **Daily** | 98-99% ✅ | Low ✅ | Low ✅ | Low ✅ |
| **Weekly** | 90-95% ⚠️ | Very Low ✅ | Very Low ✅ | Low ✅ |
| **Monthly** | 80-90% ❌ | None ✅ | None ✅ | Low ✅ |
| **Manual Only** | Variable ⚠️ | User-dependent ❌ | Variable ⚠️ | Low ✅ |

**Selected: Daily Calibration**
- ✅ Meets accuracy target (98-99%)
- ✅ Minimal disruption (3 AM, while closed)
- ✅ Low data volume (5 min × 4 detectors = 20 min data)
- ✅ Easy to automate

### Calibration Method Comparison

**Automated vs. Manual:**

| Aspect | Automated (Daily) | Manual (On-Demand) | Hybrid |
|--------|-------------------|-------------------|---------|
| **Accuracy** | 98-99% ✅ | Variable ⚠️ | 98-99% ✅ |
| **Consistency** | High ✅ | Low ❌ | High ✅ |
| **User Effort** | None ✅ | High ❌ | Low ⚠️ |
| **Timeliness** | Scheduled ✅ | On-demand ⚠️ | Flexible ✅ |
| **Failures** | Auto-retry ✅ | User-dependent ❌ | Robust ✅ |

**Selected: Automated with Manual Override**
- Automated daily calibration ensures consistency
- Manual trigger allows for immediate recalibration if needed
- User can schedule calibration for convenient times

### Calibration Quality Metrics

**Quality Checks:**

1. **Signal-to-Noise Ratio (SNR):**
```python
def calculate_snr(rssi_samples: list[float]) -> float:
    """Calculate SNR (higher is better)"""
    signal_power = np.mean([s**2 for s in rssi_samples])
    noise_power = np.var(rssi_samples)
    snr_db = 10 * np.log10(signal_power / noise_power)
    return snr_db

# Threshold: SNR > 15 dB required
if snr_db < 15:
    logger.warning("Low SNR during calibration, may need re-calibration")
```

2. **Outlier Detection:**
```python
def detect_outliers(rssi_samples: list[float]) -> list[int]:
    """Detect outliers using IQR method"""
    Q1 = np.percentile(rssi_samples, 25)
    Q3 = np.percentile(rssi_samples, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = [i for i, val in enumerate(rssi_samples)
                if val < lower_bound or val > upper_bound]
    return outliers

# Threshold: <5% outliers allowed
if len(outliers) / len(rssi_samples) > 0.05:
    logger.warning("High outlier rate during calibration")
```

3. **Consistency Check:**
```python
def check_consistency(current_baseline: dict, previous_baseline: dict) -> bool:
    """Verify new baseline is consistent with previous"""
    delta = abs(current_baseline['mean_rssi'] - previous_baseline['mean_rssi'])

    # Threshold: <10 dB shift expected
    if delta > 10:
        logger.warning(f"Large baseline shift: {delta:.2f} dB")
        return False
    return True
```

---

## Implementation

### Calibration Scheduler

**Cron Configuration:**
```python
# edge_device/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(
    trigger=CronTrigger(hour=3, minute=0),  # 3:00 AM daily
    id="daily_calibration",
    max_instances=1
)
async def scheduled_calibration():
    """Trigger daily calibration"""
    from calibration import run_calibration

    room_id = "conference-room-a"

    # Check if room is occupied (optional: use motion sensors)
    is_occupied = await check_room_occupied(room_id)

    if is_occupied:
        logger.info(f"Room {room_id} occupied, skipping calibration")
        # Retry in 1 hour
        scheduler.add_job(
            run_calibration,
            'date',
            run_date=datetime.now() + timedelta(hours=1),
            args=[room_id]
        )
    else:
        await run_calibration(room_id)

# Start scheduler on device startup
scheduler.start()
```

### Calibration Procedure

**Data Collection:**
```python
import asyncio
from datetime import datetime, timedelta

async def run_calibration(room_id: str, duration_minutes: int = 5):
    """Collect calibration data and compute baseline"""

    logger.info(f"Starting calibration for room {room_id}")

    # 1. Notify users (WebSocket, email)
    await notify_calibration_start(room_id)

    # 2. Collect RSSI data
    samples_per_detector = {}
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)

    while datetime.now() < end_time:
        for detector_id in get_detectors(room_id):
            rssi = await get_rssi_value(detector_id)

            if detector_id not in samples_per_detector:
                samples_per_detector[detector_id] = []
            samples_per_detector[detector_id].append(rssi)

        await asyncio.sleep(1)  # 1 Hz sampling

    # 3. Compute baseline statistics
    baseline = {}
    for detector_id, samples in samples_per_detector.items():
        baseline[detector_id] = {
            'mean_rssi': np.mean(samples),
            'std_rssi': np.std(samples),
            'min_rssi': np.min(samples),
            'max_rssi': np.max(samples),
            'variance': np.var(samples),
            'sample_count': len(samples)
        }

    # 4. Quality checks
    snr = calculate_snr(list(samples_per_detector.values())[0])
    outliers = detect_outliers(list(samples_per_detector.values())[0])

    if snr < 15 or len(outliers) / len(samples) > 0.05:
        logger.warning("Calibration quality check failed")
        await notify_calibration_failed(room_id, "Low quality data")
        return False

    # 5. Store baseline in database
    await store_baseline(room_id, baseline)

    # 6. Notify completion
    await notify_calibration_complete(room_id, baseline)

    logger.info(f"Calibration complete for room {room_id}")
    return True
```

**Baseline Storage:**
```python
async def store_baseline(room_id: str, baseline: dict):
    """Store calibration baseline in database"""

    # Store in PostgreSQL (metadata database)
    await db.execute(
        """INSERT INTO calibrations
           (room_id, started_at, completed_at, baseline, status)
           VALUES ($1, NOW(), NOW(), $2, 'completed')""",
        room_id, json.dumps(baseline)
    )

    # Also cache in Redis (24-hour TTL)
    await redis.setex(
        f"calibration:{room_id}",
        86400,
        json.dumps(baseline)
    )
```

### User Interface

**Calibration Management Page:**
```typescript
// app/configuration/calibration/page.tsx
'use client'

import { useState } from 'react'

export default function CalibrationPage() {
  const [calibrationStatus, setCalibrationStatus] = useState({
    lastCalibration: '2025-02-02 03:00',
    nextCalibration: '2025-02-03 03:00',
    schedule: '0 3 * * *',  // Cron expression
    status: 'completed'
  })

  const triggerManualCalibration = async () => {
    const response = await fetch('/api/v1/calibration/trigger', {
      method: 'POST',
      body: JSON.stringify({ room_id: 'conference-room-a', duration: 5 })
    })

    if (response.ok) {
      alert('Calibration started! Please leave the room empty for 5 minutes.')
    }
  }

  const updateSchedule = async (cronExpression: string) => {
    await fetch('/api/v1/calibration/schedule', {
      method: 'PUT',
      body: JSON.stringify({ schedule: cronExpression })
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Calibration Management</h1>

      {/* Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Calibration Status</h2>
        <div className="space-y-2">
          <p>Last Calibration: {calibrationStatus.lastCalibration}</p>
          <p>Next Calibration: {calibrationStatus.nextCalibration}</p>
          <p>Status: <span className="text-green-600">{calibrationStatus.status}</span></p>
        </div>
      </div>

      {/* Manual Trigger */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Manual Calibration</h2>
        <p className="text-sm text-gray-600 mb-4">
          Trigger immediate calibration. Ensure room is empty during calibration.
        </p>
        <button
          onClick={triggerManualCalibration}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Start Calibration (5 minutes)
        </button>
      </div>

      {/* Schedule Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Schedule Configuration</h2>
        <p className="text-sm text-gray-600 mb-4">
          Configure automatic calibration schedule using cron expression.
        </p>
        <select
          className="border rounded px-3 py-2"
          defaultValue="0 3 * * *"
          onChange={(e) => updateSchedule(e.target.value)}
        >
          <option value="0 3 * * *">Daily at 3:00 AM</option>
          <option value="0 4 * * *">Daily at 4:00 AM</option>
          <option value="0 3 * * 0">Weekly (Sunday 3:00 AM)</option>
          <option value="">Disabled (Manual Only)</option>
        </select>
      </div>
    </div>
  )
}
```

### Notification System

**WebSocket Notifications:**
```python
# Notification during calibration
async def notify_calibration_start(room_id: str):
    """Notify users that calibration is starting"""
    await sio.emit('calibration_start', {
        'room_id': room_id,
        'message': 'Calibration started. Please leave the room empty.',
        'estimated_duration_minutes': 5
    }, room=room_id)

async def notify_calibration_progress(room_id: str, progress: int):
    """Send progress updates (0-100%)"""
    await sio.emit('calibration_progress', {
        'room_id': room_id,
        'progress': progress
    }, room=room_id)

async def notify_calibration_complete(room_id: str, baseline: dict):
    """Notify calibration completion"""
    await sio.emit('calibration_complete', {
        'room_id': room_id,
        'baseline': baseline,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
```

**Email Notifications (Optional):**
```python
# Send email if calibration fails
async def send_calibration_alert(room_id: str, error: str):
    """Send email alert for calibration failure"""
    await email_service.send(
        to=get_admin_emails(),
        subject=f"Calibration Failed: {room_id}",
        body=f"Calibration failed for room {room_id}. Error: {error}"
    )
```

---

## Calibration Frequency Tuning

### Adaptive Calibration (Future Enhancement)

**Detect Drift:**
```python
def detect_drift(current_detection: dict, baseline: dict) -> bool:
    """Detect if baseline has drifted"""
    z_score = (current_detection['rssi_mean'] - baseline['mean_rssi']) / baseline['std_rssi']

    # Threshold: >3 sigma indicates significant drift
    if abs(z_score) > 3:
        logger.warning(f"Baseline drift detected: z-score = {z_score:.2f}")
        return True
    return False

# Trigger recalibration if drift detected
if detect_drift(latest_detection, current_baseline):
    await run_calibration(room_id, duration_minutes=2)  # Quick recalibration
```

### Environment-Based Scheduling

**Smart Scheduling:**
```python
# Schedule calibration based on room usage patterns
async def smart_schedule():
    # Analyze historical occupancy data
    occupancy_pattern = await get_occupancy_pattern(room_id)

    # Find least occupied time (e.g., 3 AM on Sundays)
    optimal_time = find_least_occupied_hour(occupancy_pattern)

    # Update schedule
    await update_calibration_schedule(room_id, optimal_time)
```

---

## Success Criteria

- **Accuracy:** >98% detection accuracy after calibration
- **Consistency:** <5% variance in baseline statistics
- **Reliability:** >95% successful calibrations
- **User Disruption:** <1% of time (5 min/day = 0.35%)
- **Notification:** 100% of users notified before calibration
- **Data Quality:** SNR >15 dB, outliers <5%

---

## References

1. [RSSI Detection Research](https://arxiv.org/html/2308.06773v2)
2. System Architecture Document: `/docs/architecture/SYSTEM_ARCHITECTURE.md`

---

**Document End**

*This ADR will be reviewed if calibration success rate drops below 95% or if user feedback is negative.*
