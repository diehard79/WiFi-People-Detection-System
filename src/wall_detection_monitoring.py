"""
Wall Detection Performance Monitoring

Monitors wall detection system performance:
- Detection accuracy
- Processing latency
- Model confidence
- System resources
"""

import logging
import time
import psutil
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from collections import deque
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DetectionMetrics:
    """Metrics for a single detection"""
    timestamp: datetime
    processing_time: float  # seconds
    wall_count: int
    confidence: float
    area: float
    material_count: int
    memory_usage_mb: float
    cpu_percent: float


@dataclass
class PerformanceReport:
    """Performance report over a time period"""
    period_start: datetime
    period_end: datetime
    total_detections: int
    avg_processing_time: float
    min_processing_time: float
    max_processing_time: float
    avg_confidence: float
    avg_wall_count: float
    avg_area: float
    success_rate: float
    memory_efficiency: float
    cpu_efficiency: float


class WallDetectionMonitor:
    """
    Monitor wall detection performance

    Tracks:
    - Detection accuracy (vs ground truth if available)
    - Processing latency (target: <30 seconds)
    - Model confidence scores
    - Resource usage (memory, CPU)
    """

    def __init__(
        self,
        max_history: int = 1000,
        report_dir: str = "wall_detection_output/reports"
    ):
        """
        Initialize monitor

        Args:
            max_history: Maximum number of metrics to keep in memory
            report_dir: Directory for saving reports
        """
        self.max_history = max_history
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Metrics history
        self.metrics_history: deque = deque(maxlen=max_history)

        # Performance targets
        self.targets = {
            'max_processing_time': 30.0,  # seconds
            'min_confidence': 0.70,  # 70%
            'min_accuracy': 0.95,  # 95% (with ground truth)
            'max_memory_mb': 500,  # MB
            'max_cpu_percent': 80  # %
        }

        # Ground truth data (if available)
        self.ground_truth: Optional[Dict] = None

        logger.info("Initialized wall detection monitor")

    def record_detection(
        self,
        processing_time: float,
        wall_count: int,
        confidence: float,
        area: float,
        material_count: int = 0
    ):
        """
        Record detection metrics

        Args:
            processing_time: Time taken for detection (seconds)
            wall_count: Number of walls detected
            confidence: Overall detection confidence
            area: Detected room area (m²)
            material_count: Number of materials classified
        """
        # Get system metrics
        process = psutil.Process()
        memory_info = process.memory_info()

        metrics = DetectionMetrics(
            timestamp=datetime.now(),
            processing_time=processing_time,
            wall_count=wall_count,
            confidence=confidence,
            area=area,
            material_count=material_count,
            memory_usage_mb=memory_info.rss / 1024 / 1024,
            cpu_percent=process.cpu_percent()
        )

        self.metrics_history.append(metrics)

        # Check if targets met
        self._check_performance_targets(metrics)

        logger.info(
            f"Recorded detection: time={processing_time:.2f}s, "
            f"walls={wall_count}, confidence={confidence:.2%}"
        )

    def _check_performance_targets(self, metrics: DetectionMetrics):
        """
        Check if performance targets are met

        Args:
            metrics: Detection metrics
        """
        warnings = []

        if metrics.processing_time > self.targets['max_processing_time']:
            warnings.append(
                f"Processing time ({metrics.processing_time:.2f}s) "
                f"exceeds target ({self.targets['max_processing_time']}s)"
            )

        if metrics.confidence < self.targets['min_confidence']:
            warnings.append(
                f"Confidence ({metrics.confidence:.2%}) "
                f"below target ({self.targets['min_confidence']:.2%})"
            )

        if metrics.memory_usage_mb > self.targets['max_memory_mb']:
            warnings.append(
                f"Memory usage ({metrics.memory_usage_mb:.1f}MB) "
                f"exceeds target ({self.targets['max_memory_mb']}MB)"
            )

        if metrics.cpu_percent > self.targets['max_cpu_percent']:
            warnings.append(
                f"CPU usage ({metrics.cpu_percent:.1f}%) "
                f"exceeds target ({self.targets['max_cpu_percent']}%)"
            )

        if warnings:
            logger.warning(f"Performance warnings: {'; '.join(warnings)}")

    def track_detection_accuracy(
        self,
        detected_walls: List,
        actual_walls: List
    ) -> float:
        """
        Track detection accuracy against ground truth

        Args:
            detected_walls: Detected wall segments
            actual_walls: Actual wall segments (ground truth)

        Returns:
            Accuracy score (0-1)
        """
        if not actual_walls:
            logger.warning("No ground truth available for accuracy calculation")
            return 0.0

        # Simple accuracy: count of correctly detected walls
        # In production, use more sophisticated metrics (IoU, etc.)

        detected_count = len(detected_walls)
        actual_count = len(actual_walls)

        # Accuracy based on count difference
        count_diff = abs(detected_count - actual_count)
        accuracy = max(0.0, 1.0 - (count_diff / max(actual_count, 1)))

        logger.info(f"Detection accuracy: {accuracy:.2%}")

        return accuracy

    def track_processing_latency(self) -> Dict[str, float]:
        """
        Track processing latency statistics

        Returns:
            Dictionary with latency stats
        """
        if not self.metrics_history:
            return {}

        processing_times = [m.processing_time for m in self.metrics_history]

        return {
            'mean': np.mean(processing_times),
            'median': np.median(processing_times),
            'std': np.std(processing_times),
            'min': np.min(processing_times),
            'max': np.max(processing_times),
            'p95': np.percentile(processing_times, 95),
            'p99': np.percentile(processing_times, 99)
        }

    def track_model_confidence(self) -> Dict[str, float]:
        """
        Track model confidence statistics

        Returns:
            Dictionary with confidence stats
        """
        if not self.metrics_history:
            return {}

        confidences = [m.confidence for m in self.metrics_history]

        return {
            'mean': np.mean(confidences),
            'median': np.median(confidences),
            'std': np.std(confidences),
            'min': np.min(confidences),
            'max': np.max(confidences),
            'below_target': sum(1 for c in confidences if c < self.targets['min_confidence'])
        }

    def get_current_status(self) -> Dict:
        """
        Get current monitoring status

        Returns:
            Dictionary with current status
        """
        if not self.metrics_history:
            return {
                'status': 'no_data',
                'message': 'No detections recorded yet'
            }

        latest = self.metrics_history[-1]

        return {
            'status': 'monitoring',
            'total_detections': len(self.metrics_history),
            'latest_detection': {
                'timestamp': latest.timestamp.isoformat(),
                'processing_time': latest.processing_time,
                'wall_count': latest.wall_count,
                'confidence': latest.confidence,
                'memory_mb': latest.memory_usage_mb,
                'cpu_percent': latest.cpu_percent
            },
            'targets_met': {
                'processing_time': latest.processing_time <= self.targets['max_processing_time'],
                'confidence': latest.confidence >= self.targets['min_confidence'],
                'memory': latest.memory_usage_mb <= self.targets['max_memory_mb'],
                'cpu': latest.cpu_percent <= self.targets['max_cpu_percent']
            }
        }

    def generate_performance_report(
        self,
        hours: int = 24
    ) -> PerformanceReport:
        """
        Generate performance report for time period

        Args:
            hours: Number of hours to include in report

        Returns:
            Performance report
        """
        if not self.metrics_history:
            raise ValueError("No metrics data available")

        # Filter metrics by time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        period_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]

        if not period_metrics:
            raise ValueError(f"No metrics data in the last {hours} hours")

        # Calculate statistics
        processing_times = [m.processing_time for m in period_metrics]
        confidences = [m.confidence for m in period_metrics]
        wall_counts = [m.wall_count for m in period_metrics]
        areas = [m.area for m in period_metrics]

        # Success rate: detections meeting all targets
        successful = sum(
            1 for m in period_metrics
            if (m.processing_time <= self.targets['max_processing_time'] and
                m.confidence >= self.targets['min_confidence'])
        )
        success_rate = successful / len(period_metrics)

        # Resource efficiency
        avg_memory = np.mean([m.memory_usage_mb for m in period_metrics])
        avg_cpu = np.mean([m.cpu_percent for m in period_metrics])

        memory_efficiency = 1.0 - (avg_memory / self.targets['max_memory_mb'])
        cpu_efficiency = 1.0 - (avg_cpu / self.targets['max_cpu_percent'])

        report = PerformanceReport(
            period_start=min(m.timestamp for m in period_metrics),
            period_end=max(m.timestamp for m in period_metrics),
            total_detections=len(period_metrics),
            avg_processing_time=np.mean(processing_times),
            min_processing_time=np.min(processing_times),
            max_processing_time=np.max(processing_times),
            avg_confidence=np.mean(confidences),
            avg_wall_count=np.mean(wall_counts),
            avg_area=np.mean(areas),
            success_rate=success_rate,
            memory_efficiency=max(0.0, memory_efficiency),
            cpu_efficiency=max(0.0, cpu_efficiency)
        )

        return report

    def save_performance_report(
        self,
        hours: int = 24
    ) -> str:
        """
        Generate and save performance report to file

        Args:
            hours: Number of hours for report

        Returns:
            Path to saved report
        """
        report = self.generate_performance_report(hours)

        # Convert to dict
        report_dict = {
            'period_start': report.period_start.isoformat(),
            'period_end': report.period_end.isoformat(),
            'total_detections': report.total_detections,
            'avg_processing_time': report.avg_processing_time,
            'min_processing_time': report.min_processing_time,
            'max_processing_time': report.max_processing_time,
            'avg_confidence': report.avg_confidence,
            'avg_wall_count': report.avg_wall_count,
            'avg_area': report.avg_area,
            'success_rate': report.success_rate,
            'memory_efficiency': report.memory_efficiency,
            'cpu_efficiency': report.cpu_efficiency,
            'targets': self.targets
        }

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_report_{timestamp}.json"
        output_path = self.report_dir / filename

        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"Saved performance report to {output_path}")
        return str(output_path)

    def get_metrics_summary(self) -> Dict:
        """
        Get summary of all metrics

        Returns:
            Dictionary with metrics summary
        """
        if not self.metrics_history:
            return {}

        return {
            'total_detections': len(self.metrics_history),
            'processing_time_stats': self.track_processing_latency(),
            'confidence_stats': self.track_model_confidence(),
            'resource_usage': {
                'avg_memory_mb': np.mean([m.memory_usage_mb for m in self.metrics_history]),
                'avg_cpu_percent': np.mean([m.cpu_percent for m in self.metrics_history])
            },
            'detection_quality': {
                'avg_wall_count': np.mean([m.wall_count for m in self.metrics_history]),
                'avg_area': np.mean([m.area for m in self.metrics_history]),
                'avg_material_count': np.mean([m.material_count for m in self.metrics_history])
            }
        }


