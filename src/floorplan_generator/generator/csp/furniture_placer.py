"""Furniture placement using backtracking with forward checking."""

from __future__ import annotations

import math
import random
import uuid

from floorplan_generator.core.dimensions import FURNITURE_SIZES
from floorplan_generator.core.enums import FurnitureType
from floorplan_generator.core.geometry import Point, Rectangle
from floorplan_generator.core.models import Door, FurnitureItem, Room
from floorplan_generator.generator.csp.constraints import violates_hard_constraints
from floorplan_generator.generator.types import Riser

# --- Orientation groups ---
# At rotation=0 the drawing's y=0 is at the item's top-left.
# Group 1: y=0 is the BACK (tank, faucet, headboard, backrest → against wall).
# Group 2: y=0 is the FRONT (control panel, door → faces room).
# Symmetric items are in neither set and allow all rotations.

_BACK_AT_Y0: frozenset[FurnitureType] = frozenset({
    FurnitureType.TOILET_BOWL, FurnitureType.SINK, FurnitureType.KITCHEN_SINK,
    FurnitureType.DOUBLE_SINK, FurnitureType.BIDET, FurnitureType.BATHTUB,
    FurnitureType.BED_SINGLE, FurnitureType.BED_DOUBLE, FurnitureType.BED_KING,
    FurnitureType.CHILD_BED,
    FurnitureType.SOFA_2, FurnitureType.SOFA_3, FurnitureType.SOFA_4,
    FurnitureType.SOFA_CORNER, FurnitureType.ARMCHAIR,
    FurnitureType.WARDROBE_SLIDING, FurnitureType.WARDROBE_SWING,
    FurnitureType.HALLWAY_WARDROBE, FurnitureType.CHILD_WARDROBE,
    FurnitureType.DRESSER, FurnitureType.NIGHTSTAND, FurnitureType.VANITY,
    FurnitureType.DESK, FurnitureType.CHILD_DESK,
    FurnitureType.TV_STAND, FurnitureType.BOOKSHELF, FurnitureType.SHELVING,
    FurnitureType.COAT_RACK, FurnitureType.SHOE_RACK, FurnitureType.BENCH,
    FurnitureType.FRIDGE, FurnitureType.FRIDGE_SIDE_BY_SIDE,
    FurnitureType.DINING_CHAIR,
})

_FRONT_AT_Y0: frozenset[FurnitureType] = frozenset({
    FurnitureType.WASHING_MACHINE, FurnitureType.DRYER,
    FurnitureType.OVEN, FurnitureType.DISHWASHER, FurnitureType.MICROWAVE,
})

# Rotation that puts y=0 against the given wall (Group 1).
_ROT_BACK: dict[str, float] = {
    "top": 0.0, "bottom": 180.0, "left": 270.0, "right": 90.0,
}
# Rotation that puts y=depth against the given wall (Group 2).
_ROT_FRONT: dict[str, float] = {
    "top": 180.0, "bottom": 0.0, "left": 90.0, "right": 270.0,
}

_ALL_ROTATIONS = [0.0, 90.0, 180.0, 270.0]

_SOFA_TYPES = frozenset({
    FurnitureType.SOFA_2, FurnitureType.SOFA_3,
    FurnitureType.SOFA_4, FurnitureType.SOFA_CORNER,
})


def _generate_wall_positions(
    item_w: float,
    item_d: float,
    room_bb: Rectangle,
    step: float = 50.0,
    ft: FurnitureType | None = None,
) -> list[tuple[Point, float]]:
    """Generate candidate positions along walls with correct orientation.

    For oriented items, only the rotation matching the wall is used.
    For symmetric items, all 4 rotations are tried.
    """
    positions: list[tuple[Point, float]] = []
    rx, ry = room_bb.x, room_bb.y
    rw, rh = room_bb.width, room_bb.height

    # Determine rotation map
    if ft in _BACK_AT_Y0:
        rot_map: dict[str, float] | None = _ROT_BACK
    elif ft in _FRONT_AT_Y0:
        rot_map = _ROT_FRONT
    else:
        rot_map = None

    walls: list[tuple[str, bool]] = [
        ("top", True),
        ("bottom", True),
        ("left", False),
        ("right", False),
    ]

    for wall_name, is_horizontal in walls:
        rotations = [rot_map[wall_name]] if rot_map else _ALL_ROTATIONS

        for rotation in rotations:
            rad = math.radians(rotation)
            cos_a = abs(math.cos(rad))
            sin_a = abs(math.sin(rad))
            eff_w = item_w * cos_a + item_d * sin_a
            eff_h = item_w * sin_a + item_d * cos_a

            if eff_w > rw + 1 or eff_h > rh + 1:
                continue

            if wall_name == "top":
                x = rx
                while x <= rx + rw - eff_w + 1:
                    positions.append((Point(x=x, y=ry), rotation))
                    x += step

            elif wall_name == "bottom":
                x = rx
                while x <= rx + rw - eff_w + 1:
                    positions.append((Point(x=x, y=ry + rh - eff_h), rotation))
                    x += step

            elif wall_name == "left":
                y = ry + step
                while y <= ry + rh - eff_h - step + 1:
                    positions.append((Point(x=rx, y=y), rotation))
                    y += step

            elif wall_name == "right":
                y = ry + step
                while y <= ry + rh - eff_h - step + 1:
                    positions.append((Point(x=rx + rw - eff_w, y=y), rotation))
                    y += step

    return positions


