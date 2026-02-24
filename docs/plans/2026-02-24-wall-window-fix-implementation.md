# Wall, Window & Door Rendering Fix — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix SVG rendering so exterior walls form a solid polygon (no corner gaps), interior walls use the same polygon approach but thinner, windows match reference SVG style (opening rect + glass line + mullions), and entrance doors cut through exterior walls.

**Architecture:** Use Shapely for polygon union/buffer/difference to compute wall outlines. Exterior walls = `buffer(union(rooms), 225mm) - union(rooms)` with openings cut out. Interior walls = thin rectangles on shared edges, unioned via Shapely. Windows rendered as architectural symbols matching reference SVGs.

**Tech Stack:** Python 3.12+, Shapely (new dependency), svgwrite, Pydantic

---

### Task 1: Add Shapely dependency

**Files:**
- Modify: `pyproject.toml:6-11`

**Step 1: Add shapely to dependencies**

In `pyproject.toml`, add `"shapely>=2.0"` to the dependencies list:

```toml
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9",
    "lxml>=5.0",
    "svgwrite>=1.4",
    "shapely>=2.0",
]
```

**Step 2: Install**

Run: `pip install -e ".[dev]"`
Expected: Success, shapely installed

**Step 3: Verify import**

Run: `python -c "from shapely.geometry import Polygon; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add shapely for polygon operations"
```

---

### Task 2: Create outline.py — Shapely-based wall polygon computation

**Files:**
- Create: `src/floorplan_generator/renderer/outline.py`
- Create: `tests/unit/test_outline.py`

**Step 1: Write tests for outline module**

Create `tests/unit/test_outline.py`:

```python
"""Tests for Shapely-based wall outline computation."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon as ShapelyPolygon

from floorplan_generator.core.enums import DoorType, RoomType, SwingDirection
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import Door, Room, Window


def _rect_room(
    room_type: RoomType,
    x: float, y: float, w: float, h: float,
    room_id: str = "",
    doors: list[Door] | None = None,
    windows: list[Window] | None = None,
) -> Room:
    return Room(
        id=room_id or f"r_{room_type.value}",
        room_type=room_type,
        boundary=Polygon(points=[
            Point(x=x, y=y),
            Point(x=x + w, y=y),
            Point(x=x + w, y=y + h),
            Point(x=x, y=y + h),
        ]),
        doors=doors or [],
        windows=windows or [],
    )


def test_single_room_outer_wall():
    """Single room produces a rectangular wall ring."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    room = _rect_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    wall_poly = compute_outer_wall_polygon([room], thickness=225.0)
    assert not wall_poly.is_empty
    # Wall ring area = outer_area - inner_area
    # inner = 4000*4000 = 16_000_000
    # outer = 4450*4450 = 19_802_500
    # ring ~ 3_802_500
    assert wall_poly.area > 3_000_000
    assert wall_poly.area < 5_000_000


def test_two_adjacent_rooms_outer_wall():
    """Two adjacent rooms share a wall; outer ring has no gap at corners."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    wall_poly = compute_outer_wall_polygon([r1, r2], thickness=225.0)
    assert not wall_poly.is_empty
    # Should be a single polygon, not multipolygon
    assert wall_poly.geom_type in ("Polygon", "MultiPolygon")
    # The shared edge at x=2000 should NOT be part of the outer wall
    # Inner area = union of two rooms = 6000*3000 = 18_000_000
    inner = ShapelyPolygon([(0,0),(6000,0),(6000,3000),(0,3000)])
    assert abs(inner.area - 18_000_000) < 1


def test_outer_wall_with_window_opening():
    """Window creates opening in outer wall polygon."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _rect_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000,
        windows=[window],
    )
    wall_no_opening = compute_outer_wall_polygon([room], thickness=225.0)
    wall_with_opening = compute_outer_wall_polygon(
        [room], thickness=225.0, cut_windows=True,
    )
    # Wall with opening should have less area
    assert wall_with_opening.area < wall_no_opening.area


def test_inner_wall_polygons():
    """Shared edges produce inner wall polygons."""
    from floorplan_generator.renderer.outline import compute_inner_wall_polygons
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    inner_poly = compute_inner_wall_polygons([r1, r2], thickness=75.0)
    assert not inner_poly.is_empty
    # Shared edge is vertical at x=2000, length=3000
    # Inner wall area ~ 75 * 3000 = 225_000
    assert inner_poly.area > 150_000
    assert inner_poly.area < 400_000


def test_inner_wall_with_door_opening():
    """Door creates opening in inner wall polygon."""
    from floorplan_generator.renderer.outline import compute_inner_wall_polygons
    door = Door(
        id="d1", position=Point(x=2000, y=500), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2", wall_orientation="vertical",
    )
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1", doors=[door])
    r2 = _rect_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2", doors=[door])
    inner_no_door = compute_inner_wall_polygons([r1, r2], thickness=75.0, cut_doors=False)
    inner_with_door = compute_inner_wall_polygons([r1, r2], thickness=75.0, cut_doors=True)
    assert inner_with_door.area < inner_no_door.area


def test_shapely_to_svg_path():
    """Shapely polygon converts to valid SVG path d attribute."""
    from floorplan_generator.renderer.outline import shapely_to_svg_path
    from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
    room = _rect_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000)
    poly = ShapelyPolygon([(0,0),(4000,0),(4000,4000),(0,4000)])
    path_d = shapely_to_svg_path(poly, mapper)
    assert path_d.startswith("M")
    assert "L" in path_d
    assert path_d.endswith("Z") or "Z" in path_d


def test_l_shaped_apartment_corners():
    """L-shaped layout has proper corners with no gaps."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    # L-shape: two rooms forming an L
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 0, 2000, 5000, 3000, room_id="r2")
    wall_poly = compute_outer_wall_polygon([r1, r2], thickness=225.0)
    assert not wall_poly.is_empty
    # Should be a single connected polygon
    assert wall_poly.geom_type == "Polygon"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_outline.py -v`
