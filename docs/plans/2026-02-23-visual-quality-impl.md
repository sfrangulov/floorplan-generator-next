# Visual Quality Improvement — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix placement bugs (missing windows, door collisions, furniture overlap) and improve SVG rendering to match the reference Illustrator files in `docs/svg/`.

**Architecture:** Phase 1 fixes the CSP placement algorithm (window thresholds, door swing_arc model, furniture clearance checks). Phase 2 overhauls the SVG renderer to match reference structure: background polygon, room groups with type-prefixed IDs, detailed furniture symbols in a `<g id="mebel">` group, and a `<g id="floor">` group for walls/doors/windows.

**Tech Stack:** Python 3.12, Pydantic 2, svgwrite, lxml, pytest

---

### Task 1: Add `wall_orientation` field to Door model

**Files:**
- Modify: `src/floorplan_generator/core/models.py:36-59`
- Modify: `tests/conftest.py:86-107` (update `make_door` fixture)
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
def test_swing_arc_inward_vertical():
    """INWARD swing on vertical wall: arc extends to the right of door."""
    door = Door(
        id="d1", position=Point(x=2000, y=500), width=800,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="a", room_to="b", wall_orientation="vertical",
    )
    arc = door.swing_arc
    assert arc.x == 2000
    assert arc.y == 500
    assert arc.width == 800
    assert arc.height == 800


def test_swing_arc_outward_vertical():
    """OUTWARD swing on vertical wall: arc extends to the left of door."""
    door = Door(
        id="d2", position=Point(x=2000, y=500), width=800,
        door_type=DoorType.INTERIOR, swing=SwingDirection.OUTWARD,
        room_from="a", room_to="b", wall_orientation="vertical",
    )
    arc = door.swing_arc
    assert arc.x == 2000 - 800  # Shifted left
    assert arc.y == 500
    assert arc.width == 800
    assert arc.height == 800


def test_swing_arc_outward_horizontal():
    """OUTWARD swing on horizontal wall: arc extends upward."""
    door = Door(
        id="d3", position=Point(x=500, y=3000), width=800,
        door_type=DoorType.INTERIOR, swing=SwingDirection.OUTWARD,
        room_from="a", room_to="b", wall_orientation="horizontal",
    )
    arc = door.swing_arc
    assert arc.x == 500
    assert arc.y == 3000 - 800  # Shifted up
    assert arc.width == 800
    assert arc.height == 800
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_swing_arc_inward_vertical -v`
Expected: FAIL — `Door.__init__` doesn't accept `wall_orientation`

**Step 3: Write minimal implementation**

In `src/floorplan_generator/core/models.py`, update Door class:

```python
class Door(BaseModel):
    """Door connecting two rooms."""

    id: str
    position: Point
    width: float  # mm (door leaf width)
    door_type: DoorType
    swing: SwingDirection
    room_from: str
    room_to: str
    wall_orientation: str = "vertical"  # "vertical" or "horizontal"

    @computed_field
    @property
    def swing_arc(self) -> Rectangle:
        """Rectangle representing the door sweep area.

        For OUTWARD swing, the arc extends away from the room
        (opposite side of the wall from the door's room_to).
        """
        if self.wall_orientation == "vertical":
            x = (
                self.position.x - self.width
                if self.swing == SwingDirection.OUTWARD
                else self.position.x
            )
            return Rectangle(
                x=x, y=self.position.y,
                width=self.width, height=self.width,
            )
        else:  # horizontal
            y = (
                self.position.y - self.width
                if self.swing == SwingDirection.OUTWARD
                else self.position.y
            )
            return Rectangle(
                x=self.position.x, y=y,
                width=self.width, height=self.width,
            )
