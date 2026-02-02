"""
Generate synthetic training data for WiFi-based people detection.

Based on research findings from arXiv:2308.06773:
- Standard deviation is key feature for presence detection
- Mean RSSI shifts with number of people
- Movement increases signal variance

IMPROVED: Better separation between people counts for counting model
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generate realistic training data for WiFi people detection"""

    def __init__(self, num_detectors: int = 4):
        self.num_detectors = num_detectors
        # Baseline RSSI for each detector (research-based)
        # More spread out baselines for better discrimination
        self.baseline_rssi = {
            f"detector_{i}": -40 - (i * 5) + np.random.normal(0, 2)
            for i in range(num_detectors)
        }

    def generate_rssi_window(self, num_people: int,
                             duration_seconds: int = 20,
                             moving: bool = False) -> List[Dict]:
        """
        Generate a 20-second window of RSSI data

        Args:
            num_people: Number of people in the room
            duration_seconds: Window length (default 20 for research)
            moving: Whether people are moving

        Returns:
            List of RSSI readings
        """
        samples = []

        # People affect RSSI (IMPROVED: stronger, more consistent effect)
        # Each person causes a predictable shift
        people_effect = num_people * -4.0  # Stronger, more linear attenuation

        # Movement increases variance
        noise_level = 1.5 if not moving else 3.5

        # Person-specific variance increases with count
        person_variance = num_people * 0.8

        # Generate samples at 1 Hz
        for t in range(duration_seconds):
            for det_id in range(self.num_detectors):
                baseline = self.baseline_rssi[f"detector_{det_id}"]

                # Add noise
                noise = np.random.normal(0, noise_level)

                # Add person-specific variance
                person_noise = np.random.normal(0, person_variance)

                # Multipath interference (increases non-linearly)
                if num_people > 1:
                    multipath = np.random.normal(0, np.sqrt(num_people) * 1.5)
                else:
                    multipath = 0

                rssi = baseline + people_effect + noise + person_noise + multipath
                rssi = max(-100, min(-30, rssi))  # Clamp to realistic range

                samples.append({
                    'detector_id': f"detector_{det_id}",
                    'timestamp': t,
                    'rssi': rssi,
                    'num_people': num_people,
                    'moving': moving
                })

        return samples

    def extract_features(self, rssi_window: List[Dict]) -> Dict[str, float]:
        """Extract features from RSSI window"""
        # Group by detector
        detector_data = {}
        for sample in rssi_window:
            det_id = sample['detector_id']
            if det_id not in detector_data:
                detector_data[det_id] = []
            detector_data[det_id].append(sample['rssi'])

        # Extract features for each detector
        all_features = {}

        for det_id, rssi_values in detector_data.items():
            # Time-domain features
            all_features[f'{det_id}_mean'] = float(np.mean(rssi_values))
            all_features[f'{det_id}_std'] = float(np.std(rssi_values))
            all_features[f'{det_id}_variance'] = float(np.var(rssi_values))
            all_features[f'{det_id}_min'] = float(np.min(rssi_values))
            all_features[f'{det_id}_max'] = float(np.max(rssi_values))
            all_features[f'{det_id}_range'] = all_features[f'{det_id}_max'] - all_features[f'{det_id}_min']
            all_features[f'{det_id}_median'] = float(np.median(rssi_values))
            all_features[f'{det_id}_skewness'] = float(float(self._skew(rssi_values)))
            all_features[f'{det_id}_kurtosis'] = float(self._kurtosis(rssi_values))

            # Frequency-domain features (simplified)
            if len(rssi_values) >= 4:
                fft_vals = np.fft.fft(rssi_values)
                power_spectrum = np.abs(fft_vals)[:len(rssi_values)//2]
                all_features[f'{det_id}_dominant_power'] = float(np.max(power_spectrum))

        return all_features

    def _skew(self, data: List[float]) -> float:
        """Calculate skewness"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean([(x - mean) ** 3 for x in data]) / (std ** 3)

    def _kurtosis(self, data: List[float]) -> float:
        """Calculate kurtosis"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return np.mean([(x - mean) ** 4 for x in data]) / (std ** 4) - 3

    def generate_dataset(self, samples_per_class: int = 100,
                        max_people: int = 5) -> pd.DataFrame:
        """
        Generate complete training dataset

        Args:
            samples_per_class: Samples to generate per people count
            max_people: Maximum number of people

        Returns:
            DataFrame with features and labels
        """
        logger.info("Generating training dataset...")

        all_data = []

        for num_people in range(max_people + 1):
            logger.info(f"Generating data for {num_people} people...")

            for _ in range(samples_per_class):
                # Randomly choose movement status
                # More movement for more people
                if num_people == 0:
                    moving = False  # Empty rooms don't have movement
                else:
                    moving = np.random.choice([True, False], p=[0.8, 0.2])

                # Generate RSSI window
                rssi_window = self.generate_rssi_window(num_people, 20, moving)

                # Extract features
                features = self.extract_features(rssi_window)

                # Add label
                features['num_people'] = num_people
                features['presence'] = 1 if num_people > 0 else 0
                features['moving'] = 1 if moving else 0

                all_data.append(features)

        df = pd.DataFrame(all_data)
        logger.info(f"Generated {len(df)} samples with {len(df.columns)} features")

        return df


def main():
    """Generate and save training data"""
    generator = TrainingDataGenerator(num_detectors=4)

    # Generate presence detection dataset
    logger.info("Generating presence detection dataset...")
    df_presence = generator.generate_dataset(samples_per_class=300, max_people=5)

    # Save datasets
    output_dir = Path("/home/vinns/experiments/detectPeople/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full dataset
    output_path = output_dir / f"training_data_{timestamp}.csv"
    df_presence.to_csv(output_path, index=False)
    logger.info(f"Saved training data to {output_path}")

    # Also save as JSON for easier loading
    json_path = output_dir / f"training_data_{timestamp}.json"
    df_presence.to_json(json_path, orient='records', indent=2)
    logger.info(f"Saved JSON data to {json_path}")

    # Print dataset statistics
    print("\n=== Dataset Statistics ===")
    print(f"Total samples: {len(df_presence)}")
    print(f"Features: {len(df_presence.columns) - 3}")  # Exclude labels
    print(f"\nSamples by people count:")
    print(df_presence['num_people'].value_counts().sort_index())
    print(f"\nSamples by presence:")
    print(df_presence['presence'].value_counts().sort_index())


if __name__ == '__main__':
    main()