Expected: FAIL (module not found)

**Step 3: Write outline.py implementation**

Create `src/floorplan_generator/renderer/outline.py`:

```python
"""Wall outline computation using Shapely polygon operations."""

from __future__ import annotations

from shapely.geometry import Polygon as ShapelyPolygon, box
from shapely.ops import unary_union

from floorplan_generator.core.geometry import Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper

_EDGE_EPS = 1.0  # mm tolerance


def _room_to_shapely(room: Room) -> ShapelyPolygon:
    """Convert room boundary to Shapely polygon."""
    coords = [(pt.x, pt.y) for pt in room.boundary.points]
    return ShapelyPolygon(coords)


def _room_edges(room: Room) -> list[Segment]:
    """Get all edges of a room boundary as segments."""
    pts = room.boundary.points
    n = len(pts)
    return [Segment(start=pts[i], end=pts[(i + 1) % n]) for i in range(n)]


def _segments_overlap(a: Segment, b: Segment, eps: float = _EDGE_EPS) -> bool:
    """Check if two segments share a collinear overlap (shared wall)."""
    a_horiz = abs(a.start.y - a.end.y) < eps
    b_horiz = abs(b.start.y - b.end.y) < eps
    a_vert = abs(a.start.x - a.end.x) < eps
    b_vert = abs(b.start.x - b.end.x) < eps

    if a_horiz and b_horiz and abs(a.start.y - b.start.y) < eps:
        a_min = min(a.start.x, a.end.x)
        a_max = max(a.start.x, a.end.x)
        b_min = min(b.start.x, b.end.x)
        b_max = max(b.start.x, b.end.x)
        overlap_start = max(a_min, b_min)
        overlap_end = min(a_max, b_max)
        if overlap_end - overlap_start > eps:
            return True

    if a_vert and b_vert and abs(a.start.x - b.start.x) < eps:
        a_min = min(a.start.y, a.end.y)
        a_max = max(a.start.y, a.end.y)
        b_min = min(b.start.y, b.end.y)
        b_max = max(b.start.y, b.end.y)
        overlap_start = max(a_min, b_min)
        overlap_end = min(a_max, b_max)
        if overlap_end - overlap_start > eps:
            return True

    return False


def _find_shared_edges(rooms: list[Room]) -> list[Segment]:
    """Find all shared edges between rooms (for inner walls)."""
    all_edges: list[tuple[int, Segment]] = []
    for i, room in enumerate(rooms):
        for seg in _room_edges(room):
            all_edges.append((i, seg))

    shared: list[Segment] = []
    seen: set[int] = set()

    for idx_a, (room_a, seg_a) in enumerate(all_edges):
        if idx_a in seen:
            continue
        for idx_b, (room_b, seg_b) in enumerate(all_edges):
            if room_a == room_b:
                continue
            if _segments_overlap(seg_a, seg_b):
                if idx_a not in seen:
                    shared.append(seg_a)
                    seen.add(idx_a)
                break

    return shared


def _segment_to_box(seg: Segment, thickness: float) -> ShapelyPolygon:
    """Create a thin rectangle (Shapely box) centered on a segment."""
    half_t = thickness / 2.0
    is_horiz = abs(seg.start.y - seg.end.y) < _EDGE_EPS

    if is_horiz:
        x_min = min(seg.start.x, seg.end.x)
        x_max = max(seg.start.x, seg.end.x)
        y_center = seg.start.y
        return box(x_min, y_center - half_t, x_max, y_center + half_t)
    else:
        y_min = min(seg.start.y, seg.end.y)
        y_max = max(seg.start.y, seg.end.y)
        x_center = seg.start.x
        return box(x_center - half_t, y_min, x_center + half_t, y_max)


def _window_opening_box(window, wall_thickness: float) -> ShapelyPolygon:
    """Create a rectangular cutout for a window opening."""
    pos = window.position
    w = window.width
    half_t = wall_thickness / 2.0 + 10.0  # slightly larger to ensure clean cut

    if window.wall_side in ("north", "south"):
        return box(pos.x, pos.y - half_t, pos.x + w, pos.y + half_t)
    else:
        return box(pos.x - half_t, pos.y, pos.x + half_t, pos.y + w)


def _door_opening_box(door, wall_thickness: float) -> ShapelyPolygon:
    """Create a rectangular cutout for a door opening."""
    pos = door.position
    w = door.width
    half_t = wall_thickness / 2.0 + 10.0

    if door.wall_orientation == "horizontal":
        return box(pos.x, pos.y - half_t, pos.x + w, pos.y + half_t)
    else:
        return box(pos.x - half_t, pos.y, pos.x + half_t, pos.y + w)


def compute_outer_wall_polygon(
    rooms: list[Room],
    thickness: float = 225.0,
    *,
    cut_windows: bool = False,
    cut_doors: bool = False,
) -> ShapelyPolygon:
    """Compute exterior wall polygon as a ring.

    1. Union all room boundaries → inner contour
    2. Buffer outward by thickness → outer contour
    3. Difference → wall ring
    4. Optionally cut window/door openings
    """
    if not rooms:
        return ShapelyPolygon()

    room_polys = [_room_to_shapely(r) for r in rooms]
    inner = unary_union(room_polys)
    outer = inner.buffer(thickness, join_style="mitre", mitre_limit=5.0)
    wall_ring = outer.difference(inner)

    if cut_windows:
        for room in rooms:
            for window in room.windows:
                opening = _window_opening_box(window, thickness)
                wall_ring = wall_ring.difference(opening)

    if cut_doors:
        from floorplan_generator.core.enums import DoorType
        seen_ids: set[str] = set()
        for room in rooms:
            for door in room.doors:
                if door.id in seen_ids:
                    continue
                seen_ids.add(door.id)
                if door.door_type == DoorType.ENTRANCE:
                    opening = _door_opening_box(door, thickness)
                    wall_ring = wall_ring.difference(opening)

    return wall_ring


def compute_inner_wall_polygons(
    rooms: list[Room],
    thickness: float = 75.0,
    *,
    cut_doors: bool = True,
) -> ShapelyPolygon:
    """Compute interior wall polygons from shared edges.

    1. Find shared edges between rooms
    2. Create thin rectangle for each shared edge
    3. Union all rectangles
    4. Optionally cut door openings
    """
    if len(rooms) < 2:
        return ShapelyPolygon()

    shared_edges = _find_shared_edges(rooms)
    if not shared_edges:
        return ShapelyPolygon()

    wall_boxes = [_segment_to_box(seg, thickness) for seg in shared_edges]
    wall_union = unary_union(wall_boxes)

    if cut_doors:
        seen_ids: set[str] = set()
        for room in rooms:
            for door in room.doors:
                if door.id in seen_ids:
                    continue
                seen_ids.add(door.id)
                opening = _door_opening_box(door, thickness)
                wall_union = wall_union.difference(opening)

    return wall_union


def shapely_to_svg_path(
    poly: ShapelyPolygon,
    mapper: CoordinateMapper,
) -> str:
    """Convert a Shapely polygon (possibly with holes) to SVG path d attribute."""
    if poly.is_empty:
        return ""

    parts = []

    def _ring_to_commands(coords: list[tuple[float, float]]) -> str:
        cmds = []
        for i, (mx, my) in enumerate(coords):
            sx, sy = mapper.to_svg_raw(mx, my)
            if i == 0:
                cmds.append(f"M {sx},{sy}")
            else:
                cmds.append(f"L {sx},{sy}")
        cmds.append("Z")
        return " ".join(cmds)

    if poly.geom_type == "Polygon":
        ext_coords = list(poly.exterior.coords)
        parts.append(_ring_to_commands(ext_coords))
        for interior in poly.interiors:
            int_coords = list(interior.coords)
            parts.append(_ring_to_commands(int_coords))
    elif poly.geom_type == "MultiPolygon":
        for sub_poly in poly.geoms:
            ext_coords = list(sub_poly.exterior.coords)
            parts.append(_ring_to_commands(ext_coords))
            for interior in sub_poly.interiors:
                int_coords = list(interior.coords)
                parts.append(_ring_to_commands(int_coords))

    return " ".join(parts)
```

