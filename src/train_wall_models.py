"""
Training Pipeline for Wall Detection Models

Usage:
    python src/train_wall_models.py --samples 50000 --epochs 50 --models models/
"""

import argparse
import logging
import sys
from pathlib import Path
import numpy as np
import torch
from synthetic_csi_generator import (
    CSIDataGenerator,
    generate_synthetic_csi_data,
    generate_material_classification_data
)
from wall_detection_models import (
    WallDetectionModel,
    MaterialClassificationModel
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_wall_detection_model(
    num_samples: int = 50000,
    epochs: int = 50,
    batch_size: int = 32,
    model_dir: str = "models",
    device: str = None
) -> dict:
    """
    Train wall detection model

    Args:
        num_samples: Number of training samples
        epochs: Number of training epochs
        batch_size: Batch size for training
        model_dir: Directory to save models
        device: Device to train on

    Returns:
        Training metrics
    """
    logger.info("=" * 80)
    logger.info("TRAINING WALL DETECTION MODEL")
    logger.info("=" * 80)

    # Generate synthetic training data
    logger.info(f"Generating {num_samples} synthetic CSI samples...")
    generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)

    X, y, materials = generator.generate_batch(
        num_samples=num_samples,
        max_walls=4,
        noise_level=0.1
    )

    logger.info(f"Generated data: X shape={X.shape}, y shape={y.shape}")

    # Use only amplitude for CNN+LSTM (can also use phase)
    X_amplitude = np.abs(X)

    # Normalize
    X_mean = X_amplitude.mean()
    X_std = X_amplitude.std()
    X_normalized = (X_amplitude - X_mean) / (X_std + 1e-8)

    logger.info(f"Data normalized: mean={X_mean:.4f}, std={X_std:.4f}")

    # Create model
    model = WallDetectionModel(input_shape=(30, 100), grid_size=10)

    # Train
    metrics = model.train_model(
        X_train=X_normalized,
        y_train=y,
        validation_split=0.2,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=0.001,
        device=device
    )

    # Save model
    model_path = Path(model_dir) / 'wall_detection_model.pth'
    model.save(str(model_path))

    # Save normalization parameters
    import json
    norm_params = {
        'mean': float(X_mean),
        'std': float(X_std),
        'n_samples': num_samples,
        'n_subcarriers': 30,
        'n_timesteps': 100,
        'grid_size': 10
    }

    norm_path = Path(model_dir) / 'wall_detection_normalization.json'
    with open(norm_path, 'w') as f:
        json.dump(norm_params, f, indent=2)

    logger.info(f"Normalization parameters saved to {norm_path}")

    # Save training metrics
    metrics_path = Path(model_dir) / 'wall_detection_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump({
            'best_val_loss': float(metrics['best_val_loss']),
            'best_val_accuracy': float(metrics['best_val_accuracy']),
            'best_epoch': int(metrics['best_epoch']),
            'final_train_accuracy': float(metrics['train_accuracies'][-1]),
            'final_val_accuracy': float(metrics['val_accuracies'][-1])
        }, f, indent=2)

    logger.info(f"Training metrics saved to {metrics_path}")

    return metrics


def train_material_classification_model(
    num_samples_per_material: int = 5000,
    model_dir: str = "models"
) -> dict:
    """
    Train material classification model

    Args:
        num_samples_per_material: Number of training samples per material
        model_dir: Directory to save models

    Returns:
        Training metrics
    """
    logger.info("=" * 80)
    logger.info("TRAINING MATERIAL CLASSIFICATION MODEL")
    logger.info("=" * 80)

    # Generate synthetic training data
    logger.info(f"Generating synthetic CSI data for material classification...")
    X, y = generate_material_classification_data(
        num_samples_per_material=num_samples_per_material
    )

    logger.info(f"Generated data: X shape={X.shape}, y shape={y.shape}")

    # Create model
    model = MaterialClassificationModel()

    # Feature names
    feature_names = [
        'amplitude_mean', 'amplitude_std', 'amplitude_max', 'amplitude_min',
        'phase_mean', 'phase_std', 'amplitude_variance',
        'diff_mean', 'diff_std', 'fft_mean', 'fft_std'
    ]
    model.feature_names = feature_names

    # Train
    metrics = model.train(X, y, validation_split=0.2)

    # Save model
    model_path = Path(model_dir) / 'material_classification_model.pkl'
    model.save(str(model_path))

    # Save training metrics
    import json
    metrics_path = Path(model_dir) / 'material_classification_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump({
            'train_accuracy': float(metrics['train_accuracy']),
            'val_accuracy': float(metrics['val_accuracy']),
            'n_features': int(metrics['n_features']),
            'n_samples': len(X)
        }, f, indent=2)

    logger.info(f"Training metrics saved to {metrics_path}")

    return metrics


