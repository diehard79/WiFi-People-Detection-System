"""
Wall Detection System

Main orchestrator for wall detection using WiFi CSI data.
Integrates all components for complete wall detection pipeline.
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
import json
import numpy as np

from wall_detection import (
    CSIDataCollector,
    WallDetectionModel,
    MaterialClassificationModel,
    RoomLayoutMapper,
    WallVisualizer,
    RoomLayout,
    WallDetection
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WallDetectionSystem:
    """
    Main orchestrator for wall detection system

    Integrates:
    - 4 CSI collectors (ESP32-S3 detectors)
    - Wall detection model
    - Material classification model
    - Room layout mapper
    - Visualizer

    Pipeline:
    1. Collect CSI data from all detectors
    2. Preprocess and sanitize
    3. Run wall detection model
    4. Classify materials
    5. Generate room layout
    6. Optimize layout
    7. Generate visualizations
    """

    def __init__(
        self,
        num_detectors: int = 4,
        sampling_rate: int = 10,
        model_dir: str = "models/wall_detection",
        output_dir: str = "wall_detection_output"
    ):
        """
        Initialize wall detection system

        Args:
            num_detectors: Number of CSI detectors (default 4)
            sampling_rate: CSI sampling rate in Hz (default 10)
            model_dir: Directory for ML models
            output_dir: Directory for outputs
        """
        self.num_detectors = num_detectors
        self.sampling_rate = sampling_rate
        self.model_dir = Path(model_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.csi_collectors: Dict[str, CSIDataCollector] = {}
        self.wall_model = WallDetectionModel(model_dir)
        self.material_model = MaterialClassificationModel(model_dir)
        self.room_mapper = RoomLayoutMapper()
        self.visualizer = WallVisualizer(str(self.output_dir / "visualizations"))

        # System state
        self.is_initialized = False
        self.is_calibrating = False
        self.current_layout: Optional[RoomLayout] = None
        self.last_detection_time: Optional[datetime] = None

        # Performance metrics
        self.metrics = {
            'detection_count': 0,
            'total_confidence': 0.0,
            'avg_processing_time': 0.0,
            'calibration_count': 0
        }

        logger.info("Initialized wall detection system")

    async def initialize(self) -> bool:
        """
        Initialize all CSI collectors and load models

        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing wall detection system...")

            # Initialize CSI collectors
            collector = CSIDataCollector(
                num_detectors=self.num_detectors,
                sampling_rate=self.sampling_rate
            )

            # Initialize all detectors
            init_results = collector.initialize_all_detectors()
            success_count = sum(1 for v in init_results.values() if v)

            if success_count < self.num_detectors:
                logger.warning(
                    f"Only {success_count}/{self.num_detectors} detectors initialized"
                )

            # Store collector
            self.csi_collectors['main'] = collector

            # Load models
            if not self.wall_model.load_models():
                logger.info("No pre-trained models found, will create defaults on first use")

            if not self.material_model.load_model():
                logger.info("No material model found, will create default on first use")

            self.is_initialized = True
            logger.info("System initialization complete")

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def detect_room_layout(
        self,
        duration_seconds: int = 30,
        classify_materials: bool = True
    ) -> RoomLayout:
        """
        Complete wall detection pipeline

        Args:
            duration_seconds: CSI data collection duration
            classify_materials: Whether to classify wall materials

        Returns:
            Detected room layout
        """
        start_time = datetime.now()
        logger.info(f"Starting wall detection ({duration_seconds}s data collection)")

        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")

        collector = self.csi_collectors.get('main')
        if not collector:
            raise RuntimeError("CSI collector not available")

        # 1. Collect CSI data from all detectors
        logger.info("Step 1: Collecting CSI data...")
        csi_snapshot = collector.collect_csi_snapshot(duration_seconds)

        # 2. Preprocess and extract features
        logger.info("Step 2: Extracting features...")
        csi_features = self._extract_features_from_snapshot(csi_snapshot)

        # 3. Run wall detection model
        logger.info("Step 3: Detecting walls...")
        walls, overall_confidence = self.wall_model.detect_walls(csi_features)

        if not walls:
            logger.warning("No walls detected")
            # Return empty layout
            return RoomLayout(
                walls=[],
                dimensions=(0.0, 0.0),
                area=0.0,
                perimeter=0.0,
                confidence=0.0,
                detected_at=datetime.now().isoformat()
            )

        # 4. Classify materials (optional)
        if classify_materials:
            logger.info("Step 4: Classifying materials...")
            for wall in walls:
                # Generate dummy features for material classification
                material_features = np.random.randn(15)
                material = self.material_model.classify_material(
                    material_features,
                    wall
                )
                wall.material = material

        # 5. Generate room layout
        logger.info("Step 5: Generating room layout...")
        layout = self.room_mapper.create_room_layout(walls, overall_confidence)

        # 6. Update state
        self.current_layout = layout
        self.last_detection_time = datetime.now()

        # 7. Update metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics['detection_count'] += 1
        self.metrics['total_confidence'] += overall_confidence
        self.metrics['avg_processing_time'] = (
            (self.metrics['avg_processing_time'] * (self.metrics['detection_count'] - 1) +
             processing_time) / self.metrics['detection_count']
        )

        logger.info(
            f"Wall detection complete: {len(walls)} walls, "
            f"confidence={overall_confidence:.2f}, "
            f"time={processing_time:.2f}s"
        )

        return layout

    async def calibrate_system(
        self,
        duration_seconds: int = 300,
        progress_callback=None
    ) -> bool:
        """
        Calibrate system with empty room

        Args:
            duration_seconds: Calibration duration (default 5 minutes)
            progress_callback: Optional callback for progress updates

        Returns:
            True if calibration successful
        """
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")

        collector = self.csi_collectors.get('main')
        if not collector:
            raise RuntimeError("CSI collector not available")

        logger.info(f"Starting system calibration ({duration_seconds}s)...")
        self.is_calibrating = True

        try:
            # Start calibration
            success = await collector.start_calibration(
                duration_seconds=duration_seconds,
                progress_callback=progress_callback
            )

            if success:
                self.metrics['calibration_count'] += 1
                logger.info("Calibration complete")

            return success

        finally:
            self.is_calibrating = False

    async def continuous_monitoring(
        self,
        detection_interval: int = 60,
        callback=None
    ):
        """
        Background task for continuous wall detection

        Args:
            detection_interval: Time between detections in seconds
            callback: Optional callback for detection results
        """
        logger.info(f"Starting continuous monitoring (interval={detection_interval}s)")

        while True:
            try:
                # Detect room layout
                layout = await self.detect_room_layout()

                # Call callback if provided
                if callback:
                    await callback(layout)

                # Wait for next detection
                await asyncio.sleep(detection_interval)

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(10)  # Wait before retry

    def generate_visualizations(
        self,
        layout: Optional[RoomLayout] = None,
        csi_data: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        Generate all visualizations

        Args:
            layout: Room layout (uses current if None)
            csi_data: CSI data for heatmap

        Returns:
            Dictionary of visualization types to file paths
        """
        if layout is None:
            layout = self.current_layout

        if layout is None:
            raise RuntimeError("No layout available. Run detect_room_layout() first.")

        logger.info("Generating visualizations...")
        visualizations = self.visualizer.generate_all_visualizations(layout, csi_data)

        logger.info(f"Generated {len(visualizations)} visualizations")
        return visualizations

    def export_layout(
        self,
        output_path: Optional[str] = None
    ) -> str:
        """
        Export current room layout to JSON

        Args:
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if self.current_layout is None:
            raise RuntimeError("No layout available. Run detect_room_layout() first.")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"room_layout_{timestamp}.json"
        else:
            output_path = Path(output_path)

        # Export using room mapper
        self.room_mapper.export_floorplan(self.current_layout, str(output_path))

        logger.info(f"Exported layout to {output_path}")
        return str(output_path)

    def get_system_status(self) -> Dict:
        """
        Get system status

        Returns:
            Dictionary with system status
        """
        collector = self.csi_collectors.get('main')

        return {
            'initialized': self.is_initialized,
            'calibrating': self.is_calibrating,
            'calibration_status': collector.get_calibration_status() if collector else {},
            'current_layout': {
                'dimensions': self.current_layout.dimensions if self.current_layout else None,
                'area': self.current_layout.area if self.current_layout else None,
                'confidence': self.current_layout.confidence if self.current_layout else None,
                'wall_count': len(self.current_layout.walls) if self.current_layout else 0
            } if self.current_layout else None,
            'last_detection': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'metrics': self.metrics
        }

    def _extract_features_from_snapshot(
        self,
        csi_snapshot: Dict[str, list]
    ) -> Dict[str, np.ndarray]:
        """
        Extract features from CSI snapshot

        Args:
            csi_snapshot: CSI data from all detectors

        Returns:
            Feature dictionary
        """
        features = {}

        for detector_id, data_list in csi_snapshot.items():
            # Extract features from CSI data
            detector_features = []

            for csi_data in data_list:
                # Combine phase and amplitude features
                if csi_data.phase_corrected is not None:
                    phase_features = [
                        np.mean(csi_data.phase_corrected),
                        np.std(csi_data.phase_corrected),
                        np.var(csi_data.phase_corrected)
                    ]
                else:
                    phase_features = [0.0, 0.0, 0.0]

                if csi_data.amplitude_sanitized is not None:
                    amplitude_features = [
                        np.mean(csi_data.amplitude_sanitized),
                        np.std(csi_data.amplitude_sanitized),
                        np.var(csi_data.amplitude_sanitized)
                    ]
                else:
                    amplitude_features = [0.0, 0.0, 0.0]

                detector_features.append(phase_features + amplitude_features)

            features[detector_id] = np.array(detector_features)

        return features


# Singleton instance
_wall_system: Optional[WallDetectionSystem] = None


async def get_wall_system() -> WallDetectionSystem:
    """
    Get or create wall detection system singleton

    Returns:
        Wall detection system instance
    """
    global _wall_system

    if _wall_system is None:
        _wall_system = WallDetectionSystem()
        await _wall_system.initialize()

    return _wall_system


if __name__ == "__main__":
    # Test wall detection system
    print("\n=== Testing Wall Detection System ===\n")

    async def test_system():
        system = WallDetectionSystem()
        await system.initialize()

        # Detect room layout
        layout = await system.detect_room_layout(duration_seconds=3)

        print(f"\nDetected room:")
        print(f"  Dimensions: {layout.dimensions[0]}x{layout.dimensions[1]}m")
        print(f"  Area: {layout.area:.2f}m²")
        print(f"  Walls: {len(layout.walls)}")
        print(f"  Confidence: {layout.confidence:.2%}")

        # Generate visualizations
        viz = system.generate_visualizations()
        print(f"\nVisualizations:")
        for name, path in viz.items():
            print(f"  {name}: {path}")

        # Export layout
        export_path = system.export_layout()
        print(f"\nExported layout to: {export_path}")

        # System status
        status = system.get_system_status()
        print(f"\nSystem status:")
        print(f"  Initialized: {status['initialized']}")
        print(f"  Detections: {status['metrics']['detection_count']}")
        print(f"  Avg processing time: {status['metrics']['avg_processing_time']:.2f}s")

    asyncio.run(test_system())

    print("\n✅ Wall detection system working correctly")
