"""Hard and soft constraint definitions for CSP solver."""

from __future__ import annotations

from floorplan_generator.core.models import Door, FurnitureItem, Room
from floorplan_generator.generator.types import Stoyak


def violates_hard_constraints(
    item: FurnitureItem,
    room: Room,
    placed: list[FurnitureItem],
    doors: list[Door],
    stoyaks: list[Stoyak] | None = None,
) -> bool:
    """Check if placing this item violates any hard constraint."""
    bb = item.bounding_box
    room_bb = room.boundary.bounding_box

    # HC02: inside room
    if (
        bb.x < room_bb.x - 1
        or bb.y < room_bb.y - 1
        or bb.x + bb.width > room_bb.x + room_bb.width + 1
        or bb.y + bb.height > room_bb.y + room_bb.height + 1
    ):
        return True

    # HC01: no overlap with placed furniture
    for p in placed:
        if bb.overlaps(p.bounding_box):
            return True

    # HC03: not blocking door swing arc
    for door in doors:
        if bb.overlaps(door.swing_arc):
            return True

    return False