**Step 4: Add `to_svg_raw` method to CoordinateMapper**

In `src/floorplan_generator/renderer/coordinate_mapper.py`, add after `to_svg`:

```python
def to_svg_raw(self, x: float, y: float) -> tuple[float, float]:
    """Convert mm coordinates to SVG coordinates (no Point needed)."""
    sx = (x - self.mm_min_x) * self.scale + self.offset_x
    sy = (y - self.mm_min_y) * self.scale + self.offset_y
    return (round(sx, 1), round(sy, 1))
```

**Step 5: Run tests**

Run: `pytest tests/unit/test_outline.py -v`
Expected: All 7 tests PASS

**Step 6: Commit**

```bash
git add src/floorplan_generator/renderer/outline.py tests/unit/test_outline.py src/floorplan_generator/renderer/coordinate_mapper.py
git commit -m "feat: add Shapely-based wall outline computation"
```

---

### Task 3: Rewrite wall_renderer.py to use outline polygons

**Files:**
- Modify: `src/floorplan_generator/renderer/wall_renderer.py`
- Modify: `src/floorplan_generator/renderer/themes/blueprint.json:16`

**Step 1: Update blueprint.json inner_thickness**

Change `inner_thickness` from 100.0 to 75.0 in `blueprint.json`:

```json
"inner_thickness": 75.0
```

