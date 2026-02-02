# ADR-013: Testing Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** WiFi-Based People Detection System Quality Assurance
**Decision:** Comprehensive Testing Pyramid with pytest, ML Validation, and Hardware Emulation

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-02 | Initial version | Technical Architect |

---

## Context

The WiFi-based people detection system requires rigorous testing to ensure:
- **ML Accuracy:** 98-99% for presence detection, 95-98% for people counting
- **System Reliability:** 99.5% uptime, graceful error handling
- **API Correctness:** RESTful endpoints, WebSocket communication
- **Performance:** <10ms ML inference, <100ms API response time
- **Data Integrity:** Time-series storage, database transactions
- **Hardware Integration:** WiFi router communication, signal collection

**Testing Challenges:**
- ML model behavior is probabilistic (non-deterministic predictions)
- Hardware dependencies (WiFi routers) in test environments
- Real-time data streams (WebSocket, time-series)
- Cross-environment testing (local dev, CI/CD, staging, production)

---

## Decision

**Selected Testing Framework: pytest (Python) + Jest/Playwright (Frontend)**

### Testing Pyramid Structure

```
                    /\
                   /  \
                  / E2E\ (10%)
                 /------\
                /        \
               /Integration\ (30%)
              /------------\
             /              \
            /   Unit Tests   \ (60%)
           /------------------\
```

**Test Distribution:**
- **Unit Tests:** 60% - Fast, isolated, cover business logic
- **Integration Tests:** 30% - API, database, ML model integration
- **E2E Tests:** 10% - Full detection flow, user workflows

---

## Rationale

### Framework Selection: pytest

**Why pytest for Python Backend:**

| Feature | pytest | unittest | nose2 |
|---------|--------|----------|-------|
| **Fixture System** | Excellent ✅ | Basic ⚠️ | Limited ❌ |
| **Async Support** | Native (pytest-asyncio) ✅ | None ❌ | Limited ❌ |
| **Assertion Syntax** | Pythonic (assert) ✅ | Verbose ❌ | Good ⚠️ |
| **Plugin Ecosystem** | 1000+ plugins ✅ | Limited ❌ | Discontinued ❌ |
| **Coverage Reporting** | pytest-cov ✅ | External ❌ | External ❌ |
| **Parallel Execution** | pytest-xdist ✅ | None ❌ | Limited ❌ |
| **Parametrization** | @pytest.mark.parametrize ✅ | None ❌ | Limited ❌ |

**pytest Advantages:**
```python
# 1. Simple, readable assertions
def test_prediction_accuracy():
    prediction = model.predict(features)
    assert prediction == 3  # Pythonic!

# 2. Powerful fixtures
@pytest.fixture
def trained_model():
    return joblib.load('models/test_model.pkl')

def test_with_model(trained_model):
    result = trained_model.predict(test_features)
    assert result is not None

# 3. Parametrization (test multiple scenarios)
@pytest.mark.parametrize("input_count,expected", [
    (0, "empty"),
    (1, "single"),
    (5, "multiple"),
])
def test_room_state(input_count, expected):
    state = get_room_state(input_count)
    assert state == expected
```

### ML Model Testing Strategy

**ML-Specific Testing Challenges:**
- Non-deterministic predictions (probabilistic models)
- Feature engineering validation
- Model version compatibility
- Training data quality assurance

**ML Test Coverage:**

| Test Type | Purpose | Tool | Frequency |
|-----------|---------|------|-----------|
| **Unit Tests** | Model loading, feature extraction | pytest | Every commit |
| **Cross-Validation** | Accuracy verification | scikit-learn | Every training |
| **Integration Tests** | End-to-end prediction pipeline | pytest | Every commit |
| **Performance Tests** | Inference latency benchmarks | pytest-benchmark | Daily |
| **Data Drift Tests** | Feature distribution monitoring | Great Expectations | Hourly |
| **A/B Tests** | Model comparison | Custom framework | On new model |

**ML Testing Examples:**

