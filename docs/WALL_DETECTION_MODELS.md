# Wall Detection Models - Implementation Summary

## Overview

Implemented ML models for wall detection using WiFi CSI (Channel State Information) data for indoor mapping applications.

## Files Created

### 1. `/home/vinns/experiments/detectPeople/src/wall_detection_cnn.py`
**Wall Detection Model (CNN + LSTM)**

- **Architecture**: 1D CNN + LSTM for spatiotemporal pattern recognition
- **Input**: CSI amplitude data (30 subcarriers × 100 time steps)
- **Output**: 10×10 grid of wall probabilities
- **Requirements**: PyTorch

**Key Features**:
- 1D Convolutional layers (64 → 128 → 256 filters)
- LSTM layer (2 layers, 128 hidden units)
- Batch normalization and dropout for regularization
- Binary cross-entropy loss
- Adam optimizer with learning rate scheduling
- Early stopping to prevent overfitting

**Model Architecture**:
```
Input (30, 100)
    ↓
Conv1d (30→64, kernel=5) + BatchNorm + ReLU + Dropout
    ↓
Conv1d (64→128, kernel=5) + BatchNorm + ReLU + Dropout
    ↓
Conv1d (128→256, kernel=3) + BatchNorm + ReLU + MaxPool + Dropout
    ↓
LSTM (256→128, 2 layers)
    ↓
FC (128→256) + BatchNorm + ReLU + Dropout
    ↓
FC (256→128) + BatchNorm + ReLU + Dropout
    ↓
FC (128→100) + Sigmoid
    ↓
Output (10×10 grid)
```

### 2. `/home/vinns/experiments/detectPeople/src/material_classification_model.py`
**Material Classification Model (Random Forest)**

- **Algorithm**: Random Forest Classifier
- **Input**: 11 features extracted from CSI data
- **Output**: Material class (concrete, drywall, wood, metal, glass)
- **Requirements**: scikit-learn

**Key Features**:
- 100 trees, max depth 20
- Feature extraction from CSI data:
  - Amplitude statistics (mean, std, max, min)
  - Phase statistics (mean, std)
  - Attenuation coefficient
  - Reflection coefficient
  - Multi-path delay spread
  - Frequency selectivity
  - Spectral features (centroid, bandwidth)
  - Phase coherence

### 3. `/home/vinns/experiments/detectPeople/src/synthetic_csi_generator.py`
**Synthetic CSI Data Generator**

Generates realistic CSI data for training based on physical models:

**Physical Models Implemented**:
- Free space path loss (Friis transmission equation)
- Wall attenuation (material-specific dB loss)
- Multi-path reflections
- Fresnel equations for reflection coefficients
- Noise and interference simulation

**Material Properties**:
| Material | Attenuation (dB) | Reflection Coeff | Delay Spread |
|----------|-----------------|------------------|--------------|
| Concrete | 12.0 | 0.7 | 0.8 |
| Drywall  | 6.0  | 0.4 | 0.3 |
| Wood     | 8.0  | 0.5 | 0.4 |
| Metal    | 25.0 | 0.95| 0.9 |
| Glass    | 4.0  | 0.3 | 0.2 |

**Usage**:
```python
from src.synthetic_csi_generator import CSIDataGenerator, WallConfig

generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)

# Create walls
walls = [
    WallConfig(x=0.5, y=0.2, length=0.6, orientation='horizontal', material='concrete'),
    WallConfig(x=0.3, y=0.5, length=0.4, orientation='vertical', material='drywall')
]

# Generate CSI sample
csi_data, wall_grid = generator.generate_sample(walls)
```

### 4. `/home/vinns/experiments/detectPeople/src/train_wall_models.py`
**Training Pipeline**

Complete training pipeline for both models with:
- Synthetic data generation
- Model training with validation
- Model serialization
- Metrics logging
- Evaluation on test set

**Usage**:
```bash
# Train wall detection model (requires PyTorch)
source venv/bin/activate
python src/train_wall_models.py --samples 50000 --epochs 50 --models models/

# Train only material classification
python src/train_wall_models.py --skip-wall --material-samples 5000

# Evaluate existing models
python src/train_wall_models.py --evaluate-only
```

## Requirements Updated

Updated `/home/vinns/experiments/detectPeople/requirements.txt`:
```
torch>=2.0.0
torchvision>=0.15.0
h5py>=3.7.0
```

## Test Results

### Material Classification Model

**Training Results** (5000 samples, 1000 per material):
- Training Accuracy: 98.30%
- Validation Accuracy: 21.00%
- **Issue**: Severe overfitting due to limited feature discriminability

**Top Features**:
1. diff_mean: 0.1011
2. amp_min: 0.0985
3. amp_max: 0.0981
4. phase_mean: 0.0971
5. phase_std: 0.0961

**Status**: Model saved to `models/material_classification_model.pkl`

### Wall Detection Model

**Status**: Implementation complete, awaiting PyTorch installation

