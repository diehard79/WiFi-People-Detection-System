"""
CSI Collector Module Tests

Comprehensive tests for CSI data collection, sanitization, and feature extraction.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.csi_collector import (
    CSIData,
    CSICollector,
    CSICollectorManager,
    CSICalibrationData,
    simulate_csi_stream,
    CSI_CONFIG
)


class TestCSIData:
    """Test CSIData dataclass."""

    def test_csi_data_creation(self):
        """Test creating CSIData object."""
        timestamp = datetime.now()
        detector_id = "test_detector"
        subcarriers = np.random.randn(30) + 1j * np.random.randn(30)
        amplitude = np.abs(subcarriers)
        phase = np.angle(subcarriers)
        csi_matrix = np.zeros((1, 2, 30), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers
        rssi = -50.0

        csi_data = CSIData(
            timestamp=timestamp,
            detector_id=detector_id,
            subcarriers=subcarriers,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=rssi
        )

        assert csi_data.detector_id == detector_id
        assert csi_data.rssi == rssi
        assert len(csi_data.subcarriers) == 30
        assert len(csi_data.amplitude) == 30
        assert len(csi_data.phase) == 30

    def test_csi_data_to_dict(self):
        """Test CSIData serialization to dictionary."""
        timestamp = datetime.now()
        subcarriers = np.random.randn(30) + 1j * np.random.randn(30)
        amplitude = np.abs(subcarriers)
        phase = np.angle(subcarriers)
        csi_matrix = np.zeros((1, 2, 30), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers

        csi_data = CSIData(
            timestamp=timestamp,
            detector_id="test",
            subcarriers=subcarriers,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=-50.0
        )

        data_dict = csi_data.to_dict()

        assert 'timestamp' in data_dict
        assert 'detector_id' in data_dict
        assert 'subcarriers_real' in data_dict
        assert 'subcarriers_imag' in data_dict
        assert 'amplitude' in data_dict
        assert 'phase' in data_dict
        assert 'rssi' in data_dict


class TestCSICollector:
    """Test CSICollector class."""

    @pytest.fixture
    def collector(self):
        """Create a CSICollector instance for testing."""
        return CSICollector(
            detector_id="test_csi",
            host="localhost",
            port=8080
        )

    def test_collector_initialization(self, collector):
        """Test collector initialization."""
        assert collector.detector_id == "test_csi"
        assert collector.host == "localhost"
        assert collector.port == 8080
        assert not collector.is_connected
        assert not collector.is_calibrated
        assert len(collector.csi_buffer) == 0

    def test_parse_csi_data_flat(self, collector):
        """Test parsing flat CSI array."""
        # Create flat complex array with enough elements for 1x2x30 matrix
        csi_flat = list(np.random.randn(60) + 1j * np.random.randn(60))

        result = collector._parse_csi_data(csi_flat)

        assert result.shape == (1, 2, 30)
        assert result.dtype == np.complex128

    def test_parse_csi_data_matrix(self, collector):
        """Test parsing structured CSI matrix."""
        # Create structured matrix
        csi_matrix = np.random.randn(1, 2, 30) + 1j * np.random.randn(1, 2, 30)

        result = collector._parse_csi_data(csi_matrix.tolist())

        assert result.shape == (1, 2, 30)
        assert result.dtype == np.complex128

    def test_apply_lpc(self, collector):
        """Test Linear Phase Compensation (LPC)."""
        # Create CSI with linear phase progression
        phase_progression = np.linspace(0, 10, 30)
        csi = 50 * np.exp(1j * phase_progression)

        csi_corrected = collector._apply_lpc(csi)

        # Check that linear phase progression is reduced
        original_phase_range = np.max(np.abs(np.diff(np.unwrap(np.angle(csi)))))
        corrected_phase_range = np.max(np.abs(np.diff(np.unwrap(np.angle(csi_corrected)))))

        assert corrected_phase_range < original_phase_range

    def test_correct_cfo(self, collector):
        """Test Carrier Frequency Offset (CFO) correction."""
        # Create CSI with CFO
        phase = np.random.randn(30) + np.linspace(0, 5, 30)
        csi = 50 * np.exp(1j * phase)

        csi_corrected = collector._correct_cfo(csi)

        # CFO correction should modify the signal
        assert not np.allclose(csi, csi_corrected)

    def test_correct_sfo(self, collector):
        """Test Sampling Frequency Offset (SFO) correction."""
        # Create CSI with SFO
        phase = np.linspace(0, 10, 30)**2
        csi = 50 * np.exp(1j * phase)

        csi_corrected = collector._correct_sfo(csi)

        # SFO correction should modify the signal
        assert not np.allclose(csi, csi_corrected)

    def test_sanitize_csi(self, collector):
        """Test full CSI sanitization pipeline."""
        # Create raw CSI with multiple issues
        raw_csi = np.zeros((1, 2, 30), dtype=np.complex128)
        phase_progression = np.linspace(0, 10, 30)
        raw_csi[0, 0, :] = 50 * np.exp(1j * phase_progression)

        sanitized_csi = collector.sanitize_csi(raw_csi)

        # Check output shape
        assert sanitized_csi.shape == raw_csi.shape
        assert sanitized_csi.dtype == np.complex128

        # Check that phase is more stable after sanitization
        raw_phase_var = np.var(np.unwrap(np.angle(raw_csi[0, 0, :])))
        sanitized_phase_var = np.var(np.unwrap(np.angle(sanitized_csi[0, 0, :])))

        assert sanitized_phase_var < raw_phase_var

    def test_extract_features(self, collector):
        """Test feature extraction from CSI data."""
        # Create sample CSI data
        timestamp = datetime.now()
        subcarriers = np.random.randn(30) + 1j * np.random.randn(30)
        amplitude = np.abs(subcarriers)
        phase = np.angle(subcarriers)
        csi_matrix = np.zeros((1, 2, 30), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers

        csi_data = CSIData(
            timestamp=timestamp,
            detector_id="test",
            subcarriers=subcarriers,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=-50.0
        )

        features = collector.extract_features(csi_data)

        # Check that features are extracted
        assert len(features) > 300  # Should extract 300+ features

        # Check for expected feature categories
        assert 'amp_mean' in features
        assert 'amp_std' in features
        assert 'phase_mean' in features
        assert 'fft_dominant_power' in features
        assert 'spectral_centroid' in features

        # Check that all values are finite
        for name, value in features.items():
            assert np.isfinite(value), f"Feature {name} is not finite: {value}"

    def test_entropy_calculation(self, collector):
        """Test entropy calculation."""
        # Create test power spectrum
        power_spectrum = np.array([1, 2, 3, 4, 5])

        entropy = collector._entropy(power_spectrum)

        assert entropy > 0
        assert np.isfinite(entropy)

    def test_buffer_operations(self, collector):
        """Test CSI buffer operations."""
        # Create sample CSI data
        subcarriers = np.random.randn(30) + 1j * np.random.randn(30)
        amplitude = np.abs(subcarriers)
        phase = np.angle(subcarriers)
        csi_matrix = np.zeros((1, 2, 30), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers

        csi_data = CSIData(
            timestamp=datetime.now(),
            detector_id="test",
            subcarriers=subcarriers,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=-50.0
        )

        # Test adding to buffer
        collector._update_buffer(csi_data)
        assert len(collector.csi_buffer) == 1

        # Test buffer size limit
        for _ in range(200):
            collector._update_buffer(csi_data)

        assert len(collector.csi_buffer) <= collector.buffer_size

        # Test clearing buffer
        collector.clear_buffer()
        assert len(collector.csi_buffer) == 0


class TestCSICollectorManager:
    """Test CSICollectorManager class."""

    @pytest.fixture
    def manager(self):
        """Create a CSICollectorManager for testing."""
        detector_configs = [
            {'id': 'csi_1', 'host': '192.168.1.101', 'port': 8080},
            {'id': 'csi_2', 'host': '192.168.1.102', 'port': 8080},
        ]
        return CSICollectorManager(detector_configs)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert len(manager.collectors) == 2
        assert 'csi_1' in manager.collectors
        assert 'csi_2' in manager.collectors

    def test_get_collector(self, manager):
        """Test getting specific collector."""
        collector = manager.get_collector('csi_1')
        assert collector is not None
        assert collector.detector_id == 'csi_1'

        # Test non-existent collector
        collector = manager.get_collector('csi_99')
        assert collector is None


class TestCSISimulation:
    """Test CSI simulation functions."""

    @pytest.mark.asyncio
    async def test_simulate_csi_stream(self):
        """Test CSI stream simulation."""
        csi_samples = await simulate_csi_stream(
            detector_id='test_csi',
            duration=2,  # 2 seconds
            sampling_rate=10
        )

        assert len(csi_samples) == 20  # 2 seconds * 10 Hz

        # Check first sample
        first_sample = csi_samples[0]
        assert isinstance(first_sample, CSIData)
        assert first_sample.detector_id == 'test_csi'
        assert len(first_sample.subcarriers) == CSI_CONFIG['subcarriers']
        assert len(first_sample.amplitude) == CSI_CONFIG['subcarriers']
        assert len(first_sample.phase) == CSI_CONFIG['subcarriers']

    @pytest.mark.asyncio
    async def test_simulate_csi_with_collector(self):
        """Test using simulated CSI with collector."""
        # Generate simulated data
        csi_samples = await simulate_csi_stream(duration=1, sampling_rate=10)

        # Create collector and extract features
        collector = CSICollector('test', 'localhost', 8080)
        features = collector.extract_features(csi_samples[0])

        # Verify features (extracts 400+ features)
        assert len(features) > 400
        assert 'amp_mean' in features


class TestCSIConfiguration:
    """Test CSI configuration."""

    def test_csi_config_exists(self):
        """Test that CSI_CONFIG is properly defined."""
        assert 'sampling_rate' in CSI_CONFIG
        assert 'subcarriers' in CSI_CONFIG
        assert 'calibration_duration' in CSI_CONFIG
        assert 'detectors' in CSI_CONFIG

    def test_csi_config_values(self):
        """Test CSI configuration values."""
        assert CSI_CONFIG['sampling_rate'] > 0
        assert CSI_CONFIG['subcarriers'] in [30, 64, 128]
        assert CSI_CONFIG['calibration_duration'] > 0
        assert len(CSI_CONFIG['detectors']) > 0


@pytest.mark.integration
class TestCSIIntegration:
    """Integration tests for CSI collection (requires hardware)."""

    @pytest.mark.asyncio
    async def test_collector_connection_mock(self):
        """Test collector connection with mocked WebSocket."""
        collector = CSICollector('test', 'localhost', 8080)

        # Mock WebSocket connection
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(return_value='{"csi": [[1+1j]], "rssi": -50}')
            mock_connect.return_value = mock_ws

            result = await collector.connect()

            # Connection attempt is made (may fail in test environment)
            assert mock_connect.called


# === Performance Tests ===

class TestCSIPerformance:
    """Performance tests for CSI processing."""

    def test_feature_extraction_performance(self):
        """Test feature extraction performance."""
        import time

        # Create sample CSI data
        subcarriers = np.random.randn(30) + 1j * np.random.randn(30)
        amplitude = np.abs(subcarriers)
        phase = np.angle(subcarriers)
        csi_matrix = np.zeros((1, 2, 30), dtype=np.complex128)
        csi_matrix[0, 0, :] = subcarriers

        csi_data = CSIData(
            timestamp=datetime.now(),
            detector_id="test",
            subcarriers=subcarriers,
            amplitude=amplitude,
            phase=phase,
            csi_matrix=csi_matrix,
            rssi=-50.0
        )

        collector = CSICollector('test', 'localhost', 8080)

        # Time feature extraction
        start = time.time()
        features = collector.extract_features(csi_data)
        elapsed = time.time() - start

        # Feature extraction should be fast (< 100ms)
        assert elapsed < 0.1
        assert len(features) > 300  # Updated to match actual implementation

    def test_sanitization_performance(self):
        """Test sanitization performance."""
        import time

        raw_csi = np.random.randn(1, 2, 30) + 1j * np.random.randn(1, 2, 30)
        collector = CSICollector('test', 'localhost', 8080)

        # Time sanitization
        start = time.time()
        for _ in range(100):
            sanitized = collector.sanitize_csi(raw_csi)
        elapsed = time.time() - start

        # Sanitization should be fast (< 1ms per sample)
        assert elapsed < 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
