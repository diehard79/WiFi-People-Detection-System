# ADR-015: Logging Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection System Observability
**Decision:** Structured JSON Logging with Python Standard Library and Log Rotation

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version | Technical Architect |

---

## Context

The WiFi-based people detection system requires comprehensive logging for:
- **Debugging:** Diagnose WiFi signal collection issues, ML model behavior
- **Audit Trail:** Track detection events, calibration runs, model updates
- **Performance Analysis:** Identify bottlenecks in signal processing, inference
- **Compliance:** GDPR requirements for privacy-preserving operation
- **Monitoring:** Feed into alerting and metrics systems

**Logging Challenges:**
- High-volume time-series RSSI data (potentially overwhelming)
- Privacy concerns (raw signal data could reveal location patterns)
- Multi-process architecture (signal collector, ML inference, API server)
- Distributed system (edge devices + cloud infrastructure)
- Log retention cost management

---

## Decision

**Selected Logging Framework: Python Standard Library (logging) + Structured JSON Output**

### Logging Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LOGGING                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Structured JSON Logging                             │  │
│  │  ✓ Consistent schema (timestamp, level, message)    │  │
│  │  ✓ Contextual fields (room_id, detector_id, ...)     │  │
│  │  ✓ Stack traces for exceptions                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Log Rotation (RotatingFileHandler)                  │  │
│  │  ✓ Size-based rotation (100MB per file)              │  │
│  │  ✓ Time-based rotation (daily)                       │  │
│  │  ✓ Retention policy (30 days)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Local Storage (/var/log/wifi-detection/)            │  │
│  │  ✓ application.log (all logs)                        │  │
│  │  ✓ errors.log (ERROR and CRITICAL only)              │  │
│  │  ✓ detections.log (detection events only)            │  │
│  │  ✓ performance.log (performance metrics)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼ (Optional)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  External Aggregation (Optional)                     │  │
│  │  ✓ Elasticsearch + Kibana                            │  │
│  │  ✓ CloudWatch Logs (AWS)                             │  │
│  │  ✓ Grafana Loki                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Log Level Strategy

| Log Level | Purpose | Examples | Volume |
|-----------|---------|----------|--------|
| **DEBUG** | Detailed diagnostic information | Raw RSSI values, feature arrays, ML internals | High (~80%) |
| **INFO** | Normal operation milestones | Detection events, calibration runs, model updates | Medium (~15%) |
| **WARNING** | Unexpected but recoverable issues | Detector offline, high latency, retries | Low (~4%) |
| **ERROR** | Errors affecting functionality | Prediction failures, database errors, API failures | Very Low (~0.9%) |
| **CRITICAL** | System-wide failures | All detectors offline, database down, model corruption | Rare (~0.1%) |

**Default Log Levels by Environment:**

| Environment | Console Level | File Level | Rationale |
|-------------|---------------|------------|-----------|
| **Development** | DEBUG | DEBUG | Full visibility for debugging |
| **Testing** | INFO | WARNING | Reduce noise in test logs |
| **Staging** | INFO | INFO | Monitor normal operation |
| **Production** | WARNING | INFO | Console minimal, file comprehensive |

### What to Log

**Event Logs (INFO level):**

```python
# Detection events
logger.info(
    "Detection completed",
    extra={
        "event_type": "detection",
        "room_id": "conference-a",
        "count": 3,
        "confidence": 0.97,
        "latency_ms": 8,
        "model_version": "v2.1.0"
    }
)

# Calibration events
logger.info(
    "Calibration completed",
    extra={
        "event_type": "calibration",
        "room_id": "conference-a",
        "duration_seconds": 300,
        "samples_collected": 1500,
        "accuracy_improvement": 0.02
    }
)

# Model update events
logger.info(
    "Model deployed",
    extra={
        "event_type": "model_deployment",
        "model_version": "v2.2.0",
        "previous_version": "v2.1.0",
        "accuracy": 0.98,
        "deployment_duration_seconds": 45
    }
)

# System events
logger.info(
    "Service started",
    extra={
        "event_type": "system_startup",
        "service": "ml_inference",
        "port": 8001,
        "model_loaded": True
    }
)
```

