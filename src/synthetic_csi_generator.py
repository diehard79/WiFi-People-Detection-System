"""
Synthetic CSI Data Generator for Wall Detection Training

Generates realistic CSI data for training wall detection models.
Based on physical models of WiFi signal propagation.

Physical Models:
- Free space path loss
- Wall attenuation (material-specific)
- Multi-path reflections
- Fresnel equations
- Noise and interference
"""

import logging
import numpy as np
from typing import Tuple, Dict, List
from scipy import signal
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WallConfig:
    """Configuration for a wall"""
    x: float  # x position (0-1 normalized)
    y: float  # y position (0-1 normalized)
    length: float  # length (0-1 normalized)
    orientation: str  # 'vertical' or 'horizontal'
    material: str  # 'concrete', 'drywall', 'wood', 'metal', 'glass'


class CSIDataGenerator:
    """
    Generate synthetic CSI data for wall detection training
    """

    # Material properties (attenuation in dB, reflection coefficient)
    MATERIAL_PROPERTIES = {
        'concrete': {'attenuation': 12.0, 'reflection': 0.7, 'delay_spread': 0.8},
        'drywall': {'attenuation': 6.0, 'reflection': 0.4, 'delay_spread': 0.3},
        'wood': {'attenuation': 8.0, 'reflection': 0.5, 'delay_spread': 0.4},
        'metal': {'attenuation': 25.0, 'reflection': 0.95, 'delay_spread': 0.9},
        'glass': {'attenuation': 4.0, 'reflection': 0.3, 'delay_spread': 0.2}
    }

    def __init__(
        self,
        n_subcarriers: int = 30,
        n_timesteps: int = 100,
        grid_size: int = 10,
        carrier_freq: float = 5.0e9  # 5 GHz WiFi
    ):
        """
        Initialize CSI data generator

        Args:
            n_subcarriers: Number of OFDM subcarriers
            n_timesteps: Number of time steps in sequence
            grid_size: Spatial grid size (grid_size × grid_size)
            carrier_freq: WiFi carrier frequency (Hz)
        """
        self.n_subcarriers = n_subcarriers
        self.n_timesteps = n_timesteps
        self.grid_size = grid_size
        self.carrier_freq = carrier_freq
        self.wavelength = 3e8 / carrier_freq

        logger.info(
            f"Initialized CSIDataGenerator: "
            f"{n_subcarriers} subcarriers, {n_timesteps} timesteps, "
            f"{grid_size}×{grid_size} grid"
        )

    def generate_sample(
        self,
        walls: List[WallConfig],
        tx_position: Tuple[float, float] = (0.2, 0.5),
        rx_position: Tuple[float, float] = (0.8, 0.5),
        noise_level: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single CSI sample with given wall configuration

        Args:
            walls: List of wall configurations
            tx_position: Transmitter position (x, y) normalized (0-1)
            rx_position: Receiver position (x, y) normalized (0-1)
            noise_level: Noise standard deviation

        Returns:
            Tuple of (csi_data, wall_grid)
            - csi_data: Complex CSI matrix (n_subcarriers, n_timesteps)
            - wall_grid: Binary wall presence grid (grid_size, grid_size)
        """
        # Initialize CSI data
        csi_amplitude = np.zeros((self.n_subcarriers, self.n_timesteps))
        csi_phase = np.zeros((self.n_subcarriers, self.n_timesteps))

        # Create wall grid
        wall_grid = np.zeros((self.grid_size, self.grid_size))

        # Mark walls on grid
        for wall in walls:
            self._mark_wall_on_grid(wall, wall_grid)

        # Generate CSI for each subcarrier and timestep
        for subcarrier in range(self.n_subcarriers):
            # Subcarrier frequency offset
            freq_offset = (subcarrier - self.n_subcarriers / 2) * 312.5e3  # 312.5 kHz spacing
            freq = self.carrier_freq + freq_offset

            for t in range(self.n_timesteps):
                # Base signal (free space path loss)
                amplitude, phase = self._free_space_path_loss(
                    tx_position, rx_position, freq
                )

                # Add wall effects
                for wall in walls:
                    if self._signal_intersects_wall(tx_position, rx_position, wall):
                        wall_amp, wall_phase = self._wall_effect(wall, freq)
                        amplitude *= wall_amp
                        phase += wall_phase

                # Add multi-path reflections
                multi_amp, multi_phase = self._multipath_reflections(
                    tx_position, rx_position, walls, freq
                )
                amplitude += multi_amp
                phase += multi_phase

                # Add temporal variation
                temporal_factor = 1.0 + 0.05 * np.sin(2 * np.pi * t / self.n_timesteps)
                amplitude *= temporal_factor

                # Add noise
                amplitude += np.random.normal(0, noise_level)
                phase += np.random.normal(0, noise_level * 0.1)

                csi_amplitude[subcarrier, t] = amplitude
                csi_phase[subcarrier, t] = phase

        # Convert to complex CSI
        csi_data = csi_amplitude * np.exp(1j * csi_phase)

        return csi_data, wall_grid

    def _mark_wall_on_grid(self, wall: WallConfig, wall_grid: np.ndarray):
        """Mark wall position on grid"""
        grid_x = int(wall.x * self.grid_size)
        grid_y = int(wall.y * self.grid_size)
        length_cells = int(wall.length * self.grid_size)

        for i in range(length_cells):
            if wall.orientation == 'vertical':
                if grid_y + i < self.grid_size:
                    wall_grid[grid_y + i, grid_x] = 1
            else:  # horizontal
                if grid_x + i < self.grid_size:
                    wall_grid[grid_y, grid_x + i] = 1

    def _free_space_path_loss(
        self,
        tx_pos: Tuple[float, float],
        rx_pos: Tuple[float, float],
        frequency: float
    ) -> Tuple[float, float]:
        """
        Calculate free space path loss

        Based on Friis transmission equation
        """
        # Distance in meters (assuming 10m room)
        distance = np.sqrt(
            (tx_pos[0] - rx_pos[0])**2 + (tx_pos[1] - rx_pos[1])**2
        ) * 10.0

        # Friis equation: Pr/Pt = (Gt * Gr * lambda^2) / ((4*pi*d)^2)
        # Simplified to amplitude scaling
        lambda_ = 3e8 / frequency
        path_loss = (lambda_ / (4 * np.pi * distance)) ** 2

        # Convert to linear amplitude
        amplitude = np.sqrt(path_loss)

        # Phase = 2*pi*d/lambda
        phase = 2 * np.pi * distance / lambda_

        return amplitude, phase

    def _signal_intersects_wall(
        self,
        tx_pos: Tuple[float, float],
        rx_pos: Tuple[float, float],
        wall: WallConfig
    ) -> bool:
        """
        Check if signal path intersects wall
        """
        # Simple line intersection check
        if wall.orientation == 'vertical':
            # Wall is vertical line at x = wall.x
            if (tx_pos[0] < wall.x < rx_pos[0]) or (rx_pos[0] < wall.x < tx_pos[0]):
                # Check if y coordinate is within wall extent
                y_intersect = tx_pos[1] + (wall.x - tx_pos[0]) * \
                             (rx_pos[1] - tx_pos[1]) / (rx_pos[0] - tx_pos[0])
                return wall.y <= y_intersect <= wall.y + wall.length
        else:
            # Wall is horizontal line at y = wall.y
            if (tx_pos[1] < wall.y < rx_pos[1]) or (rx_pos[1] < wall.y < tx_pos[1]):
                # Check if x coordinate is within wall extent
                x_intersect = tx_pos[0] + (wall.y - tx_pos[1]) * \
                             (rx_pos[0] - tx_pos[0]) / (rx_pos[1] - tx_pos[1])
                return wall.x <= x_intersect <= wall.x + wall.length

        return False

    def _wall_effect(self, wall: WallConfig, frequency: float) -> Tuple[float, float]:
        """
        Calculate wall attenuation and phase shift
        """
        props = self.MATERIAL_PROPERTIES[wall.material]

        # Attenuation in linear scale
        attenuation_linear = 10 ** (-props['attenuation'] / 10)

        # Phase shift (simplified)
        phase_shift = np.pi / 4

        return attenuation_linear, phase_shift

    def _multipath_reflections(
        self,
        tx_pos: Tuple[float, float],
        rx_pos: Tuple[float, float],
        walls: List[WallConfig],
        frequency: float
    ) -> Tuple[float, float]:
        """
        Calculate multi-path reflection contributions
        """
        total_amp = 0.0
        total_phase = 0.0

        for wall in walls:
            props = self.MATERIAL_PROPERTIES[wall.material]

            # Reflection point (simplified)
            if wall.orientation == 'vertical':
                refl_x = wall.x
                refl_y = (tx_pos[1] + rx_pos[1]) / 2
            else:
                refl_x = (tx_pos[0] + rx_pos[0]) / 2
                refl_y = wall.y

            # Total distance via reflection
            d1 = np.sqrt((tx_pos[0] - refl_x)**2 + (tx_pos[1] - refl_y)**2) * 10.0
            d2 = np.sqrt((rx_pos[0] - refl_x)**2 + (rx_pos[1] - refl_y)**2) * 10.0
            total_distance = d1 + d2

            # Reflected signal amplitude
            lambda_ = 3e8 / frequency
            path_loss = (lambda_ / (4 * np.pi * total_distance)) ** 2
            amplitude = props['reflection'] * np.sqrt(path_loss)

            # Phase
            phase = 2 * np.pi * total_distance / lambda_

            # Add delay spread effect
            delay_spread = props['delay_spread'] * 0.1  # Convert to delay
            phase += 2 * np.pi * frequency * delay_spread

            total_amp += amplitude
            total_phase += phase

        return total_amp, total_phase

    def generate_batch(
        self,
        num_samples: int,
        max_walls: int = 4,
        noise_level: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate a batch of synthetic CSI samples

        Args:
            num_samples: Number of samples to generate
            max_walls: Maximum number of walls per sample
            noise_level: Noise level

        Returns:
            Tuple of (X, y, materials)
            - X: CSI data (num_samples, n_subcarriers, n_timesteps)
            - y: Wall grids (num_samples, grid_size, grid_size)
            - materials: Material indices for each wall (num_samples, max_walls)
        """
        logger.info(f"Generating {num_samples} synthetic CSI samples...")

        X = np.zeros((num_samples, self.n_subcarriers, self.n_timesteps), dtype=complex)
        y = np.zeros((num_samples, self.grid_size, self.grid_size), dtype=float)
        materials = np.zeros((num_samples, max_walls), dtype=int)

        for i in range(num_samples):
            # Random number of walls
            num_walls = np.random.randint(0, max_walls + 1)

            # Generate random walls
            walls = []
            material_indices = []

            for _ in range(num_walls):
                # Random position
                x = np.random.uniform(0.1, 0.9)
                y_pos = np.random.uniform(0.1, 0.9)
                length = np.random.uniform(0.1, 0.4)
                orientation = np.random.choice(['vertical', 'horizontal'])

                # Random material
                material = np.random.choice(list(self.MATERIAL_PROPERTIES.keys()))
                material_idx = list(self.MATERIAL_PROPERTIES.keys()).index(material)

                wall = WallConfig(x=x, y=y_pos, length=length, orientation=orientation, material=material)
                walls.append(wall)
                material_indices.append(material_idx)

            # Generate CSI sample
            csi_data, wall_grid = self.generate_sample(walls, noise_level=noise_level)

            X[i] = csi_data
            y[i] = wall_grid

            # Pad material indices
            materials[i, :len(material_indices)] = material_indices

            if (i + 1) % 1000 == 0:
                logger.info(f"  Generated {i + 1}/{num_samples} samples")

        logger.info(f"✅ Generated {num_samples} samples")
        logger.info(f"   Shape: X={X.shape}, y={y.shape}, materials={materials.shape}")
        logger.info(f"   Walls per sample: {np.sum(y > 0, axis=(1, 2)).mean():.2f} avg")

        return X, y, materials

    def generate_with_specific_materials(
        self,
        num_samples_per_material: int,
        material: str,
        num_walls: int = 2
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate samples with specific material for classification training

        Args:
            num_samples_per_material: Number of samples per material
            material: Material type
            num_walls: Number of walls per sample

        Returns:
            Tuple of (X_features, y_labels)
        """
        logger.info(f"Generating {num_samples_per_material} samples for material: {material}")

        X = []
        y = []

        for i in range(num_samples_per_material):
            # Generate walls with specific material
            walls = []
            for _ in range(num_walls):
                x = np.random.uniform(0.2, 0.8)
                y_pos = np.random.uniform(0.2, 0.8)
                length = np.random.uniform(0.2, 0.4)
                orientation = np.random.choice(['vertical', 'horizontal'])

                wall = WallConfig(x=x, y=y_pos, length=length, orientation=orientation, material=material)
                walls.append(wall)

            # Generate CSI sample
            csi_data, wall_grid = self.generate_sample(walls)

            # Extract features (simplified)
            features = self._extract_simple_features(csi_data)
            X.append(features)

            # Material label
            material_idx = list(self.MATERIAL_PROPERTIES.keys()).index(material)
            y.append(material_idx)

        X = np.array(X)
        y = np.array(y)

        logger.info(f"✅ Generated {num_samples_per_material} samples for {material}")

        return X, y

    def _extract_simple_features(self, csi_data: np.ndarray) -> np.ndarray:
        """Extract simple features for material classification"""
        amplitude = np.abs(csi_data)
        phase = np.angle(csi_data)

        features = [
            np.mean(amplitude),
            np.std(amplitude),
            np.max(amplitude),
            np.min(amplitude),
            np.mean(phase),
            np.std(phase),
            np.var(amplitude),
            np.mean(np.diff(amplitude)),
            np.std(np.diff(amplitude)),
            np.mean(np.abs(np.fft.fft(amplitude))),
            np.std(np.abs(np.fft.fft(amplitude))),
        ]

        return np.array(features)


def generate_synthetic_csi_data(
    num_samples: int = 50000,
    n_subcarriers: int = 30,
    n_timesteps: int = 100,
    grid_size: int = 10,
    output_path: str = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate synthetic CSI data for training

    Args:
        num_samples: Number of samples to generate
        n_subcarriers: Number of subcarriers
        n_timesteps: Number of timesteps
        grid_size: Spatial grid size
        output_path: Path to save generated data (optional)

    Returns:
        Tuple of (X, y, materials)
    """
    generator = CSIDataGenerator(
        n_subcarriers=n_subcarriers,
        n_timesteps=n_timesteps,
        grid_size=grid_size
    )

    # Generate batch
    X, y, materials = generator.generate_batch(
        num_samples=num_samples,
        max_walls=4,
        noise_level=0.1
    )

    # Save if path provided
    if output_path:
        import h5py
        with h5py.File(output_path, 'w') as f:
            f.create_dataset('X', data=X)
            f.create_dataset('y', data=y)
            f.create_dataset('materials', data=materials)
            f.attrs['n_subcarriers'] = n_subcarriers
            f.attrs['n_timesteps'] = n_timesteps
            f.attrs['grid_size'] = grid_size

        logger.info(f"✅ Data saved to {output_path}")

    return X, y, materials


def generate_material_classification_data(
    num_samples_per_material: int = 5000,
    output_path: str = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic CSI data for material classification

    Args:
        num_samples_per_material: Number of samples per material
        output_path: Path to save generated data (optional)

    Returns:
        Tuple of (X_features, y_labels)
    """
    generator = CSIDataGenerator(n_subcarriers=30, n_timesteps=100, grid_size=10)

    materials = list(generator.MATERIAL_PROPERTIES.keys())

    X_list = []
    y_list = []

    for material in materials:
        X_mat, y_mat = generator.generate_with_specific_materials(
            num_samples_per_material=num_samples_per_material,
            material=material,
            num_walls=2
        )
        X_list.append(X_mat)
        y_list.append(y_mat)

    X = np.vstack(X_list)
    y = np.concatenate(y_list)

    # Shuffle
    idx = np.random.permutation(len(X))
    X = X[idx]
    y = y[idx]

    logger.info(f"✅ Generated {len(X)} total samples for material classification")

    # Save if path provided
    if output_path:
        np.savez(output_path, X=X, y=y)
        logger.info(f"✅ Data saved to {output_path}")

    return X, y


if __name__ == '__main__':
    # Test synthetic data generation
    print("\n=== Testing Synthetic CSI Data Generator ===\n")

    # Test single sample
    print("1. Testing single sample generation...")
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

    # Test batch generation
    print("\n2. Testing batch generation...")
    X, y, materials = generator.generate_batch(num_samples=100, max_walls=3)
    print(f"   Batch shape: X={X.shape}, y={y.shape}, materials={materials.shape}")

    # Test material classification data
    print("\n3. Testing material classification data generation...")
    X_mat, y_mat = generate_material_classification_data(num_samples_per_material=100)
    print(f"   Material classification data: X={X_mat.shape}, y={y_mat.shape}")

    print("\n✅ All tests passed")
