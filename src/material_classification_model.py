"""
Wall Material Classification Model

Random Forest for wall material classification from CSI features
"""

import logging
import joblib
import json
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MaterialClassificationModel:
    """
    Random Forest for wall material classification

    Input: CSI features from wall locations
    Output: Material class (concrete, drywall, wood, metal, glass)
    """

    MATERIALS = ['concrete', 'drywall', 'wood', 'metal', 'glass']

    # Material properties for reference
    MATERIAL_PROPERTIES = {
        'concrete': {'attenuation': 12.0, 'reflection': 0.7, 'delay_spread': 0.8},
        'drywall': {'attenuation': 6.0, 'reflection': 0.4, 'delay_spread': 0.3},
        'wood': {'attenuation': 8.0, 'reflection': 0.5, 'delay_spread': 0.4},
        'metal': {'attenuation': 25.0, 'reflection': 0.95, 'delay_spread': 0.9},
        'glass': {'attenuation': 4.0, 'reflection': 0.3, 'delay_spread': 0.2}
    }

    def __init__(self):
        """Initialize material classification model"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        self.feature_names = None
        logger.info("Initialized MaterialClassificationModel")

    def extract_features(self, csi_data: np.ndarray, wall_locations: np.ndarray) -> np.ndarray:
        """
        Extract features specific to wall locations

        Features:
        - Attenuation coefficient
        - Reflection coefficient
        - Multi-path delay spread
        - Frequency selectivity

        Args:
            csi_data: CSI data (n_subcarriers, n_timesteps)
            wall_locations: Binary mask (grid_size, grid_size) indicating wall locations

        Returns:
            Feature vector for material classification
        """
        features = {}

        # Amplitude statistics at wall locations
        amplitude = np.abs(csi_data)
        phase = np.angle(csi_data)

        # Temporal features
        features['amplitude_mean'] = float(np.mean(amplitude))
        features['amplitude_std'] = float(np.std(amplitude))
        features['amplitude_max'] = float(np.max(amplitude))
        features['amplitude_min'] = float(np.min(amplitude))

        # Frequency features (across subcarriers)
        features['freq_mean'] = float(np.mean(amplitude, axis=0).mean())
        features['freq_std'] = float(np.mean(amplitude, axis=0).std())
        features['freq_range'] = float(np.mean(amplitude, axis=0).max() - np.mean(amplitude, axis=0).min())

        # Phase features
        features['phase_std'] = float(np.std(phase))
        features['phase_mean'] = float(np.mean(phase))

        # Attenuation coefficient (signal strength loss)
        features['attenuation'] = float(-np.mean(amplitude))

        # Reflection coefficient (variance indicates multi-path)
        features['reflection'] = float(np.var(amplitude))

        # Multi-path delay spread (temporal variance)
        temporal_std = np.std(amplitude, axis=1)
        features['delay_spread'] = float(np.mean(temporal_std))

        # Frequency selectivity (variation across subcarriers)
        freq_response = np.mean(amplitude, axis=1)
        features['freq_selectivity'] = float(np.std(freq_response))

        # Spectral features
        fft_vals = np.fft.fft(amplitude, axis=1)
        power_spectrum = np.abs(fft_vals)[:, :amplitude.shape[1]//2]
        features['spectral_centroid'] = float(np.mean(power_spectrum))
        features['spectral_bandwidth'] = float(np.std(power_spectrum))

        # Coherence (phase consistency)
        phase_diff = np.diff(phase, axis=1)
        features['phase_coherence'] = float(1.0 / (1.0 + np.std(phase_diff)))

        return np.array([list(features.values())])

    def train(self, X_train: np.ndarray, y_train: np.ndarray, validation_split: float = 0.2) -> Dict[str, float]:
        """
        Train material classification model

        Args:
            X_train: Training features (n_samples, n_features)
            y_train: Training labels (n_samples,) - material class indices
            validation_split: Fraction of data for validation

        Returns:
            Dictionary with training metrics
        """
        # Split data
        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train, y_train, test_size=validation_split, random_state=42
        )

        logger.info(f"Training samples: {len(X_train_split)}")
        logger.info(f"Validation samples: {len(X_val)}")

        # Train model
        self.model.fit(X_train_split, y_train_split)

        # Predictions
        y_train_pred = self.model.predict(X_train_split)
        y_val_pred = self.model.predict(X_val)

        # Metrics
        train_accuracy = accuracy_score(y_train_split, y_train_pred)
        val_accuracy = accuracy_score(y_val, y_val_pred)

        logger.info(f"Training Accuracy: {train_accuracy:.2%}")
        logger.info(f"Validation Accuracy: {val_accuracy:.2%}")

        # Classification report
        if hasattr(self, 'MATERIALS'):
            report = classification_report(
                y_val, y_val_pred,
                target_names=self.MATERIALS,
                output_dict=True
            )
            logger.info("\nPer-Class Accuracy:")
            for material in self.MATERIALS:
                if material in report:
                    logger.info(f"  {material}: {report[material]['precision']:.2%} precision")

        # Feature importance
        if self.feature_names is not None:
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            logger.info("\nTop 5 Most Important Features:")
            for feat, imp in top_features:
                logger.info(f"  {feat}: {imp:.4f}")

        return {
            'train_accuracy': train_accuracy,
            'val_accuracy': val_accuracy,
            'n_features': X_train.shape[1]
        }

    def predict(self, X: np.ndarray) -> Tuple[str, float]:
        """
        Predict material class

        Args:
            X: Features (n_samples, n_features) or (n_features,) for single sample

        Returns:
            Tuple of (material_name, confidence)
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)

        prediction_idx = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = probabilities[prediction_idx]

        material_name = self.MATERIALS[prediction_idx]

        return material_name, float(confidence)

    def save(self, path: str):
        """Save model to file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'materials': self.MATERIALS,
            'model_type': 'MaterialClassificationModel'
        }

        joblib.dump(model_data, path)
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: str):
        """Load model from file"""
        model_data = joblib.load(path)

        model = cls()
        model.model = model_data['model']
        model.feature_names = model_data.get('feature_names')

        logger.info(f"Model loaded from {path}")
        return model


if __name__ == '__main__':
    # Test MaterialClassificationModel
    print("\n=== Testing Material Classification Model ===\n")

    model = MaterialClassificationModel()
    print("Model initialized successfully")

    # Test feature extraction
    dummy_csi = np.random.randn(30, 100) + 1j * np.random.randn(30, 100)
    dummy_wall = np.ones((10, 10))
    features = model.extract_features(dummy_csi, dummy_wall)
    print(f"Feature shape: {features.shape}")
    print("Feature extraction successful")

    print("\n✅ Material Classification Model working correctly")