```

Update `tests/conftest.py` `make_door` fixture to accept `wall_orientation`:

```python
def _factory(
    door_type: DoorType = DoorType.INTERIOR,
    width: float = 800.0,
    swing: SwingDirection = SwingDirection.INWARD,
    room_from: str = "room_a",
    room_to: str = "room_b",
    position: Point | None = None,
    wall_orientation: str = "vertical",
) -> Door:
    return Door(
        id=_uid(),
        position=position or Point(x=0, y=0),
        width=width,
        door_type=door_type,
        swing=swing,
        room_from=room_from,
        room_to=room_to,
        wall_orientation=wall_orientation,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py -k swing_arc -v`
Expected: 3 PASS

**Step 5: Run full test suite to check for regressions**

Run: `pytest --tb=short`
Expected: All pass. Existing code creates Door without `wall_orientation` — the default `"vertical"` handles backwards compat.

**Step 6: Commit**

```
git add src/floorplan_generator/core/models.py tests/unit/test_models.py tests/conftest.py
git commit -m "fix: add wall_orientation to Door model for correct swing_arc geometry"
```

---

### Task 2: Update door_placer to set `wall_orientation`

**Files:**
- Modify: `src/floorplan_generator/generator/csp/door_placer.py:110-148`
- Test: `tests/unit/test_csp.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_csp.py`:

```python
# CS18
def test_door_wall_orientation_set():
    """Placed doors have correct wall_orientation matching their shared wall."""
    rooms, shared_walls, _ = _simple_topology()
    rng = random.Random(42)
    doors = place_doors(rooms, shared_walls, rng)
    for door_info in doors:
        door = door_info["door"]
        wall = door_info["shared_wall"]
        is_vertical = abs(wall.start.x - wall.end.x) < 1
        expected = "vertical" if is_vertical else "horizontal"
        assert door.wall_orientation == expected, (
            f"Door {door.id}: expected {expected}, got {door.wall_orientation}"
        )


# CS19
def test_door_swing_arc_matches_placer_arc():
    """Door.swing_arc matches the arc used during placement (no mismatch)."""
    rooms, shared_walls, _ = _simple_topology()
    rng = random.Random(42)
    doors = place_doors(rooms, shared_walls, rng)
    for door_info in doors:
        door = door_info["door"]
        wall = door_info["shared_wall"]
        is_vertical = abs(wall.start.x - wall.end.x) < 1
        # Recompute what the placer would have used
        if is_vertical:
            expected_x = (
                door.position.x - door.width
                if door.swing == SwingDirection.OUTWARD
                else door.position.x
            )
            expected_arc = Rectangle(
                x=expected_x, y=door.position.y,
                width=door.width, height=door.width,
            )
        else:
            expected_y = (
                door.position.y - door.width
                if door.swing == SwingDirection.OUTWARD
                else door.position.y
            )
            expected_arc = Rectangle(
                x=door.position.x, y=expected_y,
                width=door.width, height=door.width,
            )
        assert door.swing_arc == expected_arc
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_csp.py::test_door_wall_orientation_set -v`
Expected: FAIL — Door doesn't have `wall_orientation` set

**Step 3: Write minimal implementation**

In `src/floorplan_generator/generator/csp/door_placer.py`, update the Door creation (around line 140) to pass `wall_orientation`:

```python
            orientation = "vertical" if is_vertical else "horizontal"

            door = Door(
                id=uuid.uuid4().hex[:8],
                position=door_pos,
                width=door_width,
                door_type=door_type,
                swing=swing,
                room_from=sw.room_a_id,
                room_to=sw.room_b_id,
                wall_orientation=orientation,
            )
```

**Step 4: Run tests to verify**

Run: `pytest tests/unit/test_csp.py -k "CS18 or CS19 or test_door" -v`
Expected: All pass

**Step 5: Commit**

```
git add src/floorplan_generator/generator/csp/door_placer.py tests/unit/test_csp.py
git commit -m "fix: set wall_orientation in door_placer for consistent swing_arc"
```

---

### Task 3: Fix window placement thresholds

**Files:**
- Modify: `src/floorplan_generator/generator/csp/window_placer.py:14-76`
- Test: `tests/unit/test_csp.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_csp.py`:

```python
# CS20
def test_window_on_short_wall():
    """Windows can be placed on walls as short as 700mm."""
    # Room with only a 800mm external wall
    room = _room_at(RoomType.KITCHEN, 0, 0, 800, 3000)
    canvas = Rectangle(x=0, y=0, width=5000, height=5000)
    rng = random.Random(42)
    windows = place_windows([room], canvas, rng)
    assert len(windows) >= 1, "Kitchen with 800mm external wall should get a window"


# CS21
def test_all_window_rooms_get_windows():
    """All rooms requiring windows get at least one on the simple topology."""
    rooms, shared_walls, canvas = _simple_topology()
    rng = random.Random(42)
    windows = place_windows(rooms, canvas, rng)
    rooms_with_windows = {wr["room"].id for wr in windows}
    for room in rooms:
        if room.room_type.requires_window:
            assert room.id in rooms_with_windows, (
                f"{room.room_type} (id={room.id}) has no window"
            )
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_csp.py::test_window_on_short_wall -v`
Expected: FAIL — 800mm wall is < 900mm threshold, no window placed

**Step 3: Write minimal implementation**

In `src/floorplan_generator/generator/csp/window_placer.py`:

```python
# Standard window sizes (width in mm) — includes smaller sizes
_WINDOW_SIZES = [600, 700, 900, 1200, 1500, 1800]
_WINDOW_HEIGHT = 1500.0
_MIN_WALL_LENGTH = 600  # lowered from 900


def _external_wall_segments(
    room: Room,
    canvas: Rectangle,
) -> list[Segment]:
    """Get wall segments that lie on the canvas boundary."""
    segs = wall_segments(room)
    result = []
    eps = 2.0
    for seg in segs:
        mid = seg.midpoint
        on_edge = (
            abs(mid.x - canvas.x) < eps
            or abs(mid.y - canvas.y) < eps
            or abs(mid.x - (canvas.x + canvas.width)) < eps
            or abs(mid.y - (canvas.y + canvas.height)) < eps
        )
        if on_edge and seg.length >= _MIN_WALL_LENGTH:
            result.append(seg)
    return result
```

And fix the margin check around line 75:

```python
            if width > wall.length - 150:  # reduced from 200
                continue
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_csp.py -k "window" -v`
Expected: CS06, CS07, CS20, CS21 all pass

**Step 5: Commit**

```
git add src/floorplan_generator/generator/csp/window_placer.py tests/unit/test_csp.py
git commit -m "fix: lower window placement thresholds so rooms get windows"
```

---

### Task 4: Fix furniture placement — skip items that can't fit instead of failing

**Files:**
- Modify: `src/floorplan_generator/generator/csp/furniture_placer.py:166-173`
- Test: `tests/unit/test_csp.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_csp.py`:

```python
# CS22
def test_furniture_skip_unfittable():
    """When a furniture item has positions but all violate constraints, skip it."""
    room = _room_at(RoomType.BEDROOM, 0, 0, 3000, 3000)
    # Place a huge door covering most of the room
    door = Door(
        id="bigdoor", position=Point(x=0, y=0), width=2500,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="a", room_to=room.id, wall_orientation="vertical",
    )
    rng = random.Random(42)
    # Try to fit a large wardrobe (2000mm) — should skip, not fail entirely
    furniture = place_furniture(
        room, [FurnitureType.WARDROBE_SLIDING, FurnitureType.NIGHTSTAND],
        doors=[door], stoyaks=[], rng=rng,
    )
    # Should succeed (possibly with fewer items) rather than return None
    assert furniture is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_csp.py::test_furniture_skip_unfittable -v`
Expected: FAIL — returns None because wardrobe can't be placed and `positions` list is non-empty

**Step 3: Write minimal implementation**

In `src/floorplan_generator/generator/csp/furniture_placer.py`, change the end of `_backtrack` (lines 166-173):

```python
    # If no valid position found for this item, skip it and continue
    # with the remaining items. This prevents a single large item
    # from failing the entire room's furniture placement.
    return _backtrack(
        items, index + 1, placed, room, room_bb, doors, stoyaks, rng, step,
    )
```

This replaces the current logic which returns `None` when positions exist but all violate constraints.

**Step 4: Run tests**

Run: `pytest tests/unit/test_csp.py -k "furniture" -v`
Expected: CS10, CS11, CS12, CS13, CS14, CS22 all pass

**Step 5: Commit**

```
git add src/floorplan_generator/generator/csp/furniture_placer.py tests/unit/test_csp.py
git commit -m "fix: skip unfittable furniture items instead of failing entire room"
```

---

### Task 5: Strengthen furniture constraints — door arc + entry clearance

**Files:**
- Modify: `src/floorplan_generator/generator/csp/constraints.py:49-52`
- Test: `tests/unit/test_csp.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_csp.py`:

```python
from floorplan_generator.generator.csp.constraints import violates_hard_constraints


# CS23
def test_furniture_entry_clearance():
    """Furniture must not be placed within 300mm in front of a door."""
    room = _room_at(RoomType.BEDROOM, 0, 0, 5000, 5000)
    door = Door(
        id="d1", position=Point(x=100, y=0), width=800,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="a", room_to=room.id, wall_orientation="horizontal",
    )
    # Place furniture right at the door swing arc edge + 100mm (inside clearance zone)
    from floorplan_generator.core.models import FurnitureItem
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.NIGHTSTAND,
        position=Point(x=200, y=810),  # just past the 800mm arc, within 300mm
        width=500, depth=425,
    )
    assert violates_hard_constraints(item, room, [], [door], [])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_csp.py::test_furniture_entry_clearance -v`
Expected: FAIL — current code only checks `bb.overlaps(door.swing_arc)`, not entry clearance

**Step 3: Write minimal implementation**

In `src/floorplan_generator/generator/csp/constraints.py`, add a door entry clearance check after HC03:

```python
    # HC03: not blocking door swing arc
    for door in doors:
        if bb.overlaps(door.swing_arc):
            return True

    # HC07: entry clearance — 300mm beyond door swing arc
    _DOOR_ENTRY_CLEARANCE = 300.0
    for door in doors:
        arc = door.swing_arc
        entry_zone = Rectangle(
            x=arc.x - _DOOR_ENTRY_CLEARANCE,
            y=arc.y - _DOOR_ENTRY_CLEARANCE,
            width=arc.width + 2 * _DOOR_ENTRY_CLEARANCE,
            height=arc.height + 2 * _DOOR_ENTRY_CLEARANCE,
        )
        if bb.overlaps(entry_zone) and bb.overlaps(arc) is False:
            # Item is in the clearance zone but not in the arc itself
            # Only block if item is in the "front" of the door (opening direction)
            pass  # Simplified: use the expanded arc check
        # Simpler approach: expand the arc check by the clearance
        expanded_arc = Rectangle(
            x=arc.x, y=arc.y,
            width=arc.width, height=arc.height + _DOOR_ENTRY_CLEARANCE,
        )
        if bb.overlaps(expanded_arc):
            return True
