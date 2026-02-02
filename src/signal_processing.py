"""
Signal Processing Module

Extracts features from WiFi RSSI signals for ML models.
Based on research findings from arXiv:2308.06773.
"""

import numpy as np
import logging
from typing import List, Dict
from scipy import stats
from scipy.fft import fft

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Process WiFi RSSI signals and extract features

    Key features from research:
    - Standard deviation (most important for presence)
    - Mean RSSI (shifts with people count)
    - Variance (increases with movement)
    - Frequency domain features
    """

    def __init__(self):
        """Initialize signal processor"""
        logger.info("Initialized signal processor")

    def extract_features(self, rssi_values: List[float]) -> Dict[str, float]:
        """
        Extract features from RSSI time series

        Args:
            rssi_values: List of RSSI readings

        Returns:
            Dictionary of feature names to values
        """
        features = {}
        data = np.array(rssi_values)

        # Time domain features
        features['mean'] = float(np.mean(data))
        features['std'] = float(np.std(data))
        features['variance'] = float(np.var(data))
        features['min'] = float(np.min(data))
        features['max'] = float(np.max(data))
        features['range'] = features['max'] - features['min']
        features['median'] = float(np.median(data))
        features['q25'] = float(np.percentile(data, 25))
        features['q75'] = float(np.percentile(data, 75))
        features['iqr'] = features['q75'] - features['q25']

        # Higher order moments
        features['skewness'] = float(stats.skew(data))
        features['kurtosis'] = float(stats.kurtosis(data))

        # Difference features
        if len(data) > 1:
            diff = np.diff(data)
            features['diff_mean'] = float(np.mean(diff))
            features['diff_std'] = float(np.std(diff))
            features['diff_max'] = float(np.max(diff))

        # Frequency domain features
        if len(data) >= 4:
            fft_vals = fft(data)
            power_spectrum = np.abs(fft_vals)[:len(data)//2]

            features['dominant_freq'] = float(np.argmax(power_spectrum))
            features['dominant_power'] = float(np.max(power_spectrum))
            features['total_power'] = float(np.sum(power_spectrum))
            features['power_entropy'] = float(self._entropy(power_spectrum))

        # Zero crossing rate
        features['zero_crossings'] = float(self._zero_crossing_rate(data))

        return features

    def _entropy(self, data: np.ndarray) -> float:
        """Calculate entropy of signal"""
        # Normalize
        data_norm = data / (np.sum(data) + 1e-10)
        # Calculate entropy
        entropy = -np.sum(data_norm * np.log(data_norm + 1e-10))
        return float(entropy)

    def _zero_crossing_rate(self, data: np.ndarray) -> float:
        """Calculate zero crossing rate"""
        mean = np.mean(data)
        centered = data - mean
        crossings = np.sum(np.diff(np.sign(centered)) != 0)
        return float(crossings / len(data))

    def extract_window_features(self, rssi_window: Dict[str, List[float]]) -> Dict[str, float]:
        """
        Extract features from multiple detectors

        Args:
            rssi_window: Dictionary mapping detector_id to RSSI values

        Returns:
            Combined features from all detectors
        """
        all_features = {}

        for detector_id, rssi_values in rssi_window.items():
            # Extract features for this detector
            features = self.extract_features(rssi_values)

            # Add prefix with detector ID
            for feature_name, feature_value in features.items():
                all_features[f"{detector_id}_{feature_name}"] = feature_value

        return all_features


if __name__ == '__main__':
    # Test signal processor
    processor = SignalProcessor()

    print("\n=== Testing Signal Processor ===\n")

    # Generate test data
    test_data = [np.random.normal(-45, 2) for _ in range(20)]

    # Extract features
    features = processor.extract_features(test_data)

    print(f"Extracted {len(features)} features:")
    for name, value in list(features.items())[:10]:
        print(f"  {name}: {value:.4f}")

    print("\n✅ Signal processor working correctly")
