"""
End-to-End Wall Detection Tests

Complete integration tests for the wall detection system:
- Full pipeline testing
- Calibration workflow
- Multi-room detection
- API integration
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).dirname().parent.parent / "src"))

from wall_detection_system import WallDetectionSystem
from wall_detection import (
    CSIDataCollector,
    WallDetectionModel,
    MaterialClassificationModel,
    RoomLayoutMapper,
    WallVisualizer
)


class TestWallDetectionE2E:
    """End-to-end integration tests"""

    @pytest.fixture
    async def system(self):
        """Create and initialize wall detection system"""
        # Create temporary output directory
        temp_dir = tempfile.mkdtemp()

        system = WallDetectionSystem(output_dir=temp_dir)
        await system.initialize()

        yield system

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_detection_pipeline(self, system):
        """
        Test complete wall detection pipeline from CSI to layout

        Pipeline:
        1. System initialization
        2. CSI data collection
        3. Feature extraction
        4. Wall detection
        5. Material classification
        6. Layout generation
        7. Visualization
        8. Export
        """
        # System should be initialized
        assert system.is_initialized
        assert system.csi_collectors is not None

        # Detect room layout
        layout = await system.detect_room_layout(
            duration_seconds=3,
            classify_materials=True
        )

        # Verify layout
        assert layout is not None
        assert hasattr(layout, 'walls')
        assert hasattr(layout, 'dimensions')
        assert hasattr(layout, 'area')
        assert hasattr(layout, 'confidence')

        # Check walls
        if len(layout.walls) > 0:
            # Verify wall structure
            for wall in layout.walls:
                assert hasattr(wall, 'start_point')
                assert hasattr(wall, 'end_point')
                assert hasattr(wall, 'confidence')
                assert hasattr(wall, 'thickness')

            # Check material classification
            if layout.walls[0].material:
                assert layout.walls[0].material in [
                    'concrete', 'brick', 'drywall', 'wood', 'glass'
                ]

        # Generate visualizations
        visualizations = system.generate_visualizations(layout)

        assert len(visualizations) >= 3
        assert 'floorplan' in visualizations
        assert 'confidence' in visualizations
        assert '3d' in visualizations

        # Verify visualization files exist
        for viz_path in visualizations.values():
            assert Path(viz_path).exists()

        # Export layout
        export_path = system.export_layout()
        assert Path(export_path).exists()

        # Verify export format
        import json
        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        assert 'dimensions' in exported_data
        assert 'walls' in exported_data
        assert 'area' in exported_data

    @pytest.mark.asyncio
    async def test_calibration_workflow(self, system):
        """
        Test 5-minute calibration workflow

        Tests:
        1. Calibration initiation
        2. Progress tracking
        3. Background calibration
        4. Completion handling
        """
        # Short calibration for testing (30s instead of 300s)
        calibration_duration = 2  # seconds

        # Progress tracking
        progress_updates = []

        async def progress_callback(progress: float):
            progress_updates.append(progress)

        # Start calibration
        calibration_task = asyncio.create_task(
            system.calibrate_system(
                duration_seconds=calibration_duration,
                progress_callback=progress_callback
            )
        )

        # Wait for completion
        await calibration_task

        # Verify calibration completed
        assert not system.is_calibrating
        assert len(progress_updates) > 0

        # Check final progress
        assert progress_updates[-1] >= 0.9  # Should reach near 100%

        # Verify calibration status
        collector = system.csi_collectors.get('main')
        if collector:
            status = collector.get_calibration_status()
            assert status['is_calibrated'] is True
            assert status['samples_collected'] > 0

    @pytest.mark.asyncio
    async def test_multi_detection_cycle(self, system):
        """
        Test multiple detection cycles

        Verifies system can handle multiple detections reliably
        """
        num_cycles = 3
        layouts = []

        for i in range(num_cycles):
            layout = await system.detect_room_layout(duration_seconds=2)
            layouts.append(layout)

            # Small delay between detections
            await asyncio.sleep(0.5)

        # Verify all detections completed
        assert len(layouts) == num_cycles

        # Check metrics updated
        assert system.metrics['detection_count'] == num_cycles
        assert system.metrics['avg_processing_time'] > 0

    @pytest.mark.asyncio
    async def test_continuous_monitoring(self, system):
        """
        Test continuous monitoring background task

        Verifies:
        1. Background task startup
        2. Periodic detection
        3. Callback handling
        4. Task cancellation
        """
        detections = []

        async def detection_callback(layout):
            detections.append(layout)

        # Start continuous monitoring
        monitoring_task = asyncio.create_task(
            system.continuous_monitoring(
                detection_interval=2,  # Detect every 2 seconds
                callback=detection_callback
            )
        )

        # Let it run for a few cycles
        await asyncio.sleep(5)

        # Cancel monitoring
        monitoring_task.cancel()

        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass

        # Verify detections occurred
        assert len(detections) >= 1

    @pytest.mark.asyncio
    async def test_system_status(self, system):
        """Test system status reporting"""
        # Get status before detection
        status = system.get_system_status()

        assert 'initialized' in status
        assert 'calibrating' in status
        assert 'metrics' in status

        # After detection
        await system.detect_room_layout(duration_seconds=2)

        status = system.get_system_status()
        assert status['current_layout'] is not None
        assert status['last_detection'] is not None
        assert status['metrics']['detection_count'] > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, system):
        """Test error handling and recovery"""
        # Test detection before initialization
        uninitialized_system = WallDetectionSystem()

        with pytest.raises(RuntimeError):
            await uninitialized_system.detect_room_layout()

        # Test visualization without layout
        empty_system = WallDetectionSystem()
        await empty_system.initialize()

        with pytest.raises(RuntimeError):
            empty_system.generate_visualizations()

        # Test export without layout
        with pytest.raises(RuntimeError):
            empty_system.export_layout()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, system):
        """Test concurrent detection operations"""
        # Run multiple detections concurrently
        tasks = [
            system.detect_room_layout(duration_seconds=2)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # At least some should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0


class TestComponentIntegration:
    """Test integration between components"""

    @pytest.mark.asyncio
    async def test_collector_to_features(self):
        """Test CSI collector to feature extraction"""
        collector = CSIDataCollector(num_detectors=4)
        collector.initialize_all_detectors()

        # Collect CSI data
        snapshot = collector.collect_csi_snapshot(duration_seconds=1)

        # Extract features
        features = {}
        for detector_id, data_list in snapshot.items():
            if data_list:
                # Extract phase and amplitude features
                sample = data_list[0]
                if sample.phase_corrected is not None:
                    features[f'{detector_id}_phase_mean'] = float(np.mean(sample.phase_corrected))
                    features[f'{detector_id}_phase_std'] = float(np.std(sample.phase_corrected))

                if sample.amplitude_sanitized is not None:
                    features[f'{detector_id}_amp_mean'] = float(np.mean(sample.amplitude_sanitized))
                    features[f'{detector_id}_amp_std'] = float(np.std(sample.amplitude_sanitized))

        assert len(features) > 0
        assert all(isinstance(v, float) for v in features.values())

    @pytest.mark.asyncio
    async def test_model_to_layout(self):
        """Test wall detection model to room layout"""
        # Create models
        wall_model = WallDetectionModel()
        wall_model.create_default_models()

        mapper = RoomLayoutMapper()

        # Generate features
        csi_features = {
            f'detector_{i}': np.random.randn(10, 5)
            for i in range(4)
        }

        # Detect walls
        walls, confidence = wall_model.detect_walls(csi_features)

        # Create layout
        layout = mapper.create_room_layout(walls, confidence)

        assert layout is not None
        assert hasattr(layout, 'walls')
        assert hasattr(layout, 'dimensions')

    @pytest.mark.asyncio
    async def test_layout_to_visualization(self):
        """Test room layout to visualization generation"""
        from wall_detection import WallDetection, RoomLayout

        # Create sample layout
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

        layout = RoomLayout(
            walls=walls,
            dimensions=(5.0, 4.0),
            area=20.0,
            perimeter=18.0,
            confidence=0.91,
            detected_at=datetime.now().isoformat()
        )

        # Generate visualizations
        with tempfile.TemporaryDirectory() as temp_dir:
            visualizer = WallVisualizer(output_dir=temp_dir)
            visualizations = visualizer.generate_all_visualizations(layout)

            assert len(visualizations) >= 3
            assert all(Path(p).exists() for p in visualizations.values())


class TestPerformanceE2E:
    """End-to-end performance tests"""

    @pytest.mark.asyncio
    async def test_detection_performance(self):
        """Test detection performance under load"""
        system = WallDetectionSystem()
        await system.initialize()

        # Measure multiple detections
        times = []
        for _ in range(5):
            start = datetime.now()
            await system.detect_room_layout(duration_seconds=2)
            end = datetime.now()
            times.append((end - start).total_seconds())

        avg_time = sum(times) / len(times)

        # Should complete in reasonable time
        assert avg_time < 10  # seconds

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test system doesn't leak memory"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        system = WallDetectionSystem()
        await system.initialize()

        initial_memory = process.memory_info().rss

        # Run multiple detections
        for _ in range(5):
            await system.detect_room_layout(duration_seconds=2)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100 * 1024 * 1024


class TestAPIIntegrationE2E:
    """Test API integration (would require running API server)"""

    @pytest.mark.asyncio
    async def test_api_initialization(self):
        """Test wall detection API can be initialized"""
        from wall_detection_api import initialize_wall_detection_api
        from fastapi import FastAPI

        app = FastAPI()

        # Initialize (this would normally run during startup)
        await initialize_wall_detection_api(app)

        # Check wall system is in app state
        assert hasattr(app.state, 'wall_system')

        # Check system is initialized
        assert app.state.wall_system.is_initialized


if __name__ == '__main__':
    # Run E2E tests
    pytest.main([__file__, '-v', '--tb=short', '-s'])