```

Wait — this needs more thought. The entry zone direction depends on the door orientation. Simpler approach: just expand the swing arc by 300mm on the open side.

Actually, looking at this more carefully — the simplest robust approach is to replace HC03 with a check against an expanded arc:

```python
    # HC03: not blocking door swing arc + entry clearance (300mm beyond arc)
    _DOOR_ENTRY_CLEARANCE = 300.0
    for door in doors:
        arc = door.swing_arc
        expanded = Rectangle(
            x=arc.x - _DOOR_ENTRY_CLEARANCE / 2,
            y=arc.y - _DOOR_ENTRY_CLEARANCE / 2,
            width=arc.width + _DOOR_ENTRY_CLEARANCE,
            height=arc.height + _DOOR_ENTRY_CLEARANCE,
        )
        if bb.overlaps(expanded):
            return True
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_csp.py -v`
Expected: All pass including CS23

**Step 5: Commit**

```
git add src/floorplan_generator/generator/csp/constraints.py tests/unit/test_csp.py
git commit -m "fix: add door entry clearance to furniture hard constraints"
```

---

### Task 6: Integration test — generate apartments and validate placement

**Files:**
- Create: `tests/integration/test_placement_quality.py`

**Step 1: Write the integration tests**

```python
"""Integration tests for placement quality (PQ01-PQ04)."""

