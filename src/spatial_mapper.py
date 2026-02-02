"""
Spatial Mapping and Visualization for Room Layout Detection

This module provides comprehensive room layout mapping and visualization capabilities
for wall detection using WiFi RSSI data. It includes:

- RoomLayoutMapper: Convert wall detection grids into structured room layouts
- WallVisualizer: Generate visual representations (2D floorplans, 3D views, heatmaps)
- SVG Generator: Create scalable vector graphics floorplans for web display

Author: WiFi People Detection System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Dict, Optional, Any
from pathlib import Path
import json
import logging

import numpy as np
from scipy import ndimage
from scipy.spatial import distance
from sklearn.cluster import DBSCAN
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw, ImageFont
import svgwrite
from svgwrite import cm, mm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === Data Structures ===

@dataclass
class WallSegment:
    """
    Represents a detected wall segment in the room.

    Attributes:
        start_point: (x, y) coordinates in meters
        end_point: (x, y) coordinates in meters
        material: Wall material type (concrete, drywall, wood, metal, glass)
        thickness: Wall thickness in meters
        confidence: Detection confidence (0.0 to 1.0)
        length: Length of wall segment in meters (computed)
    """
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    material: str = 'drywall'
    thickness: float = 0.1
    confidence: float = 0.8

    def __post_init__(self):
        """Compute derived attributes."""
        self.length = np.sqrt(
            (self.end_point[0] - self.start_point[0])**2 +
            (self.end_point[1] - self.start_point[1])**2
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'start_point': self.start_point,
            'end_point': self.end_point,
            'material': self.material,
            'thickness': self.thickness,
            'confidence': self.confidence,
            'length': self.length
        }


@dataclass
class RoomLayout:
    """
    Complete room layout representation.

    Attributes:
        walls: List of detected wall segments
        dimensions: (width, length) in meters
        area: Room area in square meters
        corners: List of corner coordinates
        detection_timestamp: When the layout was detected
        grid_resolution: Resolution of detection grid in meters
        detector_positions: Positions of WiFi detectors
    """
    walls: List[WallSegment] = field(default_factory=list)
    dimensions: Tuple[float, float] = (10.0, 10.0)
    area: float = 100.0
    corners: List[Tuple[float, float]] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.now)
    grid_resolution: float = 0.1
    detector_positions: List[Tuple[float, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'walls': [wall.to_dict() for wall in self.walls],
            'dimensions': self.dimensions,
            'area': self.area,
            'corners': self.corners,
            'detection_timestamp': self.detection_timestamp.isoformat(),
            'grid_resolution': self.grid_resolution,
            'detector_positions': self.detector_positions
        }

    def save(self, filepath: str):
        """Save layout to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'RoomLayout':
        """Load layout from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        walls = [WallSegment(**wall_data) for wall_data in data['walls']]
        layout = cls(walls=walls)
        layout.dimensions = tuple(data['dimensions'])
        layout.area = data['area']
        layout.corners = [tuple(corner) for corner in data['corners']]
        layout.detection_timestamp = datetime.fromisoformat(data['detection_timestamp'])
        layout.grid_resolution = data['grid_resolution']
        layout.detector_positions = [tuple(pos) for pos in data['detector_positions']]

        return layout


# === Room Layout Mapper ===

class RoomLayoutMapper:
    """
    Convert wall detection grid into structured room layout.

    Uses computer vision techniques to:
    1. Threshold probability grids
    2. Apply morphological operations
    3. Detect line segments using Hough transform
    4. Merge collinear segments
    5. Identify corners and intersections
    6. Generate optimized layouts
    """

    def __init__(self, room_size: Tuple[float, float] = (10.0, 10.0)):
        """
        Initialize room layout mapper.

        Args:
            room_size: (width, length) of room in meters
        """
        self.room_size = room_size
        self.grid_resolution = 0.1  # 10cm per grid cell
        self.grid_shape = (
            int(room_size[0] / self.grid_resolution),
            int(room_size[1] / self.grid_resolution)
        )

        # Material probability thresholds (based on signal attenuation)
        self.material_thresholds = {
            'concrete': 0.9,  # High attenuation
            'metal': 0.85,
            'wood': 0.75,
            'drywall': 0.7,
            'glass': 0.6     # Low attenuation
        }

        logger.info(f"RoomLayoutMapper initialized: room_size={room_size}m, "
                   f"grid_shape={self.grid_shape}")

    def walls_to_layout(
        self,
        wall_grid: np.ndarray,
        detector_positions: Optional[List[Tuple[float, float]]] = None
    ) -> RoomLayout:
        """
        Convert probability grid to structured room layout.

        Algorithm:
        1. Threshold probabilities (>0.7 = wall)
        2. Apply morphological operations (dilation, erosion)
        3. Detect line segments using Hough transform
        4. Merge collinear segments
        5. Identify corners and intersections
        6. Generate structured layout

        Args:
            wall_grid: 2D probability grid (0.0 to 1.0)
            detector_positions: Optional positions of WiFi detectors

        Returns:
            RoomLayout object with detected walls and metadata
        """
        logger.info("Converting wall grid to room layout...")

        # Step 1: Threshold probabilities
        binary_grid = (wall_grid > 0.7).astype(np.uint8)

        # Step 2: Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(binary_grid, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

        # Step 3: Detect lines using Hough transform
        lines = self._detect_lines_hough(cleaned)

        # Step 4: Merge collinear segments
        merged_lines = self._merge_collinear_lines(lines)

        # Step 5: Convert to wall segments
        wall_segments = self._lines_to_wall_segments(merged_lines, wall_grid)

        # Step 6: Identify corners
        corners = self._detect_corners(wall_segments)

        # Step 7: Calculate room area
        area = self._calculate_room_area(wall_segments)

        # Create layout
        layout = RoomLayout(
            walls=wall_segments,
            dimensions=self.room_size,
            area=area,
            corners=corners,
            detection_timestamp=datetime.now(),
            grid_resolution=self.grid_resolution,
            detector_positions=detector_positions or []
        )

        logger.info(f"Layout created: {len(wall_segments)} walls detected, "
                   f"area={area:.2f}m²")

        return layout

    def _detect_lines_hough(
        self,
        binary_grid: np.ndarray,
        threshold: int = 30,
        min_line_length: int = 10,
        max_line_gap: int = 5
    ) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Detect line segments using probabilistic Hough transform.

        Args:
            binary_grid: Binary image
            threshold: Accumulator threshold
            min_line_length: Minimum line length in pixels
            max_line_gap: Maximum gap between line segments

        Returns:
            List of ((x1, y1), (x2, y2)) line endpoints
        """
        lines = cv2.HoughLinesP(
            binary_grid,
            rho=1,
            theta=np.pi / 180,
            threshold=threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )

        if lines is None:
            logger.warning("No lines detected in wall grid")
            return []

        # Convert to list of endpoints
        line_segments = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_segments.append(((float(x1), float(y1)), (float(x2), float(y2))))

        logger.info(f"Detected {len(line_segments)} line segments")
        return line_segments

    def _merge_collinear_lines(
        self,
        lines: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        angle_threshold: float = 5.0,
        distance_threshold: float = 0.5
    ) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Merge collinear line segments.

        Args:
            lines: List of line segments
            angle_threshold: Maximum angle difference for collinearity (degrees)
            distance_threshold: Maximum distance for merging (meters)

        Returns:
            List of merged line segments
        """
        if not lines:
            return []

        # Calculate line angles and midpoints
        line_data = []
        for (p1, p2) in lines:
            angle = np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))
            midpoint = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            line_data.append({
                'line': (p1, p2),
                'angle': angle,
                'midpoint': midpoint,
                'length': length
            })

        # Cluster lines by angle
        merged = []
        used = set()

        for i, data_i in enumerate(line_data):
            if i in used:
                continue

            # Find collinear lines
            group = [data_i]
            used.add(i)

            for j, data_j in enumerate(line_data):
                if j in used:
                    continue

                angle_diff = abs(data_i['angle'] - data_j['angle'])
                if angle_diff > 90:
                    angle_diff = 180 - angle_diff

                if angle_diff < angle_threshold:
                    # Check distance
                    dist = distance.euclidean(data_i['midpoint'], data_j['midpoint'])
                    if dist < distance_threshold * 10:  # Convert to pixels
                        group.append(data_j)
                        used.add(j)

            # Merge group
            if len(group) > 1:
                # Extend line to encompass all segments
                all_points = [pt for data in group for pt in data['line']]
                x_coords = [p[0] for p in all_points]
                y_coords = [p[1] for p in all_points]

                # Find extreme points
                p1 = (min(x_coords), min(y_coords))
                p2 = (max(x_coords), max(y_coords))
                merged.append((p1, p2))
            else:
                merged.append(data_i['line'])

        logger.info(f"Merged {len(lines)} lines into {len(merged)} segments")
        return merged

    def _lines_to_wall_segments(
        self,
        lines: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        probability_grid: np.ndarray
    ) -> List[WallSegment]:
        """
        Convert detected lines to WallSegment objects.

        Args:
            lines: List of line segments in pixel coordinates
            probability_grid: Original probability grid

        Returns:
            List of WallSegment objects
        """
        wall_segments = []

        for (p1, p2) in lines:
            # Convert pixel coordinates to meters
            start_m = (
                p1[0] * self.grid_resolution,
                p1[1] * self.grid_resolution
            )
            end_m = (
                p2[0] * self.grid_resolution,
                p2[1] * self.grid_resolution
            )

            # Sample probabilities along the line
            num_samples = 10
            x_samples = np.linspace(p1[0], p2[0], num_samples).astype(int)
            y_samples = np.linspace(p1[1], p2[1], num_samples).astype(int)

            probs = []
            for x, y in zip(x_samples, y_samples):
                if 0 <= x < probability_grid.shape[1] and 0 <= y < probability_grid.shape[0]:
                    probs.append(probability_grid[y, x])

            avg_prob = np.mean(probs) if probs else 0.7

            # Determine material based on probability
            material = 'drywall'
            for mat, threshold in self.material_thresholds.items():
                if avg_prob >= threshold:
                    material = mat
                    break

            # Estimate thickness (simplified)
            thickness = 0.1 if material == 'drywall' else 0.15

            # Create wall segment
            wall = WallSegment(
                start_point=start_m,
                end_point=end_m,
                material=material,
                thickness=thickness,
                confidence=avg_prob
            )

            wall_segments.append(wall)

        return wall_segments

    def _detect_corners(
        self,
        walls: List[WallSegment],
        angle_threshold: float = 20.0
    ) -> List[Tuple[float, float]]:
        """
        Detect corners by finding wall intersections.

        Args:
            walls: List of wall segments
            angle_threshold: Minimum angle for corner (degrees)

        Returns:
            List of corner coordinates in meters
        """
        corners = []

        for i, wall1 in enumerate(walls):
            for j, wall2 in enumerate(walls[i+1:], i+1):
                # Check if walls intersect
                intersection = self._line_intersection(
                    wall1.start_point, wall1.end_point,
                    wall2.start_point, wall2.end_point
                )

                if intersection is not None:
                    # Calculate angle between walls
                    angle1 = np.arctan2(
                        wall1.end_point[1] - wall1.start_point[1],
                        wall1.end_point[0] - wall1.start_point[0]
                    )
                    angle2 = np.arctan2(
                        wall2.end_point[1] - wall2.start_point[1],
                        wall2.end_point[0] - wall2.start_point[0]
                    )

                    angle_diff = np.degrees(abs(angle1 - angle2))
                    if angle_diff > 90:
                        angle_diff = 180 - angle_diff

                    # Only add if angle is significant
                    if angle_diff > angle_threshold:
                        corners.append(intersection)

        # Remove duplicates
        corners_unique = []
        for corner in corners:
            is_duplicate = False
            for existing in corners_unique:
                if distance.euclidean(corner, existing) < 0.2:  # 20cm threshold
                    is_duplicate = True
                    break
            if not is_duplicate:
                corners_unique.append(corner)

        logger.info(f"Detected {len(corners_unique)} corners")
        return corners_unique

    def _line_intersection(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        """
        Find intersection point of two line segments.

        Args:
            p1, p2: Endpoints of first line
            p3, p4: Endpoints of second line

        Returns:
            Intersection point or None if no intersection
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None  # Parallel lines

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)

        return None

    def _calculate_room_area(self, walls: List[WallSegment]) -> float:
        """
        Calculate room area from wall segments.

        Args:
            walls: List of wall segments

        Returns:
            Area in square meters
        """
        if not walls:
            return self.room_size[0] * self.room_size[1]

        # Simple approximation: convex hull area
        points = []
        for wall in walls:
            points.append(wall.start_point)
            points.append(wall.end_point)

        if not points:
            return self.room_size[0] * self.room_size[1]

        # Calculate convex hull using Graham scan
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(points)
            return hull.volume  # In 2D, volume is area
        except:
            # Fallback to bounding box
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            width = max(x_coords) - min(x_coords)
            length = max(y_coords) - min(y_coords)
            return width * length

    def optimize_layout(self, layout: RoomLayout) -> RoomLayout:
        """
        Optimize wall layout using geometric constraints:
        - Walls are straight lines
        - Parallel walls (opposite sides)
        - Right angles (corners)
        - Minimum wall length (1m)

        Args:
            layout: Input room layout

        Returns:
            Optimized room layout
        """
        logger.info("Optimizing room layout...")

        # Filter short walls
        optimized_walls = [
            wall for wall in layout.walls
            if wall.length >= 1.0  # Minimum 1m
        ]

        # Snap walls to cardinal directions (0, 90, 180, 270 degrees)
        for wall in optimized_walls:
            angle = np.arctan2(
                wall.end_point[1] - wall.start_point[1],
                wall.end_point[0] - wall.start_point[0]
            )
            angle_deg = np.degrees(angle)

            # Snap to nearest 90 degrees
            snapped_angle = round(angle_deg / 90) * 90

            # Adjust endpoints if needed
            if abs(angle_deg - snapped_angle) < 10:
                length = wall.length
                snapped_rad = np.radians(snapped_angle)
                new_end = (
                    wall.start_point[0] + length * np.cos(snapped_rad),
                    wall.start_point[1] + length * np.sin(snapped_rad)
                )
                wall.end_point = new_end

        # Update layout
        layout.walls = optimized_walls
        layout.area = self._calculate_room_area(optimized_walls)
        layout.corners = self._detect_corners(optimized_walls)

        logger.info(f"Layout optimized: {len(optimized_walls)} walls remaining")
        return layout


