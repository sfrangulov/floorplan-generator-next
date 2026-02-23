"""Riser placement in wet zones."""

from __future__ import annotations

import random
import uuid

from floorplan_generator.core.geometry import Point, Rectangle
from floorplan_generator.core.models import Room
from floorplan_generator.generator.types import Riser


def place_risers(
    rooms: list[Room],
    canvas: Rectangle,
    rng: random.Random,
) -> list[Riser]:
    """Place risers at corners of wet zone rooms.

    Prefers a shared corner between multiple wet zones.
    """
    wet_rooms = [r for r in rooms if r.room_type.is_wet_zone]
    if not wet_rooms:
        return []

    # Collect all corners of wet zone rooms
    corner_counts: dict[tuple[float, float], int] = {}
    for room in wet_rooms:
        bb = room.boundary.bounding_box
        corners = [
            (bb.x, bb.y),
            (bb.x + bb.width, bb.y),
            (bb.x + bb.width, bb.y + bb.height),
            (bb.x, bb.y + bb.height),
        ]
        for c in corners:
            key = (round(c[0]), round(c[1]))
            corner_counts[key] = corner_counts.get(key, 0) + 1

    # Sort by count (most shared first), then randomize ties
    sorted_corners = sorted(
        corner_counts.items(),
        key=lambda x: (-x[1], rng.random()),
    )

    if not sorted_corners:
        return []

    # Place riser at best corner
    best = sorted_corners[0][0]
    riser = Riser(
        id=uuid.uuid4().hex[:8],
        position=Point(x=best[0], y=best[1]),
    )
    return [riser]
