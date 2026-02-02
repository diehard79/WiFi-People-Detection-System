# ADR-012: Monitoring and Alerting Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** Comprehensive System Monitoring, Alerting, and Observability
**Decision:** Prometheus + Grafana Stack with AlertManager and Loki Logging

---

## Context

The WiFi-based people detection system requires comprehensive monitoring to ensure:
- **System Reliability:** 99.9% uptime requirement
- **Performance:** Detect latency spikes, resource exhaustion
- **Accuracy:** ML model performance degradation detection
- **Security:** Intrusion detection, anomaly detection
- **Operational Excellence:** Proactive issue resolution

**Monitoring Challenges:**
- **Distributed System:** Edge devices + cloud infrastructure
- **Real-Time Requirements:** Sub-second detection latency
- **ML Model Drift:** Accuracy degradation over time
- **Network Dependency:** Edge-to-cloud connectivity issues

---

## Decision

**Selected Stack: Prometheus + Grafana + AlertManager + Loki**

### Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  MONITORING INFRASTRUCTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DATA SOURCES → METRICS COLLECTION → STORAGE → VISUALIZATION │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Edge Devices (Raspberry Pi)                         │  │
│  │  ├─ Prometheus Node Exporter (system metrics)        │  │
│  │  ├─ Custom Python Exporter (app metrics)             │  │
│  │  └─ Push Gateway (push metrics to cloud)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Services (Kubernetes)                         │  │
│  │  ├─ Backend Pods (FastAPI)                           │  │
│  │  │   └─ Prometheus Python Client                     │  │
│  │  ├─ Frontend (Next.js)                               │  │
│  │  │   └─ Custom metrics export                        │  │
│  │  ├─ Databases (InfluxDB, PostgreSQL, Redis)          │  │
│  │  │   └─ Database exporters                           │  │
│  │  └─ Kubernetes                                       │  │
│  │      └─ cAdvisor (container metrics)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prometheus Server (Metrics Storage)                 │  │
│  │  ├─ Scrape interval: 15s                             │  │
│  │  ├─ Retention: 30 days raw, 1 year downsampled      │  │
│  │  └─ HA: Prometheus + Thanos (long-term storage)      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AlertManager                                        │  │
│  │  ├─ Alert routing (severity-based)                  │  │
│  │  ├─ Grouping (deduplicate alerts)                   │  │
│  │  ├─ Silencing (maintenance windows)                 │  │
│  │  └─ Notification channels                           │  │
│  │      ├─ PagerDuty (critical)                        │  │
│  │      ├─ Slack (warnings)                            │  │
│  │      ├─ Email (info)                                │  │
│  │      └─ Webhook (custom integrations)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Grafana (Visualization)                             │  │
│  │  ├─ Pre-built dashboards (15+)                      │  │
│  │  ├─ Alert annotations (link to runbooks)            │  │
│  │  └─ User permissions (RBAC)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Loki (Log Aggregation)                              │  │
│  │  ├─ Promtail (log collector)                        │  │
│  │  ├─ Full-text search                                │  │
│  │  └─ Log retention: 30 days                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Monitoring Stack Comparison

| Stack | Pros | Cons | Scalability | Query Language | Best For |
|-------|------|------|-------------|----------------|----------|
| **Prometheus + Grafana** | Industry standard, powerful query language, cloud-native | Longer learning curve for PromQL | Excellent ✅ | PromQL | Metrics |
| Datadog | All-in-one, excellent UI | Very expensive, vendor lock-in | Excellent ✅ | Custom | Small teams |
| New Relic | Easy setup, good APM | Expensive, limited customization | Good ⚠️ | Custom | APM focus |
| ELK Stack | Logs + metrics, flexible | Complex setup, resource-intensive | Good ⚠️ | Lucene | Log analysis |
| CloudWatch | Native AWS integration | AWS-specific, expensive | Good ⚠️ | Custom | AWS-only |

