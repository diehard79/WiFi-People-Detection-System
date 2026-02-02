"""
Wall Visualizer

Generates visualizations for detected walls and room layouts:
1. 2D floorplan
2. CSI heatmap
3. 3D room visualization
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import List, Tuple, Optional
from pathlib import Path

from .wall_models import RoomLayout, WallDetection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WallVisualizer:
    """
    Visualizes wall detection results

    Generates:
    - 2D floorplans
    - CSI heatmaps
    - 3D room visualizations
    """

    def __init__(self, output_dir: str = "visualizations"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory for saving visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized wall visualizer (output_dir={output_dir})")

    def plot_floorplan(
        self,
        layout: RoomLayout,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create 2D floorplan visualization

        Args:
            layout: Room layout
            save_path: Optional save path

        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot walls
        for wall in layout.walls:
            # Plot wall line
            x = [wall.start_point[0], wall.end_point[0]]
            y = [wall.start_point[1], wall.end_point[1]]

            # Color by material
            color = self._get_material_color(wall.material)

            # Plot wall with thickness
            ax.plot(
                x, y,
                linewidth=wall.thickness * 50,
                color=color,
                alpha=0.8,
                solid_capstyle='round'
            )

            # Add wall label
            mid_x = (x[0] + x[1]) / 2
            mid_y = (y[0] + y[1]) / 2

            if wall.material:
                ax.text(
                    mid_x, mid_y,
                    wall.material,
                    fontsize=8,
                    ha='center',
                    va='center',
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor='white',
                        alpha=0.7
                    )
                )

        # Set plot limits
        ax.set_xlim(-1, layout.dimensions[0] + 1)
        ax.set_ylim(-1, layout.dimensions[1] + 1)

        # Labels and title
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Length (m)')
        ax.set_title(f'Room Floorplan ({layout.dimensions[0]:.1f}x{layout.dimensions[1]:.1f}m)\n'
                    f'Area: {layout.area:.1f}m² | Confidence: {layout.confidence:.1%}')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # Add legend
        legend_elements = [
            patches.Patch(color=self._get_material_color('concrete'), label='Concrete'),
            patches.Patch(color=self._get_material_color('brick'), label='Brick'),
            patches.Patch(color=self._get_material_color('drywall'), label='Drywall'),
            patches.Patch(color=self._get_material_color('wood'), label='Wood'),
            patches.Patch(color=self._get_material_color('glass'), label='Glass'),
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        # Save or return
        if save_path is None:
            save_path = self.output_dir / "floorplan.png"
        else:
            save_path = Path(save_path)

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved floorplan to {save_path}")
        return str(save_path)

    def plot_csi_heatmap(
        self,
        csi_data: dict,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create CSI heatmap visualization

        Args:
            csi_data: CSI data from detectors
            save_path: Optional save path

        Returns:
            Path to saved image
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        detector_names = list(csi_data.keys())

        for idx, detector_id in enumerate(detector_names[:4]):
            ax = axes[idx]

            # Get CSI data for this detector
            data = csi_data[detector_id]

            # Create heatmap
            if isinstance(data, np.ndarray) and len(data.shape) == 2:
                im = ax.imshow(data, aspect='auto', cmap='viridis')
                plt.colorbar(im, ax=ax, label='Amplitude')
            else:
                # Plot time series
                ax.plot(data)
                ax.set_ylabel('Amplitude')

            ax.set_title(f'{detector_id}')
            ax.set_xlabel('Sample Index')

        plt.suptitle('CSI Heatmap from All Detectors', fontsize=14)
        plt.tight_layout()

        # Save or return
        if save_path is None:
            save_path = self.output_dir / "csi_heatmap.png"
        else:
            save_path = Path(save_path)

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved CSI heatmap to {save_path}")
        return str(save_path)

    def plot_3d_room(
        self,
        layout: RoomLayout,
        wall_height: float = 2.5,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create 3D room visualization

        Args:
            layout: Room layout
            wall_height: Wall height in meters
            save_path: Optional save path

        Returns:
            Path to saved image
        """
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Create 3D walls
        for wall in layout.walls:
            # Wall corners
            x0, y0 = wall.start_point
            x1, y1 = wall.end_point

            # Create wall vertices
            verts = [
                [(x0, y0, 0), (x1, y1, 0), (x1, y1, wall_height), (x0, y0, wall_height)]
            ]

            # Plot wall
            poly = Poly3DCollection(verts, alpha=0.7)
            color = self._get_material_color(wall.material)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            ax.add_collection3d(poly)

        # Set plot limits
        ax.set_xlim(0, layout.dimensions[0])
        ax.set_ylim(0, layout.dimensions[1])
        ax.set_zlim(0, wall_height)

        # Labels
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Length (m)')
        ax.set_zlabel('Height (m)')
        ax.set_title(f'3D Room Visualization\n'
                    f'{layout.dimensions[0]:.1f}x{layout.dimensions[1]:.1f}x{wall_height:.1f}m')

        # Set viewing angle
        ax.view_init(elev=20, azim=45)

        # Save or return
        if save_path is None:
            save_path = self.output_dir / "room_3d.png"
        else:
            save_path = Path(save_path)

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved 3D visualization to {save_path}")
        return str(save_path)

    def plot_detection_confidence(
        self,
        layout: RoomLayout,
        save_path: Optional[str] = None
    ) -> str:
        """
        Plot detection confidence map

        Args:
            layout: Room layout
            save_path: Optional save path

        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot walls with confidence-based colors
        for wall in layout.walls:
            x = [wall.start_point[0], wall.end_point[0]]
            y = [wall.start_point[1], wall.end_point[1]]

            # Color by confidence
            color = plt.cm.RdYlGn(wall.confidence)

            ax.plot(
                x, y,
                linewidth=wall.thickness * 50,
                color=color,
                solid_capstyle='round'
            )

            # Add confidence label
            mid_x = (x[0] + x[1]) / 2
            mid_y = (y[0] + y[1]) / 2

            ax.text(
                mid_x, mid_y,
                f'{wall.confidence:.0%}',
                fontsize=8,
                ha='center',
                va='center',
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='white',
                    alpha=0.7
                )
            )

        # Set plot limits
        ax.set_xlim(-1, layout.dimensions[0] + 1)
        ax.set_ylim(-1, layout.dimensions[1] + 1)

        # Labels and title
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Length (m)')
        ax.set_title(f'Wall Detection Confidence Map\n'
                    f'Overall Confidence: {layout.confidence:.1%}')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn,
                                   norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Confidence')

        # Save or return
        if save_path is None:
            save_path = self.output_dir / "confidence_map.png"
        else:
            save_path = Path(save_path)

        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved confidence map to {save_path}")
        return str(save_path)

    def _get_material_color(self, material: Optional[str]) -> str:
        """
        Get color for material type

        Args:
            material: Material type

        Returns:
            Color string
        """
        colors = {
            'concrete': '#808080',
            'brick': '#8B4513',
            'drywall': '#F5F5DC',
            'wood': '#DEB887',
            'glass': '#ADD8E6',
            None: '#000000'
        }

        return colors.get(material, '#000000')

    def generate_all_visualizations(
        self,
        layout: RoomLayout,
        csi_data: Optional[dict] = None
    ) -> dict:
        """
        Generate all visualizations

        Args:
            layout: Room layout
            csi_data: Optional CSI data

        Returns:
            Dictionary of visualization types to paths
        """
        visualizations = {}

        # 2D floorplan
        visualizations['floorplan'] = self.plot_floorplan(layout)

        # Confidence map
        visualizations['confidence'] = self.plot_detection_confidence(layout)

        # 3D visualization
        visualizations['3d'] = self.plot_3d_room(layout)

        # CSI heatmap (if data provided)
        if csi_data:
            visualizations['csi_heatmap'] = self.plot_csi_heatmap(csi_data)

        logger.info(f"Generated {len(visualizations)} visualizations")
        return visualizations


if __name__ == "__main__":
    # Test visualizer
    print("\n=== Testing Wall Visualizer ===\n")

    from .wall_models import WallDetection, RoomLayout
    from datetime import datetime

    # Create dummy layout
    walls = [
        WallDetection(
            start_point=(0.0, 0.0),
            end_point=(5.0, 0.0),
            confidence=0.95,
            thickness=0.2,
            material='concrete'
        ),
        WallDetection(
            start_point=(5.0, 0.0),
            end_point=(5.0, 4.0),
            confidence=0.92,
            thickness=0.2,
            material='brick'
        ),
        WallDetection(
            start_point=(5.0, 4.0),
            end_point=(0.0, 4.0),
            confidence=0.88,
            thickness=0.15,
            material='drywall'
        ),
        WallDetection(
            start_point=(0.0, 4.0),
            end_point=(0.0, 0.0),
            confidence=0.90,
            thickness=0.2,
            material='concrete'
        )
    ]

    layout = RoomLayout(
        walls=walls,
        dimensions=(5.0, 4.0),
        area=20.0,
        perimeter=18.0,
        confidence=0.91,
        detected_at=datetime.now().isoformat()
    )

    # Create visualizer
    visualizer = WallVisualizer()

    # Generate all visualizations
    viz = visualizer.generate_all_visualizations(layout)

    print(f"\nGenerated visualizations:")
    for name, path in viz.items():
        print(f"  {name}: {path}")

    print("\n✅ Visualizer working correctly")