if __name__ == "__main__":
    # Test monitoring
    print("\n=== Testing Wall Detection Monitor ===\n")

    monitor = WallDetectionMonitor()

    # Record some dummy detections
    for i in range(10):
        monitor.record_detection(
            processing_time=5.0 + np.random.randn(),
            wall_count=4,
            confidence=0.85 + np.random.randn() * 0.1,
            area=20.0,
            material_count=3
        )

    # Get status
    status = monitor.get_current_status()
    print(f"Monitor status: {status['status']}")
    print(f"Total detections: {status['total_detections']}")

    # Get summary
    summary = monitor.get_metrics_summary()
    print(f"\nMetrics summary:")
    print(f"  Avg processing time: {summary['processing_time_stats']['mean']:.2f}s")
    print(f"  Avg confidence: {summary['confidence_stats']['mean']:.2%}")

    # Generate report
    report = monitor.generate_performance_report(hours=1)
    print(f"\nPerformance report:")
    print(f"  Total detections: {report.total_detections}")
    print(f"  Success rate: {report.success_rate:.2%}")
    print(f"  Memory efficiency: {report.memory_efficiency:.2%}")

    # Save report
    report_path = monitor.save_performance_report()
    print(f"\nSaved report to: {report_path}")

    print("\n✅ Monitor working correctly")