# === Wall Visualizer ===

class WallVisualizer:
    """
    Generate visual representations of room layout.

    Features:
    - Architectural floorplan images
    - 3D room views
    - Probability heatmaps
    - SVG floorplans for web display
    """

    def __init__(self):
        """Initialize visualizer with color schemes."""
        self.colors = {
            'concrete': '#808080',
            'drywall': '#F5F5DC',
            'wood': '#DEB887',
            'metal': '#C0C0C0',
            'glass': '#E0F7FA'
        }

        self.default_size = (800, 800)
        self.dpi = 100

        logger.info("WallVisualizer initialized")

    def generate_floorplan_image(
        self,
        layout: RoomLayout,
        output_path: str,
        size: Tuple[int, int] = (800, 800)
    ) -> str:
        """
        Generate architectural floorplan image.

        Features:
        - Draw walls with correct thickness and colors
        - Add dimensions and labels
        - Include compass rose
        - Show detector positions
        - Add legend

        Args:
            layout: Room layout to visualize
            output_path: Path to save image
            size: Image size (width, height) in pixels

        Returns:
            Path to saved image
        """
        logger.info(f"Generating floorplan: {output_path}")

        fig, ax = plt.subplots(figsize=(size[0]/self.dpi, size[1]/self.dpi), dpi=self.dpi)

        # Set up the plot
        ax.set_xlim(0, layout.dimensions[0])
        ax.set_ylim(0, layout.dimensions[1])
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Distance (m)')
        ax.set_title(f'Room Layout - {layout.area:.1f}m²')
        ax.grid(True, alpha=0.3)

        # Draw walls
        for wall in layout.walls:
            color = self.colors.get(wall.material, '#808080')
            linewidth = wall.thickness * 50  # Scale for visibility

            ax.plot(
                [wall.start_point[0], wall.end_point[0]],
                [wall.start_point[1], wall.end_point[1]],
                color=color,
                linewidth=linewidth,
                solid_capstyle='round',
                alpha=wall.confidence
            )

        # Draw detector positions
        if layout.detector_positions:
            detector_x = [pos[0] for pos in layout.detector_positions]
            detector_y = [pos[1] for pos in layout.detector_positions]
            ax.scatter(detector_x, detector_y, c='red', marker='^', s=200, label='WiFi Detectors', zorder=5)

        # Draw corners
        if layout.corners:
            corner_x = [c[0] for c in layout.corners]
            corner_y = [c[1] for c in layout.corners]
            ax.scatter(corner_x, corner_y, c='blue', marker='o', s=100, label='Corners', zorder=5)

        # Add compass rose
        self._add_compass_rose(ax, layout.dimensions[0] * 0.9, layout.dimensions[1] * 0.9)

        # Add legend
        ax.legend(loc='upper right')

        # Add dimensions
        ax.text(
            layout.dimensions[0] / 2,
            -0.5,
            f'{layout.dimensions[0]:.1f}m',
            ha='center',
            fontsize=10
        )
        ax.text(
            -0.5,
            layout.dimensions[1] / 2,
            f'{layout.dimensions[1]:.1f}m',
            va='center',
            rotation=90,
            fontsize=10
        )

        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Floorplan saved to {output_path}")
        return output_path

    def _add_compass_rose(self, ax, x, y, size=1.0):
        """Add compass rose to plot."""
        # North arrow
        ax.arrow(x, y, 0, size, head_width=0.1, head_length=0.1, fc='black', ec='black')
        ax.text(x, y + size + 0.1, 'N', ha='center', fontsize=12, fontweight='bold')

        # East arrow
        ax.arrow(x, y, size, 0, head_width=0.1, head_length=0.1, fc='gray', ec='gray')
        ax.text(x + size + 0.1, y, 'E', va='center', fontsize=10)

    def generate_3d_room_view(
        self,
        layout: RoomLayout,
        output_path: str,
        wall_height: float = 2.5
    ) -> str:
        """
        Generate 3D perspective view of room.

        Features:
        - 3D wall rendering
        - Textured surfaces by material
        - Depth perspective
        - Lighting effects

        Args:
            layout: Room layout to visualize
            output_path: Path to save image
            wall_height: Height of walls in meters

        Returns:
            Path to saved image
        """
        logger.info(f"Generating 3D view: {output_path}")

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Draw walls as 3D surfaces
        for wall in layout.walls:
            color = self.colors.get(wall.material, '#808080')

            # Create wall surface (proper rectangle)
            x = [wall.start_point[0], wall.end_point[0],
                 wall.end_point[0], wall.start_point[0]]
            y = [wall.start_point[1], wall.end_point[1],
                 wall.end_point[1], wall.start_point[1]]
            z = [0, 0, wall_height, wall_height]

            # Create proper vertices for plot_surface
            X = np.array([[wall.start_point[0], wall.end_point[0]],
                         [wall.start_point[0], wall.end_point[0]]])
            Y = np.array([[wall.start_point[1], wall.end_point[1]],
                         [wall.start_point[1], wall.end_point[1]]])
            Z = np.array([[0, 0], [wall_height, wall_height]])

            # Plot surface
            ax.plot_surface(X, Y, Z, color=color, alpha=wall.confidence * 0.7)

        # Set labels and limits
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Height (m)')
        ax.set_title(f'3D Room View - {layout.area:.1f}m²')

        ax.set_xlim(0, layout.dimensions[0])
        ax.set_ylim(0, layout.dimensions[1])
        ax.set_zlim(0, wall_height)

        # Set view angle
        ax.view_init(elev=20, azim=45)

        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"3D view saved to {output_path}")
        return output_path

    def generate_heatmap(
        self,
        wall_probabilities: np.ndarray,
        output_path: str,
        title: str = "Wall Detection Probability"
    ) -> str:
        """
        Generate probability heatmap visualization.

        Features:
        - Color gradient (blue=low, red=high)
        - Color bar legend
        - Grid overlay
        - Detector positions

        Args:
            wall_probabilities: 2D probability grid
            output_path: Path to save image
            title: Heatmap title

        Returns:
            Path to saved image
        """
        logger.info(f"Generating heatmap: {output_path}")

        fig, ax = plt.subplots(figsize=(10, 8))

        # Create custom colormap (blue to red)
        colors_list = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000']
        cmap = LinearSegmentedColormap.from_list('custom', colors_list)

        # Plot heatmap
        im = ax.imshow(
            wall_probabilities,
            cmap=cmap,
            interpolation='bilinear',
            origin='lower',
            vmin=0.0,
            vmax=1.0
        )

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Wall Probability', rotation=270, labelpad=20)

        # Labels and title
        ax.set_xlabel('Grid X')
        ax.set_ylabel('Grid Y')
        ax.set_title(title)

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"Heatmap saved to {output_path}")
        return output_path

    def generate_pil_floorplan(
        self,
        layout: RoomLayout,
        output_path: str,
        size: Tuple[int, int] = (800, 800)
    ) -> str:
        """
        Generate floorplan using PIL for higher quality output.

        Args:
            layout: Room layout to visualize
            output_path: Path to save image
            size: Image size (width, height) in pixels

        Returns:
            Path to saved image
        """
        logger.info(f"Generating PIL floorplan: {output_path}")

        # Create image
        img = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(img)

        # Scale factors
        scale_x = size[0] / layout.dimensions[0]
        scale_y = size[1] / layout.dimensions[1]

        # Draw walls
        for wall in layout.walls:
            # Convert to pixel coordinates
            x1 = int(wall.start_point[0] * scale_x)
            y1 = int(wall.start_point[1] * scale_y)
            x2 = int(wall.end_point[0] * scale_x)
            y2 = int(wall.end_point[1] * scale_y)

            # Get color
            color = self.colors.get(wall.material, '#808080')

            # Draw wall
            linewidth = int(wall.thickness * 50)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=linewidth)

        # Draw detectors
        if layout.detector_positions:
            for pos in layout.detector_positions:
                x = int(pos[0] * scale_x)
                y = int(pos[1] * scale_y)
                draw.ellipse([x-10, y-10, x+10, y+10], fill='red', outline='black')

        # Draw corners
        if layout.corners:
            for corner in layout.corners:
                x = int(corner[0] * scale_x)
                y = int(corner[1] * scale_y)
                draw.ellipse([x-5, y-5, x+5, y+5], fill='blue', outline='black')

        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((10, 10), f"Room Layout - {layout.area:.1f}m²", fill='black', font=font)

        # Save
        img.save(output_path, 'PNG', dpi=(self.dpi, self.dpi))

        logger.info(f"PIL floorplan saved to {output_path}")
        return output_path


