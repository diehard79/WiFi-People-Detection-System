"""
End-to-end system testing

Tests the complete detection pipeline from WiFi simulation to prediction
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML


class TestSystemE2E:
    """End-to-end system tests"""

    @pytest.fixture
    def wifi_simulator(self):
        """Create WiFi simulator"""
        return WiFiRSSISimulator(num_detectors=4)

    @pytest.fixture
    def signal_processor(self):
        """Create signal processor"""
        return SignalProcessor()

    @pytest.fixture
    def ml_models(self):
        """Create ML models"""
        models = PeopleDetectorML()
        # Try to load pre-trained models
        models.load_models()
        return models

    def test_complete_pipeline_empty_room(self, wifi_simulator, signal_processor, ml_models):
        """Test complete pipeline: empty room"""
        # Simulate WiFi data for empty room
        wifi_simulator.set_scenario(0, moving=False)

        # Collect RSSI data for 20 seconds
        rssi_data = {f"detector_{i}": [] for i in range(4)}
        for _ in range(20):
            for det_id in range(4):
                rssi = wifi_simulator.simulate_rssi(f"detector_{det_id}", 0, False)
                rssi_data[f"detector_{det_id}"].append(rssi)

        # Extract features
        all_features = {}
        for det_id, rssi_values in rssi_data.items():
            features = signal_processor.extract_features(rssi_values)
            all_features.update({f"{det_id}_{k}": v for k, v in features.items()})

        # Make prediction
        presence, presence_conf = ml_models.predict_presence(all_features)

        # Assertions
        assert presence == False, "Should detect no people"
        assert presence_conf > 0.5, "Should have some confidence"

    def test_complete_pipeline_three_people(self, wifi_simulator, signal_processor, ml_models):
        """Test complete pipeline: three people"""
        # Simulate WiFi data for 3 people
        wifi_simulator.set_scenario(3, moving=True)

        # Collect RSSI data for 20 seconds
        rssi_data = {f"detector_{i}": [] for i in range(4)}
        for _ in range(20):
            for det_id in range(4):
                rssi = wifi_simulator.simulate_rssi(f"detector_{det_id}", 3, True)
                rssi_data[f"detector_{det_id}"].append(rssi)

        # Extract features
        all_features = {}
        for det_id, rssi_values in rssi_data.items():
            features = signal_processor.extract_features(rssi_values)
            all_features.update({f"{det_id}_{k}": v for k, v in features.items()})

        # Make prediction
        presence, presence_conf = ml_models.predict_presence(all_features)
        count, count_conf = ml_models.predict_count(all_features)

        # Assertions
        assert presence == True, "Should detect people"
        assert count >= 2, f"Should detect at least 2 people, detected {count}"
        assert count <= 4, f"Should detect at most 4 people, detected {count}"
        assert presence_conf > 0.7, "Should have high confidence"


def test_wifi_simulator():
    """Test WiFi simulator"""
    sim = WiFiRSSISimulator(num_detectors=4)

    # Test empty room
    sim.set_scenario(0, moving=False)
    data = sim.simulate_window(20)

    assert len(data) == 4, "Should have 4 detectors"
    assert all(len(values) == 20 for values in data.values()), "Should have 20 samples"

    # Test with people
    sim.set_scenario(3, moving=True)
    data = sim.simulate_window(20)

    # RSSI should be lower with people
    stats = sim.get_statistics(data)
    for det_id, stat in stats.items():
        assert stat['mean'] < -40, f"RSSI should be attenuated with people"


def test_signal_processor():
    """Test signal processor"""
    processor = SignalProcessor()

    # Generate test data
    test_data = [np.random.normal(-45, 2) for _ in range(20)]

    # Extract features
    features = processor.extract_features(test_data)

    # Check important features exist
    assert 'mean' in features, "Should have mean feature"
    assert 'std' in features, "Should have std feature"
    assert 'variance' in features, "Should have variance feature"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
