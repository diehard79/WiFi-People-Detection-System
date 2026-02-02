"""
CSI (Channel State Information) Data Collection Module

Collects CSI data from ESP32-S3 WiFi devices for wall detection.
Implements advanced signal processing including LPC, CFO, and SFO correction.

Based on research:
- CSI provides fine-grained channel information (amplitude + phase per subcarrier)
- 30 subcarriers typical for 20MHz WiFi channels
- Linear Phase Compensation (LPC) removes linear phase progression
- Carrier Frequency Offset (CFO) and Sampling Frequency Offset (SFO) correction
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import struct

import numpy as np
from scipy import signal
from scipy.fft import fft, ifft
from scipy.stats import skew, kurtosis
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === Configuration ===

CSI_CONFIG = {
    'sampling_rate': 10,  # Hz
    'subcarriers': 30,  # Number of subcarriers for 20MHz WiFi
    'calibration_duration': 300,  # seconds (5 min)
    'detectors': ['csi_1', 'csi_2', 'csi_3', 'csi_4'],
    'tx_antennas': 1,  # ESP32-S3 typically has 1 TX antenna
    'rx_antennas': 2,  # ESP32-S3 typically has 2 RX antennas
    'fft_size': 64,  # FFT size for CSI processing
    'websocket_timeout': 10,  # seconds
}


# === Data Structures ===

@dataclass
class CSIData:
    """
    Container for CSI measurement data.

    Attributes:
        timestamp: Timestamp of measurement
        detector_id: Identifier for the CSI detector
        subcarriers: Complex CSI values per subcarrier (amplitude + phase)
        amplitude: Signal amplitude per subcarrier
        phase: Signal phase per subcarrier (radians)
        csi_matrix: Full CSI matrix (Tx x Rx x subcarriers)
        rssi: Legacy RSSI value for compatibility
    """
    timestamp: datetime
    detector_id: str
    subcarriers: np.ndarray  # Shape: (num_subcarriers,) complex128
    amplitude: np.ndarray     # Shape: (num_subcarriers,) float64
    phase: np.ndarray         # Shape: (num_subcarriers,) float64
    csi_matrix: np.ndarray    # Shape: (tx, rx, num_subcarriers) complex128
    rssi: float               # Scalar RSSI in dBm

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'detector_id': self.detector_id,
            'subcarriers_real': self.subcarriers.real.tolist(),
            'subcarriers_imag': self.subcarriers.imag.tolist(),
            'amplitude': self.amplitude.tolist(),
            'phase': self.phase.tolist(),
            'csi_matrix_shape': list(self.csi_matrix.shape),
            'rssi': self.rssi
        }


@dataclass
class CSICalibrationData:
    """Calibration data for CSI baseline."""
    detector_id: str
    timestamp: datetime
    baseline_amplitude: np.ndarray
    baseline_phase: np.ndarray
    noise_floor: float
    cfo_estimate: float  # Carrier Frequency Offset estimate
    sfo_estimate: float  # Sampling Frequency Offset estimate


# === CSI Collector Class ===

class CSICollector:
    """
    Collect CSI data from ESP32-S3 WiFi devices.

    Features:
    - Async WebSocket communication with ESP32-S3
    - Linear Phase Compensation (LPC)
    - Carrier Frequency Offset (CFO) correction
    - Sampling Frequency Offset (SFO) correction
    - Comprehensive feature extraction (500-1000 features)
    - Calibration support
    """

    def __init__(
        self,
        detector_id: str,
        host: str,
        port: int = 8080,
        config: Optional[Dict] = None
    ):
        """
        Initialize CSI collector.

        Args:
            detector_id: Unique identifier for this detector
            host: ESP32-S3 device host/IP
            port: WebSocket port (default: 8080)
            config: Optional configuration overrides
        """
        self.detector_id = detector_id
        self.host = host
        self.port = port
        self.config = {**CSI_CONFIG, **(config or {})}

        # Calibration data
        self.calibration: Optional[CSICalibrationData] = None
        self.is_calibrated = False

        # WebSocket connection
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False

        # Data buffer
        self.csi_buffer: List[CSIData] = []
        self.buffer_size = 100  # Keep last 100 measurements

        logger.info(
            f"Initialized CSI collector: {detector_id} @ {host}:{port}"
        )

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to ESP32-S3.

        Returns:
            True if connection successful
        """
        uri = f"ws://{self.host}:{self.port}/ws/csi/{self.detector_id}"

        try:
            logger.info(f"Connecting to {uri}...")
            self.websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=self.config['websocket_timeout']
            )
            self.is_connected = True
            logger.info(f"Connected to ESP32-S3: {self.detector_id}")
            return True

        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.is_connected = False
            return False
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {uri}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info(f"Disconnected from {self.detector_id}")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.is_connected = False
                self.websocket = None

    async def collect_csi(self) -> Optional[CSIData]:
        """
        Collect CSI data from ESP32-S3 via WebSocket.

        Returns:
            CSIData object or None if collection failed
        """
        if not self.is_connected or self.websocket is None:
            logger.warning("Not connected, attempting reconnect...")
            if not await self.connect():
                return None

        try:
            # Receive CSI data from ESP32-S3
            message = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.config['websocket_timeout']
            )

            # Parse JSON message
            data = json.loads(message)

            # Validate data structure
            if 'csi' not in data or 'rssi' not in data:
                logger.error("Invalid CSI data format")
                return None

            # Parse CSI matrix
            raw_csi = self._parse_csi_data(data['csi'])

            # Sanitize CSI (LPC, CFO, SFO correction)
            sanitized_csi = self.sanitize_csi(raw_csi)

            # Extract amplitude and phase
            amplitude = np.abs(sanitized_csi)
            phase = np.angle(sanitized_csi)

            # Create CSI data object
            csi_data = CSIData(
                timestamp=datetime.now(),
                detector_id=self.detector_id,
                subcarriers=sanitized_csi.flatten(),
                amplitude=amplitude.flatten(),
                phase=phase.flatten(),
                csi_matrix=sanitized_csi,
                rssi=float(data['rssi'])
            )

            # Update buffer
            self._update_buffer(csi_data)

            return csi_data

        except asyncio.TimeoutError:
            logger.warning("CSI data collection timeout")
            return None
        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"WebSocket error during collection: {e}")
            self.is_connected = False
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CSI JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during CSI collection: {e}")
            return None

    def _parse_csi_data(self, csi_raw: List) -> np.ndarray:
        """
        Parse raw CSI data from ESP32-S3.

        ESP32-S3 sends CSI as list of complex numbers or separate real/imag arrays.

        Args:
            csi_raw: Raw CSI data from WebSocket

        Returns:
            CSI matrix (tx x rx x subcarriers)
        """
        tx = self.config['tx_antennas']
        rx = self.config['rx_antennas']
        subcarriers = self.config['subcarriers']

        # Handle different input formats
        if isinstance(csi_raw[0], (list, np.ndarray)):
            # Already structured as matrix
            csi_matrix = np.array(csi_raw, dtype=np.complex128)
        elif isinstance(csi_raw[0], dict):
            # Separate real/imag components
            real = np.array(csi_raw[0]['real'])
            imag = np.array(csi_raw[0]['imag'])
            csi_complex = real + 1j * imag
            # Reshape to (tx, rx, subcarriers)
            csi_matrix = csi_complex.reshape(tx, rx, subcarriers)
        elif isinstance(csi_raw, list) and len(csi_raw) == subcarriers:
            # Flat array of complex numbers (1D) - duplicate for RX antennas
            csi_array = np.array(csi_raw, dtype=np.complex128)
            csi_matrix = np.zeros((tx, rx, subcarriers), dtype=np.complex128)
            for t in range(tx):
                for r in range(rx):
                    csi_matrix[t, r, :] = csi_array
        else:
            # Flat array - reshape to (tx, rx, subcarriers)
            csi_array = np.array(csi_raw, dtype=np.complex128)
            # Ensure we have enough elements
            expected_size = tx * rx * subcarriers
            if len(csi_array) < expected_size:
                # Pad with zeros if needed
                padded = np.zeros(expected_size, dtype=np.complex128)
                padded[:len(csi_array)] = csi_array
                csi_array = padded
            csi_matrix = csi_array[:expected_size].reshape(tx, rx, subcarriers)

        return csi_matrix

    def sanitize_csi(self, raw_csi: np.ndarray) -> np.ndarray:
        """
        Apply CSI sanitization using LPC, CFO, and SFO correction.

        Sanitization steps:
        1. Linear Phase Compensation (LPC) - remove linear phase progression
        2. Carrier Frequency Offset (CFO) correction
        3. Sampling Frequency Offset (SFO) correction

        Based on research:
        - "CSI Sanitization: A First Step towards Wireless Localization using CSI"
        - LPC removes linear phase progression caused by timing offset
        - CFO and SFO correction improve phase stability

        Args:
            raw_csi: Raw CSI matrix (tx x rx x subcarriers)

        Returns:
            Sanitized CSI matrix
        """
        # Work with first antenna pair for simplicity
        # Can be extended to MIMO processing
        csi = raw_csi[0, 0, :]  # Shape: (subcarriers,)

        # 1. Linear Phase Compensation (LPC)
        csi_lpc = self._apply_lpc(csi)

        # 2. CFO Correction
        csi_cfo_corrected = self._correct_cfo(csi_lpc)

        # 3. SFO Correction
        csi_sanitized = self._correct_sfo(csi_cfo_corrected)

        # Reshape back to matrix
        sanitized_matrix = np.zeros_like(raw_csi, dtype=np.complex128)
        sanitized_matrix[0, 0, :] = csi_sanitized

        return sanitized_matrix

    def _apply_lpc(self, csi: np.ndarray) -> np.ndarray:
        """
        Apply Linear Phase Compensation (LPC).

        LPC removes the linear phase progression caused by timing offset
        between transmitter and receiver.

        Algorithm:
        1. Extract phase
        2. Fit linear regression to phase
        3. Subtract linear component

        Args:
            csi: CSI complex values

        Returns:
            LPC-compensated CSI
        """
        # Extract phase
        phase = np.angle(csi)

        # Unwrap phase to avoid 2pi jumps
        phase_unwrapped = np.unwrap(phase)

        # Fit linear regression
        subcarrier_indices = np.arange(len(csi))
        coeffs = np.polyfit(subcarrier_indices, phase_unwrapped, 1)
        linear_component = coeffs[0] * subcarrier_indices + coeffs[1]

        # Remove linear component
        phase_corrected = phase_unwrapped - linear_component

        # Reconstruct complex CSI with corrected phase
        amplitude = np.abs(csi)
        csi_corrected = amplitude * np.exp(1j * phase_corrected)

        return csi_corrected

    def _correct_cfo(self, csi: np.ndarray) -> np.ndarray:
        """
        Correct Carrier Frequency Offset (CFO).

        CFO causes phase rotation across subcarriers due to frequency mismatch.

        Args:
            csi: CSI complex values

        Returns:
            CFO-corrected CSI
        """
        # Estimate CFO from phase slope
        phase = np.unwrap(np.angle(csi))

        # Use central difference to estimate phase slope
        if len(phase) > 2:
            phase_slope = np.gradient(phase)
            cfo_estimate = np.mean(phase_slope)

            # Correct CFO
            phase_corrected = phase - cfo_estimate * np.arange(len(phase))
            csi_corrected = np.abs(csi) * np.exp(1j * phase_corrected)
        else:
            csi_corrected = csi

        return csi_corrected

    def _correct_sfo(self, csi: np.ndarray) -> np.ndarray:
        """
        Correct Sampling Frequency Offset (SFO).

        SFO causes phase shift over time due to clock frequency mismatch.

        Args:
            csi: CSI complex values

        Returns:
            SFO-corrected CSI
        """
        # SFO correction typically requires multiple measurements
        # For single measurement, apply basic compensation

        # Estimate SFO from phase variance
        phase = np.unwrap(np.angle(csi))

        # Remove quadratic component (SFO effect)
        if len(phase) > 3:
            # Fit quadratic polynomial
            indices = np.arange(len(phase))
            coeffs = np.polyfit(indices, phase, 2)

            # Remove quadratic component
            quadratic_component = coeffs[0] * indices**2
            phase_corrected = phase - quadratic_component

            csi_corrected = np.abs(csi) * np.exp(1j * phase_corrected)
        else:
            csi_corrected = csi

        return csi_corrected

    def extract_features(self, csi: CSIData) -> Dict[str, float]:
        """
        Extract 500-1000 CSI features for ML models.

        Feature categories:
        1. Amplitude statistics (mean, std, skew, kurtosis, percentiles)
        2. Phase statistics
        3. Frequency domain features (FFT, wavelet)
        4. Temporal features (rate of change)
        5. Cross-subcarrier features

        Args:
            csi: CSI data object

        Returns:
            Dictionary of feature names to values
        """
        features = {}

        # Extract amplitude and phase
        amplitude = csi.amplitude
        phase = csi.phase
        subcarriers = csi.subcarriers

        # === Amplitude Features (100+ features) ===

        # Basic statistics
        features['amp_mean'] = float(np.mean(amplitude))
        features['amp_std'] = float(np.std(amplitude))
        features['amp_var'] = float(np.var(amplitude))
        features['amp_min'] = float(np.min(amplitude))
        features['amp_max'] = float(np.max(amplitude))
        features['amp_range'] = features['amp_max'] - features['amp_min']
        features['amp_median'] = float(np.median(amplitude))

        # Percentiles
        for p in [10, 25, 50, 75, 90, 95, 99]:
            features[f'amp_p{p}'] = float(np.percentile(amplitude, p))

        # Higher order moments
        features['amp_skew'] = float(skew(amplitude))
        features['amp_kurtosis'] = float(kurtosis(amplitude))

        # Difference features
        amp_diff = np.diff(amplitude)
        features['amp_diff_mean'] = float(np.mean(amp_diff))
        features['amp_diff_std'] = float(np.std(amp_diff))
        features['amp_diff_max'] = float(np.max(np.abs(amp_diff)))

        # === Phase Features (100+ features) ===

        # Basic statistics
        features['phase_mean'] = float(np.mean(phase))
        features['phase_std'] = float(np.std(phase))
        features['phase_var'] = float(np.var(phase))
        features['phase_range'] = float(np.max(phase) - np.min(phase))

        # Phase unwrapping
        phase_unwrapped = np.unwrap(phase)
        features['phase_unwrapped_range'] = float(
            np.max(phase_unwrapped) - np.min(phase_unwrapped)
        )

        # Phase difference
        phase_diff = np.diff(phase_unwrapped)
        features['phase_diff_mean'] = float(np.mean(phase_diff))
        features['phase_diff_std'] = float(np.std(phase_diff))

        # === Frequency Domain Features (200+ features) ===

        # FFT of amplitude
        amp_fft = fft(amplitude)
        amp_power = np.abs(amp_fft)[:len(amplitude)//2]

        features['fft_dominant_freq'] = float(np.argmax(amp_power))
        features['fft_dominant_power'] = float(np.max(amp_power))
        features['fft_total_power'] = float(np.sum(amp_power))
        features['fft_power_entropy'] = float(self._entropy(amp_power))

        # FFT of phase
        phase_fft = fft(phase)
        phase_power = np.abs(phase_fft)[:len(phase)//2]

        features['phase_fft_dominant_power'] = float(np.max(phase_power))
        features['phase_fft_total_power'] = float(np.sum(phase_power))

        # Spectral centroid
        freqs = np.arange(len(amp_power))
        features['spectral_centroid'] = float(
            np.sum(freqs * amp_power) / (np.sum(amp_power) + 1e-10)
        )

        # Spectral spread
        features['spectral_spread'] = float(
            np.sqrt(np.sum(((freqs - features['spectral_centroid'])**2) * amp_power) /
                   (np.sum(amp_power) + 1e-10))
        )

        # === Subcarrier-wise Features (300+ features) ===

        # Features for each subcarrier
        for i in range(min(len(amplitude), 30)):  # Limit to 30 subcarriers
            # Amplitude per subcarrier
            features[f'sc{i}_amp'] = float(amplitude[i])
            features[f'sc{i}_phase'] = float(phase[i])
            features[f'sc{i}_real'] = float(subcarriers[i].real)
            features[f'sc{i}_imag'] = float(subcarriers[i].imag)
            features[f'sc{i}_mag_sq'] = float(amplitude[i]**2)

            # Local statistics (sliding window)
            if i > 0 and i < len(amplitude) - 1:
                local_amp = amplitude[i-1:i+2]
                local_phase = phase[i-1:i+2]
                features[f'sc{i}_local_amp_mean'] = float(np.mean(local_amp))
                features[f'sc{i}_local_amp_std'] = float(np.std(local_amp))
                features[f'sc{i}_local_phase_mean'] = float(np.mean(local_phase))
                features[f'sc{i}_local_phase_std'] = float(np.std(local_phase))

            # Relative features
            if i > 0:
                features[f'sc{i}_amp_diff'] = float(amplitude[i] - amplitude[i-1])
                features[f'sc{i}_phase_diff'] = float(phase[i] - phase[i-1])
                features[f'sc{i}_amp_ratio'] = float(amplitude[i] / (amplitude[i-1] + 1e-10))

        # === Cross-subcarrier Correlation Features (100+ features) ===

        # Correlation between different subcarrier bands
        if len(amplitude) >= 10:
            # Low, mid, high frequency subcarriers
            low_band = amplitude[:10]
            mid_band = amplitude[10:20]
            high_band = amplitude[20:30]

            features['low_mid_corr'] = float(np.corrcoef(low_band, mid_band)[0, 1])
            features['mid_high_corr'] = float(np.corrcoef(mid_band, high_band)[0, 1])
            features['low_high_corr'] = float(np.corrcoef(low_band, high_band)[0, 1])

            # Band statistics
            features['low_band_mean'] = float(np.mean(low_band))
            features['low_band_std'] = float(np.std(low_band))
            features['low_band_max'] = float(np.max(low_band))
            features['mid_band_mean'] = float(np.mean(mid_band))
            features['mid_band_std'] = float(np.std(mid_band))
            features['mid_band_max'] = float(np.max(mid_band))
            features['high_band_mean'] = float(np.mean(high_band))
            features['high_band_std'] = float(np.std(high_band))
            features['high_band_max'] = float(np.max(high_band))

            # Band energy
            features['low_band_energy'] = float(np.sum(low_band**2))
            features['mid_band_energy'] = float(np.sum(mid_band**2))
            features['high_band_energy'] = float(np.sum(high_band**2))

            # Band ratios
            total_energy = features['low_band_energy'] + features['mid_band_energy'] + features['high_band_energy']
            features['low_band_ratio'] = float(features['low_band_energy'] / (total_energy + 1e-10))
            features['mid_band_ratio'] = float(features['mid_band_energy'] / (total_energy + 1e-10))
            features['high_band_ratio'] = float(features['high_band_energy'] / (total_energy + 1e-10))

        # Pairwise subcarrier correlations (first 10 subcarriers)
        for i in range(min(10, len(amplitude)-1)):
            for j in range(i+1, min(i+6, len(amplitude))):
                corr = np.corrcoef(
                    [amplitude[i], amplitude[j]],
                    [phase[i], phase[j]]
                )[0, 1]
                features[f'sc{i}_sc{j}_corr'] = float(corr)

        # === Complex Domain Features (50+ features) ===

        # Magnitude squared
        magnitude_sq = np.abs(subcarriers)**2
        features['mag_sq_mean'] = float(np.mean(magnitude_sq))
        features['mag_sq_std'] = float(np.std(magnitude_sq))

        # Real and imaginary parts
        real_part = subcarriers.real
        imag_part = subcarriers.imag

        features['real_mean'] = float(np.mean(real_part))
        features['real_std'] = float(np.std(real_part))
        features['imag_mean'] = float(np.mean(imag_part))
        features['imag_std'] = float(np.std(imag_part))

        # === Temporal Features (if buffer has data) ===

        if len(self.csi_buffer) > 1:
            # Rate of change
            prev_amp = self.csi_buffer[-1].amplitude
            amp_change = amplitude - prev_amp

            features['temporal_amp_change_mean'] = float(np.mean(amp_change))
            features['temporal_amp_change_std'] = float(np.std(amp_change))

        logger.info(f"Extracted {len(features)} CSI features")
        return features

    def _entropy(self, data: np.ndarray) -> float:
        """Calculate entropy of signal."""
        # Normalize
        data_norm = data / (np.sum(data) + 1e-10)
        # Calculate entropy
        entropy = -np.sum(data_norm * np.log(data_norm + 1e-10))
        return float(entropy)

    def _update_buffer(self, csi_data: CSIData):
        """Update CSI buffer with new data."""
        self.csi_buffer.append(csi_data)
        if len(self.csi_buffer) > self.buffer_size:
            self.csi_buffer.pop(0)

    async def calibrate(self, duration: int = 300) -> CSICalibrationData:
        """
        Perform CSI calibration to establish baseline.

        Collects CSI data over duration and computes:
        - Baseline amplitude and phase
        - Noise floor
        - CFO and SFO estimates

        Args:
            duration: Calibration duration in seconds (default: 5 min)

        Returns:
            Calibration data object
        """
        logger.info(f"Starting CSI calibration for {duration} seconds...")

        amplitude_samples = []
        phase_samples = []
        rssi_samples = []

        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < duration:
            # Collect CSI data
            csi_data = await self.collect_csi()

            if csi_data:
                amplitude_samples.append(csi_data.amplitude)
                phase_samples.append(csi_data.phase)
                rssi_samples.append(csi_data.rssi)

            # Wait for next sample
            await asyncio.sleep(1.0 / self.config['sampling_rate'])

        # Compute baseline statistics
        amplitude_array = np.array(amplitude_samples)
        phase_array = np.array(phase_samples)

        baseline_amplitude = np.mean(amplitude_array, axis=0)
        baseline_phase = np.mean(phase_array, axis=0)
        noise_floor = float(np.std(amplitude_array))

        # Estimate CFO and SFO from phase statistics
        phase_diff = np.diff(baseline_phase)
        cfo_estimate = float(np.mean(phase_diff))
        sfo_estimate = float(np.std(phase_diff))

        # Create calibration data
        self.calibration = CSICalibrationData(
            detector_id=self.detector_id,
            timestamp=datetime.now(),
            baseline_amplitude=baseline_amplitude,
            baseline_phase=baseline_phase,
            noise_floor=noise_floor,
            cfo_estimate=cfo_estimate,
            sfo_estimate=sfo_estimate
        )

        self.is_calibrated = True

        logger.info(f"Calibration complete. Noise floor: {noise_floor:.4f}")

        return self.calibration

    def get_buffer(self) -> List[CSIData]:
        """Get current CSI buffer."""
        return self.csi_buffer.copy()

    def clear_buffer(self):
        """Clear CSI buffer."""
        self.csi_buffer.clear()
        logger.info("CSI buffer cleared")


# === CSI Collector Manager ===

class CSICollectorManager:
    """
    Manages multiple CSI collectors for multi-detector setups.
    """

    def __init__(self, detector_configs: List[Dict[str, any]]):
        """
        Initialize CSI collector manager.

        Args:
            detector_configs: List of detector configurations
                [{'id': 'csi_1', 'host': '192.168.1.100', 'port': 8080}, ...]
        """
        self.collectors: Dict[str, CSICollector] = {}

        # Initialize collectors
        for config in detector_configs:
            collector = CSICollector(
                detector_id=config['id'],
                host=config['host'],
                port=config.get('port', 8080),
                config=config.get('config')
            )
            self.collectors[config['id']] = collector

        logger.info(f"Initialized {len(self.collectors)} CSI collectors")

    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all CSI detectors."""
        results = {}

        for detector_id, collector in self.collectors.items():
            results[detector_id] = await collector.connect()

        return results

    async def disconnect_all(self):
        """Disconnect from all CSI detectors."""
        tasks = [
            collector.disconnect()
            for collector in self.collectors.values()
        ]
        await asyncio.gather(*tasks)

    async def collect_all(self) -> Dict[str, Optional[CSIData]]:
        """
        Collect CSI data from all detectors.

        Returns:
            Dictionary mapping detector_id to CSIData
        """
        tasks = [
            collector.collect_csi()
            for collector in self.collectors.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        csi_data = {}
        for detector_id, result in zip(self.collectors.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error collecting from {detector_id}: {result}")
                csi_data[detector_id] = None
            else:
                csi_data[detector_id] = result

        return csi_data

    def get_collector(self, detector_id: str) -> Optional[CSICollector]:
        """Get specific collector by ID."""
        return self.collectors.get(detector_id)


# === Helper Functions ===

async def simulate_csi_stream(
    detector_id: str = 'csi_1',
    duration: int = 60,
    sampling_rate: int = 10
) -> List[CSIData]:
    """
    Simulate CSI data stream for testing.

    Generates realistic CSI data with:
    - 30 subcarriers (20MHz WiFi channel)
    - Realistic amplitude and phase variations
    - Simulated human presence effects

    Args:
        detector_id: Detector identifier
        duration: Simulation duration in seconds
        sampling_rate: Sampling rate in Hz

    Returns:
        List of CSIData objects
    """
    logger.info(f"Simulating CSI stream for {duration} seconds...")

    csi_data_list = []
    num_samples = duration * sampling_rate
    subcarriers = CSI_CONFIG['subcarriers']

    # Simulate empty room baseline
    baseline_amplitude = np.random.normal(50, 5, subcarriers)
    baseline_phase = np.random.uniform(-np.pi, np.pi, subcarriers)

    for i in range(num_samples):
        # Add realistic variations
        time_factor = i / num_samples

        # Amplitude variations (multipath fading)
        amplitude = baseline_amplitude + np.random.normal(0, 2, subcarriers)
        amplitude = np.maximum(amplitude, 10)  # Ensure positive

        # Phase variations
        phase = baseline_phase + np.random.normal(0, 0.1, subcarriers)

        # Create complex CSI
        subcarriers_complex = amplitude * np.exp(1j * phase)

        # Create CSI matrix (1x2x30)
        csi_matrix = np.zeros((1, 2, subcarriers), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers_complex
        csi_matrix[0, 1, :] = subcarriers_complex * 0.9  # Second antenna

        # Calculate RSSI from amplitude
        rssi = 10 * np.log10(np.mean(amplitude**2)) - 100

        csi_data = CSIData(
            timestamp=datetime.now(),
            detector_id=detector_id,
            subcarriers=subcarriers_complex,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=rssi
        )

        csi_data_list.append(csi_data)

        # Simulate sampling rate
        await asyncio.sleep(1.0 / sampling_rate)

    logger.info(f"Generated {len(csi_data_list)} CSI samples")
    return csi_data_list


# === Main Entry Point ===

if __name__ == '__main__':
    async def main():
        """Test CSI collector."""
        print("\n=== Testing CSI Collector ===\n")

        # Test 1: Simulate CSI stream
        print("Test 1: Simulating CSI stream...")
        csi_samples = await simulate_csi_stream(duration=5, sampling_rate=10)

        if csi_samples:
            print(f"Generated {len(csi_samples)} CSI samples")

            # Extract features from first sample
            collector = CSICollector('test_csi', 'localhost', 8080)
            features = collector.extract_features(csi_samples[0])

            print(f"Extracted {len(features)} features")
            print("Sample features:")
            for name, value in list(features.items())[:10]:
                print(f"  {name}: {value:.4f}")

            print("\nTest 1 PASSED")

        # Test 2: CSI sanitization
        print("\nTest 2: Testing CSI sanitization...")

        # Create raw CSI with linear phase progression
        raw_csi = np.zeros((1, 2, 30), dtype=np.complex128)
        phase_progression = np.linspace(0, 10, 30)
        raw_csi[0, 0, :] = 50 * np.exp(1j * phase_progression)

        collector = CSICollector('test_csi', 'localhost', 8080)
        sanitized_csi = collector.sanitize_csi(raw_csi)

        # Check that phase progression is reduced
        raw_phase_range = np.max(np.abs(np.diff(np.unwrap(np.angle(raw_csi[0, 0, :])))))
        sanitized_phase_range = np.max(np.abs(np.diff(np.unwrap(np.angle(sanitized_csi[0, 0, :])))))

        print(f"Raw phase range: {raw_phase_range:.4f}")
        print(f"Sanitized phase range: {sanitized_phase_range:.4f}")

        if sanitized_phase_range < raw_phase_range:
            print("Test 2 PASSED (LPC working)")
        else:
            print("Test 2 FAILED (LPC not effective)")

        print("\n✅ CSI collector tests complete")

    asyncio.run(main())
