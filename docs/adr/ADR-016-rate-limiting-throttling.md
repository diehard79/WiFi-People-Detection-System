# ADR-016: Rate Limiting & Throttling Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection System API Protection
**Decision:** Multi-Layer Rate Limiting with slowapi and Application-Level Throttling

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version | Technical Architect |

---

## Context

The WiFi-based people detection system exposes public APIs and WebSocket connections that require protection against:
- **API Abuse:** Excessive requests from malicious or misconfigured clients
- **Resource Exhaustion:** CPU/memory saturation from heavy load
- **Database Overload:** Too many queries causing performance degradation
- **WebSocket Spam:** Excessive message flooding
- **Cost Control:** Cloud API usage (e.g., OpenAI integration) must be bounded

**Protection Requirements:**
- Fair resource allocation among users
- Prevention of denial-of-service (DoS) attacks
- Graceful degradation under load
- Clear error messages when limits exceeded
- Configurable limits per endpoint/resource

---

## Decision

**Selected Framework: slowapi (FastAPI rate limiting) + Application-Level Throttling**

### Rate Limiting Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RATE LIMITING LAYERS                      │
│                                                               │
│  Layer 1: Global Rate Limit (IP-based)                       │
│  ├─ 100 req/min per IP (prevent abuse)                      │
│  └─ Applied at nginx/reverse proxy level                    │
│                         │                                    │
│                         ▼                                    │
│  Layer 2: API Endpoint Rate Limit (slowapi)                  │
│  ├─ Per-user rate limits (authenticated)                    │
│  ├─ Per-endpoint limits (resource-specific)                 │
│  └─ Applied at FastAPI middleware level                     │
│                         │                                    │
│                         ▼                                    │
│  Layer 3: Application-Level Throttling                       │
│  ├─ Database query throttling                               │
│  ├─ ML inference throttling                                 │
│  ├─ WebSocket message throttling                            │
│  └─ Applied at service level                                │
│                         │                                    │
│                         ▼                                    │
│  Layer 4: Cloud API Rate Limiting                           │
│  ├─ External service limits (e.g., OpenAI)                  │
│  └─ Token bucket algorithm                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### Rate Limiting Strategy

**Framework Selection: slowapi**

| Feature | slowapi | flask-limiter | fastapi-limiter |
|---------|---------|---------------|-----------------|
| **FastAPI Integration** | Native ✅ | Requires adaptation ✅ | Native ✅ |
| **Storage Backends** | Redis, Memcached, Memory ✅ | Redis, Memory ✅ | Redis ✅ |
| **Decorator Syntax** | @limiter.limit ✅ | @limiter.limit ✅ | @limit ✅ |
| **WebSocket Support** | Yes ✅ | No ❌ | No ❌ |
| **Cloud Support** | Redis ✅ | Redis ✅ | Redis ✅ |
| **Documentation** | Good ✅ | Good ✅ | Basic ⚠️ |

**slowapi Advantages:**
```python
# Simple, intuitive API
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/detection/predict")
@limiter.limit("10/minute")  # 10 requests per minute
async def predict_detection(request: Request):
    ...

# Per-user limits
@app.get("/api/v1/detection/history")
@limiter.limit("60/minute", key_func=lambda r: r.headers.get("X-User-ID"))
async def get_detection_history(request: Request):
    ...

# Multiple limits
@app.post("/api/v1/calibration/start")
@limiter.limit("5/hour;1/minute")  # 5 per hour, max 1 per minute
async def start_calibration(request: Request):
    ...
```

### Rate Limit Configuration

**Endpoint-Specific Limits:**

| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| **POST /api/v1/detection/predict** | 60/min | Real-time detection (1 per second max) |
| **GET /api/v1/detection/current** | 120/min | Polling endpoint (2 per second max) |
| **GET /api/v1/detection/history** | 30/min | Expensive query (historical data) |
| **POST /api/v1/calibration/start** | 5/hour | Resource-intensive operation |
| **WebSocket /ws/detection/{room_id}** | 10 messages/sec | Prevent message flooding |
| **ML Inference (local)** | 100 req/sec | CPU protection |
| **Database Queries** | 1000 queries/sec | Database protection |

**Implementation Example:**