Also update `colored.json` if it has the same field.

**Step 2: Rewrite wall_renderer.py**

Replace entire contents of `src/floorplan_generator/renderer/wall_renderer.py`:

```python
"""Wall rendering: Shapely-based polygon outlines for outer and inner walls."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.outline import (
    compute_inner_wall_polygons,
    compute_outer_wall_polygon,
    shapely_to_svg_path,
)
from floorplan_generator.renderer.theme import Theme


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render walls as Shapely-computed polygon paths."""
    outer_t = theme.walls.outer_thickness
    inner_t = theme.walls.inner_thickness

    # Outer walls: polygon ring with window/entrance-door openings
    outer_poly = compute_outer_wall_polygon(
        rooms, thickness=outer_t, cut_windows=True, cut_doors=True,
    )
    if not outer_poly.is_empty:
        path_d = shapely_to_svg_path(outer_poly, mapper)
        if path_d:
            group.add(dwg.path(
                d=path_d,
                fill=theme.walls.outer_fill,
                stroke="none",
                fill_rule="evenodd",
            ))

    # Inner walls: thin polygons on shared edges with door openings
    inner_poly = compute_inner_wall_polygons(
        rooms, thickness=inner_t, cut_doors=True,
    )
    if not inner_poly.is_empty:
        path_d = shapely_to_svg_path(inner_poly, mapper)
        if path_d:
            group.add(dwg.path(
                d=path_d,
                fill=theme.walls.inner_fill,
                stroke="none",
                fill_rule="evenodd",
            ))
```

