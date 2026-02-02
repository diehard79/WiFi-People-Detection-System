"""
Test script for wall detection models

Run this after PyTorch installation is complete:
    source venv/bin/activate
    python tests/test_wall_models.py
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

print("\n=== Testing Wall Detection Models ===\n")

# Test 1: Synthetic CSI Data Generator
print("1. Testing Synthetic CSI Data Generator...")
try:
    from synthetic_csi_generator import CSIDataGenerator, WallConfig

    generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)

    # Create test walls
    walls = [
        WallConfig(x=0.5, y=0.2, length=0.6, orientation='horizontal', material='concrete'),
        WallConfig(x=0.3, y=0.5, length=0.4, orientation='vertical', material='drywall')
    ]

    csi_data, wall_grid = generator.generate_sample(walls)
    print(f"   CSI data shape: {csi_data.shape}")
    print(f"   Wall grid shape: {wall_grid.shape}")
    print(f"   Wall cells: {wall_grid.sum()}")
    print("   CSI Data Generator: PASSED")
except Exception as e:
    print(f"   CSI Data Generator: FAILED - {e}")

# Test 2: Material Classification Model (scikit-learn only)
print("\n2. Testing Material Classification Model...")
try:
    from wall_detection_models import MaterialClassificationModel

    model = MaterialClassificationModel()
    print("   Model initialized successfully")

    # Test feature extraction
    dummy_csi = np.random.randn(30, 100) + 1j * np.random.randn(30, 100)
    dummy_wall = np.ones((10, 10))
    features = model.extract_features(dummy_csi, dummy_wall)
    print(f"   Feature shape: {features.shape}")
    print("   Material Classification Model: PASSED")
except Exception as e:
    print(f"   Material Classification Model: FAILED - {e}")

# Test 3: Wall Detection Model (requires PyTorch)
print("\n3. Testing Wall Detection Model (PyTorch)...")
try:
    import torch
    from wall_detection_models import WallDetectionModel

    model = WallDetectionModel(input_shape=(30, 100), grid_size=10)
    print("   Model initialized successfully")

    # Test forward pass
    dummy_input = torch.randn(4, 30, 100)
    output = model(dummy_input)
    print(f"   Output shape: {output.shape}")
    assert output.shape == (4, 10, 10), "Unexpected output shape"
    print("   Forward pass successful")

    # Test save/load
    model.save('/tmp/test_wall_model.pth')
    loaded_model = WallDetectionModel.load('/tmp/test_wall_model.pth')
    print("   Save/load successful")

    # Test prediction
    dummy_csi = np.random.randn(2, 30, 100)
    predictions = loaded_model.predict(dummy_csi)
    print(f"   Prediction shape: {predictions.shape}")
    print("   Wall Detection Model: PASSED")
except ImportError as e:
    print(f"   Wall Detection Model: SKIPPED - PyTorch not installed ({e})")
except Exception as e:
    print(f"   Wall Detection Model: FAILED - {e}")

# Test 4: Generate small training batch
print("\n4. Testing Training Batch Generation...")
try:
    from synthetic_csi_generator import CSIDataGenerator

    generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)
    X, y, materials = generator.generate_batch(num_samples=10, max_walls=2)

    print(f"   Generated batch: X={X.shape}, y={y.shape}, materials={materials.shape}")
    print(f"   Data type: X={X.dtype}, y={y.dtype}")
    print("   Training Batch Generation: PASSED")
except Exception as e:
    print(f"   Training Batch Generation: FAILED - {e}")

# Test 5: Material classification training data
print("\n5. Testing Material Classification Data Generation...")
try:
    from synthetic_csi_generator import generate_material_classification_data

    X_mat, y_mat = generate_material_classification_data(num_samples_per_material=10)
    print(f"   Generated data: X={X_mat.shape}, y={y_mat.shape}")
    print(f"   Unique labels: {np.unique(y_mat)}")
    print("   Material Classification Data Generation: PASSED")
except Exception as e:
    print(f"   Material Classification Data Generation: FAILED - {e}")

print("\n=== All Tests Complete ===\n")