def place_furniture(
    room: Room,
    furniture_types: list[FurnitureType],
    doors: list[Door],
    risers: list[Riser],
    rng: random.Random,
    step: float = 50.0,
) -> list[FurnitureItem] | None:
    """Place furniture using backtracking.

    Returns list of placed items or None if placement fails.
    """
    # Sort by area (large first)
    def item_area(ft: FurnitureType) -> float:
        if ft in FURNITURE_SIZES:
            w, d, _ = FURNITURE_SIZES[ft]
            return w * d
        return 0.0

    sorted_types = sorted(furniture_types, key=item_area, reverse=True)
    room_bb = room.boundary.bounding_box

    return _backtrack(
        sorted_types, 0, [], room, room_bb, doors, risers, rng, step,
    )


def _backtrack(
    items: list[FurnitureType],
    index: int,
    placed: list[FurnitureItem],
    room: Room,
    room_bb: Rectangle,
    doors: list[Door],
    risers: list[Riser],
    rng: random.Random,
    step: float,
) -> list[FurnitureItem] | None:
    """Recursive backtracking with forward checking."""
    if index >= len(items):
        return list(placed)

    ft = items[index]
    if ft not in FURNITURE_SIZES:
        # Skip unknown furniture, continue with rest
        return _backtrack(
            items, index + 1, placed, room, room_bb, doors, risers, rng, step,
        )

    w, d, _ = FURNITURE_SIZES[ft]
    positions = _generate_wall_positions(w, d, room_bb, step, ft=ft)

    # TV placement preference: try the wall opposite the sofa first.
    if ft == FurnitureType.TV_STAND:
        sofa_rots = [
            p.rotation for p in placed if p.furniture_type in _SOFA_TYPES
        ]
        if sofa_rots:
            target = (sofa_rots[0] + 180) % 360
            preferred = [(p, r) for p, r in positions if r == target]
            other = [(p, r) for p, r in positions if r != target]
            rng.shuffle(preferred)
            rng.shuffle(other)
            positions = preferred + other
        else:
            rng.shuffle(positions)
    else:
        rng.shuffle(positions)

    for pos, rotation in positions:
        item = FurnitureItem(
            id=uuid.uuid4().hex[:8],
            furniture_type=ft,
            position=pos,
            width=w,
            depth=d,
            rotation=rotation,
        )

        if violates_hard_constraints(item, room, placed, doors, risers):
            continue

        placed.append(item)

        # Forward checking: verify next item still has valid positions
        if index + 1 < len(items):
            next_ft = items[index + 1]
            if next_ft in FURNITURE_SIZES:
                nw, nd, _ = FURNITURE_SIZES[next_ft]
                next_positions = _generate_wall_positions(
                    nw, nd, room_bb, step, ft=next_ft,
                )
                has_valid = False
                for np_, nr in next_positions:
                    ni = FurnitureItem(
                        id="check",
                        furniture_type=next_ft,
                        position=np_,
                        width=nw,
                        depth=nd,
                        rotation=nr,
                    )
                    if not violates_hard_constraints(
                        ni, room, placed, doors, risers,
                    ):
                        has_valid = True
                        break
                if not has_valid:
                    placed.pop()
                    continue

        result = _backtrack(
            items, index + 1, placed, room, room_bb, doors, risers, rng, step,
        )
        if result is not None:
            return result

        placed.pop()

    # If no valid position found for this item, skip it and continue
    # with remaining items rather than failing the entire room.
    return _backtrack(
        items, index + 1, placed, room, room_bb, doors, risers, rng, step,
    )