```python
# tests/ml/test_model_loading.py
def test_model_loading():
    """Test that model can be loaded successfully"""
    model = joblib.load('models/counting_model.pkl')
    assert model is not None
    assert hasattr(model, 'predict')
    assert hasattr(model, 'predict_proba')

# tests/ml/test_feature_extraction.py
def test_feature_extraction_dimensions():
    """Test that feature extraction returns correct dimensions"""
    rssi_window = generate_mock_rssi(window_size=20, detectors=5)
    features = extract_features(rssi_window)
    assert features.shape == (20,)  # Expected 20 features

# tests/ml/test_prediction_accuracy.py
def test_prediction_accuracy_on_test_set():
    """Test model accuracy on held-out test set"""
    model = joblib.load('models/counting_model.pkl')
    X_test, y_test = load_test_data()

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    assert accuracy >= 0.95, f"Accuracy {accuracy:.2%} below 95% threshold"

# tests/ml/test_inference_latency.py
def test_inference_latency():
    """Test ML inference meets <10ms latency requirement"""
    model = joblib.load('models/counting_model.pkl')
    features = generate_mock_features()

    start_time = time.time()
    for _ in range(100):
        model.predict(features)
    end_time = time.time()

    avg_latency = (end_time - start_time) / 100 * 1000  # ms
    assert avg_latency < 10, f"Latency {avg_latency:.2f}ms exceeds 10ms threshold"

# tests/ml/test_reproducibility.py
def test_prediction_reproducibility():
    """Test that predictions are reproducible with same random seed"""
    np.random.seed(42)
    features = np.random.randn(1, 20)

    model = joblib.load('models/counting_model.pkl')
    prediction1 = model.predict(features)
    prediction2 = model.predict(features)

    assert prediction1[0] == prediction2[0], "Predictions not reproducible"
```

### Hardware Testing Strategy

**Challenge:** WiFi routers not available in CI/CD environments

**Solution:** Hardware emulation with mock data and record-replay testing

**Hardware Test Approaches:**

| Approach | Description | Use Case |
|----------|-------------|----------|
| **Mock Data** | Synthetic RSSI data generation | Unit tests, CI/CD |
| **Record-Replay** | Record real router signals, replay in tests | Integration tests |
| **Hardware-in-Loop** | Real routers in test environment | Pre-production validation |
| **Router Emulator** | Software router simulator | Development testing |

**Mock RSSI Data Generation:**

```python
# tests/fixtures/mock_rssi_generator.py
import numpy as np
from datetime import datetime, timedelta

class MockRSSIGenerator:
    """Generate synthetic RSSI data for testing"""

    @staticmethod
    def generate_window(
        num_people: int,
        duration_seconds: int = 20,
        sampling_rate: int = 1,
        detectors: int = 5,
        noise_level: float = 2.0
    ) -> np.ndarray:
        """
        Generate RSSI window with realistic signal patterns

        Args:
            num_people: Number of people in room (affects signal variance)
            duration_seconds: Window duration
            sampling_rate: Samples per second
            detectors: Number of WiFi detectors
            noise_level: Signal noise standard deviation (dBm)

        Returns:
            RSSI array: shape (detectors, duration_seconds * sampling_rate)
        """
        samples = duration_seconds * sampling_rate
        rssi_window = np.zeros((detectors, samples))

        # Base RSSI level (typical WiFi signal strength)
        base_rssi = -45.0  # dBm

        for detector in range(detectors):
            # Add detector-specific offset
            detector_offset = np.random.normal(0, 5)

            # Add human presence effect (more people = more variance)
            human_effect = np.random.normal(0, num_people * 0.8, samples)

            # Add environmental noise
            noise = np.random.normal(0, noise_level, samples)

            # Add temporal correlation (movement patterns)
            time_correlation = np.cumsum(np.random.normal(0, 0.5, samples))
            time_correlation = np.convolve(
                time_correlation,
                np.ones(5) / 5,  # Moving average
                mode='same'
            )

            # Combine components
            rssi_window[detector, :] = (
                base_rssi
                + detector_offset
                + human_effect
                + noise
                + time_correlation * 0.3
            )

        return rssi_window

    @staticmethod
    def generate_calibration_data(
        num_people: int,
        samples: int = 100
    ) -> list:
        """Generate labeled calibration samples"""
        data = []
        for _ in range(samples):
            window = MockRSSIGenerator.generate_window(num_people)
            features = extract_features(window)
            data.append((features, num_people))
        return data

# Usage in tests
def test_feature_extraction_with_mock_data():
    """Test feature extraction with synthetic RSSI data"""
    generator = MockRSSIGenerator()

    # Generate 3-person scenario
    rssi_window = generator.generate_window(num_people=3, duration_seconds=20)

    # Extract features
    features = extract_features(rssi_window)

    # Validate feature dimensions
    assert features.shape == (20,)
    assert -80 < features[0] < -30  # Mean RSSI in reasonable range
    assert features[1] > 0  # Standard deviation positive
```

**Record-Replay Testing:**

```python
# tests/hardware/test_wifi_collector_replay.py
class WiFiCollectorReplayTest:
    """Test WiFi signal collection with replayed real signals"""

    @pytest.fixture
    def recorded_signals(self):
        """Load recorded RSSI signals from real routers"""
        return np.load('tests/fixtures/recorded_rssi_signals.npy')

    def test_signal_collection_replay(self, recorded_signals):
        """Test signal collection pipeline with replayed data"""
        collector = WiFiCollector()

        # Replay recorded signals
        for signal in recorded_signals:
            collector.process_signal(signal)

        # Validate collected data
        assert len(collector.buffer) == len(recorded_signals)
        assert collector.validate_checksums()
```