def evaluate_wall_detection_model(model_dir: str = "models", num_test_samples: int = 1000):
    """
    Evaluate trained wall detection model

    Args:
        model_dir: Directory containing trained models
        num_test_samples: Number of test samples

    Returns:
        Evaluation metrics
    """
    logger.info("=" * 80)
    logger.info("EVALUATING WALL DETECTION MODEL")
    logger.info("=" * 80)

    # Load model
    model_path = Path(model_dir) / 'wall_detection_model.pth'
    model = WallDetectionModel.load(str(model_path))

    # Load normalization parameters
    import json
    norm_path = Path(model_dir) / 'wall_detection_normalization.json'
    with open(norm_path, 'r') as f:
        norm_params = json.load(f)

    # Generate test data
    generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)
    X_test, y_test, _ = generator.generate_batch(
        num_samples=num_test_samples,
        max_walls=4,
        noise_level=0.1
    )

    # Normalize
    X_test_amplitude = np.abs(X_test)
    X_test_normalized = (X_test_amplitude - norm_params['mean']) / (norm_params['std'] + 1e-8)

    # Predict
    predictions = model.predict(X_test_normalized)
    predictions_binary = (predictions > 0.5).astype(int)

    # Calculate metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    accuracy = accuracy_score(y_test.flatten(), predictions_binary.flatten())
    precision = precision_score(y_test.flatten(), predictions_binary.flatten(), zero_division=0)
    recall = recall_score(y_test.flatten(), predictions_binary.flatten(), zero_division=0)
    f1 = f1_score(y_test.flatten(), predictions_binary.flatten(), zero_division=0)

    # Per-sample accuracy
    sample_accuracies = []
    for i in range(len(y_test)):
        sample_acc = accuracy_score(y_test[i].flatten(), predictions_binary[i].flatten())
        sample_accuracies.append(sample_acc)

    logger.info(f"\nTest Set Performance:")
    logger.info(f"  Pixel-level Accuracy: {accuracy:.4f}")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall: {recall:.4f}")
    logger.info(f"  F1 Score: {f1:.4f}")
    logger.info(f"  Sample-level Mean Accuracy: {np.mean(sample_accuracies):.4f} (+/- {np.std(sample_accuracies):.4f})")

    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'sample_mean_accuracy': float(np.mean(sample_accuracies)),
        'sample_std_accuracy': float(np.std(sample_accuracies))
    }


def main():
    parser = argparse.ArgumentParser(description='Train wall detection models')
    parser.add_argument('--samples', type=int, default=50000,
                       help='Number of training samples for wall detection')
    parser.add_argument('--material-samples', type=int, default=5000,
                       help='Number of training samples per material')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs for wall detection')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size for training')
    parser.add_argument('--models', type=str, default='models',
                       help='Path to save trained models')
    parser.add_argument('--device', type=str, default=None,
                       help='Device to train on (cuda/cpu, or None for auto)')
    parser.add_argument('--skip-wall', action='store_true',
                       help='Skip wall detection model training')
    parser.add_argument('--skip-material', action='store_true',
                       help='Skip material classification model training')
    parser.add_argument('--evaluate-only', action='store_true',
                       help='Only evaluate existing models')

    args = parser.parse_args()

    # Create models directory
    model_dir = Path(args.models)
    model_dir.mkdir(parents=True, exist_ok=True)

    if args.evaluate_only:
        # Evaluate only
        evaluate_wall_detection_model(model_dir=str(model_dir))
        return

    # Train wall detection model
    if not args.skip_wall:
        try:
            wall_metrics = train_wall_detection_model(
                num_samples=args.samples,
                epochs=args.epochs,
                batch_size=args.batch_size,
                model_dir=str(model_dir),
                device=args.device
            )

            logger.info(f"\nWall Detection Model Training Complete:")
            logger.info(f"  Best Validation Accuracy: {wall_metrics['best_val_accuracy']:.4f}")
            logger.info(f"  Final Validation Accuracy: {wall_metrics['val_accuracies'][-1]:.4f}")

        except Exception as e:
            logger.error(f"Wall detection model training failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        logger.info("Skipping wall detection model training")

    # Train material classification model
    if not args.skip_material:
        try:
            material_metrics = train_material_classification_model(
                num_samples_per_material=args.material_samples,
                model_dir=str(model_dir)
            )

            logger.info(f"\nMaterial Classification Model Training Complete:")
            logger.info(f"  Validation Accuracy: {material_metrics['val_accuracy']:.4f}")

        except Exception as e:
            logger.error(f"Material classification model training failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        logger.info("Skipping material classification model training")

    # Evaluate if models were trained
    if not args.skip_wall:
        try:
            logger.info("\n" + "=" * 80)
            eval_metrics = evaluate_wall_detection_model(
                model_dir=str(model_dir),
                num_test_samples=1000
            )

            logger.info(f"\nFinal Test Performance:")
            logger.info(f"  Pixel-level Accuracy: {eval_metrics['accuracy']:.4f}")
            logger.info(f"  Sample-level Accuracy: {eval_metrics['sample_mean_accuracy']:.4f} +/- {eval_metrics['sample_std_accuracy']:.4f}")

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            import traceback
            traceback.print_exc()

    logger.info("\n" + "=" * 80)
    logger.info("TRAINING PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\nModels saved to: {model_dir}")
    logger.info("\nSaved files:")
    logger.info(f"  - {model_dir / 'wall_detection_model.pth'}")
    logger.info(f"  - {model_dir / 'wall_detection_normalization.json'}")
    logger.info(f"  - {model_dir / 'wall_detection_metrics.json'}")
    logger.info(f"  - {model_dir / 'material_classification_model.pkl'}")
    logger.info(f"  - {model_dir / 'material_classification_metrics.json'}")

    logger.info("\nNext steps:")
    logger.info("1. Test models: pytest tests/")
    logger.info("2. Use models in production:")
    logger.info("   from src.wall_detection_models import WallModelManager")
    logger.info("   manager = WallModelManager()")
    logger.info("   manager.load_models()")
    logger.info("   results = manager.detect_walls(csi_data)")


if __name__ == '__main__':
    main()