**Error Logs (ERROR level):**

```python
# WiFi detector failures
logger.error(
    "Detector unreachable",
    extra={
        "error_type": "detector_unreachable",
        "detector_id": "router-01",
        "room_id": "conference-a",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "attempt": 3,
        "circuit_breaker_state": "open"
    },
    exc_info=True  # Include stack trace
)

# ML prediction failures
logger.error(
    "ML prediction failed",
    extra={
        "error_type": "ml_prediction_failure",
        "model_version": "v2.1.0",
        "feature_shape": "(20,)",
        "fallback_used": "local_model",
        "confidence": 0.0
    },
    exc_info=True
)

# Database failures
logger.error(
    "Database write failed",
    extra={
        "error_type": "database_write_failure",
        "table": "detections",
        "operation": "INSERT",
        "retry_attempt": 2,
        "buffer_size": 45
    },
    exc_info=True
)
```

**Performance Logs (INFO level with performance metrics):**

```python
# Signal processing performance
logger.info(
    "Signal processing completed",
    extra={
        "event_type": "performance",
        "operation": "signal_processing",
        "room_id": "conference-a",
        "duration_ms": 15,
        "samples_processed": 20,
        "detectors": 5,
        "throughput_samples_per_sec": 1333
    }
)

# ML inference performance
logger.info(
    "ML inference completed",
    extra={
        "event_type": "performance",
        "operation": "ml_inference",
        "model_version": "v2.1.0",
        "duration_ms": 8,
        "feature_count": 20,
        "prediction": 3
    }
)
```

### What NOT to Log (Privacy & Volume)

**Excluded for Privacy:**

```python
# ❌ DON'T LOG: Raw RSSI time-series data (too detailed)
# logger.debug(f"Raw RSSI: {rssi_window}")  # 20 samples × 5 detectors = 100 data points

# ✅ DO LOG: Aggregated statistics
logger.debug(
    "RSSI statistics",
    extra={
        "room_id": room_id,
        "rssi_mean": float(np.mean(rssi_window)),
        "rssi_std": float(np.std(rssi_window)),
        "rssi_min": float(np.min(rssi_window)),
        "rssi_max": float(np.max(rssi_window)),
        "sample_count": len(rssi_window)
    }
)

# ❌ DON'T LOG: User personal information
# logger.info(f"User {user_name} accessed room {room_id}")

# ✅ DO LOG: User action (anonymized)
logger.info(
    "Room accessed",
    extra={
        "event_type": "room_access",
        "room_id": room_id,
        "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:16],  # Anonymized
        "timestamp": datetime.now().isoformat()
    }
)

# ❌ DON'T LOG: Exact device MAC addresses (GDPR concern)
# logger.info(f"Detector MAC: {mac_address}")

# ✅ DO LOG: Detector ID (non-identifiable)
logger.info(
    "Detector activated",
    extra={
        "detector_id": "router-01",  # mapped, not raw MAC
        "room_id": "conference-a"
    }
)
```

**Excluded for Volume:**

```python
# ❌ DON'T LOG: Every single RSSI sample (1 Hz × 5 detectors = 5 samples/second)
# Each sample logged would be 500KB per day per room

# ✅ DO LOG: Aggregated windows (every 20 seconds)
# Only 4,320 log entries per day per room

# ❌ DON'T LOG: Heartbeat messages every second
# logger.debug("Heartbeat")  # Too noisy

# ✅ DO LOG: Heartbeat every 60 seconds with status
logger.info(
    "Service heartbeat",
    extra={
        "event_type": "heartbeat",
        "uptime_seconds": uptime,
        "detectors_online": 4,
        "detectors_total": 5,
        "memory_usage_mb": memory_usage
    }
)
```

### Structured Logging Implementation

**Python Logging Configuration:**