### Integration Testing Strategy

**Integration Test Coverage:**

| Component | Test Scenarios | Tool |
|-----------|----------------|------|
| **REST API** | Endpoint validation, error handling | pytest + httpx |
| **WebSocket** | Real-time detection streaming | pytest + websockets |
| **PostgreSQL** | Database transactions, migrations | pytest + asyncpg |
| **InfluxDB** | Time-series writes, queries | pytest + influxdb-client |
| **Redis** | Caching, pub/sub | pytest + redis |
| **ML Pipeline** | Feature extraction → Prediction | pytest + scikit-learn |
| **External APIs** | Cloud services, webhooks | pytest + respx |

**API Integration Tests:**

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

@pytest.mark.asyncio
async def test_detection_prediction_endpoint():
    """Test POST /api/v1/detection/predict endpoint"""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/detection/predict",
            json={
                "room_id": "test-room-1",
                "features": [-42.5, 3.2, 1.8, ...]  # 20 features
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "confidence" in data
        assert 0 <= data["count"] <= 10
        assert 0 <= data["confidence"] <= 1

@pytest.mark.asyncio
async def test_detection_history_endpoint():
    """Test GET /api/v1/detection/history endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/detection/history",
            params={"room_id": "test-room-1", "hours": 24}
        )

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
        assert isinstance(data["detections"], list)
```

**WebSocket Integration Tests:**

```python
# tests/integration/test_websocket.py
import pytest
from websockets import connect

@pytest.mark.asyncio
async def test_detection_streaming():
    """Test real-time detection streaming via WebSocket"""
    async with connect("ws://localhost:8000/ws/detection/test-room-1") as ws:
        # Subscribe to detections
        await ws.send('{"action": "subscribe"}')

        # Receive detection update
        message = await ws.recv()
        data = json.loads(message)

        assert data["type"] == "detection"
        assert "count" in data["data"]
        assert "timestamp" in data["data"]
```

### End-to-End Testing Strategy

**E2E Test Scenarios:**

| Scenario | Description | Tool |
|----------|-------------|------|
| **Full Detection Flow** | WiFi collection → Processing → ML prediction → WebSocket broadcast | Playwright |
| **User Dashboard** | Login → View rooms → Monitor detections | Playwright |
| **Calibration Workflow** | Start calibration → Collect data → Train model → Deploy | Playwright |
| **Alert System** | Threshold breach → Alert trigger → Email/Webhook sent | Custom |

**E2E Test Example (Playwright):**

```typescript
// tests/e2e/detection-flow.spec.ts
import { test, expect } from '@playwright/test';

test('full detection flow', async ({ page }) => {
  // 1. Navigate to dashboard
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForURL('**/dashboard');

  // 2. Select room
  await page.click('[data-testid="room-select"]');
  await page.click('text=Conference Room A');

  // 3. Verify real-time detection display
  await page.waitForSelector('[data-testid="detection-count"]');

  const countElement = page.locator('[data-testid="detection-count"]');
  const count = await countElement.innerText();
  expect(parseInt(count)).toBeGreaterThanOrEqual(0);

  // 4. Verify detection history chart renders
  await page.waitForSelector('[data-testid="detection-chart"]');

  // 5. Trigger calibration
  await page.click('[data-testid="calibration-button"]');
  await page.waitForSelector('text=Calibration in progress');
});
```

### Coverage Targets

**Coverage Requirements:**

| Component | Unit Coverage | Integration Coverage | Combined |
|-----------|---------------|---------------------|----------|
| **Backend API** | >80% | >60% | >85% |
| **ML Models** | >90% (feature extraction) | >95% (prediction accuracy) | >95% |
| **Signal Processing** | >85% | >70% | >90% |
| **Database Layer** | >80% | >60% | >85% |
| **WebSocket Service** | >75% | >65% | >85% |
| **Frontend Components** | >70% | >50% | >80% |
| **Overall System** | >80% | >60% | >85% |

**Measurement Tools:**
```bash
# Backend coverage
pytest --cov=src --cov-report=html --cov-report=term

# Frontend coverage
npm test -- --coverage

# Combined coverage report
coverage combine
coverage report
```

---

## Consequences

### Positive Consequences

**Quality Assurance:**
- Comprehensive test coverage catches bugs early
- ML model validation ensures accuracy requirements met
- Performance tests prevent regressions
- Hardware emulation enables CI/CD testing

**Development Velocity:**
- Fast unit tests (<5 seconds) enable rapid iteration
- Fixture system reduces test boilerplate
- Parametrization tests multiple scenarios efficiently
- Parallel execution speeds up test suites

**Maintainability:**
- Clear test structure (unit → integration → E2E)
- Well-documented test scenarios
- Easy to add new tests
- Test documentation serves as usage examples

**CI/CD Integration:**
- All tests run automatically on commits
- Fast feedback loop (<5 minutes for unit tests)
- Gate deployment on test success
- Coverage trends tracked over time

### Negative Consequences

**Test Maintenance:**
- Mock data must stay synchronized with real data patterns
- Hardware emulation may not capture all edge cases
- ML test data must be updated with model changes
- E2E tests can be flaky (timing-dependent)

**Performance:**
- Full test suite can take 10-30 minutes
- ML model tests require loading models into memory
- Integration tests require database setup
- E2E tests require browser automation

**Complexity:**
- Multiple test frameworks to maintain (pytest, Jest, Playwright)
- Test fixtures require ongoing maintenance
- Hardware-in-loop tests require physical setup
- ML test data generation is complex

**Mitigation Strategies:**
```python
# 1. Use test profiles (unit vs. integration)
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (database, API)
    e2e: End-to-end tests (slow, full system)

# Run fast tests in CI
pytest -m unit  # <5 seconds

# Run all tests before deployment
pytest  # ~20 minutes

# 2. Parallel execution
pytest -n auto  # Use all CPU cores

# 3. Test data versioning
tests/fixtures/
├── mock_data_v1.pkl
├── mock_data_v2.pkl
└── current -> mock_data_v2.pkl
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/
│   ├── ml/
│   │   ├── test_feature_extraction.py
│   │   ├── test_model_loading.py
│   │   └── test_prediction.py
│   ├── api/
│   │   ├── test_endpoints.py
│   │   └── test_validation.py
│   ├── services/
│   │   ├── test_signal_collector.py
│   │   └── test_calibration.py
│   └── utils/
│       ├── test_math.py
│       └── test_logging.py
├── integration/
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   ├── test_websocket_integration.py
│   └── test_ml_pipeline.py
├── e2e/
│   ├── detection-flow.spec.ts
│   ├── dashboard.spec.ts
│   └── calibration.spec.ts
├── fixtures/
│   ├── mock_rssi_generator.py
│   ├── test_models.pkl
│   └── sample_data.json
└── conftest.py  # Shared pytest configuration
```

### pytest Configuration

```python
# conftest.py
import pytest
import numpy as np
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async database fixture
@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql://test:test@localhost/test_db")
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        yield session

# ML model fixture
@pytest.fixture
def trained_model():
    import joblib
    return joblib.load('tests/fixtures/test_model.pkl')

# Mock RSSI data fixture
@pytest.fixture
def mock_rssi_window():
    from tests.fixtures.mock_rssi_generator import MockRSSIGenerator
    return MockRSSIGenerator.generate_window(num_people=3)

# FastAPI test client fixture
@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)
```

---

## Continuous Integration

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-xdist

      - name: Run unit tests
        run: pytest -m unit -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      influxdb:
        image: influxdb:2.7
        env:
          DOCKER_INFLUXDB_INIT_MODE: setup
          DOCKER_INFLUXDB_INIT_USERNAME: admin
          DOCKER_INFLUXDB_INIT_PASSWORD: password
          DOCKER_INFLUXDB_INIT_ORG: test
          DOCKER_INFLUXDB_INIT_BUCKET: test
        options: >-
          --health-cmd "influx ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 10

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run integration tests
        run: pytest -m integration -v
        env:
          DATABASE_URL: postgresql://test:test@localhost/test_db
          REDIS_URL: redis://localhost:6379
          INFLUXDB_URL: http://localhost:8086

  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Success Criteria

- **Unit Test Coverage:** >80% for backend code
- **Integration Test Coverage:** >60% for critical paths
- **ML Model Accuracy:** >95% on test set
- **Test Execution Time:** Unit tests <5 minutes, Full suite <30 minutes
- **Test Reliability:** <1% flaky test rate
- **CI/CD Pass Rate:** >95% (automated testing gates)
- **ML Inference Latency:** <10ms (performance tests)
- **API Response Time:** <100ms P95 (load tests)

---

## References

1. [pytest Documentation](https://docs.pytest.org/)
2. [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
3. [Playwright E2E Testing](https://playwright.dev/)
4. [scikit-learn Model Evaluation](https://scikit-learn.org/stable/model_evaluation.html)
5. ADR-004: Machine Learning Framework Selection
6. ADR-002: Backend Programming Language Selection

---

**Document End**

*This ADR will be reviewed quarterly or if testing metrics indicate quality issues.*
