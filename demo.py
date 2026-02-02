#!/usr/bin/env python3
"""
Demo script for WiFi People Detection System
Shows the full pipeline working end-to-end.
"""
import sys
sys.path.insert(0, '/home/vinns/experiments/detectPeople')

import time
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML


def train_demo_models():
    """Train simple models for demo."""
    print("\n=== Training Demo Models ===")

    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 300
    n_features = 80

    X_presence = np.random.randn(n_samples, n_features)
    y_presence = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))

    X_counting = np.random.randn(n_samples * 6, n_features)
    y_counting = np.array([i for i in range(6) for _ in range(n_samples)])

    # Train models
    presence_model = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])
    presence_model.fit(X_presence, y_presence)

    counting_model = RandomForestClassifier(
        n_estimators=50,
        max_depth=10,
        random_state=42
    )
    counting_model.fit(X_counting, y_counting)

    print("✓ Models trained successfully")
    return presence_model, counting_model


def run_detection_demo():
    """Run detection demo."""
    print("\n" + "="*60)
    print("WiFi People Detection System - Live Demo")
    print("="*60)

    # Initialize components
    sim = WiFiRSSISimulator(num_detectors=4)
    processor = SignalProcessor()

    # Train models
    presence_model, counting_model = train_demo_models()

    # Demo scenarios
    scenarios = [
        (0, False, "Empty room"),
        (1, True, "One person walking"),
        (2, True, "Two people talking"),
        (3, False, "Three people sitting"),
        (0, False, "Empty room"),
        (4, True, "Four people in meeting"),
        (5, True, "Five people in group"),
    ]

    print("\n" + "-"*60)
    print("Running Detection Scenarios")
    print("-"*60)

    for num_people, moving, description in scenarios:
        print(f"\n📍 Scenario: {description}")
        print(f"   Actual: {num_people} people, moving={moving}")

        # Set scenario
        sim.set_scenario(num_people, moving)

        # Collect RSSI data (simulating 20 seconds at 1 Hz)
        rssi_data = sim.simulate_window(duration_seconds=20)

        # Extract features
        features = processor.extract_window_features(rssi_data)

        # Prepare feature vector
        feature_names = sorted(features.keys())
        feature_vector = [features[name] for name in feature_names]

        # Ensure correct feature count
        if len(feature_vector) < 80:
            feature_vector.extend([0.0] * (80 - len(feature_vector)))
        else:
            feature_vector = feature_vector[:80]

        # Make predictions
        presence_pred = presence_model.predict([feature_vector])[0]
        presence_proba = presence_model.predict_proba([feature_vector])[0]

        count_pred = counting_model.predict([feature_vector])[0]
        count_proba = counting_model.predict_proba([feature_vector])[0]

        # Display results
        presence_conf = presence_proba[presence_pred]
        count_conf = count_proba[count_pred]

        print(f"   📊 RSSI Mean: {np.mean([np.mean(v) for v in rssi_data.values()]):.2f} dBm")
        print(f"   🔍 Predicted Presence: {'YES' if presence_pred else 'NO'} (confidence: {presence_conf:.2%})")
        print(f"   👥 Predicted Count: {count_pred} people (confidence: {count_conf:.2%})")

        # Show accuracy
        presence_correct = (presence_pred == (num_people > 0))
        count_correct = (count_pred == num_people)

        status = "✅" if presence_correct else "❌"
        print(f"   {status} Presence: {'Correct' if presence_correct else 'Incorrect'}")

        status = "✅" if count_correct else "❌"
        print(f"   {status} Count: {'Correct' if count_correct else 'Incorrect'}")

    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_detection_demo()
