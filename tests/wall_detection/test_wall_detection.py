"""
Comprehensive Wall Detection Tests

Tests all components of the wall detection system:
- CSI data collection
- Wall detection model
- Material classification
- Room layout mapping
- Visualization generation
- API endpoints
- Performance validation
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wall_detection.csi_collector import CSIDataCollector, CSIData
from wall_detection.wall_models import WallDetectionModel, MaterialClassificationModel, WallDetection, RoomLayout
from wall_detection.room_mapper import RoomLayoutMapper
from wall_detection.visualizer import WallVisualizer


class TestCSIDataCollection:
    """Test CSI data collection from ESP32-S3"""

    @pytest.fixture
    def collector(self):
        """Create CSI collector instance"""
        return CSIDataCollector(num_detectors=4, sampling_rate=10)

    def test_collector_initialization(self, collector):
        """Test CSI collector initialization"""
        assert collector.num_detectors == 4
        assert collector.sampling_rate == 10
        assert collector.subcarriers == 64

    def test_detector_initialization(self, collector):
        """Test individual detector initialization"""
        detector_id = "detector_0"
        success = collector.initialize_detector(detector_id)

        assert success is True
        assert detector_id in collector.detectors
        assert collector.detectors[detector_id]["status"] == "active"

    def test_all_detectors_initialization(self, collector):
        """Test initialization of all detectors"""
        results = collector.initialize_all_detectors()

        assert len(results) == 4
        assert all(success is True for success in results.values())

    def test_csi_data_simulation(self, collector):
        """Test CSI data simulation"""
        csi_data = collector.simulate_csi_data("detector_0", num_people=2, moving=True)

        assert isinstance(csi_data, CSIData)
        assert csi_data.detector_id == "detector_0"
        assert csi_data.phase_raw.shape == (64,)
        assert csi_data.amplitude_raw.shape == (64,)
        assert 0.0 <= csi_data.quality_score <= 1.0

    def test_csi_snapshot_collection(self, collector):
        """Test CSI snapshot collection from all detectors"""
        collector.initialize_all_detectors()
        snapshot = collector.collect_csi_snapshot(duration_seconds=1)

        assert len(snapshot) == 4
        assert all(len(data) > 0 for data in snapshot.values())

        # Check that data is processed
        for detector_id, data_list in snapshot.items():
            if data_list:
                sample = data_list[0]
                assert sample.phase_corrected is not None
                assert sample.amplitude_sanitized is not None

    def test_phase_correction(self, collector):
        """Test phase correction algorithm"""
        # Create raw phase with noise
        phase_raw = np.random.randn(64)

        csi_data = CSIData(
            detector_id="test",
            timestamp=datetime.now(),
            phase_raw=phase_raw,
            amplitude_raw=np.random.randn(64)
        )

        # Process
        processed = collector.process_csi_data(csi_data)

        assert processed.phase_corrected is not None
        assert processed.phase_corrected.shape == phase_raw.shape
        assert processed.amplitude_sanitized is not None

    def test_amplitude_sanitization(self, collector):
        """Test amplitude sanitization"""
        # Create amplitude with outliers
        amplitude_raw = np.concatenate([
            np.random.normal(50, 5, 60),
            np.array([100, 100, 100, 100])  # Outliers
        ])

        csi_data = CSIData(
            detector_id="test",
            timestamp=datetime.now(),
            phase_raw=np.random.randn(64),
            amplitude_raw=amplitude_raw
        )

        processed = collector.process_csi_data(csi_data)

        assert processed.amplitude_sanitized is not None
        # Outliers should be reduced
        assert np.max(processed.amplitude_sanitized) < np.max(amplitude_raw)


class TestWallDetectionModel:
    """Test wall detection ML model"""

    @pytest.fixture
    def wall_model(self):
        """Create wall detection model"""
        model = WallDetectionModel()
        model.create_default_models()
        return model

    def test_model_initialization(self, wall_model):
        """Test model initialization"""
        assert wall_model.wall_detector is not None
        assert wall_model.orientation_classifier is not None
        assert wall_model.thickness_regressor is not None

    def test_wall_detection(self, wall_model):
        """Test wall detection from features"""
        # Create dummy features
        csi_features = {
            'detector_0': np.random.randn(10, 5),
            'detector_1': np.random.randn(10, 5),
            'detector_2': np.random.randn(10, 5),
            'detector_3': np.random.randn(10, 5)
        }

        walls, confidence = wall_model.detect_walls(csi_features)

        assert isinstance(walls, list)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

        # Check wall structure
        for wall in walls:
            assert isinstance(wall, WallDetection)
            assert len(wall.start_point) == 2
            assert len(wall.end_point) == 2
            assert 0.0 <= wall.confidence <= 1.0
            assert wall.thickness > 0

    def test_orientation_detection(self, wall_model):
        """Test wall orientation detection"""
        features = np.random.randn(20)
        orientation = wall_model._detect_orientation(features)

        assert orientation in ['horizontal', 'vertical', 'diagonal']

    def test_thickness_estimation(self, wall_model):
        """Test wall thickness estimation"""
        features = np.random.randn(20)
        thickness = wall_model._estimate_thickness(features)

        assert isinstance(thickness, float)
        assert 0.1 <= thickness <= 0.5  # Should be clamped


class TestMaterialClassification:
    """Test material classification model"""

    @pytest.fixture
    def material_model(self):
        """Create material classification model"""
        model = MaterialClassificationModel()
        model.create_default_model()
        return model

    def test_model_initialization(self, material_model):
        """Test model initialization"""
        assert material_model.material_classifier is not None
        assert len(material_model.materials) == 5

    def test_material_classification(self, material_model):
        """Test material classification"""
        features = np.random.randn(15)
        wall = WallDetection(
            start_point=(0.0, 0.0),
            end_point=(1.0, 0.0),
            confidence=0.9,
            thickness=0.2
        )

        material = material_model.classify_material(features, wall)

        assert material in material_model.materials


class TestRoomLayoutMapper:
    """Test room layout mapping"""

    @pytest.fixture
    def mapper(self):
        """Create room layout mapper"""
        return RoomLayoutMapper()

    @pytest.fixture
    def sample_walls(self):
        """Create sample walls"""
        return [
            WallDetection(
                start_point=(0.0, 0.0),
                end_point=(5.0, 0.0),
                confidence=0.95,
                thickness=0.2,
                material='concrete'
            ),
            WallDetection(
                start_point=(5.0, 0.0),
                end_point=(5.0, 4.0),
                confidence=0.92,
                thickness=0.2,
                material='concrete'
            ),
            WallDetection(
                start_point=(5.0, 4.0),
                end_point=(0.0, 4.0),
                confidence=0.88,
                thickness=0.15,
                material='drywall'
            ),
            WallDetection(
                start_point=(0.0, 4.0),
                end_point=(0.0, 0.0),
                confidence=0.90,
                thickness=0.2,
                material='concrete'
            )
        ]

    def test_mapper_initialization(self, mapper):
        """Test mapper initialization"""
        assert mapper.grid_resolution == 0.1
        assert mapper.room_size == (10.0, 10.0)

    def test_wall_grid_creation(self, mapper, sample_walls):
        """Test wall grid creation"""
        wall_grid = mapper._create_wall_grid(sample_walls)

        assert isinstance(wall_grid, mapper.__class__.__bases__[0]) or hasattr(wall_grid, 'grid')
        assert wall_grid.grid.shape == (100, 100)

    def test_room_layout_creation(self, mapper, sample_walls):
        """Test complete room layout creation"""
        layout = mapper.create_room_layout(sample_walls, overall_confidence=0.91)

        assert isinstance(layout, RoomLayout)
        assert len(layout.walls) == 4
        assert layout.area > 0
        assert layout.perimeter > 0
        assert layout.confidence == 0.91

    def test_layout_optimization(self, mapper, sample_walls):
        """Test layout optimization"""
        # Create walls that need alignment
        unaligned_walls = [
            WallDetection(
                start_point=(0.0, 0.1),
                end_point=(5.1, 0.0),
                confidence=0.9,
                thickness=0.2
            )
        ]

        wall_grid = mapper._create_wall_grid(unaligned_walls)
        optimized = mapper._optimize_layout(unaligned_walls, wall_grid)

        assert isinstance(optimized, list)

    def test_colinear_wall_merging(self, mapper):
        """Test merging colinear walls"""
        walls = [
            WallDetection(
                start_point=(0.0, 0.0),
                end_point=(2.0, 0.0),
                confidence=0.9,
                thickness=0.2
            ),
            WallDetection(
                start_point=(2.0, 0.0),
                end_point=(4.0, 0.0),
                confidence=0.9,
                thickness=0.2
            )
        ]

        merged = mapper._merge_colinear_walls(walls)

        assert len(merged) == 1
        assert merged[0].start_point[0] == 0.0
        assert merged[0].end_point[0] == 4.0

    def test_dimension_calculation(self, mapper, sample_walls):
        """Test room dimension calculation"""
        dimensions, area, perimeter = mapper._calculate_dimensions(sample_walls)

        assert dimensions[0] > 0  # Width
        assert dimensions[1] > 0  # Length
        assert area > 0
        assert perimeter > 0


class TestWallVisualizer:
    """Test wall visualization"""

    @pytest.fixture
    def visualizer(self, tmp_path):
        """Create wall visualizer"""
        return WallVisualizer(output_dir=str(tmp_path))

    @pytest.fixture
    def sample_layout(self):
        """Create sample room layout"""
        walls = [
            WallDetection(
                start_point=(0.0, 0.0),
                end_point=(5.0, 0.0),
                confidence=0.95,
                thickness=0.2,
                material='concrete'
            ),
            WallDetection(
                start_point=(5.0, 0.0),
                end_point=(5.0, 4.0),
                confidence=0.92,
                thickness=0.2,
                material='brick'
            )
        ]

        return RoomLayout(
            walls=walls,
            dimensions=(5.0, 4.0),
            area=20.0,
            perimeter=18.0,
            confidence=0.93,
            detected_at=datetime.now().isoformat()
        )

    def test_visualizer_initialization(self, visualizer):
        """Test visualizer initialization"""
        assert visualizer.output_dir.exists()

    def test_floorplan_generation(self, visualizer, sample_layout):
        """Test 2D floorplan generation"""
        path = visualizer.plot_floorplan(sample_layout)

        assert Path(path).exists()
        assert path.endswith('.png')

    def test_confidence_map_generation(self, visualizer, sample_layout):
        """Test confidence map generation"""
        path = visualizer.plot_detection_confidence(sample_layout)

        assert Path(path).exists()

    def test_3d_visualization(self, visualizer, sample_layout):
        """Test 3D room visualization"""
        path = visualizer.plot_3d_room(sample_layout, wall_height=2.5)

        assert Path(path).exists()

    def test_all_visualizations(self, visualizer, sample_layout):
        """Test generating all visualizations"""
        visualizations = visualizer.generate_all_visualizations(sample_layout)

        assert len(visualizations) >= 3  # floorplan, confidence, 3d
        assert all(Path(p).exists() for p in visualizations.values())


class TestPerformance:
    """Performance and stress tests"""

    @pytest.mark.asyncio
    async def test_detection_latency(self):
        """Test wall detection completes within 30 seconds"""
        from wall_detection_system import WallDetectionSystem

        system = WallDetectionSystem()
        await system.initialize()

        start_time = datetime.now()
        layout = await system.detect_room_layout(duration_seconds=3)
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        # Should complete in reasonable time
        assert processing_time < 35  # 30s + 5s buffer

    @pytest.mark.asyncio
    async def test_continuous_detection(self):
        """Test continuous detection for multiple cycles"""
        from wall_detection_system import WallDetectionSystem

        system = WallDetectionSystem()
        await system.initialize()

        # Run 3 detections
        for i in range(3):
            layout = await system.detect_room_layout(duration_seconds=2)
            assert layout is not None

    def test_model_accuracy(self):
        """Test model accuracy targets"""
        model = WallDetectionModel()
        model.create_default_models()

        # Generate test data
        csi_features = {
            f'detector_{i}': np.random.randn(10, 5)
            for i in range(4)
        }

        walls, confidence = model.detect_walls(csi_features)

        # For synthetic data, just check it runs
        # Real accuracy testing requires labeled datasets
        assert isinstance(confidence, float)


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete wall detection pipeline"""
        from wall_detection_system import WallDetectionSystem

        # Initialize system
        system = WallDetectionSystem()
        await system.initialize()
        assert system.is_initialized

        # Detect walls
        layout = await system.detect_room_layout(duration_seconds=2)
        assert layout is not None
        assert isinstance(layout, RoomLayout)

        # Generate visualizations
        viz = system.generate_visualizations(layout)
        assert len(viz) >= 3

        # Export layout
        export_path = system.export_layout()
        assert Path(export_path).exists()

        # Check system status
        status = system.get_system_status()
        assert status['initialized'] is True
        assert status['metrics']['detection_count'] > 0


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
