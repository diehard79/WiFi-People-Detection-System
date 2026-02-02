"""
Simple tests for WiFi People Detection Backend
"""
import sys
sys.path.insert(0, '/home/vinns/experiments/detectPeople')

import numpy as np
from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor


def test_wifi_simulator():
    """Test WiFi RSSI simulator."""
    print("\n=== Testing WiFi Simulator ===")

    sim = WiFiRSSISimulator(num_detectors=4)

    # Test initialization
    assert sim.num_detectors == 4
    assert len(sim.baseline_rssi) == 4
    print("✓ Initialization successful")

    # Test scenario setting
    sim.set_scenario(3, moving=True)
    assert sim.current_people == 3
    assert sim.current_moving is True
    print("✓ Scenario setting works")

    # Test RSSI simulation
    rssi = sim.simulate_rssi("detector_0", 2, moving=True)
    assert -100 <= rssi <= -30
    print(f"✓ RSSI simulation: {rssi:.2f} dBm")

    # Test window simulation
    data = sim.simulate_window(duration_seconds=20)
    assert len(data) == 4
    assert all(len(values) == 20 for values in data.values())
    print(f"✓ Window simulation: {len(data)} detectors, 20 samples each")

    print("✅ WiFi Simulator tests passed!\n")


def test_signal_processor():
    """Test signal processing."""
    print("\n=== Testing Signal Processor ===")

    processor = SignalProcessor()

    # Generate test data
    test_data = [np.random.normal(-45, 2) for _ in range(20)]

    # Extract features
    features = processor.extract_features(test_data)

    # Check features extracted
    assert 'mean' in features
    assert 'std' in features
    assert 'variance' in features
    print(f"✓ Extracted {len(features)} features")

    # Test multi-detector features
    rssi_window = {
        "detector_0": [np.random.normal(-45, 2) for _ in range(20)],
        "detector_1": [np.random.normal(-48, 2) for _ in range(20)],
    }

    multi_features = processor.extract_window_features(rssi_window)
    assert 'detector_0_mean' in multi_features
    assert 'detector_1_mean' in multi_features
    print(f"✓ Multi-detector features: {len(multi_features)} features")

    print("✅ Signal Processor tests passed!\n")


def test_integration():
    """Test full pipeline integration."""
    print("\n=== Testing Full Pipeline ===")

    # Initialize components
    sim = WiFiRSSISimulator(num_detectors=4)
    processor = SignalProcessor()

    # Simulate scenario
    sim.set_scenario(num_people=3, moving=True)
    print(f"✓ Set scenario: 3 people, moving")

    # Collect data
    rssi_data = sim.simulate_window(duration_seconds=20)
    print(f"✓ Collected RSSI data from {len(rssi_data)} detectors")

    # Extract features
    features = processor.extract_window_features(rssi_data)
    print(f"✓ Extracted {len(features)} features")

    # Show some features
    print("\nSample features:")
    for key in list(features.keys())[:5]:
        print(f"  {key}: {features[key]:.4f}")

    print("✅ Integration test passed!\n")


if __name__ == "__main__":
    test_wifi_simulator()
    test_signal_processor()
    test_integration()

    print("\n" + "="*50)
    print("ALL TESTS PASSED!")
    print("="*50 + "\n")