```python
# src/logging_config.py
import logging
import logging.config
import json
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields from `extra` parameter
        if hasattr(record, "room_id"):
            log_data["room_id"] = record.room_id
        if hasattr(record, "detector_id"):
            log_data["detector_id"] = record.detector_id

        # Add all extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(
    environment: str = "production",
    log_dir: Path = Path("/var/log/wifi-detection")
):
    """Configure structured logging for the application"""

    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine log levels
    if environment == "development":
        console_level = logging.DEBUG
        file_level = logging.DEBUG
    elif environment == "testing":
        console_level = logging.INFO
        file_level = logging.WARNING
    elif environment == "staging":
        console_level = logging.INFO
        file_level = logging.INFO
    else:  # production
        console_level = logging.WARNING
        file_level = logging.INFO

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "src.logging_config.JSONFormatter"
            },
            "console": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_level,
                "formatter": "console",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": file_level,
                "formatter": "json",
                "filename": str(log_dir / "application.log"),
                "maxBytes": 100 * 1024 * 1024,  # 100MB
                "backupCount": 30,  # 30 days retention
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "json",
                "filename": str(log_dir / "errors.log"),
                "maxBytes": 100 * 1024 * 1024,
                "backupCount": 90,  # 90 days retention for errors
                "encoding": "utf-8"
            },
            "detection_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.INFO,
                "formatter": "json",
                "filename": str(log_dir / "detections.log"),
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 30,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": logging.DEBUG,
                "handlers": ["console", "file", "error_file"]
            },
            "detection_events": {
                "level": logging.INFO,
                "handlers": ["detection_file"],
                "propagate": False
            }
        }
    })

# Usage in application
# src/main.py
from src.logging_config import setup_logging
import logging

setup_logging(environment="production")
logger = logging.getLogger(__name__)

# Log with context
detection_logger = logging.getLogger("detection_events")
detection_logger.info(
    "Detection completed",
    extra={
        "room_id": "conference-a",
        "count": 3,
        "confidence": 0.97
    }
)
```

### Log Retention Strategy

**Retention Policy:**

| Log File | Retention | Max Size | Rationale |
|----------|-----------|----------|-----------|
| **application.log** | 30 days | 3GB (30 × 100MB) | Recent operational history |
| **errors.log** | 90 days | 9GB (90 × 100MB) | Extended retention for debugging |
| **detections.log** | 30 days | 1.5GB (30 × 50MB) | Audit trail for compliance |
| **performance.log** | 7 days | 500MB | Short-term performance analysis |

**Storage Costs (Edge Device - 64GB SD Card):**

```
Total Log Storage: ~14GB for 90-day retention
SD Card Capacity: 64GB
Log Usage: 22% of capacity
Available for other data: 50GB
```

**Log Rotation:**

```python
# Automatic rotation with RotatingFileHandler
# When file reaches 100MB:
#   application.log → application.log.1
#   application.log.1 → application.log.2
#   ...
#   application.log.30 → deleted (after 30 days)

# Time-based rotation (alternative)
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    filename="application.log",
    when="midnight",  # Rotate daily
    interval=1,
    backupCount=30  # Keep 30 days
)
```

### Log Aggregation (Optional)

**Option 1: Elasticsearch + Kibana**

```yaml
# docker-compose.yml for log aggregation
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

  filebeat:
    image: elastic/filebeat:8.11.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log/wifi-detection:/var/log/wifi-detection:ro
    depends_on:
      - elasticsearch
```

**Option 2: Grafana Loki (Lighter Alternative)**

```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log/wifi-detection:/var/log/wifi-detection:ro
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
```

**Option 3: CloudWatch Logs (AWS)**

```python
# CloudWatch log forwarding
import boto3

cloudwatch_client = boto3.client('logs', region_name='us-east-1')

def forward_to_cloudwatch(log_group: str, log_stream: str, log_events: list):
    """Forward log events to AWS CloudWatch"""
    cloudwatch_client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=log_events
    )

# Usage: Periodically batch upload logs
async def cloudwatch_forwarder():
    while True:
        logs = read_recent_logs()
        await forward_to_cloudwatch("wifi-detection/prod", "edge-device-01", logs)
        await asyncio.sleep(60)  # Upload every 60 seconds
```

