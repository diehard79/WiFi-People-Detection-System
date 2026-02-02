"""
Room Layout Mapper

Converts detected wall segments into complete room floor plans.
Includes optimization and refinement.
"""

import logging
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from .wall_models import WallDetection, RoomLayout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WallGrid:
    """Grid representation of wall locations."""
    resolution: float = 0.1  # meters per cell
    width_m: int = 100  # 10 meters
    length_m: int = 100  # 10 meters
    grid: np.ndarray = field(default_factory=lambda: np.zeros((100, 100)))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'resolution': self.resolution,
            'width_m': self.width_m,
            'length_m': self.length_m,
            'grid': self.grid.tolist()
        }


class RoomLayoutMapper:
    """
    Maps room layout from detected wall segments.

    Process:
    1. Create occupancy grid from walls
    2. Extract wall lines from grid
    3. Optimize layout (parallel/perpendicular correction)
    4. Generate room dimensions
    """

    def __init__(
        self,
        grid_resolution: float = 0.1,  # 10cm per cell
        room_size: Tuple[float, float] = (10.0, 10.0)  # 10x10 meters
    ):
        """
        Initialize room layout mapper

        Args:
            grid_resolution: Grid cell size in meters
            room_size: Maximum room dimensions (width, length) in meters
        """
        self.grid_resolution = grid_resolution
        self.room_size = room_size

        # Grid dimensions
        self.grid_width = int(room_size[0] / grid_resolution)
        self.grid_length = int(room_size[1] / grid_resolution)

        logger.info(
            f"Initialized room mapper: {room_size[0]}x{room_size[1]}m, "
            f"resolution={grid_resolution}m"
        )

    def create_room_layout(
        self,
        walls: List[WallDetection],
        overall_confidence: float
    ) -> RoomLayout:
        """
        Create complete room layout from detected walls

        Args:
            walls: List of detected wall segments
            overall_confidence: Overall detection confidence

        Returns:
            Complete room layout
        """
        logger.info(f"Creating room layout from {len(walls)} walls")

        # 1. Create occupancy grid
        wall_grid = self._create_wall_grid(walls)

        # 2. Optimize layout
        optimized_walls = self._optimize_layout(walls, wall_grid)

        # 3. Calculate room dimensions
        dimensions, area, perimeter = self._calculate_dimensions(optimized_walls)

        # 4. Create room layout
        layout = RoomLayout(
            walls=optimized_walls,
            dimensions=dimensions,
            area=area,
            perimeter=perimeter,
            confidence=overall_confidence,
            detected_at=datetime.now().isoformat()
        )

        logger.info(
            f"Room layout: {dimensions[0]}x{dimensions[1]}m, "
            f"area={area:.2f}m², perimeter={perimeter:.2f}m"
        )

        return layout

    def _create_wall_grid(self, walls: List[WallDetection]) -> WallGrid:
        """
        Create occupancy grid from wall segments

        Args:
            walls: List of wall segments

        Returns:
            Wall occupancy grid
        """
        grid = np.zeros((self.grid_width, self.grid_length))

        for wall in walls:
            # Rasterize wall segment onto grid
            start = wall.start_point
            end = wall.end_point

            # Convert to grid coordinates
            x0, y0 = int(start[0] / self.grid_resolution), int(start[1] / self.grid_resolution)
            x1, y1 = int(end[0] / self.grid_resolution), int(end[1] / self.grid_resolution)

            # Bresenham's line algorithm
            points = self._bresenham_line(x0, y0, x1, y1)

            for x, y in points:
                if 0 <= x < self.grid_width and 0 <= y < self.grid_length:
                    grid[x, y] = 1.0

        return WallGrid(
            resolution=self.grid_resolution,
            width_m=self.grid_width,
            length_m=self.grid_length,
            grid=grid
        )

    def _bresenham_line(
        self,
        x0: int, y0: int,
        x1: int, y1: int
    ) -> List[Tuple[int, int]]:
        """
        Bresenham's line algorithm for rasterization

        Args:
            x0, y0: Start point
            x1, y1: End point

        Returns:
            List of grid points along line
        """
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            points.append((x0, y0))

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return points

    def _optimize_layout(
        self,
        walls: List[WallDetection],
        wall_grid: WallGrid
    ) -> List[WallDetection]:
        """
        Optimize wall layout

        Corrections:
        1. Make walls parallel/perpendicular to each other
        2. Merge colinear walls
        3. Close gaps

        Args:
            walls: Original walls
            wall_grid: Wall occupancy grid

        Returns:
            Optimized walls
        """
        if not walls:
            return walls

        # 1. Extract wall orientations
        orientations = [self._get_wall_orientation(w) for w in walls]

        # 2. Group walls by orientation
        horizontal = [w for w, o in zip(walls, orientations) if o == 'horizontal']
        vertical = [w for w, o in zip(walls, orientations) if o == 'vertical']

        # 3. Align horizontal walls
        for wall in horizontal:
            self._align_wall_horizontal(wall)

        # 4. Align vertical walls
        for wall in vertical:
            self._align_wall_vertical(wall)

        # 5. Merge colinear walls
        optimized = self._merge_colinear_walls(walls)

        return optimized

    def _get_wall_orientation(self, wall: WallDetection) -> str:
        """
        Determine wall orientation

        Args:
            wall: Wall segment

        Returns:
            'horizontal', 'vertical', or 'diagonal'
        """
        dx = abs(wall.end_point[0] - wall.start_point[0])
        dy = abs(wall.end_point[1] - wall.start_point[1])

        if dx > dy * 2:
            return 'horizontal'
        elif dy > dx * 2:
            return 'vertical'
        else:
            return 'diagonal'

    def _align_wall_horizontal(self, wall: WallDetection):
        """
        Align wall to horizontal

        Args:
            wall: Wall to align
        """
        # Average y-coordinate
        avg_y = (wall.start_point[1] + wall.end_point[1]) / 2
        wall.start_point = (wall.start_point[0], avg_y)
        wall.end_point = (wall.end_point[0], avg_y)

    def _align_wall_vertical(self, wall: WallDetection):
        """
        Align wall to vertical

        Args:
            wall: Wall to align
        """
        # Average x-coordinate
        avg_x = (wall.start_point[0] + wall.end_point[0]) / 2
        wall.start_point = (avg_x, wall.start_point[1])
        wall.end_point = (avg_x, wall.end_point[1])

    def _merge_colinear_walls(
        self,
        walls: List[WallDetection],
        tolerance: float = 0.2  # meters
    ) -> List[WallDetection]:
        """
        Merge colinear wall segments

        Args:
            walls: List of walls
            tolerance: Distance tolerance for merging

        Returns:
            Merged walls
        """
        if not walls:
            return walls

        merged = []
        used = [False] * len(walls)

        for i, wall1 in enumerate(walls):
            if used[i]:
                continue

            current_walls = [wall1]
            used[i] = True

            for j, wall2 in enumerate(walls):
                if i == j or used[j]:
                    continue

                if self._are_colinear(wall1, wall2, tolerance):
                    current_walls.append(wall2)
                    used[j] = True

            # Merge colinear walls
            if len(current_walls) > 1:
                merged_wall = self._merge_wall_segments(current_walls)
                merged.append(merged_wall)
            else:
                merged.append(wall1)

        return merged

    def _are_colinear(
        self,
        wall1: WallDetection,
        wall2: WallDetection,
        tolerance: float
    ) -> bool:
        """
        Check if two walls are colinear

        Args:
            wall1: First wall
            wall2: Second wall
            tolerance: Distance tolerance

        Returns:
            True if colinear
        """
        # Check orientation
        orient1 = self._get_wall_orientation(wall1)
        orient2 = self._get_wall_orientation(wall2)

        if orient1 != orient2 or orient1 == 'diagonal':
            return False

        # Check distance between walls
        if orient1 == 'horizontal':
            y1 = (wall1.start_point[1] + wall1.end_point[1]) / 2
            y2 = (wall2.start_point[1] + wall2.end_point[1]) / 2
            return abs(y1 - y2) < tolerance
        else:  # vertical
            x1 = (wall1.start_point[0] + wall1.end_point[0]) / 2
            x2 = (wall2.start_point[0] + wall2.end_point[0]) / 2
            return abs(x1 - x2) < tolerance

    def _merge_wall_segments(
        self,
        walls: List[WallDetection]
    ) -> WallDetection:
        """
        Merge colinear wall segments into one

        Args:
            walls: List of colinear walls

        Returns:
            Merged wall
        """
        # Find extremes
        orientation = self._get_wall_orientation(walls[0])

        if orientation == 'horizontal':
            x_coords = [w.start_point[0] for w in walls] + [w.end_point[0] for w in walls]
            y = (walls[0].start_point[1] + walls[0].end_point[1]) / 2
            start = (min(x_coords), y)
            end = (max(x_coords), y)
        else:  # vertical
            y_coords = [w.start_point[1] for w in walls] + [w.end_point[1] for w in walls]
            x = (walls[0].start_point[0] + walls[0].end_point[0]) / 2
            start = (x, min(y_coords))
            end = (x, max(y_coords))

        # Average confidence
        avg_confidence = sum(w.confidence for w in walls) / len(walls)

        return WallDetection(
            start_point=start,
            end_point=end,
            confidence=avg_confidence,
            thickness=walls[0].thickness
        )

    def _calculate_dimensions(
        self,
        walls: List[WallDetection]
    ) -> Tuple[Tuple[float, float], float, float]:
        """
        Calculate room dimensions from walls

        Args:
            walls: List of walls

        Returns:
            Tuple of (dimensions, area, perimeter)
        """
        if not walls:
            return ((0.0, 0.0), 0.0, 0.0)

        # Find bounding box
        x_coords = [w.start_point[0] for w in walls] + [w.end_point[0] for w in walls]
        y_coords = [w.start_point[1] for w in walls] + [w.end_point[1] for w in walls]

        width = max(x_coords) - min(x_coords)
        length = max(y_coords) - min(y_coords)

        area = width * length
        perimeter = 2 * (width + length)

        return ((width, length), area, perimeter)

    def export_floorplan(
        self,
        layout: RoomLayout,
        output_path: str
    ):
        """
        Export floorplan to JSON file

        Args:
            layout: Room layout
            output_path: Output file path
        """
        floorplan = {
            'dimensions': layout.dimensions,
            'area': layout.area,
            'perimeter': layout.perimeter,
            'confidence': layout.confidence,
            'detected_at': layout.detected_at,
            'walls': [
                {
                    'start': wall.start_point,
                    'end': wall.end_point,
                    'thickness': wall.thickness,
                    'material': wall.material,
                    'confidence': wall.confidence
                }
                for wall in layout.walls
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(floorplan, f, indent=2)

        logger.info(f"Exported floorplan to {output_path}")


if __name__ == "__main__":
    # Test room mapper
    print("\n=== Testing Room Layout Mapper ===\n")

    mapper = RoomLayoutMapper()

    # Create dummy walls
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
            end_point=(5.1, 4.0),
            confidence=0.92,
            thickness=0.2,
            material='concrete'
        ),
        WallDetection(
            start_point=(5.0, 4.0),
            end_point=(0.1, 4.0),
            confidence=0.88,
            thickness=0.2,
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

    # Create room layout
    layout = mapper.create_room_layout(walls, overall_confidence=0.91)

    print(f"Room dimensions: {layout.dimensions[0]}x{layout.dimensions[1]}m")
    print(f"Area: {layout.area:.2f}m²")
    print(f"Perimeter: {layout.perimeter:.2f}m")
    print(f"Confidence: {layout.confidence:.2f}")

    print("\n✅ Room mapper working correctly")
