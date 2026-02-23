"""Candidate slot generation for room placement."""

from __future__ import annotations

from floorplan_generator.core.dimensions import ADJACENCY_MATRIX
from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.geometry import Point, Rectangle, Segment
from floorplan_generator.core.models import Room
from floorplan_generator.generator.types import Alignment, RoomSpec, Side, Slot

MIN_SHARED_WALL = 700.0  # mm — smallest door width


def adjacency_forbidden(type_a: RoomType, type_b: RoomType) -> bool:
    """Check if adjacency between two room types is forbidden."""
    if type_a in ADJACENCY_MATRIX and type_b in ADJACENCY_MATRIX[type_a]:
        return ADJACENCY_MATRIX[type_a][type_b] == "-"
    if type_b in ADJACENCY_MATRIX and type_a in ADJACENCY_MATRIX[type_b]:
        return ADJACENCY_MATRIX[type_b][type_a] == "-"
    return False


def compute_shared_wall(
    rect_a: Rectangle,
    rect_b: Rectangle,
) -> Segment | None:
    """Compute shared wall segment between two touching rectangles."""
    eps = 1.0

    # Right of A = Left of B
    if abs((rect_a.x + rect_a.width) - rect_b.x) < eps:
        y_start = max(rect_a.y, rect_b.y)
        y_end = min(rect_a.y + rect_a.height, rect_b.y + rect_b.height)
        if y_end - y_start > eps:
            x = rect_a.x + rect_a.width
            return Segment(
                start=Point(x=x, y=y_start), end=Point(x=x, y=y_end),
            )

    # Left of A = Right of B
    if abs(rect_a.x - (rect_b.x + rect_b.width)) < eps:
        y_start = max(rect_a.y, rect_b.y)
        y_end = min(rect_a.y + rect_a.height, rect_b.y + rect_b.height)
        if y_end - y_start > eps:
            x = rect_a.x
            return Segment(
                start=Point(x=x, y=y_start), end=Point(x=x, y=y_end),
            )

    # Bottom of A = Top of B
    if abs((rect_a.y + rect_a.height) - rect_b.y) < eps:
        x_start = max(rect_a.x, rect_b.x)
        x_end = min(rect_a.x + rect_a.width, rect_b.x + rect_b.width)
        if x_end - x_start > eps:
            y = rect_a.y + rect_a.height
            return Segment(
                start=Point(x=x_start, y=y), end=Point(x=x_end, y=y),
            )

    # Top of A = Bottom of B
    if abs(rect_a.y - (rect_b.y + rect_b.height)) < eps:
        x_start = max(rect_a.x, rect_b.x)
        x_end = min(rect_a.x + rect_a.width, rect_b.x + rect_b.width)
        if x_end - x_start > eps:
            y = rect_a.y
            return Segment(
                start=Point(x=x_start, y=y), end=Point(x=x_end, y=y),
            )

    return None


def _attach_position(
    spec: RoomSpec,
    target_bb: Rectangle,
    side: Side,
    alignment: Alignment,
) -> Point:
    """Calculate position for attaching a room to a target on a given side."""
    if side == Side.RIGHT:
        x = target_bb.x + target_bb.width
        if alignment == Alignment.START:
            y = target_bb.y
        elif alignment == Alignment.CENTER:
            y = target_bb.y + (target_bb.height - spec.height) / 2
        else:
            y = target_bb.y + target_bb.height - spec.height
    elif side == Side.LEFT:
        x = target_bb.x - spec.width
        if alignment == Alignment.START:
            y = target_bb.y
        elif alignment == Alignment.CENTER:
            y = target_bb.y + (target_bb.height - spec.height) / 2
        else:
            y = target_bb.y + target_bb.height - spec.height
    elif side == Side.BOTTOM:
        y = target_bb.y + target_bb.height
        if alignment == Alignment.START:
            x = target_bb.x
        elif alignment == Alignment.CENTER:
            x = target_bb.x + (target_bb.width - spec.width) / 2
        else:
            x = target_bb.x + target_bb.width - spec.width
    else:  # TOP
        y = target_bb.y - spec.height
        if alignment == Alignment.START:
            x = target_bb.x
        elif alignment == Alignment.CENTER:
            x = target_bb.x + (target_bb.width - spec.width) / 2
        else:
            x = target_bb.x + target_bb.width - spec.width

    return Point(x=x, y=y)


def find_candidate_slots(
    spec: RoomSpec,
    placed: list[Room],
    canvas: Rectangle,
) -> list[Slot]:
    """Find all valid candidate positions for placing a room."""
    candidates = []

    for target in placed:
        if adjacency_forbidden(spec.room_type, target.room_type):
            continue

        target_bb = target.boundary.bounding_box

        for side in Side:
            for alignment in Alignment:
                pos = _attach_position(spec, target_bb, side, alignment)
                cand_rect = Rectangle(
                    x=pos.x, y=pos.y,
                    width=spec.width, height=spec.height,
                )

                # Inside canvas
                if (
                    cand_rect.x < canvas.x - 1
                    or cand_rect.y < canvas.y - 1
                    or cand_rect.x + cand_rect.width > canvas.x + canvas.width + 1
                    or cand_rect.y + cand_rect.height > canvas.y + canvas.height + 1
                ):
                    continue

                # No overlap with placed rooms
                if any(cand_rect.overlaps(p.boundary.bounding_box) for p in placed):
                    continue

                # Shared wall length >= MIN_SHARED_WALL
                sw = compute_shared_wall(cand_rect, target_bb)
                if sw is None or sw.length < MIN_SHARED_WALL:
                    continue

                candidates.append(Slot(
                    position=pos,
                    target_room_id=target.id,
                    side=side,
                    alignment=alignment,
                    shared_wall=sw,
                ))

    return candidates