**Expected Performance** (based on architecture):
- Target: >95% pixel-level accuracy
- Target: >90% sample-level accuracy
- Training time: ~2-4 hours on CPU for 50K samples

## Current Status

### Completed ✅
1. Wall detection CNN+LSTM model implementation
2. Material classification Random Forest model
3. Synthetic CSI data generator with physical models
4. Training pipeline with validation and metrics
5. Requirements updated with PyTorch dependencies
6. Material classification model trained and saved
7. Test suite created

### In Progress 🔄
1. PyTorch installation (via pip in venv)
2. Wall detection model training

### Pending ⏳
1. Wall detection model training (awaiting PyTorch)
2. Model evaluation and validation
3. Performance optimization for material classifier

## Next Steps

### Immediate
1. **Complete PyTorch Installation**:
   ```bash
   source venv/bin/activate
   pip install torch torchvision h5py
   ```

2. **Train Wall Detection Model**:
   ```bash
   python src/train_wall_models.py --samples 50000 --epochs 50
   ```

3. **Evaluate Models**:
   ```bash
   python src/train_wall_models.py --evaluate-only
   ```

### Improvements Needed

**Material Classification**:
- Current issue: Overfitting (98% train, 21% val)
- Possible solutions:
  - Increase training data diversity
  - Add more discriminative features
  - Use deeper neural network instead of Random Forest
  - Implement data augmentation
  - Tune hyperparameters (reduce tree depth, increase min_samples)

**Wall Detection**:
- Monitor training for overfitting
- Consider data augmentation techniques
- Tune hyperparameters if validation performance is poor

## Model Files

### Saved Models
```
models/
├── material_classification_model.pkl          # Random Forest model
├── material_classification_metrics.json       # Training metrics
└── wall_detection_model.pth                   # CNN+LSTM model (pending)
```

### Model Metadata

**Material Classification Model**:
```json
{
  "train_accuracy": 0.9830,
  "val_accuracy": 0.2100,
  "n_features": 11,
  "n_samples": 5000,
  "materials": ["concrete", "drywall", "wood", "metal", "glass"]
}
```

## Usage Examples

### Load and Use Material Classification Model

```python
from src.material_classification_model import MaterialClassificationModel
import numpy as np

# Load model
model = MaterialClassificationModel.load('models/material_classification_model.pkl')

# Predict material
csi_data = np.random.randn(30, 100) + 1j * np.random.randn(30, 100)
wall_locations = np.ones((10, 10))

# Extract features and predict
features = model.extract_features(csi_data, wall_locations)
material, confidence = model.predict(features)

print(f"Material: {material}, Confidence: {confidence:.2%}")
```

### Load and Use Wall Detection Model (after PyTorch installed)

```python
from src.wall_detection_cnn import WallDetectionModel
import numpy as np

# Load model
model = WallDetectionModel.load('models/wall_detection_model.pth')

# Predict walls
csi_data = np.random.randn(10, 30, 100)  # 10 samples
wall_predictions = model.predict(csi_data)

print(f"Wall predictions shape: {wall_predictions.shape}")
print(f"Wall probability at (5,5): {wall_predictions[0, 5, 5]:.2%}")
```

## Architecture Decisions

### Why CNN + LSTM?
- **1D CNN**: Captures spatial patterns across subcarriers (frequency domain)
- **LSTM**: Models temporal dependencies across time steps
- **Combined**: Effective for spatiotemporal CSI data

### Why Random Forest for Material Classification?
- **Interpretability**: Feature importance analysis
- **Robustness**: Handles mixed feature types well
- **Training Speed**: Faster than neural networks for small datasets
- **Baseline**: Good starting point, can upgrade to neural network if needed

### Why Synthetic Data?
- **Labeled Data Scarcity**: Real CSI data with wall labels is hard to obtain
- **Controlled Experiments**: Test model architecture before collecting real data
- **Physical Models**: Based on actual signal propagation physics
- **Scalability**: Generate unlimited training data

## Known Limitations

1. **Synthetic Data Gap**: Real CSI data may have different characteristics
2. **Material Overfitting**: Current model overfits to synthetic patterns
3. **Simplified Physics**: Does not model all real-world phenomena
4. **Grid Resolution**: 10×10 grid may be too coarse for detailed mapping
5. **Single Receiver**: Assumes fixed TX/RX positions

## Future Improvements

1. **Transfer Learning**: Pre-train on synthetic, fine-tune on real data
2. **Attention Mechanism**: Add attention to CNN+LSTM for better focus
3. **Multi-View**: Use multiple receiver positions for better accuracy
4. **Higher Resolution**: Increase grid size (e.g., 20×20 or 50×50)
5. **Ensemble Methods**: Combine multiple models for robustness
6. **Real Data Collection**: Collect labeled CSI data for validation

## References

- WiFi CSI-based indoor localization research
- Channel State Information fundamentals
- Deep learning for time series classification
- RF signal propagation models

---

**Created**: 2026-02-02
**Status**: Implementation complete, training in progress
**Dependencies**: PyTorch (pending), scikit-learn, numpy, scipy