```python
# src/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
import redis

# Redis-backed rate limiter (for distributed systems)
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["200/hour"]  # Default limit for all endpoints
)

# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom error message for rate limit exceeded"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after  # Seconds until retry allowed
        }
    )

# Apply to endpoints
from src.rate_limit import limiter

@app.post("/api/v1/detection/predict")
@limiter.limit("60/minute")  # 60 predictions per minute
async def predict_detection(
    request: Request,
    prediction_request: PredictionRequest
):
    """Predict people count with rate limiting"""
    features = prediction_request.features
    prediction = model.predict(features)

    return {
        "count": int(prediction),
        "confidence": float(model.predict_proba(features).max())
    }

@app.get("/api/v1/detection/history")
@limiter.limit("30/minute")  # 30 history requests per minute
async def get_detection_history(
    request: Request,
    room_id: str,
    hours: int = 24
):
    """Get detection history with rate limiting"""
    history = await db.fetch_detections(room_id, hours)
    return {"detections": history}

# Multiple limits (calibration is expensive)
@app.post("/api/v1/calibration/start")
@limiter.limit("5/hour;1/minute")  # 5 per hour, max 1 per minute
async def start_calibration(request: Request, calibration_request: CalibrationRequest):
    """Start calibration with strict rate limiting"""
    calibration_id = await calibration_service.start(
        calibration_request.room_id
    )
    return {"calibration_id": calibration_id}
```

### WebSocket Rate Limiting

**WebSocket Message Throttling:**

```python
# src/websocket_rate_limit.py
from collections import defaultdict
import time
import asyncio

class WebSocketRateLimiter:
    """Rate limiter for WebSocket messages"""

    def __init__(self, max_messages: int = 10, window_seconds: int = 1):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_counts = defaultdict(list)

    async def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded message rate limit

        Returns True if allowed, False if rate limited
        """
        now = time.time()
        client_history = self.message_counts[client_id]

        # Remove old messages outside window
        client_history[:] = [
            timestamp for timestamp in client_history
            if now - timestamp < self.window_seconds
        ]

        # Check if limit exceeded
        if len(client_history) >= self.max_messages:
            return False

        # Add current message
        client_history.append(now)
        return True

# WebSocket endpoint with rate limiting
ws_rate_limiter = WebSocketRateLimiter(max_messages=10, window_seconds=1)

@app.websocket("/ws/detection/{room_id}")
async def detection_websocket(websocket: WebSocket, room_id: str):
    """WebSocket detection streaming with rate limiting"""
    await websocket.accept()
    client_id = f"{room_id}:{id(websocket)}"

    try:
        while True:
            # Receive message from client
            message = await websocket.receive_json()

            # Rate limit incoming messages
            if not await ws_rate_limiter.check_rate_limit(client_id):
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded. Slow down."
                })
                continue

            # Process message
            if message["action"] == "subscribe":
                await subscribe_to_detection(websocket, room_id)
            elif message["action"] == "unsubscribe":
                await unsubscribe_from_detection(websocket, room_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
```

### Database Query Throttling

**Query Rate Limiting:**

```python
# src/database_throttle.py
import asyncio
from collections import deque

class DatabaseThrottler:
    """Throttle database queries to prevent overload"""

    def __init__(self, max_queries_per_second: int = 1000):
        self.max_queries_per_second = max_queries_per_second
        self.query_times = deque()

    async def throttle_query(self):
        """Wait if query rate exceeds limit"""
        now = time.time()

        # Remove old query timestamps (>1 second ago)
        while self.query_times and now - self.query_times[0] > 1.0:
            self.query_times.popleft()

        # Check if rate limit exceeded
        if len(self.query_times) >= self.max_queries_per_second:
            # Calculate wait time
            sleep_time = 1.0 - (now - self.query_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # Record query time
        self.query_times.append(time.time())

# Usage in database operations
db_throttler = DatabaseThrottler(max_queries_per_second=1000)

async def fetch_detections(room_id: str, hours: int):
    """Fetch detections with throttling"""
    await db_throttler.throttle_query()

    query = """
        SELECT * FROM detections
        WHERE room_id = $1 AND timestamp > NOW() - INTERVAL '$2 hours'
        ORDER BY timestamp DESC
    """
    return await db.fetch(query, room_id, hours)
```

### ML Inference Throttling

**CPU Protection via Throttling:**

```python
# src/ml_throttle.py
import asyncio
from threading import Semaphore

class MLInferenceThrottler:
    """Throttle ML inference to prevent CPU exhaustion"""

    def __init__(self, max_concurrent: int = 4):
        self.semaphore = Semaphore(max_concurrent)

    async def infer(self, model, features: np.ndarray) -> int:
        """Run ML inference with concurrency limit"""
        with self.semaphore:
            # Run inference in thread pool (CPU-bound)
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None,  # Default executor
                model.predict,
                features.reshape(1, -1)
            )
            return int(prediction[0])

# Global inference throttler
inference_throttler = MLInferenceThrottler(max_concurrent=4)

# Usage in API endpoint
@app.post("/api/v1/detection/predict")
@limiter.limit("60/minute")
async def predict_detection(request: Request, prediction_request: PredictionRequest):
    """Predict with ML inference throttling"""
    features = np.array(prediction_request.features)

    # Throttled inference
    prediction = await inference_throttler.infer(model, features)

    return {"count": prediction, "confidence": 0.97}
```

