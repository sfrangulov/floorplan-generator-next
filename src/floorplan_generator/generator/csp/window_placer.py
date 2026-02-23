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
    """Get wall segments that lie on or near the canvas boundary.

    A wall is considered external if it is parallel to and within ``eps``
    of a canvas edge.  For vertical walls we compare the constant x
    coordinate; for horizontal walls we compare the constant y
    coordinate.  This avoids misclassifying interior walls that happen
    to have their midpoint near an edge.

    Uses a 250mm tolerance to account for greedy layout grid snapping,
    which can leave gaps between room walls and the canvas edge.
    """
    segs = wall_segments(room)
    result = []
    eps = 250.0
    for seg in segs:
        if seg.length < 600:
            continue
        is_vertical = abs(seg.start.x - seg.end.x) < 1
        is_horizontal = abs(seg.start.y - seg.end.y) < 1
        if is_vertical:
            x = seg.start.x
            if abs(x - canvas.x) < eps or abs(x - (canvas.x + canvas.width)) < eps:
                result.append(seg)
        elif is_horizontal:
            y = seg.start.y
            if abs(y - canvas.y) < eps or abs(y - (canvas.y + canvas.height)) < eps:
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
            # Fallback: use the longest wall for rooms that must have a window.
            # This represents a light-well or courtyard-facing window.
            all_walls = [
                s for s in wall_segments(room) if s.length >= 600
            ]
            if all_walls:
                ext_walls = [max(all_walls, key=lambda s: s.length)]
            else:
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
                    "west"
                    if abs(wall.start.x - canvas.x)
                    < abs(wall.start.x - (canvas.x + canvas.width))
                    else "east"
                )
            else:
                mid_x = (wall.start.x + wall.end.x) / 2
                pos = Point(x=mid_x - width / 2, y=wall.start.y)
                wall_side = (
                    "north"
                    if abs(wall.start.y - canvas.y)
                    < abs(wall.start.y - (canvas.y + canvas.height))
                    else "south"
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
