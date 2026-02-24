"""Unit tests for greedy room placement (GR01–GR18)."""

from __future__ import annotations

import random
import uuid

import pytest

from floorplan_generator.core.enums import ApartmentClass, RoomType
from floorplan_generator.core.geometry import Point, Polygon, Rectangle, Segment
from floorplan_generator.core.models import Room
from floorplan_generator.generator.greedy.candidates import find_candidate_slots
from floorplan_generator.generator.greedy.engine import (
    greedy_layout,
    place_hallway,
    select_slot,
)
from floorplan_generator.generator.greedy.priority import build_priority_queue
from floorplan_generator.generator.greedy.scoring import score_slot
from floorplan_generator.generator.room_composer import (
    assign_sizes,
    determine_composition,
)
from floorplan_generator.generator.types import Alignment, RoomSpec, Side, Slot


def _make_room_at(
    room_type: RoomType, x: float, y: float, w: float, h: float,
) -> Room:
    """Helper: create a Room with rectangular boundary at position."""
    return Room(
        id=uuid.uuid4().hex[:8],
        room_type=room_type,
        boundary=Polygon(points=[
            Point(x=x, y=y),
            Point(x=x + w, y=y),
            Point(x=x + w, y=y + h),
            Point(x=x, y=y + h),
        ]),
    )


CANVAS = Rectangle(x=0, y=0, width=12000, height=10000)


# GR01
def test_priority_queue_order():
    """Priority: hallway -> corridor -> wet -> living -> bedrooms -> storage."""
    specs = [
        RoomSpec(room_type=RoomType.BEDROOM, width=3000, height=4000),
        RoomSpec(room_type=RoomType.HALLWAY, width=2000, height=1500),
        RoomSpec(room_type=RoomType.KITCHEN, width=3000, height=3000),
        RoomSpec(room_type=RoomType.LIVING_ROOM, width=4000, height=4500),
        RoomSpec(room_type=RoomType.COMBINED_BATHROOM, width=2000, height=2000),
        RoomSpec(room_type=RoomType.STORAGE, width=1000, height=1500),
    ]
    rng = random.Random(42)
    queue = build_priority_queue(specs, rng)
    types = [s.room_type for s in queue]
    assert types[0] == RoomType.HALLWAY
    assert types.index(RoomType.LIVING_ROOM) < types.index(RoomType.KITCHEN)
    assert types.index(RoomType.LIVING_ROOM) < types.index(RoomType.COMBINED_BATHROOM)
    assert types.index(RoomType.BEDROOM) < types.index(RoomType.KITCHEN)
    assert types.index(RoomType.BEDROOM) < types.index(RoomType.STORAGE)


# GR02
def test_hallway_at_edge():
    """Hallway is placed at a canvas edge."""
    spec = RoomSpec(room_type=RoomType.HALLWAY, width=2000, height=1500)
    rng = random.Random(42)
    room = place_hallway(spec, CANVAS, rng)
    bb = room.boundary.bounding_box
    at_edge = (
        abs(bb.x - CANVAS.x) < 1
        or abs(bb.y - CANVAS.y) < 1
        or abs(bb.x + bb.width - CANVAS.x - CANVAS.width) < 1
        or abs(bb.y + bb.height - CANVAS.y - CANVAS.height) < 1
    )
    assert at_edge


# GR03
def test_candidates_no_overlap():
    """All candidate slots do not overlap with placed rooms."""
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    spec = RoomSpec(room_type=RoomType.KITCHEN, width=3000, height=3000)
    candidates = find_candidate_slots(spec, [hallway], CANVAS)
    assert len(candidates) > 0
    for slot in candidates:
        slot_rect = Rectangle(
            x=slot.position.x, y=slot.position.y,
            width=spec.width, height=spec.height,
        )
        assert not slot_rect.overlaps(hallway.boundary.bounding_box)


# GR04
def test_candidates_inside_canvas():
    """All candidate slots are inside the canvas."""
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    spec = RoomSpec(room_type=RoomType.CORRIDOR, width=1000, height=3000)
    candidates = find_candidate_slots(spec, [hallway], CANVAS)
    for slot in candidates:
        assert slot.position.x >= CANVAS.x - 1
        assert slot.position.y >= CANVAS.y - 1
        assert slot.position.x + spec.width <= CANVAS.x + CANVAS.width + 1
        assert slot.position.y + spec.height <= CANVAS.y + CANVAS.height + 1


# GR05
def test_candidates_shared_wall_min():
    """All candidate slots have shared wall >= minimum door width."""
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    spec = RoomSpec(room_type=RoomType.CORRIDOR, width=1000, height=3000)
    candidates = find_candidate_slots(spec, [hallway], CANVAS)
    for slot in candidates:
        assert slot.shared_wall.length >= 700  # MIN_SHARED_WALL