---

## Consequences

### Positive Consequences

**Debugging:**
- Structured logs enable fast query and filtering
- JSON format parsed by log aggregators
- Contextual fields (room_id, detector_id) simplify troubleshooting
- Stack traces aid error diagnosis

**Compliance:**
- Detection event log provides audit trail
- Privacy-preserving by design (no raw RSSI data)
- Retention policy meets GDPR requirements
- Anonymized user data

**Monitoring:**
- Logs feed into alerting systems
- Performance metrics identify bottlenecks
- Error rates tracked over time
- Operational dashboards powered by logs

**Operational Excellence:**
- Centralized logging (optional aggregation)
- Log rotation prevents disk exhaustion
- Consistent format across services
- Easy to search and visualize

### Negative Consequences

**Storage Costs:**
- Logs consume disk space (14GB for 90-day retention)
- SD card wear leveling concerns (frequent writes)
- Backup costs for centralized log storage
- Network bandwidth for log forwarding

**Performance:**
- Synchronous logging adds latency (~1ms per log)
- High-volume DEBUG logging can impact performance
- Disk I/O contention with other services
- Log aggregation CPU overhead

**Complexity:**
- Multiple log files to manage
- Log rotation configuration
- Retention policy enforcement
- Optional log aggregation setup

**Mitigation Strategies:**
```python
# 1. Asynchronous logging
import queue
import logging.handlers

log_queue = queue.Queue(-1)  # Unlimited queue
queue_handler = logging.handlers.QueueHandler(log_queue)
logger.addHandler(queue_handler)

# Separate thread for writing logs
import threading
queue_listener = logging.handlers.QueueListener(log_queue, file_handler)
queue_listener.start()

# 2. Conditional DEBUG logging
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_data = compute_expensive_debug_data()
    logger.debug(f"Debug data: {expensive_debug_data}")

# 3. Log sampling (reduce volume)
import random

if random.random() < 0.1:  # Log 10% of DEBUG events
    logger.debug("Sampled debug event")

# 4. Rate limit repetitive logs
from collections import defaultdict

last_log_time = defaultdict(float)

def rate_limit_log(logger, level, msg, key, interval_seconds=60):
    now = time.time()
    if now - last_log_time[key] >= interval_seconds:
        logger.log(level, msg)
        last_log_time[key] = now
```

---

## Implementation Plan

### Phase 1: Basic Logging (Week 1)

- Set up JSON structured logging
- Configure log rotation (size-based)
- Add logging to all services
- Define log levels by environment

### Phase 2: Enhanced Logging (Week 2)

- Add contextual fields (room_id, detector_id)
- Implement separate log files (errors, detections)
- Add performance logging
- Create log query examples

### Phase 3: Privacy & Optimization (Week 2-3)

- Remove raw RSSI data from logs
- Add user ID anonymization
- Implement log sampling for DEBUG
- Add rate limiting for repetitive logs

### Phase 4: Optional Aggregation (Week 3-4)

- Set up Elasticsearch + Kibana (or Loki)
- Configure Filebeat/Promtail
- Create Kibana dashboards
- Set up log retention policies

---

## Success Criteria

- **Log Coverage:** 100% of services log to structured format
- **Error Logging:** 100% of errors logged with stack traces
- **Performance Impact:** <2% overhead from logging
- **Query Performance:** <1 second to search 30 days of logs
- **Retention:** 90 days for errors, 30 days for other logs
- **Privacy:** Zero raw RSSI data or personal information in logs
- **Log Availability:** >99.9% (logging failures are rare)

---

## References

1. [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
2. [Structured Logging Best Practices](https://brandur.org/structured-logs)
3. [GDPR Compliance Guidelines](https://gdpr.eu/)
4. ADR-009: Privacy-Preserving Techniques
5. ADR-012: Monitoring & Alerting Strategy

---

**Document End**

*This ADR will be reviewed quarterly or if storage costs/privacy concerns arise.*