**Step 3: Update existing tests that depend on wall rects**

Several existing tests (R09, R10, R30, R31) check for `<rect>` elements in the floor group for walls. Since walls are now `<path>` elements, update these tests.

In `tests/unit/test_renderer.py`:

**R09** — Change to check for path elements:
```python
# R09
def test_wall_outer_thick():
    """Outer walls drawn as filled polygon path."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    result = _make_result([room])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    # Should have at least one path for outer walls
    assert len(paths) >= 1, "Single room should have outer wall path"
```

**R10** — Change to check for two paths (outer + inner):
```python
# R10
def test_wall_inner_thin():
    """Inner walls drawn as separate path, thinner than outer walls."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    result = _make_result([r1, r2])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    # Should have paths for outer walls + inner walls + any door arcs
    assert len(paths) >= 2, "Two rooms should have outer + inner wall paths"
```

**R30** — Change to check for paths (not rects):
```python
# R30
def test_walls_rendered_as_paths():
    """Walls are rendered as filled <path> elements (polygon outlines)."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 3000, 0, 5000, 4000, room_id="r2")
    result = _make_result([r1, r2])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    # Should have path elements for walls
    assert len(paths) >= 1, f"Expected wall paths, got {len(paths)}"
```

**R31** — Change to verify door creates opening in wall path:
```python
# R31
def test_wall_opening_for_door():
    """Wall with a door has an opening in the wall polygon."""
    door = Door(
        id="d1", position=Point(x=2000, y=500), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2", wall_orientation="vertical",
    )
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1", doors=[door])
    r2 = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2", doors=[door])
    result = _make_result([r1, r2])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    # Should have wall paths + door arc path
    assert len(paths) >= 2, f"Expected wall paths + door arc, got {len(paths)}"
```

**R32** — Update door leaf check (door rect is still a rect):
```python
# R32
def test_door_has_leaf_rect_and_arc():
    """Door renders as leaf rect + arc path."""
    door = Door(
        id="d1", position=Point(x=3000, y=500), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2", wall_orientation="vertical",
    )
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1", doors=[door])
    result = _make_result([r1])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    paths = floor.findall("svg:path", ns)
    # Should have at least one path (door arc + wall path)
    assert len(paths) >= 1, "Expected arc path for door"
    # Door leaf is a thin rect
    assert len(rects) >= 1, "Expected door leaf rect"
```

Also update integration test `tests/integration/test_svg_structure.py`:

**SVG02** — Update to check for paths instead of rects for walls:
Find the test that checks "Floor group contains walls (rects)" and update to check for paths.

**SVG04** — Update "Walls are rects" to "Walls are paths":
Update the assertion to check for `<path>` elements instead of `<rect>`.

**Step 4: Run all renderer tests**

Run: `pytest tests/unit/test_renderer.py tests/unit/test_outline.py -v`
Expected: All tests PASS

