"""Window placement on external walls."""

from __future__ import annotations

import random
import uuid

from floorplan_generator.core.dimensions import WINDOW_RATIOS
from floorplan_generator.core.geometry import Point, Rectangle, Segment
from floorplan_generator.core.models import Room, Window
from floorplan_generator.rules.geometry_helpers import wall_segments

# Standard window sizes (width in mm)
_WINDOW_SIZES = [600, 700, 900, 1200, 1500, 1800]
_WINDOW_HEIGHT = 1500.0


def _external_wall_segments(
    room: Room,
    canvas: Rectangle,
) -> list[Segment]:
    """Get wall segments that lie on the canvas boundary."""
    segs = wall_segments(room)
    result = []
    eps = 2.0
    for seg in segs:
        mid = seg.midpoint
        on_edge = (
            abs(mid.x - canvas.x) < eps
            or abs(mid.y - canvas.y) < eps
            or abs(mid.x - (canvas.x + canvas.width)) < eps
            or abs(mid.y - (canvas.y + canvas.height)) < eps
        )
        if on_edge and seg.length >= 600:
            result.append(seg)
    return result


def place_windows(
    rooms: list[Room],
    canvas: Rectangle,
    rng: random.Random,
) -> list[dict]:
    """Place windows on external walls for rooms that require them.

    Returns list of {"room": Room, "window": Window}.
    """
    results: list[dict] = []

    for room in rooms:
        if not room.room_type.requires_window:
            continue

        ext_walls = _external_wall_segments(room, canvas)
        if not ext_walls:
            continue

        needed_area_m2 = room.area_m2 * WINDOW_RATIOS["min_ratio"]
        placed_area_m2 = 0.0

        for wall in ext_walls:
            if placed_area_m2 >= needed_area_m2:
                break

            remaining_need = needed_area_m2 - placed_area_m2
            # Choose window size
            width = _WINDOW_SIZES[0]
            for w in sorted(_WINDOW_SIZES, reverse=True):
                if w <= wall.length - 500:  # 250mm gap each side
                    win_area = (w * _WINDOW_HEIGHT) / 1_000_000
                    if win_area >= remaining_need * 0.5:
                        width = w
                        break

            if width > wall.length - 150:
                continue

            # Center window on wall
            is_vertical = abs(wall.start.x - wall.end.x) < 1
            if is_vertical:
                mid_y = (wall.start.y + wall.end.y) / 2
                pos = Point(x=wall.start.x, y=mid_y - _WINDOW_HEIGHT / 2)
                wall_side = (
                    "west" if abs(wall.start.x - canvas.x) < 2 else "east"
                )
            else:
                mid_x = (wall.start.x + wall.end.x) / 2
                pos = Point(x=mid_x - width / 2, y=wall.start.y)
                wall_side = (
                    "north" if abs(wall.start.y - canvas.y) < 2 else "south"
                )

            window = Window(
                id=uuid.uuid4().hex[:8],
                position=pos,
                width=float(width),
                height=_WINDOW_HEIGHT,
                wall_side=wall_side,
            )
            results.append({"room": room, "window": window})
            placed_area_m2 += window.area_m2

    return results