**Selected: Prometheus + Grafana**
- ✅ Industry standard (largest monitoring community)
- ✅ Cloud-native (Kubernetes integration)
- ✅ Cost-effective (open-source, self-hosted)
- ✅ Powerful query language (PromQL)
- ✅ Excellent visualization (Grafana)
- ✅ Flexible alerting (AlertManager)
- ✅ Long-term storage (Thanos, Cortex)

---

## Key Metrics to Monitor

### System Metrics

**1. Infrastructure Metrics:**
```yaml
# CPU, Memory, Disk, Network
node_cpu_seconds_total
node_memory_MemAvailable_bytes
node_filesystem_avail_bytes
node_network_receive_bytes_total
```

**2. Kubernetes Metrics:**
```yaml
# Pod/Container resources
kube_pod_container_status_ready
container_cpu_usage_seconds_total
container_memory_working_set_bytes
```

**3. Application Metrics:**
```yaml
# Backend (FastAPI)
http_requests_total{method, path, status}
http_request_duration_seconds{method, path}
websocket_connections_active
ml_predictions_total{model_type, result}
ml_prediction_duration_seconds{model_type}
```

**4. Database Metrics:**
```yaml
# PostgreSQL
pg_stat_database_blks_hit
pg_stat_database_blks_read
pg_stat_activity_count

# InfluxDB
influxdb_query_duration_seconds
influxdb_write_duration_seconds

# Redis
redis_commands_processed_total
redis_memory_used_bytes
```

### Business Metrics

**1. ML Model Performance:**
```yaml
# Accuracy metrics
ml_detection_accuracy{room_id}
ml_detection_confidence{room_id}
ml_false_positive_rate{room_id}
ml_false_negative_rate{room_id}

# Drift detection
ml_baseline_drift_detected{room_id}
ml_calibration_age_hours{room_id}
```

**2. Device Health:**
```yaml
# Edge device connectivity
edge_device_last_seen_seconds{device_id}
edge_device_uptime_seconds{device_id}
edge_device_rssi_signal_strength{device_id}
```

**3. Business KPIs:**
```yaml
# Detection metrics
detections_total{room_id, result}
detection_latency_seconds{room_id}
people_count_average{room_id}
room_occupancy_percentage{room_id}
```

---

## Alert Rules

### Critical Alerts (PagerDuty + Phone Call)

**1. Service Down:**
```yaml
- alert: ServiceDown
  expr: up{job="wifi-detection-backend"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.job }} is down"
    description: "{{ $labels.instance }} has been down for more than 1 minute."
```

**2. High Error Rate:**
```yaml
- alert: HighErrorRate
  expr: |
    (
      sum(rate(http_requests_total{status=~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
    ) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes."
```

**3. ML Model Accuracy Drop:**
```yaml
- alert: ModelAccuracyDrop
  expr: |
    ml_detection_accuracy < 0.90
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "ML model accuracy below 90%"
    description: "Room {{ $labels.room_id }} accuracy is {{ $value | humanizePercentage }}"
```

### Warning Alerts (Slack + Email)

**4. High CPU Usage:**
```yaml
- alert: HighCPUUsage
  expr: |
    (
      sum(rate(container_cpu_usage_seconds_total{container="wifi-detection-backend"}[5m]))
      by (pod)
      /
      sum(kube_pod_container_resource_limits{resource="cpu", container="wifi-detection-backend"})
      by (pod)
    ) > 0.8
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage on {{ $labels.pod }}"
    description: "CPU usage is {{ $value | humanizePercentage }} for the last 10 minutes."
```

**5. Disk Space Low:**
```yaml
- alert: DiskSpaceLow
  expr: |
    (
      node_filesystem_avail_bytes{mountpoint="/"}
      /
      node_filesystem_size_bytes{mountpoint="/"}
    ) < 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Disk space low on {{ $labels.instance }}"
    description: "Only {{ $value | humanizePercentage }} disk space available."
```