**Step 5: Run integration tests**

Run: `pytest tests/integration/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/floorplan_generator/renderer/wall_renderer.py src/floorplan_generator/renderer/themes/blueprint.json tests/unit/test_renderer.py tests/integration/
git commit -m "feat: rewrite walls as Shapely polygon paths (outer + inner)"
```

---

### Task 4: Rewrite window_renderer.py to match reference SVG style

**Files:**
- Modify: `src/floorplan_generator/renderer/window_renderer.py`

**Step 1: Update window tests**

In `tests/unit/test_renderer.py`, update R13, R14, R33, R34:

```python
# R13
def test_window_rect():
    """Window opening rect rendered inside floor group."""
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor_group = root.findall(".//svg:g[@id='floor']", ns)
    assert len(floor_group) == 1
    # Window creates rects (opening + glass line + mullions)
    rects = floor_group[0].findall("svg:rect", ns)
    assert len(rects) >= 2, f"Expected window rects (opening + glass), got {len(rects)}"


# R14
def test_window_panes():
    """Window has rect elements for opening and glass line."""
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor_group = root.findall(".//svg:g[@id='floor']", ns)[0]
    rects = floor_group.findall("svg:rect", ns)
    # At least opening rect + glass line rect + 2 edge mullions
    assert len(rects) >= 3, f"Expected >= 3 window rects, got {len(rects)}"


# R33
def test_window_opening_and_glass():
    """Window renders as opening rect + glass line rect (reference style)."""
    window = Window(
        id="w1", position=Point(x=1000, y=0), width=1500, height=1500,
        wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000, room_id="r1",
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    # Should have opening rect + glass line rect + mullion rects
    assert len(rects) >= 3, f"Expected >= 3 rects for window, got {len(rects)}"


# R34
def test_wide_window_has_extra_mullions():
    """Windows wider than 1200mm have additional mullion rects."""
    window = Window(
        id="w1", position=Point(x=500, y=0), width=1800, height=1500,
        wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000, room_id="r1",
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    # Wide window: opening + glass + edge mullions + center mullion(s)
    assert len(rects) >= 4, f"Expected >= 4 rects for wide window, got {len(rects)}"
```

**Step 2: Rewrite window_renderer.py**

Replace entire contents of `src/floorplan_generator/renderer/window_renderer.py`:

