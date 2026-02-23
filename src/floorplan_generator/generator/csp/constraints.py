"""Hard and soft constraint definitions for CSP solver."""

from __future__ import annotations

from floorplan_generator.core.enums import FurnitureType
from floorplan_generator.core.geometry import Rectangle
from floorplan_generator.core.models import Door, FurnitureItem, Room
from floorplan_generator.generator.types import Stoyak

# Minimum clearance in front of furniture items (mm)
_FRONT_CLEARANCES: dict[FurnitureType, float] = {
    FurnitureType.TOILET_BOWL: 600.0,
    FurnitureType.SINK: 700.0,
    FurnitureType.BATHTUB: 550.0,
    FurnitureType.STOVE: 200.0,  # side wall distance
}

# Minimum clearance between toilet center and side wall (mm)
_TOILET_CENTER_FROM_WALL = 350.0

# Minimum passage width between furniture/wall (mm)
_MIN_PASSAGE = 500.0


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

    # HC03: not blocking door swing arc + entry clearance zone
    _DOOR_ENTRY_CLEARANCE = 300.0
    for door in doors:
        arc = door.swing_arc
        # Check direct overlap with swing arc
        if bb.overlaps(arc):
            return True
        # Check entry clearance: expanded arc by 300mm on all sides
        expanded = Rectangle(
            x=arc.x - _DOOR_ENTRY_CLEARANCE / 2,
            y=arc.y - _DOOR_ENTRY_CLEARANCE / 2,
            width=arc.width + _DOOR_ENTRY_CLEARANCE,
            height=arc.height + _DOOR_ENTRY_CLEARANCE,
        )
        if bb.overlaps(expanded):
            return True

    # HC04: clearance — minimum front space for key items
    if item.furniture_type in _FRONT_CLEARANCES:
        clearance = _FRONT_CLEARANCES[item.furniture_type]
        # Check that there is enough space in at least one direction
        # from the item's bounding box to the room boundary
        gaps = [
            bb.x - room_bb.x,                                 # left
            (room_bb.x + room_bb.width) - (bb.x + bb.width),  # right
            bb.y - room_bb.y,                                  # bottom
            (room_bb.y + room_bb.height) - (bb.y + bb.height), # top
        ]
        # At least one non-wall-adjacent side must have clearance
        # (the side(s) touching walls are where the item is placed against)
        non_wall_gaps = [g for g in gaps if g > 10]  # >10mm = not against wall
        if non_wall_gaps and max(non_wall_gaps) < clearance:
            return True

    # HC05: toilet center must be >= 350mm from side wall
    if item.furniture_type == FurnitureType.TOILET_BOWL:
        center_x = bb.x + bb.width / 2
        dist_left = center_x - room_bb.x
        dist_right = (room_bb.x + room_bb.width) - center_x
        if min(dist_left, dist_right) < _TOILET_CENTER_FROM_WALL:
            return True

    # HC06: minimum passage between furniture items
    for p in placed:
        pbb = p.bounding_box
        # Calculate gap between items (axis-aligned)
        dx = max(0.0, max(pbb.x - (bb.x + bb.width), bb.x - (pbb.x + pbb.width)))
        dy = max(0.0, max(pbb.y - (bb.y + bb.height), bb.y - (pbb.y + pbb.height)))
        # If items are on the same axis (overlapping range), check gap
        if dx == 0 and dy > 0 and dy < _MIN_PASSAGE:
            return True
        if dy == 0 and dx > 0 and dx < _MIN_PASSAGE:
            return True

    return False
