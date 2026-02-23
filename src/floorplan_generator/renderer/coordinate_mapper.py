"""Coordinate mapping from mm (domain) to SVG units."""

from __future__ import annotations

from floorplan_generator.core.geometry import Point
from floorplan_generator.core.models import Room


class CoordinateMapper:
    """Maps millimeter coordinates to SVG canvas coordinates.

    Computes scale and offset to fit all rooms within the canvas
    with padding, preserving aspect ratio.
    """

    def __init__(
        self,
        rooms: list[Room],
        canvas_width: int = 2000,
        canvas_height: int = 2000,
        padding: int = 100,
    ) -> None:
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = padding

        # Compute bounding box of all rooms in mm
        all_xs: list[float] = []
        all_ys: list[float] = []
        for room in rooms:
            for pt in room.boundary.points:
                all_xs.append(pt.x)
                all_ys.append(pt.y)

        if not all_xs:
            self.scale = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0
            self.mm_min_x = 0.0
            self.mm_min_y = 0.0
            return

        self.mm_min_x = min(all_xs)
        self.mm_min_y = min(all_ys)
        mm_max_x = max(all_xs)
        mm_max_y = max(all_ys)

        mm_width = mm_max_x - self.mm_min_x
        mm_height = mm_max_y - self.mm_min_y

        if mm_width == 0 or mm_height == 0:
            self.scale = 1.0
            self.offset_x = float(padding)
            self.offset_y = float(padding)
            return

        available_w = canvas_width - 2 * padding
        available_h = canvas_height - 2 * padding

        scale_x = available_w / mm_width
        scale_y = available_h / mm_height
        self.scale = min(scale_x, scale_y)

        # Center on canvas
        scaled_w = mm_width * self.scale
        scaled_h = mm_height * self.scale
        self.offset_x = (canvas_width - scaled_w) / 2
        self.offset_y = (canvas_height - scaled_h) / 2

    def to_svg(self, point: Point) -> tuple[float, float]:
        """Convert mm point to SVG coordinates."""
        x = (point.x - self.mm_min_x) * self.scale + self.offset_x
        y = (point.y - self.mm_min_y) * self.scale + self.offset_y
        return (round(x, 1), round(y, 1))

    def scale_length(self, mm_length: float) -> float:
        """Convert mm length to SVG length (no offset)."""
        return round(mm_length * self.scale, 1)
