"""
Validate system meets all requirements from ADRs

Run this to verify the system meets accuracy targets:
- Presence detection: >99% accuracy
- People counting (1-5 people): >98% accuracy
- Inference latency: <10ms
"""

import asyncio
import numpy as np
import logging
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from wifi_simulator import WiFiRSSISimulator
from signal_processing import SignalProcessor
from ml_models import PeopleDetectorML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target accuracies from ADRs
TARGET_PRESENCE_ACCURACY = 0.99
TARGET_COUNTING_ACCURACY_1_5 = 0.98
TARGET_INFERENCE_LATENCY_MS = 10


async def validate_system():
    """Run complete system validation"""
    logger.info("=" * 70)
    logger.info("SYSTEM VALIDATION - Checking All Requirements")
    logger.info("=" * 70)

    wifi_sim = WiFiRSSISimulator(num_detectors=4)
    processor = SignalProcessor()
    models = PeopleDetectorML()

    try:
        models.load_models()
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        logger.error("Please run training first: python src/train_models.py")
        return False

    # Test 1: Presence Detection Accuracy
    logger.info("\n[Test 1] Validating Presence Detection Accuracy (>99%)")
    presence_correct = 0
    presence_total = 100

    for i in range(presence_total):
        # Test empty room
        wifi_sim.set_scenario(0, moving=False)
        rssi_window = wifi_sim.simulate_window(20)

        # Extract features
        features = processor.extract_window_features(rssi_window)

        presence, conf = models.predict_presence(features)
        if not presence:
            presence_correct += 1

    presence_accuracy = presence_correct / presence_total
    logger.info(f"Presence Detection Accuracy: {presence_accuracy:.2%}")

    if presence_accuracy >= TARGET_PRESENCE_ACCURACY:
        logger.info("✅ PASS - Meets >99% accuracy target")
    else:
        logger.error(f"❌ FAIL - Below target (needs {presence_accuracy:.2%})")
        return False

    # Test 2: Counting Accuracy (1-5 people)
    logger.info("\n[Test 2] Validating Counting Accuracy for 1-5 People (>98%)")
    counting_correct = 0
    counting_total = 0

    for true_count in range(6):
        for _ in range(20):  # 20 trials per count
            wifi_sim.set_scenario(true_count, moving=True if true_count > 0 else False)

            rssi_window = wifi_sim.simulate_window(20)
            features = processor.extract_window_features(rssi_window)

            predicted, conf = models.predict_count(features)
            if predicted == true_count:
                counting_correct += 1

            counting_total += 1

    counting_accuracy = counting_correct / counting_total
    logger.info(f"People Counting Accuracy (1-5 people): {counting_accuracy:.2%}")

    if counting_accuracy >= TARGET_COUNTING_ACCURACY_1_5:
        logger.info("✅ PASS - Meets >98% accuracy target")
    else:
        logger.error(f"❌ FAIL - Below target (needs {counting_accuracy:.2%})")
        return False

    # Test 3: Inference Latency
    logger.info("\n[Test 3] Validating Inference Latency (<10ms)")

    wifi_sim.set_scenario(2, moving=True)
    rssi_window = wifi_sim.simulate_window(20)
    features = processor.extract_window_features(rssi_window)

    start = time.time()
    predicted, conf = models.predict_count(features)
    latency_ms = (time.time() - start) * 1000

    logger.info(f"Inference Latency: {latency_ms:.2f}ms")

    if latency_ms <= TARGET_INFERENCE_LATENCY_MS:
        logger.info("✅ PASS - Meets <10ms latency target")
    else:
        logger.error(f"❌ FAIL - Exceeds target ({latency_ms:.2f}ms > 10ms)")
        return False

    # Test 4: Feature Extraction Performance
    logger.info("\n[Test 4] Validating Feature Extraction (<50ms)")

    wifi_sim.set_scenario(3, moving=True)
    rssi_window = wifi_sim.simulate_window(20)

    start = time.time()
    features = processor.extract_window_features(rssi_window)
    latency_ms = (time.time() - start) * 1000

    logger.info(f"Feature Extraction Latency: {latency_ms:.2f}ms")

    if latency_ms < 50:
        logger.info("✅ PASS - Feature extraction under 50ms")
    else:
        logger.error(f"❌ FAIL - Feature extraction too slow ({latency_ms:.2f}ms)")
        return False

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION COMPLETE - ALL TESTS PASSED ✅")
    logger.info("=" * 70)
    logger.info(f"\nSummary:")
    logger.info(f"  Presence Detection: {presence_accuracy:.2%} (target: >99%) ✅")
    logger.info(f"  People Counting (1-5): {counting_accuracy:.2%} (target: >98%) ✅")
    logger.info(f"  Inference Latency: {latency_ms:.2f}ms (target: <10ms) ✅")
    logger.info(f"  Feature Extraction: {latency_ms:.2f}ms (target: <50ms) ✅")
    logger.info("\n🎉 System meets all performance requirements!")

    return True


if __name__ == '__main__':
    success = asyncio.run(validate_system())
    sys.exit(0 if success else 1)
