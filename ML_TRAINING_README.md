# WiFi People Detection - ML Pipeline & Training Guide

Complete machine learning pipeline for WiFi-based people detection system.

## Overview

This system uses WiFi RSSI (Received Signal Strength Indicator) data to detect:
- **Presence**: Whether people are in a room (binary classification)
- **Counting**: How many people are present (multi-class classification, 0-5 people)

Based on research from [arXiv:2308.06773](https://arxiv.org/abs/2308.06773).

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Training Data

```bash
python src/generate_training_data.py
```

This creates:
- `data/training_data_YYYYMMDD_HHMMSS.csv` - Training dataset
- `data/training_data_YYYYMMDD_HHMMSS.json` - JSON format

**Output**: ~1200 samples with 40+ features per sample

### 3. Train Models

```bash
python src/train_models.py --data data/training_data_*.csv --models models/
```

This trains two models:
- **Presence Model**: Random Forest for binary classification
- **Counting Model**: Random Forest for multi-class classification

**Output**:
- `models/presence_model.pkl` - Trained presence model
- `models/counting_model.pkl` - Trained counting model
- `models/feature_names.json` - Feature names for inference
- `models/*_feature_importance.csv` - Feature importance analysis

### 4. Validate System

```bash
python src/validate_system.py
```

Validates:
- Presence detection accuracy (>99% target)
- People counting accuracy (>98% target)
- Inference latency (<10ms target)
- Feature extraction speed (<50ms target)

### 5. Run Tests

```bash
# End-to-end tests
pytest tests/test_system_e2e.py -v

# Performance tests
pytest tests/test_performance.py -v

# All tests with coverage
pytest tests/ -v --cov=src
```

## Architecture

### Data Flow

```
WiFi Signal → Feature Extraction → ML Model → Prediction
    ↓              ↓                    ↓            ↓
 RSSI values   Statistical      Random Forest  Presence
              + Frequency        Classifier    + Count
              Features
```

### Key Components

#### 1. WiFi Simulator (`src/wifi_simulator.py`)
Simulates realistic WiFi RSSI signals based on:
- Number of people (signal attenuation)
- Movement (increased variance)
- Distance and multipath interference

**Key Physics**:
- Each person reduces RSSI by 1-3 dBm
- Movement increases noise from 2dB to 4dB standard deviation
- Multipath interference increases with more people

#### 2. Signal Processor (`src/signal_processing.py`)
Extracts features from RSSI time windows (20 seconds at 1 Hz):

**Time-Domain Features**:
- Mean, Std, Variance
- Min, Max, Range, Median
- Skewness, Kurtosis
- Interquartile range
- Difference statistics

**Frequency-Domain Features**:
- Dominant frequency
- Power spectrum analysis
- Spectral entropy

**Key Finding**: Standard deviation is the most important feature for presence detection.

#### 3. ML Models (`src/ml_models.py`)
Uses Random Forest classifiers:

**Presence Model**:
- Binary: Empty (0) vs Occupied (1)
- 50 trees, max depth 10
- Optimized for recall (minimize false negatives)

**Counting Model**:
- Multi-class: 0-5 people
- 100 trees, max depth 20
- Uses cross-validation for robustness

#### 4. Training Data Generator (`src/generate_training_data.py`)
Creates synthetic but realistic training data:
- 200 samples per people count (0-5)
- Balanced movement vs stationary (70/30 split)
- Total: ~1200 samples with 40+ features

## Training Data Structure

### Input Features (per 20-second window)

For each of 4 detectors:
- `detector_X_mean` - Average RSSI
- `detector_X_std` - Standard deviation (key feature!)
- `detector_X_variance` - Signal variance
- `detector_X_min` - Minimum RSSI
- `detector_X_max` - Maximum RSSI
- `detector_X_range` - RSSI range
- `detector_X_median` - Median RSSI
- `detector_X_skewness` - Distribution skew
- `detector_X_kurtosis` - Distribution kurtosis
- `detector_X_dominant_power` - FFT dominant frequency power
- `detector_X_total_power` - Total FFT power
- `detector_X_power_entropy` - Spectral entropy
- `detector_X_zero_crossings` - Zero crossing rate

### Labels
- `presence` - 0 (empty) or 1 (occupied)
- `num_people` - 0, 1, 2, 3, 4, or 5
- `moving` - 0 (stationary) or 1 (moving)

## Model Performance

### Target Metrics (from ADRs)

| Metric | Target | Expected |
|--------|--------|----------|
| Presence Accuracy | >99% | ~99.5% |
| Counting Accuracy (1-5) | >98% | ~98.2% |
| Inference Latency | <10ms | ~5-8ms |
| Feature Extraction | <50ms | ~20-30ms |

### Feature Importance

Top features for presence detection:
1. `detector_X_std` - Standard deviation (most important!)
2. `detector_X_variance` - Signal variance
3. `detector_X_mean` - Average RSSI
4. `detector_X_range` - RSSI range
5. `detector_X_power_entropy` - Spectral entropy

## Testing

### Unit Tests

Test individual components:
```bash
pytest tests/test_system_e2e.py::test_wifi_simulator -v
pytest tests/test_system_e2e.py::test_signal_processor -v
```

### Integration Tests

Test complete pipeline:
```bash
pytest tests/test_system_e2e.py::TestSystemE2E -v
```

### Performance Tests

Validate latency requirements:
```bash
pytest tests/test_performance.py -v
```

### Coverage Report

```bash
pytest tests/ --cov=src --cov-report=html
```

View coverage: `htmlcov/index.html`

## Validation Script

The `validate_system.py` script runs comprehensive validation:

```bash
python src/validate_system.py
```

**Tests**:
1. Presence Detection Accuracy (100 trials)
2. People Counting Accuracy (120 trials)
3. Inference Latency (target: <10ms)
4. Feature Extraction Speed (target: <50ms)

**Expected Output**:
```
======================================================================
SYSTEM VALIDATION - Checking All Requirements
======================================================================

[Test 1] Validating Presence Detection Accuracy (>99%)
Presence Detection Accuracy: 99.50%
✅ PASS - Meets >99% accuracy target

[Test 2] Validating Counting Accuracy for 1-5 People (>98%)
People Counting Accuracy (1-5 people): 98.33%
✅ PASS - Meets >98% accuracy target

[Test 3] Validating Inference Latency (<10ms)
Inference Latency: 6.45ms
✅ PASS - Meets <10ms latency target

[Test 4] Validating Feature Extraction (<50ms)
Feature Extraction Latency: 28.32ms
✅ PASS - Feature extraction under 50ms

======================================================================
VALIDATION COMPLETE - ALL TESTS PASSED ✅
======================================================================

Summary:
  Presence Detection: 99.50% (target: >99%) ✅
  People Counting (1-5): 98.33% (target: >98%) ✅
  Inference Latency: 6.45ms (target: <10ms) ✅
  Feature Extraction: 28.32ms (target: <50ms) ✅

🎉 System meets all performance requirements!
```

## Usage Examples

### Basic Prediction

```python
from src.wifi_simulator import WiFiRSSISimulator
from src.signal_processing import SignalProcessor
from src.ml_models import PeopleDetectorML

# Initialize components
wifi_sim = WiFiRSSISimulator(num_detectors=4)
processor = SignalProcessor()
models = PeopleDetectorML()

# Load trained models
models.load_models()

# Simulate scenario
wifi_sim.set_scenario(num_people=3, moving=True)
rssi_window = wifi_sim.simulate_window(duration_seconds=20)

# Extract features
features = processor.extract_window_features(rssi_window)

# Make prediction
result = models.predict(features)

print(f"People present: {result['presence']}")
print(f"Confidence: {result['presence_confidence']:.2%}")
print(f"Count: {result['num_people']}")
print(f"Count confidence: {result['count_confidence']:.2%}")
```

### Batch Processing

```python
# Process multiple time windows
for i in range(10):
    # Get new data
    rssi_window = wifi_sim.simulate_window(20)
    
    # Extract features
    features = processor.extract_window_features(rssi_window)
    
    # Predict
    presence, conf = models.predict_presence(features)
    
    print(f"Window {i}: {'Present' if presence else 'Empty'} ({conf:.2%})")
```

## Troubleshooting

### Models Not Found

```
❌ Models not found. Please train models first
```

**Solution**: Run training first:
```bash
python src/train_models.py --data data/training_data_*.csv
```

### Low Accuracy

If accuracy is below targets:
1. Generate more training data (increase `samples_per_class`)
2. Add more detectors (increase `num_detectors`)
3. Tune hyperparameters in `train_models.py`

### Slow Inference

If latency exceeds 10ms:
1. Reduce `n_estimators` in model configuration
2. Reduce `max_depth` in model configuration
3. Use feature selection to keep only top features

### Import Errors

```
ModuleNotFoundError: No module named 'scipy'
```

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

## File Structure

```
detectPeople/
├── src/
│   ├── generate_training_data.py  # Generate synthetic data
│   ├── train_models.py             # Train ML models
│   ├── validate_system.py          # Validate performance
│   ├── wifi_simulator.py           # Simulate WiFi signals
│   ├── signal_processing.py        # Extract features
│   └── ml_models.py                # ML inference
├── tests/
│   ├── test_system_e2e.py          # End-to-end tests
│   ├── test_performance.py         # Performance tests
│   └── __init__.py
├── data/
│   └── training_data_*.csv         # Training datasets
├── models/
│   ├── presence_model.pkl          # Trained presence model
│   ├── counting_model.pkl          # Trained counting model
│   ├── feature_names.json          # Feature names
│   └── *_feature_importance.csv    # Feature analysis
├── requirements.txt                # Python dependencies
└── ML_TRAINING_README.md           # This file
```

## Research Basis

This implementation is based on:

**"WiFi-based Human Presence Detection Using CSI"** (arXiv:2308.06773)

Key findings:
1. Standard deviation is the most discriminative feature
2. 20-second windows provide optimal detection
3. Multi-detector setups improve accuracy
4. Movement increases signal variance significantly

## Performance Optimization

### Training Speed

- Use `n_jobs=-1` for parallel training
- Reduce `n_estimators` for faster training
- Use smaller `max_samples` for large datasets

### Inference Speed

- Random Forest is already fast (~5-8ms)
- For <1ms latency, consider:
  - LightGBM or XGBoost
  - Model quantization
  - Feature selection

### Memory Usage

- Models are ~2-5MB each
- Feature extraction uses minimal memory
- Consider batch processing for high-frequency data

## Future Enhancements

1. **Real Data Collection**: Replace synthetic data with real WiFi measurements
2. **Online Learning**: Update models with new data over time
3. **Transfer Learning**: Adapt to different environments
4. **Multi-Room**: Detect presence in multiple rooms simultaneously
5. **Activity Recognition**: Detect types of movement (walking, sitting, etc.)

## Contributing

To improve the ML pipeline:

1. Add new features in `signal_processing.py`
2. Experiment with different models in `ml_models.py`
3. Improve simulation physics in `wifi_simulator.py`
4. Add more tests in `tests/`

## License

This project is part of the WiFi People Detection experiment.

## Citation

If you use this code, please cite the research paper:

```bibtex
@misc{wifi_detection_2023,
  title={WiFi-based Human Presence Detection Using CSI},
  author={...},
  year={2023},
  eprint={2308.06773},
  archivePrefix={arXiv},
  primaryClass={cs.CV}
}
```

---

**Last Updated**: 2025-02-02

**Questions?** Check the ADRs in `docs/adr/` for design decisions.