### Cloud API Rate Limiting

**External Service Protection (Token Bucket):**

```python
# src/cloud_api_throttle.py
import time
from collections import deque

class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, rate: int, capacity: int):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens (bucket size)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens if available

        Returns True if tokens consumed, False if insufficient tokens
        """
        now = time.time()

        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        # Check if enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# Cloud API rate limiter (e.g., OpenAI API: 3500 requests per minute)
openai_limiter = TokenBucket(rate=58.33, capacity=100)  # 3500/min ≈ 58.33/sec

async def call_openai_api(prompt: str) -> str:
    """Call OpenAI API with rate limiting"""
    # Wait for token
    while not openai_limiter.consume(tokens=1):
        await asyncio.sleep(0.1)  # Wait 100ms and retry

    # Make API call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]},
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

---

## Consequences

### Positive Consequences

**Resource Protection:**
- Prevents API abuse and DoS attacks
- Fair resource allocation among users
- Database and CPU protection
- Predictable performance under load

**Cost Control:**
- Bounded cloud API usage
- Prevents unexpected cost spikes
- Enables capacity planning
- Resource quota enforcement

**User Experience:**
- Clear error messages when limits exceeded
- Graceful degradation (not hard failures)
- Retry-after header informs clients
- Consistent performance

### Negative Consequences

**Complexity:**
- Multiple rate limit layers to manage
- Configuration tuning required
- Monitoring of rate limit hits
- Documentation for API consumers

**Performance:**
- Redis dependency for distributed rate limiting
- Additional latency (checking limits)
- Memory overhead (tracking client requests)
- Network calls to Redis

**User Limitations:**
- Legitimate heavy users may be throttled
- Polling applications affected
- Bulk operations slower
- Requires client-side optimization

**Mitigation Strategies:**
```python
# 1. Provide rate limit headers in responses
@app.post("/api/v1/detection/predict")
@limiter.limit("60/minute")
async def predict_detection(request: Request, ...):
    ...

    # Add rate limit headers
    return JSONResponse(
        content={"count": prediction},
        headers={
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "59",
            "X-RateLimit-Reset": int(time.time() + 60)
        }
    )

# 2. Offer higher limits for authenticated users
@limiter.limit("200/minute", key_func=lambda r: r.user.id if r.user.is_authenticated else None)
async def premium_endpoint(request: Request):
    """Higher rate limit for authenticated users"""
    ...

# 3. Provide burst capacity (token bucket)
# Allow short bursts above average rate
class BurstRateLimiter:
    def __init__(self, rate: int, burst: int):
        self.rate = rate  # Average rate
        self.burst = burst  # Burst capacity
        ...

# 4. Bulk operation endpoints (bypass normal limits)
@app.post("/api/v1/detection/bulk_predict")
@limiter.limit("10/minute")  # Stricter limit, but processes 100 predictions
async def bulk_predict(request: Request, items: list[PredictionRequest]):
    """Bulk prediction endpoint"""
    predictions = []
    for item in items:
        predictions.append(model.predict(item.features))
    return {"predictions": predictions}
```

---

## Implementation Plan

### Phase 1: Basic Rate Limiting (Week 1)

- Install and configure slowapi
- Add rate limits to all public API endpoints
- Set up Redis for distributed rate limiting
- Implement custom rate limit exceeded handler

### Phase 2: Advanced Rate Limiting (Week 1-2)

- WebSocket message throttling
- Database query throttling
- ML inference throttling
- Cloud API rate limiting (token bucket)

### Phase 3: Monitoring & Tuning (Week 2)

- Track rate limit hits (Prometheus metrics)
- Monitor throttled requests
- Adjust limits based on usage patterns
- Create dashboards for rate limit visibility

### Phase 4: Documentation & Communication (Week 2-3)

- Document rate limits for API consumers
- Provide rate limit error examples
- Create client-side SDK with automatic retries
- Communicate limits in API documentation

---

## Success Criteria

- **API Protection:** Zero downtime from API abuse
- **Resource Utilization:** CPU <80%, Database connections <80%
- **Rate Limit Accuracy:** <1% false positives (legitimate requests blocked)
- **Response Time:** Rate limit check <5ms overhead
- **Client Satisfaction:** <5% support requests related to rate limiting
- **Cloud API Costs:** Within budget (rate limits enforced)
- **Monitoring:** 100% visibility into rate limit hits

---

## References

1. [slowapi Documentation](https://slowapi.readthedocs.io/)
2. [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
3. [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
4. ADR-002: Backend Programming Language (FastAPI)
5. ADR-008: Authentication Strategy (user-based limits)

---

**Document End**

*This ADR will be reviewed quarterly or if rate limiting impacts legitimate users.*
