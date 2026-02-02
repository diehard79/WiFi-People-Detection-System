# ADR-014: Error Handling & Resilience Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection System Reliability
**Decision:** Comprehensive Error Handling with Retry Policies, Circuit Breakers, and Graceful Degradation

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version | Technical Architect |

---

## Context

The WiFi-based people detection system operates in a complex, failure-prone environment:
- **Hardware Failures:** WiFi routers can malfunction, lose power, or become unreachable
- **Network Issues:** Intermittent connectivity, high latency, packet loss
- **ML Model Failures:** Prediction errors, model corruption, feature extraction failures
- **Database Errors:** Connection drops, query timeouts, transaction deadlocks
- **External Service Failures:** Cloud APIs unavailable, rate limits exceeded
- **Resource Exhaustion:** CPU/memory spikes, disk space exhaustion

**Reliability Requirements:**
- 99.5% uptime target
- <25 seconds end-to-end detection latency
- Graceful degradation when components fail
- No silent failures (all errors logged and visible)

---

## Decision

**Selected Strategy: Multi-Layered Resilience with Circuit Breakers, Retries, and Fallbacks**

### Error Handling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Try-Catch-Log Pattern (Python)                      │  │
│  │  ✓ Structured error logging                          │  │
│  │  ✓ Error context capture                             │  │
│  │  ✓ User-friendly error messages                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Retry Layer (tenacity library)                      │  │
│  │  ✓ Exponential backoff                               │  │
│  │  ✓ Jitter (thundering herd prevention)               │  │
│  │  ✓ Max retry attempts                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Circuit Breaker (pybreaker library)                 │  │
│  │  ✓ Open circuit after failures                       │  │
│  │  ✓ Half-open state (test recovery)                   │  │
│  │  ✓ Automatic close on recovery                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Fallback Layer                                      │  │
│  │  ✓ Local cache                                      │  │
│  │  ✓ Degraded mode operation                          │  │
│  │  ✓ Default values                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Error Categories & Handling Strategies

| Error Type | Impact | Handling Strategy | Fallback |
|------------|--------|-------------------|----------|
| **WiFi Router Offline** | No signal data | Retry + Circuit Breaker | Use last known state |
| **ML Prediction Failure** | No detection | Retry + Fallback model | Heuristic estimation |
| **Database Connection Lost** | Can't persist data | Retry + Exponential backoff | Local cache + sync later |
| **InfluxDB Write Failure** | Time-series data lost | Retry + Circuit breaker | Memory buffer |
| **Cloud API Unavailable** | No enhanced features | Circuit breaker | Edge-only mode |
| **Redis Cache Failure** | Performance degradation | Fail open | No caching |
| **WebSocket Disconnect** | No real-time updates | Auto-reconnect | Polling fallback |

### Retry Policy Design

**Retry Configuration:**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Retry policy for transient errors
@retry(
    stop=stop_after_attempt(3),  # Max 3 attempts
    wait=wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def collect_rssi_from_router(router_ip: str) -> dict:
    """Collect RSSI data from WiFi router with retry logic"""
    response = await httpx.AsyncClient().get(
        f"http://{router_ip}/api/rssi",
        timeout=5.0
    )
    response.raise_for_status()
    return response.json()

# Retry policy for database operations
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    retry=retry_if_exception_type((asyncpg.PostgresConnectionError,)),
)
async def write_detection_to_db(detection: dict):
    """Write detection to PostgreSQL with retry"""
    await db.execute(
        "INSERT INTO detections (room_id, count, timestamp) VALUES ($1, $2, $3)",
        detection["room_id"],
        detection["count"],
        detection["timestamp"]
    )
```

**Retry Strategy Rationale:**

| Component | Max Attempts | Backoff | Rationale |
|-----------|--------------|---------|-----------|
| **WiFi Router** | 3 | 1s, 2s, 4s | Router likely still offline after 3 attempts |
| **Database** | 5 | 0.5s, 1s, 2s, 4s, 8s | Connection pools recover quickly |
| **ML Inference** | 2 | 1s, 2s | Model errors usually persistent |
| **Cloud API** | 3 | 2s, 4s, 8s | Rate limits need time to reset |
| **InfluxDB** | 3 | 1s, 2s, 4s | Time-series writes often recover |

### Circuit Breaker Pattern

**Circuit Breaker Configuration:**

```python
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker for WiFi routers
wifi_router_breaker = CircuitBreaker(
    fail_max=5,  # Open circuit after 5 consecutive failures
    timeout_duration=60  # Try again after 60 seconds
)

# Circuit breaker for cloud APIs
cloud_api_breaker = CircuitBreaker(
    fail_max=10,
    timeout_duration=30
)

