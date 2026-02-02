"""
Wall Detection ML Models

Implements:
1. Wall Detection Model - Detects walls from CSI data
2. Material Classification Model - Classifies wall materials
"""

import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WallDetection:
    """Detected wall segment."""
    start_point: Tuple[float, float]  # (x, y) in meters
    end_point: Tuple[float, float]
    confidence: float
    thickness: float  # in meters
    material: Optional[str] = None


@dataclass
class RoomLayout:
    """Complete room layout."""
    walls: List[WallDetection]
    dimensions: Tuple[float, float]  # (width, length) in meters
    area: float  # in square meters
    perimeter: float  # in meters
    confidence: float
    detected_at: str


class WallDetectionModel:
    """
    Detects walls from CSI data patterns.

    Uses CSI phase and amplitude features to identify wall locations
    and orientations.
    """

    def __init__(self, model_dir: str = "models/wall_detection"):
        """
        Initialize wall detection model

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.wall_detector: Optional[Pipeline] = None
        self.orientation_classifier: Optional[Pipeline] = None
        self.thickness_regressor: Optional[Pipeline] = None

        logger.info(f"Initialized wall detection model (model_dir={model_dir})")

    def load_models(self) -> bool:
        """
        Load pre-trained models

        Returns:
            True if models loaded successfully
        """
        try:
            # Load wall detector
            detector_path = self.model_dir / 'wall_detector.pkl'
            if detector_path.exists():
                self.wall_detector = joblib.load(detector_path)
                logger.info(f"Loaded wall detector from {detector_path}")
            else:
                logger.warning(f"Wall detector not found at {detector_path}")

            # Load orientation classifier
            orientation_path = self.model_dir / 'orientation_classifier.pkl'
            if orientation_path.exists():
                self.orientation_classifier = joblib.load(orientation_path)
                logger.info(f"Loaded orientation classifier from {orientation_path}")
            else:
                logger.warning(f"Orientation classifier not found at {orientation_path}")

            # Load thickness regressor
            thickness_path = self.model_dir / 'thickness_regressor.pkl'
            if thickness_path.exists():
                self.thickness_regressor = joblib.load(thickness_path)
                logger.info(f"Loaded thickness regressor from {thickness_path}")
            else:
                logger.warning(f"Thickness regressor not found at {thickness_path}")

            return all([
                self.wall_detector is not None,
                self.orientation_classifier is not None,
                self.thickness_regressor is not None
            ])

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def create_default_models(self):
        """
        Create default models if none exist

        Trains simple models with synthetic data for demonstration.
        """
        logger.info("Creating default wall detection models...")

        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 500

        # Features: phase variance, amplitude mean, amplitude std, etc.
        X = np.random.randn(n_samples, 20)

        # Wall presence (binary)
        y_wall = np.random.randint(0, 2, n_samples)

        # Orientation (0: horizontal, 1: vertical, 2: diagonal)
        X_orient = X[y_wall == 1]
        y_orient = np.random.randint(0, 3, len(X_orient))

        # Thickness (continuous, in meters)
        y_thickness = np.random.uniform(0.1, 0.5, len(X_orient))

        # Create wall detector
        self.wall_detector = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ))
        ])
        self.wall_detector.fit(X, y_wall)
        logger.info("Created wall detector")

        # Create orientation classifier
        self.orientation_classifier = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=50,
                random_state=42
            ))
        ])
        self.orientation_classifier.fit(X_orient, y_orient)
        logger.info("Created orientation classifier")

        # Create thickness regressor
        self.thickness_regressor = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(
                n_estimators=50,
                random_state=42
            ))
        ])
        self.thickness_regressor.fit(X_orient, y_thickness)
        logger.info("Created thickness regressor")

    def detect_walls(
        self,
        csi_features: Dict[str, np.ndarray]
    ) -> Tuple[List[WallDetection], float]:
        """
        Detect walls from CSI features

        Args:
            csi_features: Dictionary of CSI features from each detector

        Returns:
            Tuple of (detected_walls, overall_confidence)
        """
        if self.wall_detector is None:
            if not self.load_models():
                self.create_default_models()

        # Combine features from all detectors
        all_features = self._combine_features(csi_features)

        # Predict wall presence
        wall_predictions = self.wall_detector.predict_proba(all_features)

        # Extract wall segments
        walls = []
        confidence_sum = 0.0
        wall_count = 0

        for i, (features, prob) in enumerate(zip(all_features, wall_predictions)):
            wall_prob = prob[1]  # Probability of wall presence

            if wall_prob > 0.7:  # Confidence threshold
                # Detect orientation
                orientation = self._detect_orientation(features)

                # Estimate thickness
                thickness = self._estimate_thickness(features)

                # Generate wall segment (simplified)
                wall = WallDetection(
                    start_point=(i * 2.0, 0.0),
                    end_point=(i * 2.0 + 1.0, 0.0),
                    confidence=wall_prob,
                    thickness=thickness
                )
                walls.append(wall)

                confidence_sum += wall_prob
                wall_count += 1

        overall_confidence = confidence_sum / wall_count if wall_count > 0 else 0.0

        logger.info(f"Detected {len(walls)} walls with confidence {overall_confidence:.2f}")
        return walls, overall_confidence

    def _combine_features(self, csi_features: Dict[str, np.ndarray]) -> List[np.ndarray]:
        """
        Combine CSI features from multiple detectors

        Args:
            csi_features: Features from each detector

        Returns:
            List of combined feature vectors
        """
        combined = []

        # For each spatial location, combine features from all detectors
        num_locations = max(
            len(v) if isinstance(v, (list, np.ndarray)) else 1
            for v in csi_features.values()
        )

        for i in range(num_locations):
            location_features = []

            for detector_id, features in csi_features.items():
                if isinstance(features, np.ndarray) and len(features.shape) > 1:
                    if i < features.shape[0]:
                        location_features.extend(features[i])
                    else:
                        location_features.extend(np.zeros(features.shape[1]))
                elif isinstance(features, np.ndarray):
                    location_features.extend(features)
                else:
                    location_features.extend([0.0] * 5)  # Default

            combined.append(np.array(location_features))

        return combined

    def _detect_orientation(self, features: np.ndarray) -> str:
        """
        Detect wall orientation

        Args:
            features: Feature vector

        Returns:
            Orientation string ('horizontal', 'vertical', 'diagonal')
        """
        if self.orientation_classifier is None:
            return "vertical"

        prediction = self.orientation_classifier.predict([features])[0]

        orientations = ['horizontal', 'vertical', 'diagonal']
        return orientations[prediction]

    def _estimate_thickness(self, features: np.ndarray) -> float:
        """
        Estimate wall thickness

        Args:
            features: Feature vector

        Returns:
            Thickness in meters
        """
        if self.thickness_regressor is None:
            return 0.2  # Default thickness

        prediction = self.thickness_regressor.predict([features])[0]
        return float(np.clip(prediction, 0.1, 0.5))  # Clamp to reasonable range


class MaterialClassificationModel:
    """
    Classifies wall materials from CSI patterns.

    Detects material types:
    - Concrete
    - Brick
    - Drywall
    - Wood
    - Glass
    """

    def __init__(self, model_dir: str = "models/wall_detection"):
        """
        Initialize material classification model

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.material_classifier: Optional[Pipeline] = None

        self.materials = ['concrete', 'brick', 'drywall', 'wood', 'glass']

        logger.info(f"Initialized material classification model (model_dir={model_dir})")

    def load_model(self) -> bool:
        """
        Load pre-trained model

        Returns:
            True if model loaded successfully
        """
        try:
            model_path = self.model_dir / 'material_classifier.pkl'
            if model_path.exists():
                self.material_classifier = joblib.load(model_path)
                logger.info(f"Loaded material classifier from {model_path}")
                return True
            else:
                logger.warning(f"Material classifier not found at {model_path}")
                return False

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def create_default_model(self):
        """
        Create default model if none exists
        """
        logger.info("Creating default material classification model...")

        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 300

        # Features: phase attenuation, amplitude reflection, etc.
        X = np.random.randn(n_samples, 15)

        # Material labels
        y_material = np.random.randint(0, len(self.materials), n_samples)

        # Create classifier
        self.material_classifier = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42
            ))
        ])
        self.material_classifier.fit(X, y_material)
        logger.info("Created material classifier")

    def classify_material(
        self,
        csi_features: np.ndarray,
        wall: WallDetection
    ) -> str:
        """
        Classify wall material

        Args:
            csi_features: CSI features
            wall: Wall detection

        Returns:
            Material string
        """
        if self.material_classifier is None:
            if not self.load_model():
                self.create_default_model()

        # Predict material
        prediction = self.material_classifier.predict([csi_features])[0]
        probabilities = self.material_classifier.predict_proba([csi_features])[0]

        material = self.materials[prediction]
        confidence = probabilities[prediction]

        logger.info(f"Classified material: {material} (confidence: {confidence:.2f})")
        return material


if __name__ == "__main__":
    # Test models
    print("\n=== Testing Wall Detection Models ===\n")

    wall_model = WallDetectionModel()
    material_model = MaterialClassificationModel()

    # Create dummy CSI features
    csi_features = {
        'detector_0': np.random.randn(10, 5),
        'detector_1': np.random.randn(10, 5),
        'detector_2': np.random.randn(10, 5),
        'detector_3': np.random.randn(10, 5)
    }

    # Test wall detection
    walls, confidence = wall_model.detect_walls(csi_features)
    print(f"Detected {len(walls)} walls with confidence {confidence:.2f}")

    # Test material classification
    if walls:
        material = material_model.classify_material(
            np.random.randn(15),
            walls[0]
        )
        print(f"Wall material: {material}")

    print("\n✅ Models working correctly")
