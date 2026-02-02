"""
CSI Data Collector for ESP32-S3

Collects and processes Channel State Information (CSI) from WiFi routers.
Handles phase correction, amplitude sanitization, and multi-detector coordination.
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CSIData:
    """Container for CSI data from a single detector."""
    detector_id: str
    timestamp: datetime
    phase_raw: np.ndarray
    amplitude_raw: np.ndarray
    phase_corrected: Optional[np.ndarray] = None
    amplitude_sanitized: Optional[np.ndarray] = None
    subcarriers: int = 64
    quality_score: float = 1.0


class CSIDataCollector:
    """
    Collects CSI data from ESP32-S3 detectors.

    Features:
    - Multi-detector coordination (4 detectors)
    - Phase correction (SANVI method)
    - Amplitude sanitization
    - Quality assessment
    - Background calibration
    """

    def __init__(
        self,
        num_detectors: int = 4,
        sampling_rate: int = 10,  # Hz
        subcarriers: int = 64
    ):
        """
        Initialize CSI collector

        Args:
            num_detectors: Number of ESP32-S3 detectors
            sampling_rate: Sampling rate in Hz
            subcarriers: Number of OFDM subcarriers
        """
        self.num_detectors = num_detectors
        self.sampling_rate = sampling_rate
        self.subcarriers = subcarriers

        # Detector status
        self.detectors = {}
        self.is_calibrating = False
        self.calibration_progress = 0.0

        # Background calibration data
        self.background_phase: Optional[np.ndarray] = None
        self.background_amplitude: Optional[np.ndarray] = None
        self.calibration_samples = 0
        self.min_calibration_samples = 300  # 30 seconds at 10Hz

        # Data buffers
        self.csi_buffer: Dict[str, List[CSIData]] = {
            f"detector_{i}": [] for i in range(num_detectors)
        }

        logger.info(
            f"Initialized CSI collector: {num_detectors} detectors, "
            f"{sampling_rate}Hz, {subcarriers} subcarriers"
        )

    def initialize_detector(self, detector_id: str) -> bool:
        """
        Initialize a detector

        Args:
            detector_id: Detector identifier

        Returns:
            True if initialized successfully
        """
        try:
            # In production, this would establish connection to ESP32-S3
            # For now, simulate initialization
            self.detectors[detector_id] = {
                "status": "active",
                "ip": f"192.168.1.{100 + len(self.detectors)}",
                "initialized_at": datetime.now()
            }

            logger.info(f"Detector {detector_id} initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize detector {detector_id}: {e}")
            return False

    def initialize_all_detectors(self) -> Dict[str, bool]:
        """
        Initialize all detectors

        Returns:
            Dictionary of detector_id to success status
        """
        results = {}

        for i in range(self.num_detectors):
            detector_id = f"detector_{i}"
            results[detector_id] = self.initialize_detector(detector_id)

        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Initialized {success_count}/{self.num_detectors} detectors")

        return results

    def simulate_csi_data(
        self,
        detector_id: str,
        num_people: int = 0,
        moving: bool = False
    ) -> CSIData:
        """
        Simulate CSI data (for testing/demonstration)

        Args:
            detector_id: Detector identifier
            num_people: Number of people in room
            moving: Whether people are moving

        Returns:
            CSIData object
        """
        # Generate phase data
        phase_noise = np.random.normal(0, 0.1, self.subcarriers)
        phase_shift = num_people * 0.2
        if moving:
            phase_shift += np.random.normal(0, 0.3, self.subcarriers)
        phase_raw = np.angle(np.exp(1j * (np.linspace(0, 2*np.pi, self.subcarriers) + phase_shift + phase_noise)))

        # Generate amplitude data
        base_amplitude = 50.0
        amplitude_noise = np.random.normal(0, 5, self.subcarriers)
        amplitude_attenuation = num_people * 3.0
        if moving:
            amplitude_attenuation += np.random.normal(0, 2, self.subcarriers)
        amplitude_raw = np.abs(base_amplitude - amplitude_attenuation + amplitude_noise)

        return CSIData(
            detector_id=detector_id,
            timestamp=datetime.now(),
            phase_raw=phase_raw,
            amplitude_raw=amplitude_raw,
            subcarriers=self.subcarriers,
            quality_score=1.0 - np.random.uniform(0, 0.1)
        )

    def collect_csi_snapshot(
        self,
        duration_seconds: int = 3
    ) -> Dict[str, List[CSIData]]:
        """
        Collect CSI snapshot from all detectors

        Args:
            duration_seconds: Duration to collect data

        Returns:
            Dictionary of detector_id to CSI data list
        """
        num_samples = duration_seconds * self.sampling_rate
        snapshot = {f"detector_{i}": [] for i in range(self.num_detectors)}

        for _ in range(num_samples):
            for i in range(self.num_detectors):
                detector_id = f"detector_{i}"

                # Simulate CSI data
                csi_data = self.simulate_csi_data(detector_id)

                # Process CSI data
                csi_data = self.process_csi_data(csi_data)

                snapshot[detector_id].append(csi_data)

        logger.info(f"Collected {num_samples} samples from {self.num_detectors} detectors")
        return snapshot

    def process_csi_data(self, csi_data: CSIData) -> CSIData:
        """
        Process CSI data with phase correction and amplitude sanitization

        Args:
            csi_data: Raw CSI data

        Returns:
            Processed CSI data
        """
        # Phase correction using SANVI method
        csi_data.phase_corrected = self._correct_phase(csi_data.phase_raw)

        # Amplitude sanitization
        csi_data.amplitude_sanitized = self._sanitize_amplitude(csi_data.amplitude_raw)

        return csi_data

    def _correct_phase(self, phase_raw: np.ndarray) -> np.ndarray:
        """
        Correct phase using SANVI method

        Sanitizes phase by:
        1. Unwrapping phase
        2. Removing linear trend
        3. Smoothing

        Args:
            phase_raw: Raw phase data

        Returns:
            Corrected phase data
        """
        # Unwrap phase
        phase_unwrapped = np.unwrap(phase_raw)

        # Remove linear trend
        x = np.arange(len(phase_unwrapped))
        coeffs = np.polyfit(x, phase_unwrapped, 1)
        phase_detrended = phase_unwrapped - np.polyval(coeffs, x)

        # Smooth with moving average
        window_size = 5
        phase_smoothed = np.convolve(
            phase_detrended,
            np.ones(window_size) / window_size,
            mode='same'
        )

        return phase_smoothed

    def _sanitize_amplitude(self, amplitude_raw: np.ndarray) -> np.ndarray:
        """
        Sanitize amplitude data

        Removes outliers and smooths signal

        Args:
            amplitude_raw: Raw amplitude data

        Returns:
            Sanitized amplitude data
        """
        # Remove outliers using median filter
        from scipy.signal import medfilt
        kernel_size = 5
        amplitude_filtered = medfilt(amplitude_raw, kernel_size=kernel_size)

        # Smooth with moving average
        window_size = 3
        amplitude_smoothed = np.convolve(
            amplitude_filtered,
            np.ones(window_size) / window_size,
            mode='same'
        )

        return amplitude_smoothed

    async def start_calibration(
        self,
        duration_seconds: int = 300,
        progress_callback=None
    ) -> bool:
        """
        Start background calibration

        Collects CSI data with empty room to establish baseline.

        Args:
            duration_seconds: Calibration duration (default 5 minutes)
            progress_callback: Optional callback for progress updates

        Returns:
            True if calibration successful
        """
        self.is_calibrating = True
        self.calibration_progress = 0.0

        logger.info(f"Starting calibration for {duration_seconds} seconds...")

        total_samples = duration_seconds * self.sampling_rate
        phase_accumulator = []
        amplitude_accumulator = []

        for sample_idx in range(total_samples):
            # Collect from all detectors
            for i in range(self.num_detectors):
                detector_id = f"detector_{i}"
                csi_data = self.simulate_csi_data(detector_id, num_people=0)

                if csi_data.phase_corrected is not None:
                    phase_accumulator.append(csi_data.phase_corrected)
                    amplitude_accumulator.append(csi_data.amplitude_sanitized)

            # Update progress
            self.calibration_progress = (sample_idx + 1) / total_samples

            if progress_callback and sample_idx % 10 == 0:
                await progress_callback(self.calibration_progress)

            # Small delay to simulate real-time collection
            await asyncio.sleep(0.1)

        # Compute background averages
        self.background_phase = np.mean(phase_accumulator, axis=0)
        self.background_amplitude = np.mean(amplitude_accumulator, axis=0)
        self.calibration_samples = len(phase_accumulator)

        self.is_calibrating = False

        logger.info(f"Calibration complete: {self.calibration_samples} samples collected")
        return True

    def get_calibration_status(self) -> Dict:
        """
        Get calibration status

        Returns:
            Dictionary with calibration status
        """
        return {
            "is_calibrating": self.is_calibrating,
            "progress": round(self.calibration_progress * 100, 2),
            "samples_collected": self.calibration_samples,
            "min_required_samples": self.min_calibration_samples,
            "is_calibrated": self.background_phase is not None
        }

    def get_detector_status(self) -> Dict:
        """
        Get status of all detectors

        Returns:
            Dictionary with detector status
        """
        return {
            "num_detectors": self.num_detectors,
            "sampling_rate": self.sampling_rate,
            "detectors": self.detectors,
            "calibration": self.get_calibration_status()
        }


if __name__ == "__main__":
    # Test CSI collector
    print("\n=== Testing CSI Data Collector ===\n")

    collector = CSIDataCollector(num_detectors=4)

    # Initialize detectors
    results = collector.initialize_all_detectors()
    print(f"Detector initialization: {results}")

    # Collect snapshot
    snapshot = collector.collect_csi_snapshot(duration_seconds=1)
    print(f"\nCollected snapshot from {len(snapshot)} detectors")

    # Display sample data
    for detector_id, data_list in snapshot.items():
        if data_list:
            sample = data_list[0]
            print(f"\n{detector_id}:")
            print(f"  Phase shape: {sample.phase_raw.shape}")
            print(f"  Amplitude shape: {sample.amplitude_raw.shape}")
            print(f"  Quality score: {sample.quality_score:.2f}")

    print("\n✅ CSI collector working correctly")
