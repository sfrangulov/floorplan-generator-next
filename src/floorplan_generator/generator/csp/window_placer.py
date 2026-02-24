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


def _compute_footprint(rooms: list[Room]) -> Rectangle:
    """Compute the building footprint as bounding box of all rooms."""
    all_bbs = [r.boundary.bounding_box for r in rooms]
    min_x = min(bb.x for bb in all_bbs)
    min_y = min(bb.y for bb in all_bbs)
    max_x = max(bb.x + bb.width for bb in all_bbs)
    max_y = max(bb.y + bb.height for bb in all_bbs)
    return Rectangle(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


def _external_wall_segments(
    room: Room,
    footprint: Rectangle,
) -> list[Segment]:
    """Get wall segments that lie on or near the building perimeter.

    A wall is considered external if it is parallel to and within ``eps``
    of a footprint edge.  For vertical walls we compare the constant x
    coordinate; for horizontal walls we compare the constant y
    coordinate.

    Uses a 250mm tolerance to account for greedy layout grid snapping.
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
            if (
                abs(x - footprint.x) < eps
                or abs(x - (footprint.x + footprint.width)) < eps
            ):
                result.append(seg)
        elif is_horizontal:
            y = seg.start.y
            if (
                abs(y - footprint.y) < eps
                or abs(y - (footprint.y + footprint.height)) < eps
            ):
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
    # Use actual building footprint, not the padded canvas
    footprint = _compute_footprint(rooms)

    results: list[dict] = []

    for room in rooms:
        if not room.room_type.requires_window:
            continue

        ext_walls = _external_wall_segments(room, footprint)
        if not ext_walls:
            # Room has no external walls — cannot have windows.
            # Validation rules will catch this (P12/P13).
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
                    if abs(wall.start.x - footprint.x)
                    < abs(wall.start.x - (footprint.x + footprint.width))
                    else "east"
                )
            else:
                mid_x = (wall.start.x + wall.end.x) / 2
                pos = Point(x=mid_x - width / 2, y=wall.start.y)
                wall_side = (
                    "north"
                    if abs(wall.start.y - footprint.y)
                    < abs(wall.start.y - (footprint.y + footprint.height))
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