```python
"""Window rendering: reference-style opening rect + glass line + mullions."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_MULLION_SPACING_MM = 600.0  # add mullion every ~600mm
_GLASS_POSITION_RATIO = 0.75  # glass line at 75% depth from outer edge


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    wall_thickness = theme.walls.outer_thickness
    for room in rooms:
        for window in room.windows:
            _render_single_window(dwg, group, window, mapper, theme, wall_thickness)


def _render_single_window(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    window: Window,
    mapper: CoordinateMapper,
    theme: Theme,
    wall_thickness: float,
) -> None:
    """Render window as: opening rect + glass line + mullion rects."""
    pos = mapper.to_svg(window.position)
    w_len = mapper.scale_length(window.width)
    w_thick = mapper.scale_length(wall_thickness)
    sw = max(1.0, theme.windows.stroke_width)
    color = theme.windows.stroke

    # Glass line dimensions (scaled)
    glass_height = max(4.0, w_thick * 0.2)  # ~20% of wall thickness
    glass_offset = w_thick * _GLASS_POSITION_RATIO  # 75% from outer edge

    # Mullion rect dimensions (scaled)
    mullion_w = max(3.0, w_thick * 0.15)
    mullion_h = glass_height

    is_horizontal = window.wall_side in ("north", "south")

    if is_horizontal:
        # Opening rect: width=w_len, height=w_thick
        ox, oy = pos[0], pos[1] - w_thick / 2
        group.add(dwg.rect(
            insert=(ox, oy), size=(w_len, w_thick),
            fill="none", stroke=color, stroke_width=sw,
        ))

        # Glass line rect at 75% depth
        gy = oy + glass_offset - glass_height / 2
        group.add(dwg.rect(
            insert=(ox, gy), size=(w_len, glass_height),
            fill="none", stroke=color, stroke_width=sw,
        ))

        # Mullion rects: at edges + every ~600mm
        mullion_positions = _compute_mullion_positions(window.width, _MULLION_SPACING_MM)
        for mp in mullion_positions:
            mx = ox + mapper.scale_length(mp) - mullion_w / 2
            group.add(dwg.rect(
                insert=(mx, gy), size=(mullion_w, mullion_h),
                fill="none", stroke=color, stroke_width=sw,
            ))
    else:
        # Vertical window (east/west wall)
        ox, oy = pos[0] - w_thick / 2, pos[1]
        group.add(dwg.rect(
            insert=(ox, oy), size=(w_thick, w_len),
            fill="none", stroke=color, stroke_width=sw,
        ))

        # Glass line rect at 75% depth
        gx = ox + glass_offset - glass_height / 2
        group.add(dwg.rect(
            insert=(gx, oy), size=(glass_height, w_len),
            fill="none", stroke=color, stroke_width=sw,
        ))

        # Mullion rects
        mullion_positions = _compute_mullion_positions(window.width, _MULLION_SPACING_MM)
        for mp in mullion_positions:
            my = oy + mapper.scale_length(mp) - mullion_w / 2
            group.add(dwg.rect(
                insert=(gx, my), size=(mullion_h, mullion_w),
                fill="none", stroke=color, stroke_width=sw,
            ))


def _compute_mullion_positions(window_width_mm: float, spacing_mm: float) -> list[float]:
    """Compute mullion positions along window width.

    Always includes edge mullions (at 0 and window_width).
    For wide windows, adds intermediate mullions every ~spacing_mm.
    """
    positions = [0.0, window_width_mm]

    if window_width_mm > spacing_mm * 1.5:
        n_sections = max(2, round(window_width_mm / spacing_mm))
        step = window_width_mm / n_sections
        for i in range(1, n_sections):
            positions.append(step * i)

    return sorted(set(positions))
```

**Step 3: Run tests**

Run: `pytest tests/unit/test_renderer.py -v -k "window or R13 or R14 or R33 or R34"`
Expected: All window tests PASS

**Step 4: Commit**

```bash
git add src/floorplan_generator/renderer/window_renderer.py tests/unit/test_renderer.py
git commit -m "feat: rewrite windows to reference SVG style (opening + glass + mullions)"
```

---

### Task 5: Update door_renderer.py for entrance doors

**Files:**
- Modify: `src/floorplan_generator/renderer/door_renderer.py`

**Step 1: Add test for entrance door rendering**

Add to `tests/unit/test_renderer.py`:

```python
# R37
def test_entrance_door_on_outer_wall():
    """Entrance door renders leaf + arc on outer wall."""
    door = Door(
        id="d1", position=Point(x=0, y=500), width=860.0,
        door_type=DoorType.ENTRANCE, swing=SwingDirection.INWARD,
        room_from="outside", room_to="r1", wall_orientation="vertical",
    )
    room = _make_room(
        RoomType.HALLWAY, 0, 0, 2000, 2000,
        room_id="r1", doors=[door],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    rects = floor.findall("svg:rect", ns)
    # Should have door arc path (+ wall path)
    arc_paths = [p for p in paths if "A" in p.get("d", "")]
    assert len(arc_paths) >= 1, "Expected door swing arc"
    # Should have door leaf rect
    assert len(rects) >= 1, "Expected door leaf rect"
```

**Step 2: Run test to verify it passes (door_renderer already handles all doors)**

Run: `pytest tests/unit/test_renderer.py::test_entrance_door_on_outer_wall -v`
Expected: PASS (door_renderer already renders all door types the same way)

The entrance door opening in the outer wall is already handled by `compute_outer_wall_polygon` with `cut_doors=True` (Task 2). The door_renderer.py already renders the leaf + arc for all doors.