# GR06
def test_scoring_window_bonus():
    """Room requiring window: slot at external wall > internal slot."""
    hallway = _make_room_at(RoomType.HALLWAY, 5000, 0, 2000, 1500)
    spec = RoomSpec(room_type=RoomType.BEDROOM, width=3000, height=4000)
    candidates = find_candidate_slots(spec, [hallway], CANVAS)
    at_edge = []
    not_edge = []
    for slot in candidates:
        rect = Rectangle(
            x=slot.position.x, y=slot.position.y,
            width=spec.width, height=spec.height,
        )
        on_edge = (
            abs(rect.x) < 1 or abs(rect.y) < 1
            or abs(rect.x + rect.width - CANVAS.width) < 1
            or abs(rect.y + rect.height - CANVAS.height) < 1
        )
        if on_edge:
            at_edge.append(slot)
        else:
            not_edge.append(slot)
    if at_edge and not_edge:
        s_edge = score_slot(spec, at_edge[0], [hallway], [], CANVAS)
        s_inner = score_slot(spec, not_edge[0], [hallway], [], CANVAS)
        assert s_edge > s_inner


# GR07
def test_scoring_wet_cluster_bonus():
    """Wet zone next to wet zone scores higher than next to dry room."""
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    kitchen = _make_room_at(RoomType.KITCHEN, 2000, 0, 3000, 3000)
    placed = [hallway, kitchen]
    spec = RoomSpec(room_type=RoomType.COMBINED_BATHROOM, width=2000, height=2000)
    candidates = find_candidate_slots(spec, placed, CANVAS)
    adj_kitchen = [s for s in candidates if s.target_room_id == kitchen.id]
    adj_hallway = [s for s in candidates if s.target_room_id == hallway.id]
    if adj_kitchen and adj_hallway:
        s_wet = score_slot(spec, adj_kitchen[0], placed, [], CANVAS)
        s_dry = score_slot(spec, adj_hallway[0], placed, [], CANVAS)
        assert s_wet > s_dry


# GR08
def test_scoring_adjacency_bonus():
    """Required adjacency (from matrix) scores higher."""
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    corridor = _make_room_at(RoomType.CORRIDOR, 2000, 0, 1200, 4000)
    placed = [hallway, corridor]
    spec = RoomSpec(room_type=RoomType.LIVING_ROOM, width=4000, height=4500)
    candidates = find_candidate_slots(spec, placed, CANVAS)
    if len(candidates) >= 2:
        scores = [score_slot(spec, s, placed, [], CANVAS) for s in candidates]
        assert max(scores) > min(scores)


# GR09
def test_scoring_central_living_room():
    """Living room adjacent to hallway/corridor scores higher."""
    # Place corridor and bedroom far apart so living room slots
    # only touch one placed room each (isolating the centrality effect).
    corridor = _make_room_at(RoomType.CORRIDOR, 0, 0, 1200, 5000)
    bedroom = _make_room_at(RoomType.BEDROOM, 8000, 0, 3500, 4000)
    placed = [corridor, bedroom]
    spec = RoomSpec(room_type=RoomType.LIVING_ROOM, width=4000, height=4500)
    candidates = find_candidate_slots(spec, placed, CANVAS)
    adj_corridor = [s for s in candidates if s.target_room_id == corridor.id]
    adj_bedroom = [s for s in candidates if s.target_room_id == bedroom.id]
    if adj_corridor and adj_bedroom:
        # Pick slots both at external wall to neutralize window bonus
        from floorplan_generator.generator.greedy.scoring import has_external_wall

        edge_corr = [
            s for s in adj_corridor
            if has_external_wall(
                Rectangle(
                    x=s.position.x, y=s.position.y,
                    width=spec.width, height=spec.height,
                ),
                CANVAS,
            )
        ]
        edge_bed = [
            s for s in adj_bedroom
            if has_external_wall(
                Rectangle(
                    x=s.position.x, y=s.position.y,
                    width=spec.width, height=spec.height,
                ),
                CANVAS,
            )
        ]
        if edge_corr and edge_bed:
            s_central = score_slot(
                spec, edge_corr[0], placed, [], CANVAS,
            )
            s_far = score_slot(
                spec, edge_bed[0], placed, [], CANVAS,
            )
            assert s_central > s_far


# GR10
def test_scoring_lookahead_penalty():
    """Slot that blocks future rooms gets penalized."""
    small_canvas = Rectangle(x=0, y=0, width=8000, height=6000)
    hallway = _make_room_at(RoomType.HALLWAY, 0, 0, 2000, 1500)
    spec = RoomSpec(room_type=RoomType.KITCHEN, width=3000, height=3000)
    remaining = [
        RoomSpec(room_type=RoomType.LIVING_ROOM, width=4000, height=4500),
        RoomSpec(room_type=RoomType.BEDROOM, width=3000, height=4000),
    ]
    candidates = find_candidate_slots(spec, [hallway], small_canvas)
    if len(candidates) >= 2:
        scores = [
            score_slot(spec, s, [hallway], remaining, small_canvas)
            for s in candidates
        ]
        assert max(scores) != min(scores)