# === SVG Floorplan Generator ===

def generate_svg_floorplan(
    layout: RoomLayout,
    width: int = 800,
    height: int = 800
) -> str:
    """
    Generate SVG floorplan for web display.

    Features:
    - Scalable vector graphics
    - Interactive elements (hover for details)
    - Material-based styling
    - Responsive design

    Args:
        layout: Room layout to visualize
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        SVG string
    """
    logger.info("Generating SVG floorplan")

    # Calculate scale
    scale_x = width / layout.dimensions[0]
    scale_y = height / layout.dimensions[1]

    # Create SVG document
    svg = svgwrite.Drawing(
        size=(f"{width}px", f"{height}px"),
        viewBox=f"0 0 {width} {height}"
    )

    # Add background
    svg.add(svgwrite.shapes.Rect(insert=(0, 0), size=(width, height), fill='white'))

    # Add title
    svg.add(svgwrite.text.Text(
        f"Room Layout - {layout.area:.1f}m²",
        insert=(width // 2, 30),
        font_size='24',
        text_anchor='middle',
        font_weight='bold'
    ))

    # Add walls
    for wall in layout.walls:
        # Convert to pixel coordinates
        x1 = wall.start_point[0] * scale_x
        y1 = wall.start_point[1] * scale_y
        x2 = wall.end_point[0] * scale_x
        y2 = wall.end_point[1] * scale_y

        # Get color
        color = {
            'concrete': '#808080',
            'drywall': '#F5F5DC',
            'wood': '#DEB887',
            'metal': '#C0C0C0',
            'glass': '#E0F7FA'
        }.get(wall.material, '#808080')

        # Create line with hover effect
        line = svgwrite.shapes.Line(
            start=(x1, y1),
            end=(x2, y2),
            stroke=color,
            stroke_width=wall.thickness * 50,
            stroke_opacity=wall.confidence
        )

        # Add tooltip
        line.set_desc(
            f"Wall: {wall.material}\n"
            f"Length: {wall.length:.2f}m\n"
            f"Thickness: {wall.thickness*100:.1f}cm\n"
            f"Confidence: {wall.confidence:.1%}"
        )

        svg.add(line)

    # Add detector positions
    if layout.detector_positions:
        for i, pos in enumerate(layout.detector_positions):
            x = pos[0] * scale_x
            y = pos[1] * scale_y

            # Draw detector as triangle
            points = [(x, y-10), (x-10, y+10), (x+10, y+10)]
            triangle = svgwrite.shapes.Polygon(points, fill='red', stroke='black')
            triangle.set_desc(f"Detector {i+1}\nPosition: ({pos[0]:.1f}, {pos[1]:.1f})")
            svg.add(triangle)

    # Add corners
    if layout.corners:
        for i, corner in enumerate(layout.corners):
            x = corner[0] * scale_x
            y = corner[1] * scale_y

            circle = svgwrite.shapes.Circle(
                center=(x, y),
                r=5,
                fill='blue',
                stroke='black'
            )
            circle.set_desc(f"Corner {i+1}\nPosition: ({corner[0]:.1f}, {corner[1]:.1f})")
            svg.add(circle)

    # Add legend
    legend_y = height - 120
    svg.add(svgwrite.text.Text("Legend:", insert=(20, legend_y), font_size='16', font_weight='bold'))

    legend_items = [
        ("WiFi Detectors", 'red', 'triangle'),
        ("Corners", 'blue', 'circle'),
    ]

    for i, (label, color, shape) in enumerate(legend_items):
        y = legend_y + 25 + i * 25
        if shape == 'triangle':
            points = [(30, y-5), (25, y+5), (35, y+5)]
            svg.add(svgwrite.shapes.Polygon(points, fill=color))
        else:
            svg.add(svgwrite.shapes.Circle(center=(30, y), r=5, fill=color))

        svg.add(svgwrite.text.Text(label, insert=(50, y+5), font_size='14'))

    # Add dimensions
    svg.add(svgwrite.text.Text(
        f"{layout.dimensions[0]:.1f}m",
        insert=(width // 2, height - 10),
        font_size='14',
        text_anchor='middle'
    ))

    svg_string = svg.tostring()

    logger.info("SVG floorplan generated")
    return svg_string


# === Utility Functions ===

def create_sample_wall_grid(
    grid_size: Tuple[int, int] = (100, 100),
    room_type: str = "rectangular"
) -> np.ndarray:
    """
    Create sample wall probability grid for testing.

    Args:
        grid_size: (width, height) in grid cells
        room_type: Type of room layout

    Returns:
        2D probability grid
    """
    grid = np.zeros(grid_size)

    if room_type == "rectangular":
        # Simple rectangular room
        # Top and bottom walls
        grid[0:10, :] = 0.9
        grid[-10:, :] = 0.9
        # Left and right walls
        grid[:, 0:10] = 0.9
        grid[:, -10:] = 0.9

    elif room_type == "l_shaped":
        # L-shaped room
        grid[0:10, :] = 0.9
        grid[:, 0:10] = 0.9
        grid[50:60, 50:] = 0.9
        grid[50:, 50:60] = 0.9

    elif room_type == "with_partition":
        # Room with internal partition
        grid[0:10, :] = 0.9
        grid[-10:, :] = 0.9
        grid[:, 0:10] = 0.9
        grid[:, -10:] = 0.9
        grid[45:55, 20:80] = 0.8  # Internal wall

    # Add some noise
    noise = np.random.randn(*grid_size) * 0.05
    grid = np.clip(grid + noise, 0, 1)

    return grid


def save_layout_comparison(
    layout1: RoomLayout,
    layout2: RoomLayout,
    output_path: str
):
    """
    Save side-by-side comparison of two layouts.

    Args:
        layout1: First layout (e.g., raw detection)
        layout2: Second layout (e.g., optimized)
        output_path: Path to save comparison image
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Plot first layout
    ax1.set_title(f"Raw Detection - {len(layout1.walls)} walls")
    for wall in layout1.walls:
        ax1.plot(
            [wall.start_point[0], wall.end_point[0]],
            [wall.start_point[1], wall.end_point[1]],
            linewidth=wall.thickness * 50,
            alpha=wall.confidence
        )
    ax1.set_xlim(0, layout1.dimensions[0])
    ax1.set_ylim(0, layout1.dimensions[1])
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)

    # Plot second layout
    ax2.set_title(f"Optimized - {len(layout2.walls)} walls")
    for wall in layout2.walls:
        ax2.plot(
            [wall.start_point[0], wall.end_point[0]],
            [wall.start_point[1], wall.end_point[1]],
            linewidth=wall.thickness * 50,
            alpha=wall.confidence
        )
    ax2.set_xlim(0, layout2.dimensions[0])
    ax2.set_ylim(0, layout2.dimensions[1])
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close()

    logger.info(f"Layout comparison saved to {output_path}")


# === Main Demo ===

if __name__ == "__main__":
    """Demo the spatial mapping system."""

    print("=" * 60)
    print("Spatial Mapper Demo")
    print("=" * 60)

    # Create directories
    Path("docs/floorplan_examples").mkdir(parents=True, exist_ok=True)

    # Create sample wall grid
    print("\n1. Creating sample wall grid...")
    wall_grid = create_sample_wall_grid(room_type="rectangular")

    # Initialize mapper
    print("\n2. Initializing RoomLayoutMapper...")
    mapper = RoomLayoutMapper(room_size=(10.0, 10.0))

    # Add detector positions
    detector_positions = [
        (2.0, 2.0),
        (8.0, 2.0),
        (2.0, 8.0),
        (8.0, 8.0)
    ]

    # Convert to layout
    print("\n3. Converting grid to layout...")
    layout = mapper.walls_to_layout(wall_grid, detector_positions)

    print(f"   - Detected {len(layout.walls)} walls")
    print(f"   - Room area: {layout.area:.2f} m²")
    print(f"   - Found {len(layout.corners)} corners")

    # Optimize layout
    print("\n4. Optimizing layout...")
    optimized_layout = mapper.optimize_layout(layout)

    print(f"   - Optimized to {len(optimized_layout.walls)} walls")
    print(f"   - Optimized area: {optimized_layout.area:.2f} m²")

    # Initialize visualizer
    print("\n5. Generating visualizations...")
    visualizer = WallVisualizer()

    # Generate floorplan
    print("   - Floorplan image...")
    visualizer.generate_floorplan_image(
        optimized_layout,
        "docs/floorplan_examples/floorplan.png"
    )

    # Generate 3D view
    print("   - 3D room view...")
    visualizer.generate_3d_room_view(
        optimized_layout,
        "docs/floorplan_examples/3d_view.png"
    )

    # Generate heatmap
    print("   - Probability heatmap...")
    visualizer.generate_heatmap(
        wall_grid,
        "docs/floorplan_examples/heatmap.png"
    )

    # Generate PIL floorplan
    print("   - High-quality PIL floorplan...")
    visualizer.generate_pil_floorplan(
        optimized_layout,
        "docs/floorplan_examples/floorplan_pil.png"
    )

    # Generate SVG floorplan
    print("   - SVG floorplan...")
    svg_string = generate_svg_floorplan(optimized_layout)

    with open("docs/floorplan_examples/floorplan.svg", 'w') as f:
        f.write(svg_string)

    # Save layout comparison
    print("   - Layout comparison...")
    save_layout_comparison(
        layout,
        optimized_layout,
        "docs/floorplan_examples/comparison.png"
    )

    # Save layout to JSON
    print("\n6. Saving layout data...")
    optimized_layout.save("docs/floorplan_examples/layout.json")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - docs/floorplan_examples/floorplan.png")
    print("  - docs/floorplan_examples/3d_view.png")
    print("  - docs/floorplan_examples/heatmap.png")
    print("  - docs/floorplan_examples/floorplan_pil.png")
    print("  - docs/floorplan_examples/floorplan.svg")
    print("  - docs/floorplan_examples/comparison.png")
    print("  - docs/floorplan_examples/layout.json")
    print()
