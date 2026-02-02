"""
Train ML models for people detection

Usage:
    python src/train_models.py --data data/training_data_*.csv --models models/
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support
)
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_presence_model(X, y, model_path: Path):
    """Train presence detection model"""
    logger.info("=" * 60)
    logger.info("TRAINING PRESENCE DETECTION MODEL")
    logger.info("=" * 60)

    # Use presence label
    y_presence = y['presence']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_presence, test_size=0.2, random_state=42, stratify=y_presence
    )

    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")

    # Train model
    logger.info("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"\nAccuracy: {accuracy:.2%}")

    # Classification report
    report = classification_report(y_test, y_pred,
                                   target_names=['Absent', 'Present'],
                                   output_dict=True)

    logger.info(f"Precision (Present): {report['Present']['precision']:.2%}")
    logger.info(f"Recall (Present): {report['Present']['recall']:.2%}")
    logger.info(f"F1 (Present): {report['Present']['f1-score']:.2%}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info("\nConfusion Matrix:")
    logger.info(f"True Negatives: {cm[0][0]}")
    logger.info(f"False Positives: {cm[0][1]}")
    logger.info(f"False Negatives: {cm[1][0]}")
    logger.info(f"True Positives: {cm[1][1]}")

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    logger.info("\nTop 10 Most Important Features:")
    logger.info(feature_importance.head(10).to_string())

    # Save model
    joblib.dump(model, model_path / 'presence_model.pkl')
    logger.info(f"\nModel saved to {model_path / 'presence_model.pkl'}")

    # Save feature importance
    feature_importance.to_csv(model_path / 'presence_feature_importance.csv', index=False)
    logger.info(f"Feature importance saved to {model_path / 'presence_feature_importance.csv'}")

    # Save feature names
    feature_names = list(X.columns)
    with open(model_path / 'feature_names.json', 'w') as f:
        json.dump(feature_names, f, indent=2)
    logger.info(f"Feature names saved to {model_path / 'feature_names.json'}")

    return accuracy


def train_counting_model(X, y, model_path: Path):
    """Train people counting model"""
    logger.info("=" * 60)
    logger.info("TRAINING PEOPLE COUNTING MODEL")
    logger.info("=" * 60)

    # Use num_people label
    y_counting = y['num_people']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_counting, test_size=0.2, random_state=42, stratify=y_counting
    )

    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")

    # Train model
    logger.info("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Cross-validation
    cv_scores = cross_val_score(model, X, y_counting, cv=5)
    logger.info(f"\nCross-Validation Accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std():.2%})")

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    logger.info(f"\nTest Accuracy: {accuracy:.2%}")

    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info("\nPer-Class Accuracy:")
    for class_name in sorted(y_test.unique()):
        class_idx = int(class_name)
        if str(class_name) in report:
            logger.info(f"  {class_name} people: {report[str(class_name)]['precision']:.2%} precision")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info("\nConfusion Matrix:")
    print(cm)

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    logger.info("\nTop 10 Most Important Features:")
    logger.info(feature_importance.head(10).to_string())

    # Save model
    joblib.dump(model, model_path / 'counting_model.pkl')
    logger.info(f"\nModel saved to {model_path / 'counting_model.pkl'}")

    # Save feature importance
    feature_importance.to_csv(model_path / 'counting_feature_importance.csv', index=False)
    logger.info(f"Feature importance saved to {model_path / 'counting_feature_importance.csv'}")

    return accuracy


def main():
    parser = argparse.ArgumentParser(description='Train ML models')
    parser.add_argument('--data', type=str, required=True,
                       help='Path to training data CSV')
    parser.add_argument('--models', type=str, default='models',
                       help='Path to save trained models')
    args = parser.parse_args()

    # Load data
    logger.info(f"Loading training data from {args.data}...")
    df = pd.read_csv(args.data)

    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")

    # Separate features and labels
    feature_cols = [col for col in df.columns if col.startswith('detector_')]
    label_cols = ['presence', 'num_people']

    X = df[feature_cols]
    y = df[label_cols]

    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Labels: {label_cols}")

    # Handle missing values
    X = X.fillna(X.mean())

    # Create models directory
    model_path = Path(args.models)
    model_path.mkdir(parents=True, exist_ok=True)

    # Train presence model
    presence_accuracy = train_presence_model(X, y, model_path)

    # Train counting model
    counting_accuracy = train_counting_model(X, y, model_path)

    logger.info("\n" + "=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Presence Model Accuracy: {presence_accuracy:.2%}")
    logger.info(f"Counting Model Accuracy: {counting_accuracy:.2%}")
    logger.info(f"\nModels saved to: {model_path}")
    logger.info("\nNext steps:")
    logger.info("1. Test models with: pytest tests/")
    logger.info("2. Validate system: python src/validate_system.py")


if __name__ == '__main__':
    main()
