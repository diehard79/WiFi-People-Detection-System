"""
Wall Detection Model (CNN + LSTM)

1D CNN + LSTM for wall detection from CSI time series.
Requires PyTorch.
"""

import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. Wall detection model will not work.")

from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSIDataset(Dataset):
    """PyTorch Dataset for CSI data"""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        Args:
            X: CSI data (n_samples, n_subcarriers, n_timesteps)
            y: Wall labels (n_samples, grid_height, grid_width)
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class WallDetectionModel(nn.Module):
    """
    1D CNN + LSTM for wall detection from CSI time series

    Input: CSI amplitude + phase (30 subcarriers × 100 time steps)
    Output: Binary classification (wall present/absent per spatial grid cell)

    Architecture:
    - 1D CNN layers for spatial pattern extraction across subcarriers
    - LSTM for temporal sequence modeling
    - Fully connected layers for grid prediction
    """

    def __init__(self, input_shape: Tuple[int, int] = (30, 100), grid_size: int = 10):
        """
        Initialize wall detection model

        Args:
            input_shape: (n_subcarriers, n_timesteps)
            grid_size: Size of spatial grid (grid_size × grid_size)
        """
        super(WallDetectionModel, self).__init__()

        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed. Please install it to use WallDetectionModel.")

        self.n_subcarriers = input_shape[0]
        self.n_timesteps = input_shape[1]
        self.grid_size = grid_size

        # 1D CNN layers for spatial patterns
        self.conv1 = nn.Conv1d(
            in_channels=self.n_subcarriers,
            out_channels=64,
            kernel_size=5,
            stride=1,
            padding=2
        )
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)

        self.conv2 = nn.Conv1d(
            in_channels=64,
            out_channels=128,
            kernel_size=5,
            stride=1,
            padding=2
        )
        self.bn2 = nn.BatchNorm1d(128)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.3)

        self.conv3 = nn.Conv1d(
            in_channels=128,
            out_channels=256,
            kernel_size=3,
            stride=1,
            padding=1
        )
        self.bn3 = nn.BatchNorm1d(256)
        self.relu3 = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
        self.dropout3 = nn.Dropout(0.3)

        # LSTM for temporal sequences
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            dropout=0.3
        )

        # Fully connected layers for grid prediction
        self.fc1 = nn.Linear(128, 256)
        self.fc_bn1 = nn.BatchNorm1d(256)
        self.fc_relu1 = nn.ReLU()
        self.fc_dropout1 = nn.Dropout(0.4)

        self.fc2 = nn.Linear(256, 128)
        self.fc_bn2 = nn.BatchNorm1d(128)
        self.fc_relu2 = nn.ReLU()
        self.fc_dropout2 = nn.Dropout(0.4)

        # Output layer: grid_size × grid_size wall probabilities
        self.fc_out = nn.Linear(128, grid_size * grid_size)
        self.sigmoid = nn.Sigmoid()

        logger.info(f"Initialized WallDetectionModel with input_shape={input_shape}, grid_size={grid_size}")

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor (batch_size, n_subcarriers, n_timesteps)

        Returns:
            Wall probabilities (batch_size, grid_size, grid_size)
        """
        batch_size = x.size(0)

        # 1D CNN layers
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.dropout1(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.dropout2(x)

        x = self.conv3(x)
        x = self.bn3(x)
        x = self.relu3(x)
        x = self.pool(x)
        x = self.dropout3(x)

        # Reshape for LSTM: (batch, seq_len, features)
        x = x.permute(0, 2, 1)

        # LSTM
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use last hidden state
        x = lstm_out[:, -1, :]

        # Fully connected layers
        x = self.fc1(x)
        x = self.fc_bn1(x)
        x = self.fc_relu1(x)
        x = self.fc_dropout1(x)

        x = self.fc2(x)
        x = self.fc_bn2(x)
        x = self.fc_relu2(x)
        x = self.fc_dropout2(x)

        # Output
        x = self.fc_out(x)
        x = self.sigmoid(x)

        # Reshape to grid
        x = x.view(batch_size, self.grid_size, self.grid_size)

        return x

    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.2,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        device: str = None
    ) -> Dict[str, float]:
        """
        Train the wall detection model

        Args:
            X_train: Training CSI data (n_samples, n_subcarriers, n_timesteps)
            y_train: Training wall labels (n_samples, grid_size, grid_size)
            validation_split: Fraction of data for validation
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for Adam optimizer
            device: Device to train on ('cuda', 'cpu', or None for auto)

        Returns:
            Dictionary with training metrics
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")

        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'

        logger.info(f"Training on device: {device}")
        self.to(device)

        # Split data
        X_train_split, X_val, y_train_split, y_val = train_test_split(
            X_train, y_train, test_size=validation_split, random_state=42
        )

        # Create datasets and dataloaders
        train_dataset = CSIDataset(X_train_split, y_train_split)
        val_dataset = CSIDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )

        # Training loop
        best_val_loss = float('inf')
        best_epoch = 0
        patience_counter = 0
        patience = 10

        train_losses = []
        val_losses = []
        train_accuracies = []
        val_accuracies = []

        for epoch in range(epochs):
            # Training
            self.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)

                optimizer.zero_grad()
                outputs = self(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

                # Calculate accuracy
                predictions = (outputs > 0.5).float()
                train_correct += (predictions == batch_y).sum().item()
                train_total += batch_y.numel()

            train_loss /= len(train_loader)
            train_accuracy = train_correct / train_total
            train_losses.append(train_loss)
            train_accuracies.append(train_accuracy)

            # Validation
            self.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(device), batch_y.to(device)

                    outputs = self(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()

                    predictions = (outputs > 0.5).float()
                    val_correct += (predictions == batch_y).sum().item()
                    val_total += batch_y.numel()

            val_loss /= len(val_loader)
            val_accuracy = val_correct / val_total
            val_losses.append(val_loss)
            val_accuracies.append(val_accuracy)

            # Learning rate scheduling
            scheduler.step(val_loss)

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                patience_counter = 0

                # Save best model
                torch.save(self.state_dict(), 'best_wall_model_temp.pth')
            else:
                patience_counter += 1

            # Logging
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logger.info(
                    f"Epoch [{epoch+1}/{epochs}] "
                    f"Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy:.4f} | "
                    f"Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}"
                )

            # Early stopping
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break

        # Load best model
        self.load_state_dict(torch.load('best_wall_model_temp.pth'))
        import os
        os.remove('best_wall_model_temp.pth')

        logger.info(f"Training complete. Best validation loss: {best_val_loss:.4f} at epoch {best_epoch+1}")
        logger.info(f"Final validation accuracy: {val_accuracies[best_epoch]:.4f}")

        # Move back to CPU for inference
        self.to('cpu')

        return {
            'best_val_loss': best_val_loss,
            'best_val_accuracy': val_accuracies[best_epoch],
            'best_epoch': best_epoch,
            'train_losses': train_losses,
            'val_losses': val_losses,
            'train_accuracies': train_accuracies,
            'val_accuracies': val_accuracies
        }

    def predict(self, csi_data: np.ndarray) -> np.ndarray:
        """
        Predict wall locations from CSI data

        Args:
            csi_data: CSI data (n_samples, n_subcarriers, n_timesteps) or
                     (n_subcarriers, n_timesteps) for single sample

        Returns:
            Wall probabilities (n_samples, grid_size, grid_size) or
            (grid_size, grid_size) for single sample
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")

        self.eval()

        # Handle single sample
        if csi_data.ndim == 2:
            csi_data = csi_data[np.newaxis, :]

        # Convert to tensor
        x = torch.FloatTensor(csi_data)

        with torch.no_grad():
            outputs = self(x)
            predictions = outputs.cpu().numpy()

        # Return single sample if input was single
        if predictions.shape[0] == 1:
            return predictions[0]

        return predictions

    def save(self, path: str):
        """Save model to file"""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'state_dict': self.state_dict(),
            'n_subcarriers': self.n_subcarriers,
            'n_timesteps': self.n_timesteps,
            'grid_size': self.grid_size,
            'model_type': 'WallDetectionModel'
        }

        torch.save(model_data, path)
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: str):
        """Load model from file"""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed.")

        model_data = torch.load(path, map_location='cpu')

        model = cls(
            input_shape=(model_data['n_subcarriers'], model_data['n_timesteps']),
            grid_size=model_data['grid_size']
        )
        model.load_state_dict(model_data['state_dict'])

        logger.info(f"Model loaded from {path}")
        return model


if __name__ == '__main__':
    # Test WallDetectionModel
    print("\n=== Testing Wall Detection Model ===\n")

    if not TORCH_AVAILABLE:
        print("PyTorch not available. Skipping tests.")
    else:
        model = WallDetectionModel(input_shape=(30, 100), grid_size=10)
        print("Model initialized successfully")

        # Test forward pass
        dummy_input = torch.randn(4, 30, 100)
        output = model(dummy_input)
        print(f"Output shape: {output.shape}")
        assert output.shape == (4, 10, 10), "Unexpected output shape"
        print("Forward pass successful")

        # Test save/load
        model.save('/tmp/test_wall_model.pth')
        loaded_model = WallDetectionModel.load('/tmp/test_wall_model.pth')
        print("Save/load successful")

        # Test prediction
        dummy_csi = np.random.randn(2, 30, 100)
        predictions = loaded_model.predict(dummy_csi)
        print(f"Prediction shape: {predictions.shape}")

        print("\n✅ Wall Detection Model working correctly")