from __future__ import annotations

import random

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.core.geometry import Rectangle
from floorplan_generator.generator.layout_engine import generate_apartment


def _generate(apartment_class: ApartmentClass, num_rooms: int, seed: int):
    return generate_apartment(apartment_class, num_rooms, seed, max_restarts=20)


# PQ01
def test_living_rooms_have_windows():
    """All living rooms and kitchens get at least one window."""
    for seed in range(42, 52):
        result = _generate(ApartmentClass.ECONOMY, 1, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            if room.room_type.requires_window:
                assert len(room.windows) >= 1, (
                    f"seed={seed}: {room.room_type} has no window"
                )


# PQ02
def test_no_door_arc_collisions():
    """No pair of doors has overlapping swing arcs."""
    for seed in range(42, 52):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is None:
            continue
        all_doors = []
        seen = set()
        for room in result.apartment.rooms:
            for door in room.doors:
                if door.id not in seen:
                    seen.add(door.id)
                    all_doors.append(door)
        for i, d1 in enumerate(all_doors):
            for j, d2 in enumerate(all_doors):
                if i < j:
                    assert not d1.swing_arc.overlaps(d2.swing_arc), (
                        f"seed={seed}: doors {d1.id} and {d2.id} arcs collide"
                    )


# PQ03
def test_furniture_inside_rooms():
    """All furniture items are inside their room boundary."""
    for seed in range(42, 47):
        result = _generate(ApartmentClass.ECONOMY, 1, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            bb = room.boundary.bounding_box
            for item in room.furniture:
                ibb = item.bounding_box
                assert ibb.x >= bb.x - 2, f"seed={seed}: {item.furniture_type} outside room left"
                assert ibb.y >= bb.y - 2, f"seed={seed}: {item.furniture_type} outside room top"
                assert ibb.x + ibb.width <= bb.x + bb.width + 2
                assert ibb.y + ibb.height <= bb.y + bb.height + 2


# PQ04
def test_furniture_not_overlapping_doors():
    """No furniture item overlaps a door swing arc in the same room."""
    for seed in range(42, 47):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            for item in room.furniture:
                for door in room.doors:
                    assert not item.bounding_box.overlaps(door.swing_arc), (
                        f"seed={seed}: {item.furniture_type} overlaps door {door.id} arc "
                        f"in {room.room_type}"
                    )
```

**Step 2: Run tests**

Run: `pytest tests/integration/test_placement_quality.py -v`
Expected: All pass (after Tasks 1-5 fixes)

**Step 3: Commit**

```
git add tests/integration/test_placement_quality.py
git commit -m "test: add placement quality integration tests (PQ01-PQ04)"
```

---

### Task 7: Restructure SVG renderer — background + room groups + mebel + floor

**Files:**
- Modify: `src/floorplan_generator/renderer/svg_renderer.py` (full rewrite of `render_svg`)
- Modify: `src/floorplan_generator/renderer/room_renderer.py` (add room ID prefixes)
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R21
def test_svg_structure_matches_reference():
    """SVG has correct layer order: background, room groups, mebel, floor."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000, room_id="r_living")
    result = _make_result([room])
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    children = list(root)
    # Find named groups
    ids = [child.get("id") for child in children if child.get("id")]
    assert "background" in ids, f"Missing background element, got {ids}"
    assert "mebel" in ids, f"Missing mebel group, got {ids}"
    assert "floor" in ids, f"Missing floor group, got {ids}"
    # Background should come before mebel, mebel before floor
    bg_idx = ids.index("background")
    mebel_idx = ids.index("mebel")
    floor_idx = ids.index("floor")
    assert bg_idx < mebel_idx < floor_idx


# R22
def test_room_group_ids_have_type_prefix():
    """Room groups use type-prefix IDs (h1, r1, s1, c1)."""
    hallway = _make_room(RoomType.HALLWAY, 0, 0, 2000, 1500, room_id="hallway1")
    living = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 4000, room_id="living1")
    bathroom = _make_room(
        RoomType.COMBINED_BATHROOM, 0, 1500, 2000, 2000, room_id="bath1",
    )
    result = _make_result([hallway, living, bathroom])
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    group_ids = [el.get("id") for el in root.iter() if el.get("id")]
    # Should have h1, r1, s1 (type-prefixed room groups)
    assert "h1" in group_ids, f"Missing h1 for hallway, got {group_ids}"
    assert "r1" in group_ids, f"Missing r1 for living room, got {group_ids}"
    assert "s1" in group_ids, f"Missing s1 for bathroom, got {group_ids}"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_renderer.py::test_svg_structure_matches_reference -v`
Expected: FAIL — current SVG doesn't have `id="background"` or correct structure

**Step 3: Implement SVG structure overhaul**

Update `src/floorplan_generator/renderer/room_renderer.py` — add a function to compute room group IDs:

```python
# Room type -> ID prefix mapping (matches reference Illustrator SVGs)
_ROOM_PREFIX: dict[RoomType, str] = {
    RoomType.HALLWAY: "h",
    RoomType.CORRIDOR: "h",  # also hallway-like
    RoomType.HALL: "h",
    RoomType.LIVING_ROOM: "r",
    RoomType.BEDROOM: "r",
    RoomType.CHILDREN: "r",
    RoomType.CABINET: "r",
    RoomType.KITCHEN: "c",
    RoomType.KITCHEN_DINING: "c",
    RoomType.KITCHEN_NICHE: "c",
    RoomType.BATHROOM: "s",
    RoomType.TOILET: "s",
    RoomType.COMBINED_BATHROOM: "s",
    RoomType.STORAGE: "c",
    RoomType.WARDROBE: "c",
    RoomType.LAUNDRY: "s",
    RoomType.BALCONY: "c",
}


def compute_room_group_ids(rooms: list[Room]) -> dict[str, str]:
    """Assign type-prefixed IDs: h1, h2, r1, r2, s1, c1, etc."""
    counters: dict[str, int] = {}
    result: dict[str, str] = {}
    for room in rooms:
        prefix = _ROOM_PREFIX.get(room.room_type, "c")
        counters[prefix] = counters.get(prefix, 0) + 1
        result[room.id] = f"{prefix}{counters[prefix]}"
    return result
```

Update `render_rooms` to emit individual room groups with proper IDs.

Update `src/floorplan_generator/renderer/svg_renderer.py`:

```python
def render_svg(
    result: GenerationResult,
    theme: Theme | None = None,
) -> str:
    if theme is None:
        theme = get_default_theme()

    rooms = result.apartment.rooms
    cw = theme.canvas.width
    ch = theme.canvas.height
    mapper = CoordinateMapper(rooms, cw, ch)

    dwg = svgwrite.Drawing(
        size=(f"{cw}px", f"{ch}px"),
        viewBox=f"0 0 {cw} {ch}",
    )

    # Layer 1: Background path (apartment exterior polygon)
    bg_points = _compute_exterior_polygon(rooms, mapper)
    if bg_points:
        d = "M " + " L ".join(f"{x},{y}" for x, y in bg_points) + " Z"
        dwg.add(dwg.path(d=d, id="background", fill=theme.canvas.background))
    else:
        dwg.add(dwg.rect(
            insert=(0, 0), size=(cw, ch), id="background",
            fill=theme.canvas.background,
        ))

    # Layer 2: Room groups (individual <g id="h1">, <g id="r1">, etc.)
    room_ids = compute_room_group_ids(rooms)
    render_rooms(dwg, rooms, room_ids, mapper, theme)

    # Layer 3: Furniture (<g id="mebel">)
    mebel_group = dwg.g(id="mebel")
    render_furniture(dwg, mebel_group, rooms, mapper, theme)
    dwg.add(mebel_group)

    # Layer 4: Floor group (walls + doors + windows)
    floor_group = dwg.g(id="floor")
    render_walls(dwg, floor_group, rooms, mapper, theme)
    render_doors(dwg, floor_group, rooms, mapper, theme)
    render_windows(dwg, floor_group, rooms, mapper, theme)
    render_stoyaks(dwg, floor_group, result.stoyaks, mapper, theme)
    dwg.add(floor_group)

    return dwg.tostring()
```

Also update `render_rooms` signature in `room_renderer.py` to add rooms directly to `dwg` with their own `<g>` per room.

**Step 4: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: R21, R22 pass. Check that R01-R20 still pass (may need minor adjustments to find elements under new structure).

**Step 5: Commit**

```
git add src/floorplan_generator/renderer/svg_renderer.py src/floorplan_generator/renderer/room_renderer.py tests/unit/test_renderer.py
git commit -m "feat: restructure SVG output to match reference (background, room groups, mebel, floor)"
```

---

### Task 8: Update door renderer — bezier arc + gap rect

**Files:**
- Modify: `src/floorplan_generator/renderer/door_renderer.py`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R23
def test_door_renders_bezier_arc():
    """Door swing arc is rendered as a bezier curve path, not a polygon."""
    door = Door(
        id="d1", position=Point(x=2000, y=500), width=800,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="a", room_to="b", wall_orientation="vertical",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000, room_id="a", doors=[door],
    )
    result = _make_result([room])
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    # Find path elements inside the floor group
    floor = root.find(".//*[@id='floor']")
    assert floor is not None
    arcs = [el for el in floor.iter() if el.tag.endswith("path")]
    assert len(arcs) >= 1, "Expected at least one arc path in floor group"
    # Arc path should use cubic bezier (c command) or arc (A command)
    d = arcs[0].get("d", "")
    assert "A" in d or "c" in d, f"Arc path should use bezier/arc commands: {d}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_renderer.py::test_door_renders_bezier_arc -v`
Expected: FAIL — current code renders doors in a separate "doors" group, not in "floor"

**Step 3: Implement door rendering update**

Update `src/floorplan_generator/renderer/door_renderer.py`:

```python
def _render_single_door(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    door: Door,
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render a single door: gap rect + bezier swing arc."""
    pos = mapper.to_svg(door.position)
    w = mapper.scale_length(door.width)
    is_vertical = door.wall_orientation == "vertical"

    # Gap rectangle (covers wall line)
    if is_vertical:
        gap_h = w
        group.add(dwg.rect(
            insert=(pos[0] - 2, pos[1]),
            size=(4, gap_h),
            fill=theme.doors.gap_fill, stroke="none",
        ))
    else:
        gap_w = w
        group.add(dwg.rect(
            insert=(pos[0], pos[1] - 2),
            size=(gap_w, 4),
            fill=theme.doors.gap_fill, stroke="none",
        ))

    # Swing arc — quarter circle using SVG arc command
    hx, hy = pos
    r = w
    if is_vertical:
        if door.swing == SwingDirection.INWARD:
            # Arc from (hx, hy) sweeping right and down
            arc_path = f"M {hx},{hy} L {hx + r},{hy} A {r},{r} 0 0,1 {hx},{hy + r}"
        else:
            arc_path = f"M {hx},{hy} L {hx - r},{hy} A {r},{r} 0 0,0 {hx},{hy + r}"
    else:
        if door.swing == SwingDirection.INWARD:
            arc_path = f"M {hx},{hy} L {hx},{hy + r} A {r},{r} 0 0,0 {hx + r},{hy}"
        else:
            arc_path = f"M {hx},{hy} L {hx},{hy - r} A {r},{r} 0 0,1 {hx + r},{hy}"

    group.add(dwg.path(
        d=arc_path,
        fill="none",
        stroke=theme.doors.arc_stroke,
        stroke_width=theme.doors.arc_width,
    ))
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: All pass

**Step 5: Commit**

```
git add src/floorplan_generator/renderer/door_renderer.py tests/unit/test_renderer.py
git commit -m "feat: update door renderer with bezier arcs and wall-orientation-aware gap"
```

---

### Task 9: Update window renderer — simple line segments

**Files:**
- Modify: `src/floorplan_generator/renderer/window_renderer.py`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R24
def test_window_renders_as_line():
    """Windows are rendered as line segments on exterior walls."""
    window = Window(
        id="w1", position=Point(x=1000, y=0), width=1500, height=1500,
        wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000, room_id="r1",
        windows=[window],
    )
    result = _make_result([room])
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    floor = root.find(".//*[@id='floor']")
    assert floor is not None
    lines = [el for el in floor.iter() if el.tag.endswith("line")]
    assert len(lines) >= 1, "Expected at least one window line in floor group"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_renderer.py::test_window_renders_as_line -v`

**Step 3: Implement**

Update `src/floorplan_generator/renderer/window_renderer.py`:

```python
def _render_single_window(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    window: Window,
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render a window as a line segment on the exterior wall."""
    pos = mapper.to_svg(window.position)
    w = mapper.scale_length(window.width)

    is_horizontal_wall = window.wall_side in ("north", "south")

    if is_horizontal_wall:
        # Window runs horizontally on the wall
        group.add(dwg.line(
            start=(pos[0], pos[1]),
            end=(pos[0] + w, pos[1]),
            stroke=theme.windows.stroke,
            stroke_width=theme.windows.stroke_width * 3,
            stroke_linecap="round",
        ))
    else:
        # Window runs vertically on the wall
        group.add(dwg.line(
            start=(pos[0], pos[1]),
            end=(pos[0], pos[1] + w),
            stroke=theme.windows.stroke,
            stroke_width=theme.windows.stroke_width * 3,
            stroke_linecap="round",
        ))
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: All pass

**Step 5: Commit**

```
git add src/floorplan_generator/renderer/window_renderer.py tests/unit/test_renderer.py
git commit -m "feat: render windows as line segments matching reference SVGs"
```

---

### Task 10: Extract and port furniture symbols from reference SVGs

**Files:**
- Modify: `src/floorplan_generator/renderer/symbols/furniture.py` (rewrite symbol functions)
- Test: `tests/unit/test_renderer.py`

This is the largest task. The approach:
1. Read several reference SVGs from `docs/svg/` to extract representative furniture shapes
2. Port the most recognizable elements (bed with pillows/headboard, toilet oval, bathtub rounded shape, stove burners, fridge with compartment lines, sofa with cushion detail, table/chairs)
3. Keep the draw function interface the same: `draw_xxx(g, w, d, style)`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R25
def test_bed_has_pillow_elements():
    """Bed symbol includes pillow rectangles with rounded corners."""
    from floorplan_generator.renderer.symbols.furniture import draw_bed
    import svgwrite
    dwg = svgwrite.Drawing()
    g = dwg.g()
    draw_bed(g, 160, 200, {"stroke": "#000", "fill": "none"})
    elements = list(g.elements)
    # Should have more than 3 elements (headboard + mattress + 2 pillows minimum)
    assert len(elements) >= 4, f"Bed should have >= 4 elements, got {len(elements)}"
    # Check at least one rect has rounded corners (rx attribute)
    rounded = [e for e in elements if hasattr(e, "attribs") and "rx" in e.attribs]
    assert len(rounded) >= 1, "Bed should have at least one rounded-corner pillow"
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/test_renderer.py::test_bed_has_pillow_elements -v`
Expected: PASS — current bed already has rounded pillows. Good, this verifies existing quality.

**Step 3: Enhance furniture symbols**

Update each draw function in `src/floorplan_generator/renderer/symbols/furniture.py` to add more detail inspired by reference SVGs. Key improvements:

- **draw_bed**: Add mattress edge lines, more defined headboard (already has pillows — verify this is good enough)
- **draw_sofa**: Add cushion division lines (vertical lines separating seat cushions), armrest shapes
- **draw_stove**: Already has 4 burners with concentric circles — matches reference well
- **draw_fridge**: Add compartment division line (horizontal line separating fridge/freezer)
- **draw_toilet**: Add seat detail line
- **draw_bathtub**: Already has inner basin + drain — close to reference
- **draw_wardrobe**: Add door handle circles, vertical door division
- **draw_table**: Add leg circles at corners for round table variant
- **draw_washing_machine**: Add control panel rect at top

The exact changes depend on examining the reference SVGs closely. The key principle: each symbol should be clearly identifiable at a glance.

**Step 4: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: All pass

**Step 5: Commit**

```
git add src/floorplan_generator/renderer/symbols/furniture.py tests/unit/test_renderer.py
git commit -m "feat: enhance furniture symbols with more detail to match reference"
```

---

### Task 11: Final integration test — render and validate SVG structure

**Files:**
- Create: `tests/integration/test_svg_structure.py`

**Step 1: Write the test**

```python
"""Integration tests for SVG output structure (SVG01-SVG03)."""

from __future__ import annotations

from xml.etree import ElementTree

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.renderer.svg_renderer import render_svg


# SVG01
def test_generated_svg_has_reference_structure():
    """Full pipeline: generate + render produces SVG with reference structure."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    assert "background" in ids
    assert "mebel" in ids
    assert "floor" in ids
    # At least one room group with type prefix
    room_groups = [i for i in ids if len(i) <= 3 and i[0] in "hrsc" and i[1:].isdigit()]
    assert len(room_groups) >= 3, f"Expected room groups, got {ids}"


# SVG02
def test_floor_group_contains_walls_and_doors():
    """The floor group contains wall lines and door elements."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    floor = None
    for el in root.iter():
        if el.get("id") == "floor":
            floor = el
            break
    assert floor is not None
    # Should have line elements (walls) and path elements (door arcs)
    lines = [el for el in floor.iter() if el.tag.endswith("line")]
    paths = [el for el in floor.iter() if el.tag.endswith("path")]
    assert len(lines) >= 4, f"Floor should have wall lines, got {len(lines)}"
    assert len(paths) >= 1, f"Floor should have door arc paths, got {len(paths)}"


# SVG03
def test_mebel_group_contains_furniture():
    """The mebel group contains furniture elements."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    mebel = None
    for el in root.iter():
        if el.get("id") == "mebel":
            mebel = el
            break
    assert mebel is not None
    children = list(mebel)
    assert len(children) >= 1, "mebel group should have furniture"
```

**Step 2: Run tests**

Run: `pytest tests/integration/test_svg_structure.py -v`
Expected: All pass

**Step 3: Commit**

```
git add tests/integration/test_svg_structure.py
git commit -m "test: add SVG structure integration tests (SVG01-SVG03)"
```

---

### Task 12: Visual regression — generate sample SVGs and verify

**Step 1: Generate sample SVGs with both themes**

Run:
```bash
floorplan generate --class economy --rooms 1 --count 5 --seed 42 --output ./output/economy_after --theme blueprint
floorplan generate --class comfort --rooms 2 --count 5 --seed 42 --output ./output/comfort_after --theme colored
```

**Step 2: Visually inspect SVGs**

Open the generated SVGs in a browser and compare against reference files in `docs/svg/`.

Check:
- Windows visible on exterior walls
- No door arc collisions
- Furniture placed sensibly (against walls, not blocking doors)
- SVG structure matches (background path, room groups, mebel, floor)
- Doors have proper arc curves
- Windows rendered as line segments

**Step 3: Run full test suite**

Run: `pytest -v`
Expected: All pass

**Step 4: Final commit**

```
git add -A
git commit -m "chore: visual quality improvements complete — placement fixes + renderer overhaul"
```
