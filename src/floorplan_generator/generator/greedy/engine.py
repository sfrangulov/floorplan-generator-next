"""Main greedy layout engine with restarts."""

from __future__ import annotations

import math
import random
import uuid

from floorplan_generator.core.geometry import Point, Polygon, Rectangle
from floorplan_generator.core.models import Room
from floorplan_generator.generator.greedy.candidates import (
    MIN_SHARED_WALL,
    compute_shared_wall,
    find_candidate_slots,
)
from floorplan_generator.generator.greedy.priority import build_priority_queue
from floorplan_generator.generator.greedy.scoring import score_slot
from floorplan_generator.generator.types import GreedyResult, RoomSpec, SharedWall, Slot


def create_room_at(spec: RoomSpec, position: Point) -> Room:
    """Create a Room with rectangular boundary at given position."""
    boundary = Polygon(points=[
        Point(x=position.x, y=position.y),
        Point(x=position.x + spec.width, y=position.y),
        Point(x=position.x + spec.width, y=position.y + spec.height),
        Point(x=position.x, y=position.y + spec.height),
    ])
    return Room(
        id=uuid.uuid4().hex[:8],
        room_type=spec.room_type,
        boundary=boundary,
    )


def place_hallway(
    spec: RoomSpec,
    canvas: Rectangle,
    rng: random.Random,
) -> Room:
    """Place hallway at a random canvas edge."""
    edge = rng.choice(["top", "bottom", "left", "right"])
    if edge == "top":
        x = rng.uniform(canvas.x, canvas.x + canvas.width - spec.width)
        y = canvas.y
    elif edge == "bottom":
        x = rng.uniform(canvas.x, canvas.x + canvas.width - spec.width)
        y = canvas.y + canvas.height - spec.height
    elif edge == "left":
        x = canvas.x
        y = rng.uniform(canvas.y, canvas.y + canvas.height - spec.height)
    else:  # right
        x = canvas.x + canvas.width - spec.width
        y = rng.uniform(canvas.y, canvas.y + canvas.height - spec.height)

    x = round(x / 50) * 50
    y = round(y / 50) * 50
    return create_room_at(spec, Point(x=x, y=y))


def select_slot(
    candidates: list[Slot],
    rng: random.Random,
    top_k: int = 3,
    temperature: float = 0.5,
) -> Slot:
    """Select a slot using softmax over top-K candidates."""
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)[:top_k]
    if len(ranked) == 1:
        return ranked[0]

    scores = [c.score / temperature for c in ranked]
    max_s = max(scores)
    exps = [math.exp(s - max_s) for s in scores]
    total = sum(exps)
    probs = [e / total for e in exps]
    return rng.choices(ranked, weights=probs, k=1)[0]


def _collect_shared_walls(
    room: Room,
    placed: list[Room],
    primary_target_id: str,
    primary_wall: SharedWall,
) -> list[SharedWall]:
    """Collect all shared walls between a new room and placed rooms."""
    walls = [primary_wall]
    room_bb = room.boundary.bounding_box
    for p in placed:
        if p.id == primary_target_id:
            continue
        sw = compute_shared_wall(room_bb, p.boundary.bounding_box)
        if sw and sw.length >= MIN_SHARED_WALL:
            walls.append(SharedWall(
                room_a_id=room.id,
                room_b_id=p.id,
                segment=sw,
            ))
    return walls


def greedy_place(
    queue: list[RoomSpec],
    canvas: Rectangle,
    rng: random.Random,
    temperature: float = 0.5,
) -> GreedyResult:
    """Place all rooms from queue using greedy attachment."""
    placed: list[Room] = []
    shared_walls: list[SharedWall] = []

    if not queue:
        return GreedyResult(success=True)

    # First room — hallway at canvas edge
    hallway = place_hallway(queue[0], canvas, rng)
    placed.append(hallway)

    for i, spec in enumerate(queue[1:], 1):
        candidates = find_candidate_slots(spec, placed, canvas)

        if not candidates:
            return GreedyResult(
                success=False,
                rooms=placed,
                shared_walls=shared_walls,
                failed_room=spec,
            )

        remaining = queue[i + 1:] if i + 1 < len(queue) else []

        scored = []
        for slot in candidates:
            s = score_slot(spec, slot, placed, remaining, canvas)
            scored.append(Slot(
                position=slot.position,
                target_room_id=slot.target_room_id,
                side=slot.side,
                alignment=slot.alignment,
                shared_wall=slot.shared_wall,
                score=s,
            ))

        best = select_slot(scored, rng, temperature=temperature)
        room = create_room_at(spec, best.position)

        primary_wall = SharedWall(
            room_a_id=room.id,
            room_b_id=best.target_room_id,
            segment=best.shared_wall,
        )
        new_walls = _collect_shared_walls(
            room, placed, best.target_room_id, primary_wall,
        )
        shared_walls.extend(new_walls)
        placed.append(room)

    return GreedyResult(
        success=True, rooms=placed, shared_walls=shared_walls,
    )


def greedy_layout(
    specs: list[RoomSpec],
    canvas: Rectangle,
    seed: int,
    max_restarts: int = 10,
    temperature: float = 0.5,
) -> GreedyResult | None:
    """Run greedy layout with restarts on dead ends."""
    for restart in range(max_restarts):
        current_seed = seed + restart * 1000
        rng = random.Random(current_seed)
        queue = build_priority_queue(list(specs), rng)
        result = greedy_place(queue, canvas, rng, temperature)
        if result.success:
            return result
    return None
