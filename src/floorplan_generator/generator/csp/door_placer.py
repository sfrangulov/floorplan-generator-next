"""Door placement on shared walls."""

from __future__ import annotations

import random
import uuid

from floorplan_generator.core.dimensions import DOOR_SIZES
from floorplan_generator.core.enums import DoorType, RoomType, SwingDirection
from floorplan_generator.core.geometry import Point, Rectangle
from floorplan_generator.core.models import Door, Room
from floorplan_generator.generator.types import SharedWall

_BATHROOM_TYPES = frozenset({
    RoomType.BATHROOM,
    RoomType.TOILET,
    RoomType.COMBINED_BATHROOM,
})

# Forbidden direct connections
_FORBIDDEN_PAIRS = frozenset({
    (RoomType.KITCHEN, RoomType.TOILET),
    (RoomType.TOILET, RoomType.KITCHEN),
})


def _determine_door_type(type_a: RoomType, type_b: RoomType) -> DoorType:
    """Determine door type based on connected rooms."""
    if type_a == RoomType.HALLWAY or type_b == RoomType.HALLWAY:
        return DoorType.ENTRANCE
    if type_a in _BATHROOM_TYPES:
        return DoorType.BATHROOM
    if type_b in _BATHROOM_TYPES:
        return DoorType.BATHROOM
    if RoomType.KITCHEN in (type_a, type_b):
        return DoorType.KITCHEN
    return DoorType.INTERIOR


def _door_swing(type_from: RoomType, type_to: RoomType) -> SwingDirection:
    """Determine swing direction. Bathroom doors swing outward."""
    if type_to in _BATHROOM_TYPES:
        return SwingDirection.OUTWARD
    return SwingDirection.INWARD


def place_doors(
    rooms: list[Room],
    shared_walls: list[SharedWall],
    rng: random.Random,
) -> list[dict]:
    """Place doors on shared walls.

    Returns list of {"door": Door, "shared_wall": Segment, "room_a_id", "room_b_id"}.
    """
    room_map = {r.id: r for r in rooms}
    placed_doors: list[dict] = []
    placed_arcs: list[Rectangle] = []

    for sw in shared_walls:
        room_a = room_map.get(sw.room_a_id)
        room_b = room_map.get(sw.room_b_id)
        if room_a is None or room_b is None:
            continue

        # P15: no kitchen-toilet
        if (room_a.room_type, room_b.room_type) in _FORBIDDEN_PAIRS:
            continue

        door_type = _determine_door_type(room_a.room_type, room_b.room_type)
        door_width = DOOR_SIZES[door_type][0]  # Use min width
        swing = _door_swing(room_a.room_type, room_b.room_type)

        wall = sw.segment
        wall_len = wall.length

        if wall_len < door_width + 200:
            continue  # Wall too short for door + gaps

        # Determine if wall is vertical or horizontal
        is_vertical = abs(wall.start.x - wall.end.x) < 1

        wall_start = (
            min(wall.start.y, wall.end.y)
            if is_vertical
            else min(wall.start.x, wall.end.x)
        )
        wall_end = (
            max(wall.start.y, wall.end.y)
            if is_vertical
            else max(wall.start.x, wall.end.x)
        )

        # Try positions with 50mm step, 100mm gap from wall ends
        step = 50.0
        min_pos = wall_start + 100
        max_pos = wall_end - door_width - 100

        if min_pos > max_pos:
            continue

        # Randomize starting position for diversity
        positions: list[float] = []
        pos = min_pos
        while pos <= max_pos:
            positions.append(pos)
            pos += step
        rng.shuffle(positions)

        for pos in positions:
            if is_vertical:
                door_pos = Point(x=wall.start.x, y=pos)
                arc = Rectangle(
                    x=(
                        door_pos.x - door_width
                        if swing == SwingDirection.OUTWARD
                        else door_pos.x
                    ),
                    y=door_pos.y,
                    width=door_width,
                    height=door_width,
                )
            else:
                door_pos = Point(x=pos, y=wall.start.y)
                arc = Rectangle(
                    x=door_pos.x,
                    y=(
                        door_pos.y - door_width
                        if swing == SwingDirection.OUTWARD
                        else door_pos.y
                    ),
                    width=door_width,
                    height=door_width,
                )

            # P22: no swing arc collision
            if any(arc.overlaps(a) for a in placed_arcs):
                continue

            door = Door(
                id=uuid.uuid4().hex[:8],
                position=door_pos,
                width=door_width,
                door_type=door_type,
                swing=swing,
                room_from=sw.room_a_id,
                room_to=sw.room_b_id,
            )

            placed_doors.append({
                "door": door,
                "shared_wall": wall,
                "room_a_id": sw.room_a_id,
                "room_b_id": sw.room_b_id,
            })
            placed_arcs.append(arc)
            break

    return placed_doors
