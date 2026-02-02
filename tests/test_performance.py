"""
Performance and load testing
"""

import pytest
import asyncio
import time
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML


class TestPerformance:
    """Performance tests"""

    @pytest.fixture
    def ml_models(self):
        """Load models for testing"""
        models = PeopleDetectorML()
        models.load_models()
        return models

    @pytest.fixture
    def signal_processor(self):
        """Create signal processor"""
        return SignalProcessor()

    def test_inference_latency(self, signal_processor, ml_models):
        """Test ML inference latency"""
        # Generate features
        rssi_data = [np.random.normal(-45, 2, 20) for _ in range(4)]
        features = {}
        for i, data in enumerate(rssi_data):
            det_features = signal_processor.extract_features(data)
            features.update({f"detector_{i}_{k}": v for k, v in det_features.items()})

        # Measure inference time
        start = time.time()
        presence, conf = ml_models.predict_presence(features)
        latency_ms = (time.time() - start) * 1000

        # Assert latency is acceptable (< 10ms per ADR-004)
        assert latency_ms < 10, f"Inference too slow: {latency_ms:.2f}ms"
        print(f"\nInference latency: {latency_ms:.2f}ms")

    def test_feature_extraction_speed(self, signal_processor):
        """Test feature extraction performance"""
        # Generate 20-second RSSI window
        rssi_data = [np.random.normal(-45, 2, 20) for _ in range(4)]

        # Measure extraction time
        start = time.time()
        for i, data in enumerate(rssi_data):
            features = signal_processor.extract_features(data)
        latency_ms = (time.time() - start) * 1000

        # Assert it's fast enough (< 50ms per ADR-004)
        assert latency_ms < 50, f"Feature extraction too slow: {latency_ms:.2f}ms"
        print(f"\nFeature extraction latency: {latency_ms:.2f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
