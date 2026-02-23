"""Scoring function for candidate slots."""

from __future__ import annotations

from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.geometry import Rectangle
from floorplan_generator.core.models import Room
from floorplan_generator.generator.greedy.candidates import (
    MIN_SHARED_WALL,
    compute_shared_wall,
    find_candidate_slots,
)
from floorplan_generator.generator.types import RoomSpec, Slot

# Scoring weights (from algorithm doc)
W_WINDOW = 15.0
W_CENTRAL = 12.0
W_ADJ = 10.0
W_WET = 8.0
W_ZONE = 5.0
W_BLOCK = 5.0
W_COMPACT = 3.0

_DAY_ROOMS = frozenset({
    RoomType.LIVING_ROOM,
    RoomType.KITCHEN,
    RoomType.KITCHEN_DINING,
})
_NIGHT_ROOMS = frozenset({
    RoomType.BEDROOM,
    RoomType.CHILDREN,
    RoomType.CABINET,
})
_ENTRY_ROOMS = frozenset({
    RoomType.HALLWAY,
    RoomType.CORRIDOR,
    RoomType.HALL,
})


def has_external_wall(
    rect: Rectangle,
    canvas: Rectangle,
) -> bool:
    """Check if rectangle has at least one edge on canvas boundary."""
    eps = 1.0
    return (
        abs(rect.x - canvas.x) < eps
        or abs(rect.y - canvas.y) < eps
        or abs(rect.x + rect.width - canvas.x - canvas.width) < eps
        or abs(rect.y + rect.height - canvas.y - canvas.height) < eps
    )


def _count_adjacencies(
    spec: RoomSpec,
    slot: Slot,
    placed: list[Room],
) -> int:
    """Count allowed adjacencies for this slot."""
    slot_rect = Rectangle(
        x=slot.position.x, y=slot.position.y,
        width=spec.width, height=spec.height,
    )
    count = 0
    for p in placed:
        sw = compute_shared_wall(slot_rect, p.boundary.bounding_box)
        if sw and sw.length >= MIN_SHARED_WALL:
            count += 1
    return count


def _count_wet_neighbors(
    spec: RoomSpec,
    slot: Slot,
    placed: list[Room],
) -> int:
    """Count wet zone neighbors for this slot."""
    slot_rect = Rectangle(
        x=slot.position.x, y=slot.position.y,
        width=spec.width, height=spec.height,
    )
    count = 0
    for p in placed:
        if p.room_type.is_wet_zone:
            sw = compute_shared_wall(slot_rect, p.boundary.bounding_box)
            if sw and sw.length >= MIN_SHARED_WALL:
                count += 1
    return count


def _zone_score(
    spec: RoomSpec,
    slot: Slot,
    placed: list[Room],
) -> float:
    """Score for correct day/night zone placement."""
    if spec.room_type in _DAY_ROOMS:
        zone = "day"
    elif spec.room_type in _NIGHT_ROOMS:
        zone = "night"
    else:
        return 0.0

    slot_rect = Rectangle(
        x=slot.position.x, y=slot.position.y,
        width=spec.width, height=spec.height,
    )
    same = 0
    diff = 0
    for p in placed:
        sw = compute_shared_wall(slot_rect, p.boundary.bounding_box)
        if sw and sw.length >= MIN_SHARED_WALL:
            if zone == "day" and p.room_type in _DAY_ROOMS:
                same += 1
            elif zone == "night" and p.room_type in _NIGHT_ROOMS:
                same += 1
            elif (zone == "day" and p.room_type in _NIGHT_ROOMS) or (
                zone == "night" and p.room_type in _DAY_ROOMS
            ):
                diff += 1
    return float(same - diff)


def _adjacent_to_entry(
    slot: Slot,
    placed: list[Room],
    spec: RoomSpec,
) -> float:
    """1.0 if adjacent to hallway/corridor, 0.0 otherwise."""
    slot_rect = Rectangle(
        x=slot.position.x, y=slot.position.y,
        width=spec.width, height=spec.height,
    )
    for p in placed:
        if p.room_type in _ENTRY_ROOMS:
            sw = compute_shared_wall(slot_rect, p.boundary.bounding_box)
            if sw and sw.length >= MIN_SHARED_WALL:
                return 1.0
    return 0.0


def _compactness(
    slot: Slot,
    spec: RoomSpec,
    placed: list[Room],
    canvas: Rectangle,
) -> float:
    """Score for compactness (minimize total bounding box growth)."""
    if not placed:
        return 0.0

    all_bbs = [p.boundary.bounding_box for p in placed]
    min_x = min(bb.x for bb in all_bbs)
    min_y = min(bb.y for bb in all_bbs)
    max_x = max(bb.x + bb.width for bb in all_bbs)
    max_y = max(bb.y + bb.height for bb in all_bbs)
    area_before = (max_x - min_x) * (max_y - min_y)

    sx, sy = slot.position.x, slot.position.y
    new_min_x = min(min_x, sx)
    new_min_y = min(min_y, sy)
    new_max_x = max(max_x, sx + spec.width)
    new_max_y = max(max_y, sy + spec.height)
    area_after = (new_max_x - new_min_x) * (new_max_y - new_min_y)

    if canvas.area == 0:
        return 0.0
    return 1.0 - (area_after - area_before) / canvas.area


def future_blocking_penalty(
    slot: Slot,
    spec: RoomSpec,
    placed: list[Room],
    remaining: list[RoomSpec],
    canvas: Rectangle,
) -> float:
    """Penalty if placing here blocks future rooms from finding candidates."""
    if not remaining:
        return 0.0

    from floorplan_generator.generator.greedy.engine import create_room_at

    test_room = create_room_at(spec, slot.position)
    test_placed = placed + [test_room]

    check = remaining[:3]
    blocked = 0.0
    for future_spec in check:
        future_candidates = find_candidate_slots(future_spec, test_placed, canvas)
        if len(future_candidates) == 0:
            blocked += 1.0
        elif len(future_candidates) < 3:
            blocked += 0.3

    return blocked / max(len(check), 1)


def score_slot(
    spec: RoomSpec,
    slot: Slot,
    placed: list[Room],
    remaining: list[RoomSpec],
    canvas: Rectangle,
) -> float:
    """Score a candidate slot using weighted criteria."""
    s = 0.0

    # Adjacency
    s += W_ADJ * _count_adjacencies(spec, slot, placed)

    # Wet cluster
    if spec.room_type.is_wet_zone:
        s += W_WET * _count_wet_neighbors(spec, slot, placed)

    # External wall for windows
    if spec.room_type.requires_window:
        cand_rect = Rectangle(
            x=slot.position.x, y=slot.position.y,
            width=spec.width, height=spec.height,
        )
        if has_external_wall(cand_rect, canvas):
            s += W_WINDOW * 1.0
        else:
            s += W_WINDOW * (-0.5)

    # Zone separation
    s += W_ZONE * _zone_score(spec, slot, placed)

    # Compactness
    s += W_COMPACT * _compactness(slot, spec, placed, canvas)

    # Living room centrality
    if spec.room_type == RoomType.LIVING_ROOM:
        s += W_CENTRAL * _adjacent_to_entry(slot, placed, spec)

    # Look-ahead penalty
    if remaining:
        s -= W_BLOCK * future_blocking_penalty(
            slot, spec, placed, remaining, canvas,
        )

    return s
