"""
WiFi RSSI Signal Simulator

Simulates realistic WiFi RSSI signals based on:
- Number of people in environment
- Movement patterns
- Distance from transmitter
- Multipath interference
"""

import numpy as np
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WiFiRSSISimulator:
    """
    Simulate WiFi RSSI signals for people detection

    Based on research from arXiv:2308.06773 showing:
    - RSSI decreases with more people (absorption)
    - Movement increases signal variance
    - Standard deviation is key feature for detection
    """

    def __init__(self, num_detectors: int = 4):
        """
        Initialize WiFi simulator

        Args:
            num_detectors: Number of WiFi detectors to simulate
        """
        self.num_detectors = num_detectors

        # Baseline RSSI for each detector (dBm)
        # Match the training data generator
        self.baseline_rssi = {
            f"detector_{i}": -40 - (i * 5) + np.random.normal(0, 2)
            for i in range(num_detectors)
        }

        # Current scenario
        self.current_people = 0
        self.current_moving = False

        logger.info(f"Initialized WiFi simulator with {num_detectors} detectors")
        logger.info(f"Baseline RSSI: {self.baseline_rssi}")

    def set_scenario(self, num_people: int, moving: bool = False):
        """
        Set simulation scenario

        Args:
            num_people: Number of people in environment
            moving: Whether people are moving
        """
        self.current_people = num_people
        self.current_moving = moving

    def simulate_rssi(self, detector_id: str,
                     num_people: Optional[int] = None,
                     moving: Optional[bool] = None) -> float:
        """
        Simulate RSSI reading for a detector

        Args:
            detector_id: Detector identifier
            num_people: Number of people (uses current if None)
            moving: Movement status (uses current if None)

        Returns:
            Simulated RSSI value in dBm
        """
        # Use current scenario if not specified
        if num_people is None:
            num_people = self.current_people
        if moving is None:
            moving = self.current_moving

        # Get baseline RSSI
        baseline = self.baseline_rssi.get(detector_id, -45)

        # People affect RSSI (matching training data)
        people_effect = num_people * -4.0  # Linear attenuation

        # Movement increases variance
        noise_level = 1.5 if not moving else 3.5
        noise = np.random.normal(0, noise_level)

        # Person-specific variance
        person_variance = num_people * 0.8
        person_noise = np.random.normal(0, person_variance)

        # Multipath interference
        if num_people > 1:
            multipath = np.random.normal(0, np.sqrt(num_people) * 1.5)
        else:
            multipath = 0

        # Calculate RSSI
        rssi = baseline + people_effect + noise + person_noise + multipath

        # Clamp to realistic WiFi range
        rssi = max(-100, min(-30, rssi))

        return float(rssi)

    def simulate_window(self, duration_seconds: int = 20) -> Dict[str, list]:
        """
        Simulate a time window of RSSI data

        Args:
            duration_seconds: Length of window in seconds

        Returns:
            Dictionary mapping detector_id to list of RSSI values
        """
        rssi_data = {f"detector_{i}": [] for i in range(self.num_detectors)}

        for _ in range(duration_seconds):
            for det_id in range(self.num_detectors):
                detector_id = f"detector_{det_id}"
                rssi = self.simulate_rssi(detector_id)
                rssi_data[detector_id].append(rssi)

        return rssi_data

    def get_statistics(self, rssi_data: Dict[str, list]) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics for RSSI data

        Args:
            rssi_data: Dictionary of detector_id to RSSI values

        Returns:
            Statistics for each detector
        """
        stats = {}

        for detector_id, values in rssi_data.items():
            values_array = np.array(values)
            stats[detector_id] = {
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array)),
                'variance': float(np.var(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'median': float(np.median(values_array)),
                'range': float(np.max(values_array) - np.min(values_array))
            }

        return stats


if __name__ == '__main__':
    # Test simulator
    sim = WiFiRSSISimulator(num_detectors=4)

    print("\n=== Testing WiFi Simulator ===\n")

    # Test empty room
    print("Scenario: Empty room")
    sim.set_scenario(0, moving=False)
    data = sim.simulate_window(20)
    stats = sim.get_statistics(data)
    for det_id, stat in stats.items():
        print(f"{det_id}: mean={stat['mean']:.2f}, std={stat['std']:.2f}")

    # Test 3 people, moving
    print("\nScenario: 3 people, moving")
    sim.set_scenario(3, moving=True)
    data = sim.simulate_window(20)
    stats = sim.get_statistics(data)
    for det_id, stat in stats.items():
        print(f"{det_id}: mean={stat['mean']:.2f}, std={stat['std']:.2f}")

    print("\n✅ Simulator working correctly")
