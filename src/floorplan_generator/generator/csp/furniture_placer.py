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
from floorplan_generator.generator.types import Stoyak


def _generate_wall_positions(
    item_w: float,
    item_d: float,
    room_bb: Rectangle,
    step: float = 50.0,
) -> list[tuple[Point, float]]:
    """Generate candidate positions along walls (wall-snap heuristic)."""
    positions: list[tuple[Point, float]] = []
    rx, ry = room_bb.x, room_bb.y
    rw, rh = room_bb.width, room_bb.height

    for rotation in [0.0, 90.0, 180.0, 270.0]:
        rad = math.radians(rotation)
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))
        eff_w = item_w * cos_a + item_d * sin_a
        eff_h = item_w * sin_a + item_d * cos_a

        if eff_w > rw + 1 or eff_h > rh + 1:
            continue

        # Against bottom wall (y = ry)
        x = rx
        while x <= rx + rw - eff_w + 1:
            positions.append((Point(x=x, y=ry), rotation))
            x += step

        # Against top wall (y = ry + rh - eff_h)
        x = rx
        while x <= rx + rw - eff_w + 1:
            positions.append((Point(x=x, y=ry + rh - eff_h), rotation))
            x += step

        # Against left wall (x = rx), skip corners already covered
        y = ry + step
        while y <= ry + rh - eff_h - step + 1:
            positions.append((Point(x=rx, y=y), rotation))
            y += step

        # Against right wall (x = rx + rw - eff_w)
        y = ry + step
        while y <= ry + rh - eff_h - step + 1:
            positions.append((Point(x=rx + rw - eff_w, y=y), rotation))
            y += step

    return positions


def place_furniture(
    room: Room,
    furniture_types: list[FurnitureType],
    doors: list[Door],
    stoyaks: list[Stoyak],
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
        sorted_types, 0, [], room, room_bb, doors, stoyaks, rng, step,
    )


def _backtrack(
    items: list[FurnitureType],
    index: int,
    placed: list[FurnitureItem],
    room: Room,
    room_bb: Rectangle,
    doors: list[Door],
    stoyaks: list[Stoyak],
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
            items, index + 1, placed, room, room_bb, doors, stoyaks, rng, step,
        )

    w, d, _ = FURNITURE_SIZES[ft]
    positions = _generate_wall_positions(w, d, room_bb, step)
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

        if violates_hard_constraints(item, room, placed, doors, stoyaks):
            continue

        placed.append(item)

        # Forward checking: verify next item still has valid positions
        if index + 1 < len(items):
            next_ft = items[index + 1]
            if next_ft in FURNITURE_SIZES:
                nw, nd, _ = FURNITURE_SIZES[next_ft]
                next_positions = _generate_wall_positions(nw, nd, room_bb, step)
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
                        ni, room, placed, doors, stoyaks,
                    ):
                        has_valid = True
                        break
                if not has_valid:
                    placed.pop()
                    continue

        result = _backtrack(
            items, index + 1, placed, room, room_bb, doors, stoyaks, rng, step,
        )
        if result is not None:
            return result

        placed.pop()

    # If no valid position found for this item, skip it and continue
    # with remaining items rather than failing the entire room.
    return _backtrack(
        items, index + 1, placed, room, room_bb, doors, stoyaks, rng, step,
    )