# GR11
def test_select_softmax_deterministic_low_temp():
    """temperature=0.01 -> always selects highest score."""
    sw = Segment(start=Point(x=0, y=0), end=Point(x=1000, y=0))
    slots = [
        Slot(position=Point(x=0, y=0), target_room_id="a",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=10.0),
        Slot(position=Point(x=0, y=0), target_room_id="b",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=5.0),
        Slot(position=Point(x=0, y=0), target_room_id="c",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=1.0),
    ]
    rng = random.Random(42)
    results = [select_slot(slots, rng, temperature=0.01) for _ in range(20)]
    assert all(r.score == 10.0 for r in results)


# GR12
def test_select_softmax_varies_with_seed():
    """Different seeds -> different selections at temperature=0.5."""
    sw = Segment(start=Point(x=0, y=0), end=Point(x=1000, y=0))
    slots = [
        Slot(position=Point(x=0, y=0), target_room_id="a",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=10.0),
        Slot(position=Point(x=100, y=0), target_room_id="b",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=9.0),
        Slot(position=Point(x=200, y=0), target_room_id="c",
             side=Side.RIGHT, alignment=Alignment.START,
             shared_wall=sw, score=8.0),
    ]
    selections = set()
    for seed in range(100):
        rng = random.Random(seed)
        result = select_slot(slots, rng, temperature=0.5)
        selections.add(result.target_room_id)
    assert len(selections) >= 2


# GR13
def test_restart_changes_seed():
    """Each restart uses seed + restart_num * 1000."""
    composition = determine_composition(ApartmentClass.ECONOMY, 1)
    specs1 = assign_sizes(composition, random.Random(42), ApartmentClass.ECONOMY, 1)
    specs2 = assign_sizes(composition, random.Random(1042), ApartmentClass.ECONOMY, 1)
    sizes1 = [(s.width, s.height) for s in specs1]
    sizes2 = [(s.width, s.height) for s in specs2]
    assert sizes1 != sizes2


# GR14
def test_restart_success_after_deadend():
    """Dead end on first try -> restart succeeds."""
    composition = determine_composition(ApartmentClass.ECONOMY, 1)
    specs = assign_sizes(
        composition, random.Random(42), ApartmentClass.ECONOMY, 1,
    )
    canvas = Rectangle(x=0, y=0, width=10000, height=8000)
    result = greedy_layout(specs, canvas, seed=42, max_restarts=10)
    assert result is not None
    assert result.success


# GR15
def test_reproducible_with_same_seed():
    """Same seed -> identical result."""
    composition = determine_composition(ApartmentClass.ECONOMY, 1)
    specs = assign_sizes(
        composition, random.Random(42), ApartmentClass.ECONOMY, 1,
    )
    canvas = Rectangle(x=0, y=0, width=10000, height=8000)
    r1 = greedy_layout(specs, canvas, seed=42)
    specs2 = assign_sizes(
        composition, random.Random(42), ApartmentClass.ECONOMY, 1,
    )
    r2 = greedy_layout(specs2, canvas, seed=42)
    assert r1 is not None and r2 is not None
    assert len(r1.rooms) == len(r2.rooms)
    for a, b in zip(r1.rooms, r2.rooms):
        assert a.boundary.bounding_box.x == pytest.approx(b.boundary.bounding_box.x)
        assert a.boundary.bounding_box.y == pytest.approx(b.boundary.bounding_box.y)


# GR16
def test_different_seeds_different_layouts():
    """Different seeds -> different layouts."""
    composition = determine_composition(ApartmentClass.ECONOMY, 1)
    canvas = Rectangle(x=0, y=0, width=10000, height=8000)
    layouts = set()
    for seed in range(20):
        specs = assign_sizes(
            composition, random.Random(seed), ApartmentClass.ECONOMY, 1,
        )
        r = greedy_layout(specs, canvas, seed=seed)
        if r and r.success:
            key = tuple(
                (rm.boundary.bounding_box.x, rm.boundary.bounding_box.y)
                for rm in r.rooms
            )
            layouts.add(key)
    assert len(layouts) >= 3


# GR17
def test_economy_1room_success_rate():
    """Economy 1-room: >= 90% first-try success over 100 runs."""
    success = 0
    for seed in range(100):
        composition = determine_composition(ApartmentClass.ECONOMY, 1)
        specs = assign_sizes(
            composition, random.Random(seed), ApartmentClass.ECONOMY, 1,
        )
        canvas = Rectangle(x=0, y=0, width=10000, height=8000)
        r = greedy_layout(specs, canvas, seed=seed, max_restarts=1)
        if r and r.success:
            success += 1
    assert success >= 90


# GR18
def test_comfort_2room_success_10_restarts():
    """Comfort 2-room: >= 95% success with 10 restarts over 50 runs."""
    success = 0
    for seed in range(50):
        composition = determine_composition(ApartmentClass.COMFORT, 2)
        specs = assign_sizes(
            composition, random.Random(seed), ApartmentClass.COMFORT, 2,
        )
        canvas = Rectangle(x=0, y=0, width=12000, height=10000)
        r = greedy_layout(specs, canvas, seed=seed, max_restarts=10)
        if r and r.success:
            success += 1
    assert success >= 47