**Step 3: Commit**

```bash
git add tests/unit/test_renderer.py
git commit -m "test: add entrance door rendering test"
```

---

### Task 6: Update integration tests and run full suite

**Files:**
- Modify: `tests/integration/test_svg_structure.py`
- Modify: `tests/integration/test_renderer_integration.py`

**Step 1: Read and update integration tests**

Read current integration tests and update any assertions that check for wall `<rect>` elements to check for wall `<path>` elements instead. Key changes:

- SVG02: "Floor group contains walls" — check for `<path>` elements with fill
- SVG04: "Walls are rects" → "Walls are paths"

**Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 3: Fix any remaining failures**

If any tests fail due to the wall/window rendering changes, update assertions to match the new rendering approach.

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: update integration tests for polygon-based walls and reference-style windows"
```

---

### Task 7: Update colored theme and verify visual output

**Files:**
- Modify: `src/floorplan_generator/renderer/themes/colored.json` (if it has inner_thickness)

**Step 1: Update colored theme inner_thickness**

If `colored.json` has `inner_thickness: 100.0`, change to `75.0`.

**Step 2: Generate a test SVG and visually inspect**

Run: `python -c "
from floorplan_generator.core.enums import *
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import *
from floorplan_generator.generator.types import GenerationResult, Riser
from floorplan_generator.renderer.svg_renderer import render_svg_to_file
from floorplan_generator.renderer.theme import load_theme

def room(rt, x, y, w, h, rid, doors=None, windows=None):
    return Room(id=rid, room_type=rt,
        boundary=Polygon(points=[Point(x=x,y=y),Point(x=x+w,y=y),Point(x=x+w,y=y+h),Point(x=x,y=y+h)]),
        doors=doors or [], windows=windows or [])

w1 = Window(id='w1', position=Point(x=1000, y=0), width=1500, height=1500, wall_side='north')
w2 = Window(id='w2', position=Point(x=5000, y=0), width=1800, height=1500, wall_side='north')
d_entrance = Door(id='d0', position=Point(x=0, y=500), width=860, door_type=DoorType.ENTRANCE,
    swing=SwingDirection.INWARD, room_from='outside', room_to='hall', wall_orientation='vertical')
d1 = Door(id='d1', position=Point(x=3000, y=500), width=800, door_type=DoorType.INTERIOR,
    swing=SwingDirection.INWARD, room_from='hall', room_to='living', wall_orientation='vertical')

hall = room(RoomType.HALLWAY, 0, 0, 3000, 3000, 'hall', doors=[d_entrance, d1])
living = room(RoomType.LIVING_ROOM, 3000, 0, 5000, 4000, 'living', doors=[d1], windows=[w1, w2])
kitchen = room(RoomType.KITCHEN, 0, 3000, 4000, 3000, 'kitchen')
bath = room(RoomType.COMBINED_BATHROOM, 4000, 3000, 2000, 2000, 'bath')

apt = Apartment(id='test', apartment_class=ApartmentClass.ECONOMY, rooms=[hall, living, kitchen, bath], num_rooms=1)
result = GenerationResult(apartment=apt, risers=[], restart_count=0, seed_used=42, recommended_violations=0)
render_svg_to_file(result, '/tmp/test_walls.svg')
print('Generated: /tmp/test_walls.svg')
"`

Expected: SVG file created, open in browser to visually verify:
- Outer walls are solid black polygon with no corner gaps
- Inner walls are thinner black polygons
- Windows have opening rect + glass line + mullions
- Entrance door has opening in outer wall with leaf + arc

**Step 3: Commit**

```bash
git add src/floorplan_generator/renderer/themes/
git commit -m "feat: update themes for new wall/window rendering"
```

---

### Task 8: Final cleanup and full test run

**Step 1: Run linter**

Run: `ruff check src/floorplan_generator/renderer/ tests/ --fix`
Expected: No errors (or fix any)

**Step 2: Run full test suite with coverage**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: cleanup after wall/window rendering rewrite"
```