**6. Database Connection Pool Exhausted:**
```yaml
- alert: DatabasePoolExhausted
  expr: |
    pg_stat_activity_count / pg_settings_max_connections > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Database connection pool nearly exhausted"
    description: "{{ $value | humanizePercentage }} of connections used."
```

### Info Alerts (Email Only)

**7. SSL Certificate Expiring:**
```yaml
- alert: SSLCertificateExpiring
  expr: |
    (ssl_cert_not_after - time()) < 86400 * 30
  labels:
    severity: info
  annotations:
    summary: "SSL certificate expiring in less than 30 days"
```

---

## Dashboards

### Pre-Built Grafana Dashboards

**1. System Overview Dashboard:**
- Service health (up/down)
- Request rate (RPS)
- Error rate (%)
- Latency (P50, P95, P99)
- Active WebSocket connections

**2. Infrastructure Dashboard:**
- CPU usage (per pod)
- Memory usage (per pod)
- Network I/O
- Disk I/O
- Container restarts

**3. ML Model Performance Dashboard:**
- Detection accuracy (per room)
- Confidence distribution
- False positive/negative rates
- Calibration status
- Baseline drift alerts

**4. Database Dashboard:**
- Connection pool usage
- Query latency (P95)
- Slow query log
- Replication lag
- Disk usage

**5. Edge Device Dashboard:**
- Device online/offline status
- Signal strength (RSSI)
- Uptime percentage
- Firmware version
- Battery level (if applicable)

**6. Business KPI Dashboard:**
- People count trends (per room)
- Occupancy heatmaps
- Peak usage hours
- Detection latency trends
- Alert frequency

---

## Implementation

### Prometheus Configuration

**`prometheus.yml`:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'wifi-detection-production'
    replica: 'prometheus-1'

# AlertManager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules once
rule_files:
  - '/etc/prometheus/rules/*.yml'

# Scrape configurations
scrape_configs:
  # Backend services
  - job_name: 'wifi-detection-backend'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: [production]
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: wifi-detection-backend
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: $1:8000

  # Kubernetes nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        target_label: __address__
        replacement: '$1:9100'

  # PostgreSQL exporter
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis exporter
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  # InfluxDB exporter
  - job_name: 'influxdb-exporter'
    static_configs:
      - targets: ['influxdb:8086']
```

### Application Metrics (Python)

**`src/metrics.py`:**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import functools

# HTTP metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# ML metrics
ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model_type', 'result']
)

ml_prediction_duration = Histogram(
    'ml_prediction_duration_seconds',
    'ML prediction latency',
    ['model_type']
)

ml_detection_accuracy = Gauge(
    'ml_detection_accuracy',
    'Detection accuracy (rolling window)',
    ['room_id']
)

# WebSocket metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type', 'table']
)

# Decorator for HTTP endpoint metrics
def track_http_endpoint(method: str, endpoint: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "200"

            try:
                result = await func(*args, **kwargs)
                return result
            except HTTPException as e:
                status = str(e.status_code)
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

        return wrapper
    return decorator

# Start metrics server on startup
def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")
```

---

## Success Criteria

- **Visibility:** 100% of services instrumented with metrics
- **Alert Coverage:** All critical failure modes have alerts
- **MTTD (Mean Time To Detect):** <5 minutes for critical issues
- **MTTR (Mean Time To Recover):** <15 minutes (automated rollback)
- **False Positive Rate:** <5% of alerts are false positives
- **Dashboard Usability:** All dashboards load <3 seconds
- **Log Retention:** 30 days searchable, 1 year archive
- **Metrics Retention:** 30 days raw, 1 year aggregated (5-minute)

---

## References

1. [Prometheus Best Practices](https://prometheus.io/docs/practices/)
2. [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
3. [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
4. ADR-002: Backend Programming Language (Python metrics)
5. ADR-006: Deployment Architecture (Infrastructure monitoring)

---

**Document End**

*This ADR will be reviewed if MTTD exceeds 5 minutes or if false positive rate exceeds 5%.*