# Circuit breaker for database
database_breaker = CircuitBreaker(
    fail_max=3,
    timeout_duration=10
)

@wifi_router_breaker
async def fetch_router_data(router_ip: str) -> dict:
    """Fetch router data with circuit breaker protection"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{router_ip}/api/rssi",
                timeout=3.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Router {router_ip} failed: {e}")
        raise  # Triggers circuit breaker

# Usage with fallback
async def get_router_data_with_fallback(router_ip: str) -> dict:
    """Get router data with fallback to cached data"""
    try:
        return await fetch_router_data(router_ip)
    except CircuitBreakerError:
        logger.warning(f"Circuit open for {router_ip}, using cached data")
        return await get_cached_router_data(router_ip)
```

**Circuit Breaker States:**

```
CLOSED (Normal) → OPEN (Failure threshold reached) → HALF-OPEN (Testing recovery) → CLOSED
     ↑                                                                              ↓
     └──────────────────────────────────────────────────────────────────────────────┘
```

| State | Behavior | Transition |
|-------|----------|------------|
| **CLOSED** | Requests pass through normally | → OPEN after N failures |
| **OPEN** | Requests fail immediately (no actual call) | → HALF-OPEN after timeout |
| **HALF-OPEN** | Allow 1 test request | → CLOSED if success, OPEN if failure |

### Graceful Degradation

**Degradation Modes:**

```python
class DetectionService:
    """People detection service with graceful degradation"""

    def __init__(self):
        self.cloud_model = None  # High-accuracy cloud model
        self.local_model = None  # Fallback local model
        self.heuristic_model = None  # Last resort heuristic

    async def predict_count(self, features: np.ndarray) -> dict:
        """
        Predict people count with graceful degradation

        Degradation hierarchy:
        1. Cloud ML model (98% accuracy)
        2. Local ML model (95% accuracy)
        3. Heuristic estimation (85% accuracy)
        4. Last known state (cached value)
        """
        try:
            # Level 1: Cloud model (highest accuracy)
            prediction = await self._predict_with_cloud(features)
            return {
                "count": prediction,
                "accuracy": "high",
                "method": "cloud_model"
            }
        except CircuitBreakerError:
            logger.warning("Cloud model unavailable, degrading to local model")
        except Exception as e:
            logger.error(f"Cloud model failed: {e}, degrading to local model")

        try:
            # Level 2: Local model (good accuracy)
            prediction = self._predict_with_local(features)
            return {
                "count": prediction,
                "accuracy": "medium",
                "method": "local_model"
            }
        except Exception as e:
            logger.error(f"Local model failed: {e}, degrading to heuristic")

        try:
            # Level 3: Heuristic estimation (basic accuracy)
            prediction = self._predict_with_heuristic(features)
            return {
                "count": prediction,
                "accuracy": "low",
                "method": "heuristic"
            }
        except Exception as e:
            logger.error(f"Heuristic failed: {e}, using cached state")

        # Level 4: Last known state (no new detection)
        last_count = await self._get_last_known_count()
        return {
            "count": last_count,
            "accuracy": "cached",
            "method": "last_known_state"
        }

    async def _predict_with_cloud(self, features: np.ndarray) -> int:
        """High-accuracy cloud model prediction"""
        @cloud_api_breaker
        async def call_cloud_api():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{CLOUD_API_URL}/predict",
                    json={"features": features.tolist()},
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()["count"]

        return await call_cloud_api()

    def _predict_with_local(self, features: np.ndarray) -> int:
        """Local model prediction (edge device)"""
        if self.local_model is None:
            raise ValueError("Local model not loaded")

        prediction = self.local_model.predict(features.reshape(1, -1))[0]
        return int(prediction)

    def _predict_with_heuristic(self, features: np.ndarray) -> int:
        """
        Heuristic estimation based on RSSI variance

        Research finding: RSSI standard deviation correlates with people count
        """
        rssi_std = features[1]  # Index 1 = standard deviation

        # Simple heuristic (calibrated thresholds)
        if rssi_std < 1.0:
            return 0
        elif rssi_std < 2.0:
            return 1
        elif rssi_std < 3.5:
            return 2
        elif rssi_std < 5.0:
            return 3
        else:
            return min(int(rssi_std / 1.5), 10)  # Cap at 10

    async def _get_last_known_count(self) -> int:
        """Get last successful detection from cache"""
        cached = await redis.get("last_detection_count")
        if cached:
            return int(cached)
        return 0  # Default to 0 if no cache
```

### Specific Error Handling Scenarios

**Scenario 1: WiFi Router Offline**

```python
async def collect_rssi_with_fallback(detectors: list[str]) -> np.ndarray:
    """
    Collect RSSI from multiple detectors with individual fallback

    Strategy:
    - Collect from all available detectors
    - If detector offline, use last known values
    - If <50% detectors available, trigger alert
    """
    available_detectors = []
    missing_detectors = []

    for detector in detectors:
        try:
            rssi = await collect_rssi_from_router(detector)
            available_detectors.append(rssi)
        except (ConnectionError, TimeoutError, CircuitBreakerError) as e:
            logger.warning(f"Detector {detector} unavailable: {e}")
            missing_detectors.append(detector)

            # Use cached RSSI values
            cached_rssi = await redis.get(f"rssi_cache:{detector}")
            if cached_rssi:
                available_detectors.append(json.loads(cached_rssi))

    # Check if we have enough detectors
    availability_rate = len(available_detectors) / len(detectors)
    if availability_rate < 0.5:
        logger.error(f"Only {availability_rate:.0%} detectors available")
        await alerting.send_alert(
            severity="high",
            message=f"Detector availability dropped to {availability_rate:.0%}",
            room_id=current_room
        )

    return np.array(available_detectors)
```

**Scenario 2: Database Connection Lost**

```python
async def persist_detection_with_buffer(detection: dict):
    """
    Persist detection with local buffering if database unavailable

    Strategy:
    1. Try to write to PostgreSQL
    2. If fails, buffer in memory
    3. Periodically retry buffered writes
    4. Alert if buffer exceeds threshold
    """
    try:
        await write_detection_to_db(detection)

        # Also flush any buffered detections
        await flush_buffered_detections()

    except Exception as e:
        logger.error(f"Database write failed: {e}, buffering locally")

        # Add to in-memory buffer
        await redis.rpush("detection_buffer", json.dumps(detection))

        # Check buffer size
        buffer_size = await redis.llen("detection_buffer")
        if buffer_size > 1000:
            await alerting.send_alert(
                severity="critical",
                message=f"Detection buffer has {buffer_size} items",
                room_id=detection["room_id"]
            )

async def flush_buffered_detections():
    """Retry writing buffered detections"""
    buffer_size = await redis.llen("detection_buffer")

    if buffer_size == 0:
        return

    logger.info(f"Flushing {buffer_size} buffered detections")

    for _ in range(buffer_size):
        detection_json = await redis.lpop("detection_buffer")
        detection = json.loads(detection_json)

        try:
            await write_detection_to_db(detection)
        except Exception as e:
            # Put back in buffer if write fails
            await redis.lpush("detection_buffer", detection_json)
            break
```

**Scenario 3: ML Model Corruption**

```python
class MLModelManager:
    """Manage ML models with automatic fallback"""

    def __init__(self):
        self.primary_model = None
        self.backup_model = None

    async def load_models(self):
        """Load primary and backup models"""
        try:
            self.primary_model = joblib.load("models/counting_model_v2.pkl")
            logger.info("Primary model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load primary model: {e}")

        try:
            self.backup_model = joblib.load("models/counting_model_v1.pkl")
            logger.info("Backup model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load backup model: {e}")

    async def predict(self, features: np.ndarray) -> int:
        """Predict with model fallback"""
        # Try primary model
        if self.primary_model is not None:
            try:
                return self.primary_model.predict(features.reshape(1, -1))[0]
            except Exception as e:
                logger.error(f"Primary model prediction failed: {e}")

        # Fallback to backup model
        if self.backup_model is not None:
            try:
                return self.backup_model.predict(features.reshape(1, -1))[0]
            except Exception as e:
                logger.error(f"Backup model prediction failed: {e}")

        # Last resort: heuristic
        raise ModelUnavailableError("All models unavailable")
```

**Scenario 4: WebSocket Disconnection**

```python
class DetectionStreamer:
    """WebSocket streaming with auto-reconnect"""

    def __init__(self):
        self.ws_connections = {}
        self.reconnect_attempts = {}

    async def stream_detection(self, room_id: str, detection: dict):
        """Stream detection to all subscribed clients"""
        if room_id not in self.ws_connections:
            return  # No subscribers

        dead_connections = []

        for ws_id, websocket in self.ws_connections[room_id].items():
            try:
                await websocket.send_json({
                    "type": "detection",
                    "data": detection
                })
            except Exception as e:
                logger.warning(f"WebSocket {ws_id} send failed: {e}")
                dead_connections.append(ws_id)

        # Remove dead connections
        for ws_id in dead_connections:
            await self.remove_connection(room_id, ws_id)

    async def remove_connection(self, room_id: str, ws_id: str):
        """Remove failed WebSocket connection"""
        if room_id in self.ws_connections:
            self.ws_connections[room_id].pop(ws_id, None)

        # Attempt reconnection if client-side initiated
        await self.schedule_reconnect(room_id, ws_id)

    async def schedule_reconnect(self, room_id: str, ws_id: str):
        """Schedule reconnection with exponential backoff"""
        attempt = self.reconnect_attempts.get(ws_id, 0)
        backoff = min(2 ** attempt, 60)  # Max 60 seconds

        logger.info(f"Scheduling reconnect for {ws_id} in {backoff}s")

        await asyncio.sleep(backoff)

        # Notify client to reconnect
        await self.notify_reconnect(room_id, ws_id)

        self.reconnect_attempts[ws_id] = attempt + 1
```

---

## Consequences

### Positive Consequences

**Reliability:**
- Automatic recovery from transient failures
- Graceful degradation maintains service availability
- Circuit breakers prevent cascading failures
- Local buffering prevents data loss

**User Experience:**
- Continuous operation even during partial failures
- Clear communication of degraded mode
- No silent failures (all errors visible)
- Predictable behavior under stress

**Operational Excellence:**
- Detailed error logging for debugging
- Automated alerts for critical failures
- Metrics on error rates and recovery
- Easy to diagnose and fix issues

### Negative Consequences

**Complexity:**
- Multiple layers of error handling increase code complexity
- Testing all failure scenarios is challenging
- Circuit breaker state must be monitored
- Retry logic can mask persistent issues

**Performance:**
- Retries add latency (acceptable for transient failures)
- Circuit breakers add overhead (tracking state)
- Local buffering consumes memory
- Degraded modes provide lower accuracy

**Operational Overhead:**
- Must monitor circuit breaker states
- Alert fatigue if too many notifications
- Buffer flush monitoring required
- Recovery procedures must be documented

**Mitigation Strategies:**
```python
# 1. Structured error tracking
class ErrorTracker:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.last_error_time = {}

    def record_error(self, error_type: str, component: str):
        key = f"{component}:{error_type}"
        self.error_counts[key] += 1
        self.last_error_time[key] = datetime.now()

        # Alert if error rate exceeds threshold
        if self.error_counts[key] > 10:
            alerting.send_alert(
                severity="warning",
                message=f"Error rate for {key}: {self.error_counts[key]} errors"
            )

# 2. Health check integration
@app.get("/health/degraded")
async def health_check_degraded():
    """Health check that reports degraded mode"""
    status = {
        "status": "healthy",
        "components": {},
        "degraded_modes": []
    }

    # Check circuit breakers
    if wifi_router_breaker.current_state == "open":
        status["degraded_modes"].append("wifi_routers")
        status["components"]["wifi_routers"] = "unavailable"

    if cloud_api_breaker.current_state == "open":
        status["degraded_modes"].append("cloud_api")
        status["components"]["cloud_api"] = "unavailable"

    if status["degraded_modes"]:
        status["status"] = "degraded"

    return status
```

---

## Implementation Plan

### Phase 1: Core Error Handling (Week 1-2)

- Implement retry policies for external dependencies
- Add circuit breakers for WiFi routers and cloud APIs
- Create fallback mechanisms for ML predictions
- Add structured error logging

### Phase 2: Graceful Degradation (Week 2-3)

- Implement degraded mode detection service
- Add local buffering for database failures
- Create WebSocket reconnection logic
- Build health check endpoints

### Phase 3: Monitoring & Alerting (Week 3-4)

- Add error rate metrics (Prometheus)
- Create alerting rules for critical failures
- Build circuit breaker state monitoring
- Implement buffer size monitoring

### Phase 4: Testing & Validation (Week 4-5)

- Chaos engineering (inject failures)
- Test all degradation modes
- Validate recovery procedures
- Document runbook for common failures

---

## Success Criteria

- **Circuit Breaker Activation:** <5% of operational time
- **Retry Success Rate:** >80% of retries succeed
- **Degraded Mode Availability:** >99% uptime (even in degraded mode)
- **Error Detection:** 100% of errors logged and tracked
- **MTTR (Mean Time To Recovery):** <5 minutes for transient failures
- **Data Loss:** <0.1% (due to local buffering)
- **Alert Accuracy:** >95% (alerts correspond to real issues)

---

## References

1. [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
2. [Tenacity Retry Library](https://tenacity.readthedocs.io/)
3. [Pybreaker Library](https://pybreaker.readthedocs.io/)
4. ADR-006: Deployment Architecture (Hybrid deployment requirements)
5. ADR-002: Backend Programming Language (Python error handling)

---

**Document End**

*This ADR will be reviewed quarterly or if error rates indicate resilience issues.*
