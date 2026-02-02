"""
ML Models for People Detection

Implements:
1. Presence detection (binary classification)
2. People counting (multi-class classification)
"""

import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PeopleDetectorML:
    """
    Machine Learning models for WiFi-based people detection

    Uses Random Forest for:
    - Presence detection (binary: empty/occupied)
    - People counting (multi-class: 0-5 people)
    """

    def __init__(self, model_dir: str = "models"):
        """
        Initialize ML models

        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = Path(model_dir)
        self.presence_model = None
        self.counting_model = None
        self.feature_names = None

        logger.info(f"Initialized ML models (model_dir={model_dir})")

    def load_models(self) -> bool:
        """
        Load pre-trained models

        Returns:
            True if models loaded successfully, False otherwise
        """
        try:
            # Load presence model
            presence_path = self.model_dir / 'presence_model.pkl'
            if presence_path.exists():
                self.presence_model = joblib.load(presence_path)
                logger.info(f"Loaded presence model from {presence_path}")
            else:
                logger.warning(f"Presence model not found at {presence_path}")

            # Load counting model
            counting_path = self.model_dir / 'counting_model.pkl'
            if counting_path.exists():
                self.counting_model = joblib.load(counting_path)
                logger.info(f"Loaded counting model from {counting_path}")
            else:
                logger.warning(f"Counting model not found at {counting_path}")

            # Load feature names if available
            feature_path = self.model_dir / 'feature_names.json'
            if feature_path.exists():
                import json
                with open(feature_path, 'r') as f:
                    self.feature_names = json.load(f)
                logger.info(f"Loaded {len(self.feature_names)} feature names")

            return self.presence_model is not None and self.counting_model is not None

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def predict_presence(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """
        Predict if people are present

        Args:
            features: Dictionary of feature names to values

        Returns:
            Tuple of (presence_detected, confidence)
        """
        if self.presence_model is None:
            logger.error("Presence model not loaded")
            raise RuntimeError("Presence model not loaded. Call load_models() first.")

        # Convert to feature vector
        feature_vector = self._prepare_features(features)

        # Make prediction
        prediction = self.presence_model.predict([feature_vector])[0]
        probabilities = self.presence_model.predict_proba([feature_vector])[0]

        # Get confidence for predicted class
        confidence = probabilities[prediction]

        return bool(prediction), float(confidence)

    def predict_count(self, features: Dict[str, float]) -> Tuple[int, float]:
        """
        Predict number of people

        Args:
            features: Dictionary of feature names to values

        Returns:
            Tuple of (num_people, confidence)
        """
        if self.counting_model is None:
            logger.error("Counting model not loaded")
            raise RuntimeError("Counting model not loaded. Call load_models() first.")

        # Convert to feature vector
        feature_vector = self._prepare_features(features)

        # Make prediction
        prediction = self.counting_model.predict([feature_vector])[0]
        probabilities = self.counting_model.predict_proba([feature_vector])[0]

        # Get confidence for predicted class
        confidence = probabilities[prediction]

        return int(prediction), float(confidence)

    def predict(self, features: Dict[str, float]) -> Dict:
        """
        Make complete prediction

        Args:
            features: Dictionary of feature names to values

        Returns:
            Dictionary with presence and count predictions
        """
        presence, presence_conf = self.predict_presence(features)
        count, count_conf = self.predict_count(features)

        return {
            'presence': presence,
            'presence_confidence': presence_conf,
            'num_people': count if presence else 0,
            'count_confidence': count_conf
        }

    def _prepare_features(self, features: Dict[str, float]) -> list:
        """
        Prepare features for model input

        Args:
            features: Dictionary of feature names to values

        Returns:
            List of feature values in correct order
        """
        if self.presence_model is None:
            raise RuntimeError("Model not loaded")

        # Get expected feature names from model
        expected_features = self.presence_model.feature_names_in_

        # Create feature vector
        feature_vector = []
        for feature_name in expected_features:
            if feature_name in features:
                feature_vector.append(features[feature_name])
            else:
                # Use default value if feature missing
                feature_vector.append(0.0)
                logger.warning(f"Feature {feature_name} not found, using 0.0")

        return feature_vector

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from presence model

        Returns:
            Dictionary of feature names to importance scores
        """
        if self.presence_model is None:
            raise RuntimeError("Model not loaded")

        feature_names = self.presence_model.feature_names_in_
        importance = self.presence_model.feature_importances_

        return dict(zip(feature_names, importance))


if __name__ == '__main__':
    # Test ML models
    detector = PeopleDetectorML()

    print("\n=== Testing ML Models ===\n")

    # Try to load models
    if detector.load_models():
        print("✅ Models loaded successfully")

        # Test prediction with dummy features
        test_features = {
            'detector_0_mean': -45.0,
            'detector_0_std': 2.0,
            'detector_0_variance': 4.0,
            'detector_1_mean': -48.0,
            'detector_1_std': 3.0,
            'detector_1_variance': 9.0,
        }

        try:
            result = detector.predict(test_features)
            print(f"\nPrediction result:")
            print(f"  Presence: {result['presence']} (confidence: {result['presence_confidence']:.2f})")
            print(f"  Count: {result['num_people']} (confidence: {result['count_confidence']:.2f})")
        except Exception as e:
            print(f"Prediction test failed (expected if training not done): {e}")

        # Show feature importance
        try:
            importance = detector.get_feature_importance()
            print(f"\nTop 5 important features:")
            for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {feat}: {imp:.4f}")
        except Exception as e:
            print(f"Could not get feature importance: {e}")

    else:
        print("❌ Models not found. Please train models first:")
        print("   python src/train_models.py --data data/training_data_*.csv")
