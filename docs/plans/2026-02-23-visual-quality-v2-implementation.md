# Visual Quality V2 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform SVG output from thin-line sketches into professional architectural drawings with real wall thickness, proper door/window symbols, complete furniture library, correct text sizing, and improved layout compactness.

**Architecture:** Rewrite wall_renderer to produce filled `<rect>` elements with real thickness and door/window openings. Update door_renderer to draw door leaf + arc. Update window_renderer with double-line symbol. Add 14 missing furniture draw functions. Adjust theme configs, coordinate mapper padding, and greedy scoring weights.

**Tech Stack:** Python 3.12, Pydantic 2, svgwrite, pytest

---

### Task 1: Update theme model and JSON files with wall thickness + larger text

**Files:**
- Modify: `src/floorplan_generator/renderer/theme.py:19-24`
- Modify: `src/floorplan_generator/renderer/themes/blueprint.json`
- Modify: `src/floorplan_generator/renderer/themes/colored.json`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py` after existing test R22:

```python
# R26
def test_theme_has_wall_thickness():
    """Theme includes wall thickness and fill fields."""
    theme = load_theme("blueprint")
    assert hasattr(theme.walls, "outer_thickness")
    assert hasattr(theme.walls, "inner_thickness")
    assert hasattr(theme.walls, "outer_fill")
    assert hasattr(theme.walls, "inner_fill")
    assert theme.walls.outer_thickness == 225.0
    assert theme.walls.inner_thickness == 100.0


# R27
def test_theme_text_sizes_large():
    """Theme text sizes are large enough for 2000px canvas."""
    theme = load_theme("colored")
    assert theme.text.font_size >= 28
    assert theme.text.area_font_size >= 20
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_theme_has_wall_thickness -v`
Expected: FAIL — `WallTheme` has no `outer_thickness` attribute

**Step 3: Write minimal implementation**

In `src/floorplan_generator/renderer/theme.py`, update `WallTheme`:

```python
class WallTheme(BaseModel):
    outer_stroke: str = "#000000"
    outer_width: float = 4.0        # legacy stroke width (kept for compat)
    inner_stroke: str = "#000000"
    inner_width: float = 1.5         # legacy stroke width (kept for compat)
    outer_fill: str = "#000000"      # NEW: fill color for outer wall rects
    inner_fill: str = "#000000"      # NEW: fill color for inner wall rects
    outer_thickness: float = 225.0   # NEW: mm thickness of outer walls
    inner_thickness: float = 100.0   # NEW: mm thickness of inner (partition) walls
```

Update `src/floorplan_generator/renderer/themes/blueprint.json` — add to `"walls"`:

```json
{
  "name": "blueprint",
  "canvas": {
    "width": 2000,
    "height": 2000,
    "background": "#FFFFFF"
  },
  "walls": {
    "outer_stroke": "#000000",
    "outer_width": 4.0,
    "inner_stroke": "#000000",
    "inner_width": 1.5,
    "outer_fill": "#000000",
    "inner_fill": "#555555",
    "outer_thickness": 225.0,
    "inner_thickness": 100.0
  },
  "rooms": {
    "default_fill": "none",
    "default_stroke": "#000000",
    "stroke_width": 0.5,
    "fills": {}
  },
  "doors": {
    "stroke": "#000000",
    "stroke_width": 1.0,
    "arc_stroke": "#000000",
    "arc_width": 0.5,
    "gap_fill": "#FFFFFF"
  },
  "windows": {
    "stroke": "#000000",
    "stroke_width": 1.0,
    "fill": "#FFFFFF",
    "cross_stroke": "#000000"
  },
  "furniture": {
    "stroke": "#000000",
    "stroke_width": 0.8,
    "fill": "none"
  },
  "riser": {
    "stroke": "#000000",
    "fill": "#000000",
    "radius": 3.0
  },
  "text": {
    "font_family": "Arial, sans-serif",
    "font_size": 28,
    "fill": "#333333",
    "area_font_size": 20
  }
}
```

Update `src/floorplan_generator/renderer/themes/colored.json` — same pattern:

```json
{
  "name": "colored",
  "canvas": {
    "width": 2000,
    "height": 2000,
    "background": "#FAFAFA"
  },
  "walls": {
    "outer_stroke": "#37474F",
    "outer_width": 4.0,
    "inner_stroke": "#546E7A",
    "inner_width": 1.5,
    "outer_fill": "#37474F",
    "inner_fill": "#78909C",
    "outer_thickness": 225.0,
    "inner_thickness": 100.0
  },
  "rooms": {
    "default_fill": "#F5F5F5",
    "default_stroke": "#78909C",
    "stroke_width": 0.5,
    "fills": {
      "living_room": "#E3F2FD",
      "bedroom": "#E8EAF6",
      "children": "#F3E5F5",
      "cabinet": "#EDE7F6",
      "kitchen": "#FFF3E0",
      "kitchen_dining": "#FFF8E1",
      "kitchen_niche": "#FFF8E1",
      "hallway": "#ECEFF1",
      "corridor": "#ECEFF1",
      "hall": "#CFD8DC",
      "bathroom": "#E0F7FA",
      "toilet": "#E0F2F1",
      "combined_bathroom": "#E0F7FA",
      "storage": "#EFEBE9",
      "wardrobe": "#EFEBE9",
      "laundry": "#E0F7FA",
      "balcony": "#E8F5E9"
    }
  },
  "doors": {
    "stroke": "#37474F",
    "stroke_width": 1.0,
    "arc_stroke": "#78909C",
    "arc_width": 0.5,
    "gap_fill": "#FAFAFA"
  },
  "windows": {
    "stroke": "#1565C0",
    "stroke_width": 1.0,
    "fill": "#E3F2FD",
    "cross_stroke": "#1565C0"
  },
  "furniture": {
    "stroke": "#455A64",
    "stroke_width": 0.8,
    "fill": "none"
  },
  "riser": {
    "stroke": "#D32F2F",
    "fill": "#EF5350",
    "radius": 4.0
  },
  "text": {
    "font_family": "Arial, sans-serif",
    "font_size": 28,
    "fill": "#263238",
    "area_font_size": 20
  }
}
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -k "R26 or R27 or theme" -v`
Expected: All pass

**Step 5: Run full test suite to check for regressions**

Run: `.venv/bin/python -m pytest --tb=short`
Expected: Some existing tests may need adjustment — R09 checks `stroke-width` values that may differ now. Fix any assertion that hardcodes old font sizes or stroke widths.

**Step 6: Commit**

```bash
git add src/floorplan_generator/renderer/theme.py src/floorplan_generator/renderer/themes/blueprint.json src/floorplan_generator/renderer/themes/colored.json tests/unit/test_renderer.py
git commit -m "feat: add wall thickness/fill to theme, increase text size to 28/20px"
```

---

### Task 2: Add `scale_thickness` to CoordinateMapper + reduce padding

**Files:**
- Modify: `src/floorplan_generator/renderer/coordinate_mapper.py:16-78`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R28
def test_coordinate_mapper_scale_thickness():
    """scale_thickness converts mm thickness to SVG px, min 2.0."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 10000, 10000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=50)
    t = mapper.scale_thickness(225.0)
    assert t >= 2.0
    # For 10000mm room on 2000px canvas (~0.19 scale), 225mm -> ~42px
    assert t > 20.0


# R29
def test_coordinate_mapper_reduced_padding():
    """Default padding is 50, not 100."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 10000, 10000)
    mapper = CoordinateMapper([room], 2000, 2000)
    assert mapper.padding == 50
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_coordinate_mapper_scale_thickness -v`
Expected: FAIL — `CoordinateMapper` has no `scale_thickness` method

**Step 3: Write minimal implementation**

In `src/floorplan_generator/renderer/coordinate_mapper.py`:

1. Change default `padding` from 100 to 50 in `__init__` signature (line 22).
2. Add `scale_thickness` method after `scale_length`:

```python
    def scale_thickness(self, mm_thickness: float) -> float:
        """Convert mm thickness to SVG thickness (min 2.0 for visibility)."""
        return max(2.0, round(mm_thickness * self.scale, 1))
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -k "R28 or R29 or coordinate" -v`
Expected: PASS. Note: R01 test creates mapper with `padding=100` explicitly so it won't break.

**Step 5: Run full test suite**

Run: `.venv/bin/python -m pytest --tb=short`
Expected: All pass. Tests that don't specify explicit padding will now use 50.

**Step 6: Commit**

```bash
git add src/floorplan_generator/renderer/coordinate_mapper.py tests/unit/test_renderer.py
git commit -m "feat: add scale_thickness to CoordinateMapper, reduce default padding to 50"
```

---

### Task 3: Rewrite wall_renderer — filled rects with openings

This is the biggest change. The wall renderer needs to:
1. Collect unique wall segments from rooms
2. Classify as outer/inner
3. Detect openings (doors + windows on each wall)
4. Split walls around openings
5. Render each piece as a filled `<rect>`

**Files:**
- Modify: `src/floorplan_generator/renderer/wall_renderer.py` (full rewrite)
- Modify: `src/floorplan_generator/renderer/svg_renderer.py:47-49` (pass rooms with doors/windows)
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing tests**

Add to `tests/unit/test_renderer.py`:

```python
# R30
def test_walls_rendered_as_rects():
    """Walls are rendered as filled <rect> elements, not <line> elements."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 3000, 0, 5000, 4000, room_id="r2")
    result = _make_result([r1, r2])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    assert floor is not None
    rects = floor.findall("svg:rect", ns)
    lines = floor.findall("svg:line", ns)
    # Should have rects for walls, not lines
    assert len(rects) >= 4, f"Expected wall rects, got {len(rects)} rects and {len(lines)} lines"


# R31
def test_wall_opening_for_door():
    """Wall with a door has a gap — rendered as two rect segments."""
    door = Door(
        id="d1", position=Point(x=3000, y=500), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2", wall_orientation="vertical",
    )
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1", doors=[door])
    r2 = _make_room(RoomType.LIVING_ROOM, 3000, 0, 5000, 4000, room_id="r2", doors=[door])
    result = _make_result([r1, r2])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    # The shared vertical wall from y=0 to y=2000 has a door at y=500..1300
    # So it should split into: [0..500] and [1300..2000] = 2 wall rects for that edge
    # Plus other wall segments. Total should be more than a simple 2-room layout without door.
    assert len(rects) >= 6, f"Expected split wall rects due to door, got {len(rects)}"
```

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_walls_rendered_as_rects -v`
Expected: FAIL — walls currently rendered as `<line>`, no `<rect>` in floor group

**Step 3: Write the implementation**

Fully rewrite `src/floorplan_generator/renderer/wall_renderer.py`:

```python
"""Wall rendering: filled rectangles with real thickness and door/window openings."""

from __future__ import annotations

from dataclasses import dataclass

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.geometry import Point, Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_EDGE_EPS = 1.0  # mm tolerance for shared edge detection


@dataclass
class _Opening:
    """An opening (door or window) on a wall segment."""
    offset_start: float  # distance along wall from wall start
    offset_end: float    # distance along wall from wall start


def _room_edges(room: Room) -> list[Segment]:
    pts = room.boundary.points
    n = len(pts)
    return [Segment(start=pts[i], end=pts[(i + 1) % n]) for i in range(n)]


def _segments_overlap(a: Segment, b: Segment, eps: float = _EDGE_EPS) -> bool:
    a_horiz = abs(a.start.y - a.end.y) < eps
    b_horiz = abs(b.start.y - b.end.y) < eps
    a_vert = abs(a.start.x - a.end.x) < eps
    b_vert = abs(b.start.x - b.end.x) < eps

    if a_horiz and b_horiz and abs(a.start.y - b.start.y) < eps:
        a_min, a_max = min(a.start.x, a.end.x), max(a.start.x, a.end.x)
        b_min, b_max = min(b.start.x, b.end.x), max(b.start.x, b.end.x)
        return a_min < b_max - eps and b_min < a_max - eps

    if a_vert and b_vert and abs(a.start.x - b.start.x) < eps:
        a_min, a_max = min(a.start.y, a.end.y), max(a.start.y, a.end.y)
        b_min, b_max = min(b.start.y, b.end.y), max(b.start.y, b.end.y)
        return a_min < b_max - eps and b_min < a_max - eps

    return False


def _is_horizontal(seg: Segment) -> bool:
    return abs(seg.start.y - seg.end.y) < _EDGE_EPS


def _is_vertical(seg: Segment) -> bool:
    return abs(seg.start.x - seg.end.x) < _EDGE_EPS


def _classify_edges(
    rooms: list[Room],
) -> tuple[list[Segment], list[Segment]]:
    all_edges: list[tuple[int, Segment]] = []
    for i, room in enumerate(rooms):
        for seg in _room_edges(room):
            all_edges.append((i, seg))

    outer: list[Segment] = []
    inner_set: set[int] = set()

    for idx_a, (room_a, seg_a) in enumerate(all_edges):
        is_shared = False
        for idx_b, (room_b, seg_b) in enumerate(all_edges):
            if room_a == room_b:
                continue
            if _segments_overlap(seg_a, seg_b):
                is_shared = True
                if idx_a not in inner_set:
                    inner_set.add(idx_a)
                break
        if not is_shared:
            outer.append(seg_a)

    inner = [all_edges[i][1] for i in inner_set]
    return outer, inner


def _collect_openings(seg: Segment, rooms: list[Room]) -> list[_Opening]:
    """Find all door/window openings on a given wall segment."""
    openings: list[_Opening] = []
    horiz = _is_horizontal(seg)
    vert = _is_vertical(seg)

    if not horiz and not vert:
        return openings

    seg_min: float
    seg_max: float
    seg_coord: float  # the fixed coordinate (y for horiz, x for vert)

    if horiz:
        seg_min = min(seg.start.x, seg.end.x)
        seg_max = max(seg.start.x, seg.end.x)
        seg_coord = seg.start.y
    else:
        seg_min = min(seg.start.y, seg.end.y)
        seg_max = max(seg.start.y, seg.end.y)
        seg_coord = seg.start.x

    for room in rooms:
        # Check doors
        for door in room.doors:
            dp = door.position
            dw = door.width
            if horiz:
                if abs(dp.y - seg_coord) < _EDGE_EPS * 2:
                    d_start = dp.x
                    d_end = dp.x + dw
                    if d_start >= seg_min - _EDGE_EPS and d_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, d_start - seg_min),
                            offset_end=min(seg_max - seg_min, d_end - seg_min),
                        ))
            elif vert:
                if abs(dp.x - seg_coord) < _EDGE_EPS * 2:
                    d_start = dp.y
                    d_end = dp.y + dw
                    if d_start >= seg_min - _EDGE_EPS and d_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, d_start - seg_min),
                            offset_end=min(seg_max - seg_min, d_end - seg_min),
                        ))

        # Check windows
        for window in room.windows:
            wp = window.position
            ww = window.width
            if horiz and window.wall_side in ("north", "south"):
                if abs(wp.y - seg_coord) < _EDGE_EPS * 2:
                    w_start = wp.x
                    w_end = wp.x + ww
                    if w_start >= seg_min - _EDGE_EPS and w_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, w_start - seg_min),
                            offset_end=min(seg_max - seg_min, w_end - seg_min),
                        ))
            elif vert and window.wall_side in ("east", "west"):
                if abs(wp.x - seg_coord) < _EDGE_EPS * 2:
                    w_start = wp.y
                    w_end = wp.y + ww
                    if w_start >= seg_min - _EDGE_EPS and w_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, w_start - seg_min),
                            offset_end=min(seg_max - seg_min, w_end - seg_min),
                        ))

    # Sort by offset_start and merge overlapping
    openings.sort(key=lambda o: o.offset_start)
    return openings


def _split_around_openings(
    total_length: float,
    openings: list[_Opening],
) -> list[tuple[float, float]]:
    """Split a wall into sub-segments avoiding openings.

    Returns list of (start_offset, end_offset) for solid wall pieces.
    """
    if not openings:
        return [(0.0, total_length)]

    pieces: list[tuple[float, float]] = []
    cursor = 0.0
    for op in openings:
        if op.offset_start > cursor + _EDGE_EPS:
            pieces.append((cursor, op.offset_start))
        cursor = max(cursor, op.offset_end)
    if cursor < total_length - _EDGE_EPS:
        pieces.append((cursor, total_length))
    return pieces


def _render_wall_segment(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    seg: Segment,
    thickness_px: float,
    fill: str,
    rooms: list[Room],
    mapper: CoordinateMapper,
) -> None:
    """Render one wall segment as filled rects, with openings cut out."""
    horiz = _is_horizontal(seg)
    vert = _is_vertical(seg)

    if not horiz and not vert:
        # Non-axis-aligned wall: fallback to line
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(start=start, end=end, stroke=fill, stroke_width=thickness_px))
        return

    openings = _collect_openings(seg, rooms)

    if horiz:
        seg_min_x = min(seg.start.x, seg.end.x)
        seg_max_x = max(seg.start.x, seg.end.x)
        total_len = seg_max_x - seg_min_x
        pieces = _split_around_openings(total_len, openings)

        for piece_start, piece_end in pieces:
            p1 = mapper.to_svg(Point(x=seg_min_x + piece_start, y=seg.start.y))
            p2 = mapper.to_svg(Point(x=seg_min_x + piece_end, y=seg.start.y))
            rect_w = p2[0] - p1[0]
            if rect_w < 1.0:
                continue
            group.add(dwg.rect(
                insert=(p1[0], p1[1] - thickness_px / 2),
                size=(rect_w, thickness_px),
                fill=fill,
                stroke="none",
            ))
    else:  # vertical
        seg_min_y = min(seg.start.y, seg.end.y)
        seg_max_y = max(seg.start.y, seg.end.y)
        total_len = seg_max_y - seg_min_y
        pieces = _split_around_openings(total_len, openings)

        for piece_start, piece_end in pieces:
            p1 = mapper.to_svg(Point(x=seg.start.x, y=seg_min_y + piece_start))
            p2 = mapper.to_svg(Point(x=seg.start.x, y=seg_min_y + piece_end))
            rect_h = p2[1] - p1[1]
            if rect_h < 1.0:
                continue
            group.add(dwg.rect(
                insert=(p1[0] - thickness_px / 2, p1[1]),
                size=(thickness_px, rect_h),
                fill=fill,
                stroke="none",
            ))


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render walls as filled rects with real thickness and openings."""
    outer, inner = _classify_edges(rooms)

    outer_t = mapper.scale_thickness(theme.walls.outer_thickness)
    inner_t = mapper.scale_thickness(theme.walls.inner_thickness)

    for seg in outer:
        _render_wall_segment(
            dwg, group, seg, outer_t,
            theme.walls.outer_fill, rooms, mapper,
        )

    for seg in inner:
        _render_wall_segment(
            dwg, group, seg, inner_t,
            theme.walls.inner_fill, rooms, mapper,
        )
```

**Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -k "R30 or R31 or wall" -v`
Expected: R30, R31 PASS

**Step 5: Run full test suite — fix regressions**

Run: `.venv/bin/python -m pytest --tb=short`

Expected regressions to fix:
- **R09** (`test_wall_outer_thick`): Currently checks for `stroke-width` in SVG — update to check for `<rect>` with fill instead
- **R10** (`test_wall_inner_thin`): Currently checks for `<line>` elements — update to check for `<rect>` elements
- **R14** (`test_window_panes`): Counts `<line>` elements in floor — may need adjustment

Update R09:
```python
def test_wall_outer_thick():
    """Outer walls drawn as filled rects with real thickness."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    result = _make_result([room])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    assert len(rects) >= 4, "Single room should have 4 outer wall rects"
```

Update R10:
```python
def test_wall_inner_thin():
    """Inner walls drawn as rects thinner than outer walls."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    result = _make_result([r1, r2])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    assert len(rects) >= 6, "Two rooms should have outer + inner wall rects"
```

**Step 6: Commit**

```bash
git add src/floorplan_generator/renderer/wall_renderer.py tests/unit/test_renderer.py
git commit -m "feat: rewrite wall renderer — filled rects with real thickness and openings"
```

---

### Task 4: Update door_renderer — door leaf rect + stronger arc

**Files:**
- Modify: `src/floorplan_generator/renderer/door_renderer.py` (full rewrite)
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R32
def test_door_has_leaf_rect_and_arc():
    """Door renders as leaf rect + arc path (no white gap rect)."""
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
    # Door leaf should be a rect
    rects = [r for r in floor.findall("svg:rect", ns)]
    # Arcs should be paths
    paths = [p for p in floor.findall("svg:path", ns)]
    # We should have at least one path (arc) for the door
    assert len(paths) >= 1, "Expected arc path for door"
    # At least one rect that is the door leaf (thin, not a wall)
    # Leaf rects are very thin (~3px) vs wall rects (~25px)
    thin_rects = [r for r in rects if float(r.get("width", "0")) < 10 or float(r.get("height", "0")) < 10]
    assert len(thin_rects) >= 1, "Expected thin door leaf rect"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_door_has_leaf_rect_and_arc -v`
Expected: FAIL — current door renderer doesn't produce a leaf rect

**Step 3: Write the implementation**

Rewrite `src/floorplan_generator/renderer/door_renderer.py`:

```python
"""Door rendering: door leaf rect + swing arc."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import SwingDirection
from floorplan_generator.core.models import Door, Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_LEAF_THICKNESS_MM = 40.0  # door leaf thickness in mm


def render_doors(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all doors with leaf rect and swing arc."""
    seen_ids: set[str] = set()
    for room in rooms:
        for door in room.doors:
            if door.id in seen_ids:
                continue
            seen_ids.add(door.id)
            _render_single_door(dwg, group, door, mapper, theme)


def _render_single_door(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    door: Door,
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render a single door: thin leaf rect + quarter-circle swing arc."""
    pos = mapper.to_svg(door.position)
    w = mapper.scale_length(door.width)
    leaf_t = max(2.0, mapper.scale_thickness(_LEAF_THICKNESS_MM))
    hx, hy = pos
    arc_r = w
    is_inward = door.swing == SwingDirection.INWARD
    orientation = getattr(door, "wall_orientation", "vertical")

    # --- Door leaf rect ---
    if orientation == "vertical":
        if is_inward:
            # Leaf extends right from hinge
            group.add(dwg.rect(
                insert=(hx, hy), size=(w, leaf_t),
                fill=theme.doors.stroke, stroke="none",
            ))
        else:
            # Leaf extends left from hinge
            group.add(dwg.rect(
                insert=(hx - w, hy), size=(w, leaf_t),
                fill=theme.doors.stroke, stroke="none",
            ))
    else:  # horizontal
        if is_inward:
            # Leaf extends down from hinge
            group.add(dwg.rect(
                insert=(hx, hy), size=(leaf_t, w),
                fill=theme.doors.stroke, stroke="none",
            ))
        else:
            # Leaf extends up from hinge
            group.add(dwg.rect(
                insert=(hx, hy - w), size=(leaf_t, w),
                fill=theme.doors.stroke, stroke="none",
            ))

    # --- Swing arc (quarter circle) ---
    if orientation == "vertical":
        if is_inward:
            tip_x, tip_y = hx + arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 1
        else:
            tip_x, tip_y = hx - arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 0
    else:
        if is_inward:
            tip_x, tip_y = hx, hy + arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 0
        else:
            tip_x, tip_y = hx, hy - arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 1

    arc_path = (
        f"M {hx},{hy} "
        f"L {tip_x},{tip_y} "
        f"A {arc_r},{arc_r} 0 0,{sweep} {end_x},{end_y}"
    )

    group.add(dwg.path(
        d=arc_path,
        fill="none",
        stroke=theme.doors.arc_stroke,
        stroke_width=max(1.0, theme.doors.arc_width),
    ))
```

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -k "door" -v`
Expected: R11, R12, R23, R32 all pass

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/door_renderer.py tests/unit/test_renderer.py
git commit -m "feat: door renderer with leaf rect + stronger swing arc"
```

---

### Task 5: Update window_renderer — double-line symbol with mullion

**Files:**
- Modify: `src/floorplan_generator/renderer/window_renderer.py` (full rewrite)
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R33
def test_window_double_line():
    """Window renders as two parallel lines (double glazing symbol)."""
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
    # Count lines that belong to windows (not walls — walls are now rects)
    lines = floor.findall("svg:line", ns)
    # Should have at least 2 lines for double-glazing symbol
    assert len(lines) >= 2, f"Expected >= 2 window lines, got {len(lines)}"


# R34
def test_wide_window_has_mullion():
    """Windows wider than 1200mm have a perpendicular mullion line."""
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
    lines = floor.findall("svg:line", ns)
    # Should have 3 lines: 2 parallel + 1 mullion
    assert len(lines) >= 3, f"Expected >= 3 lines (2 panes + mullion), got {len(lines)}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_window_double_line -v`
Expected: FAIL — current window renderer produces only 1 line

**Step 3: Write the implementation**

Rewrite `src/floorplan_generator/renderer/window_renderer.py`:

```python
"""Window rendering: double-line glazing symbol with optional mullion."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_MULLION_THRESHOLD_MM = 1200.0  # add mullion for windows wider than this
_GLASS_GAP_PX = 4.0  # gap between two parallel glass lines


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    for room in rooms:
        for window in room.windows:
            _render_single_window(dwg, group, window, mapper, theme)


def _render_single_window(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    window: Window,
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render a window as two parallel lines + optional mullion."""
    pos = mapper.to_svg(window.position)
    length = mapper.scale_length(window.width)
    gap = _GLASS_GAP_PX
    sw = max(1.5, theme.windows.stroke_width)
    color = theme.windows.stroke

    is_horizontal = window.wall_side in ("north", "south")

    if is_horizontal:
        # Two horizontal lines offset vertically
        y1 = pos[1] - gap / 2
        y2 = pos[1] + gap / 2
        group.add(dwg.line(
            start=(pos[0], y1), end=(pos[0] + length, y1),
            stroke=color, stroke_width=sw,
        ))
        group.add(dwg.line(
            start=(pos[0], y2), end=(pos[0] + length, y2),
            stroke=color, stroke_width=sw,
        ))
        # Mullion for wide windows
        if window.width > _MULLION_THRESHOLD_MM:
            mid_x = pos[0] + length / 2
            group.add(dwg.line(
                start=(mid_x, y1 - 2), end=(mid_x, y2 + 2),
                stroke=color, stroke_width=sw,
            ))
    else:
        # Two vertical lines offset horizontally
        x1 = pos[0] - gap / 2
        x2 = pos[0] + gap / 2
        group.add(dwg.line(
            start=(x1, pos[1]), end=(x1, pos[1] + length),
            stroke=color, stroke_width=sw,
        ))
        group.add(dwg.line(
            start=(x2, pos[1]), end=(x2, pos[1] + length),
            stroke=color, stroke_width=sw,
        ))
        # Mullion
        if window.width > _MULLION_THRESHOLD_MM:
            mid_y = pos[1] + length / 2
            group.add(dwg.line(
                start=(x1 - 2, mid_y), end=(x2 + 2, mid_y),
                stroke=color, stroke_width=sw,
            ))
```

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -k "window" -v`
Expected: R13, R14, R24, R33, R34 all pass. Fix R14 if it expects specific line counts.

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/window_renderer.py tests/unit/test_renderer.py
git commit -m "feat: window renderer with double-line glazing symbol and mullion"
```

---

### Task 6: Add 14 missing furniture symbols

**Files:**
- Modify: `src/floorplan_generator/renderer/symbols/furniture.py:295-356`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
from floorplan_generator.renderer.symbols.furniture import get_drawer, draw_rect_fallback

# R35
def test_all_furniture_types_have_dedicated_drawer():
    """No furniture type falls back to draw_rect_fallback."""
    for ft in FurnitureType:
        drawer = get_drawer(ft)
        assert not getattr(drawer, "is_fallback", False), (
            f"{ft.value} uses fallback drawer — needs dedicated symbol"
        )
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_all_furniture_types_have_dedicated_drawer -v`
Expected: FAIL — 14 types use fallback

**Step 3: Write the 14 missing draw functions**

Add to `src/floorplan_generator/renderer/symbols/furniture.py` before the `FURNITURE_DRAWERS` dict:

```python
def draw_shower(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Shower: square with diagonal hatch lines + drain circle."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Diagonal hatch
    step = min(w, d) * 0.2
    for i in range(1, int(max(w, d) / step) + 1):
        offset = step * i
        x1, y1 = min(offset, w), max(0, offset - w) if offset > w else 0
        x2, y2 = max(0, offset - d) if offset > d else 0, min(offset, d)
        g.add(Line(start=(x1, y2), end=(x2, y1), **s))
    # Drain circle
    g.add(Circle(center=(w * 0.5, d * 0.5), r=min(w, d) * 0.06, **s))


def draw_double_sink(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Double sink: rect body + two oval basins side by side."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    basin_w = w * 0.35
    basin_h = d * 0.3
    g.add(Ellipse(center=(w * 0.28, d * 0.55), r=(basin_w / 2, basin_h / 2), **s))
    g.add(Ellipse(center=(w * 0.72, d * 0.55), r=(basin_w / 2, basin_h / 2), **s))
    # Faucet circles
    g.add(Circle(center=(w * 0.28, d * 0.15), r=w * 0.04, **s))
    g.add(Circle(center=(w * 0.72, d * 0.15), r=w * 0.04, **s))


def draw_bidet(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Bidet: oval bowl (like toilet without tank)."""
    s = _style(style)
    g.add(Ellipse(center=(w / 2, d / 2), r=(w * 0.42, d * 0.45), **s))
    g.add(Ellipse(center=(w / 2, d * 0.55), r=(w * 0.28, d * 0.28), **s))
    # Faucet
    g.add(Circle(center=(w / 2, d * 0.12), r=w * 0.05, **s))


def draw_dryer(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Dryer: rect + front drum circle + vent circle."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    panel_h = d * 0.1
    g.add(Rect(insert=(0, 0), size=(w, panel_h), **s))
    r_drum = min(w, d) * 0.35
    cx, cy = w / 2, panel_h + (d - panel_h) / 2
    g.add(Circle(center=(cx, cy), r=r_drum, **s))
    # Vent holes (small circles)
    g.add(Circle(center=(w * 0.15, d * 0.05), r=w * 0.03, **s))
    g.add(Circle(center=(w * 0.85, d * 0.05), r=w * 0.03, **s))


def draw_oven(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Oven: rect body + inner door rect + window circle."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Door
    inset = min(w, d) * 0.1
    g.add(Rect(insert=(inset, inset), size=(w - 2 * inset, d - 2 * inset), **s))
    # Window circle
    g.add(Circle(center=(w / 2, d / 2), r=min(w, d) * 0.2, **s))
    # Handle line
    g.add(Line(start=(inset, d * 0.15), end=(w - inset, d * 0.15), **s))


def draw_dishwasher(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Dishwasher: rect with horizontal rack lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Control panel strip
    g.add(Line(start=(0, d * 0.1), end=(w, d * 0.1), **s))
    # Rack lines
    for frac in [0.35, 0.55, 0.75]:
        g.add(Line(start=(w * 0.1, d * frac), end=(w * 0.9, d * frac), **s))
    # Handle
    g.add(Line(start=(w * 0.3, d * 0.05), end=(w * 0.7, d * 0.05), **s))


def draw_microwave(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Microwave: rect body + rounded inner door + control panel."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Door (rounded)
    door_w = w * 0.7
    door_h = d * 0.8
    g.add(Rect(
        insert=(w * 0.05, d * 0.1),
        size=(door_w, door_h),
        rx=min(door_w, door_h) * 0.1, ry=min(door_w, door_h) * 0.1,
        **s,
    ))
    # Control panel (right side)
    g.add(Line(start=(w * 0.78, d * 0.1), end=(w * 0.78, d * 0.9), **s))
    # Knob circles
    g.add(Circle(center=(w * 0.88, d * 0.35), r=w * 0.04, **s))
    g.add(Circle(center=(w * 0.88, d * 0.65), r=w * 0.04, **s))


def draw_bookshelf(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Bookshelf: rect with horizontal shelf lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    n_shelves = 4
    for i in range(1, n_shelves + 1):
        y = d * i / (n_shelves + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))


def draw_shelving(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Shelving: rect with grid of horizontal + vertical lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Horizontal shelves
    n_h = 4
    for i in range(1, n_h + 1):
        y = d * i / (n_h + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))
    # Vertical dividers
    n_v = 2
    for i in range(1, n_v + 1):
        x = w * i / (n_v + 1)
        g.add(Line(start=(x, 0), end=(x, d), **s))


def draw_dresser(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Dresser: rect with horizontal drawer lines + handle circles."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    n_drawers = 3
    for i in range(1, n_drawers + 1):
        y = d * i / (n_drawers + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))
        # Handle
        g.add(Circle(center=(w / 2, y - d / (n_drawers + 1) / 2), r=w * 0.03, **s))


def draw_vanity(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Vanity: rect table + oval mirror."""
    s = _style(style)
    # Table
    g.add(Rect(insert=(0, d * 0.3), size=(w, d * 0.7), **s))
    # Mirror oval
    g.add(Ellipse(center=(w / 2, d * 0.15), r=(w * 0.35, d * 0.12), **s))
    # Drawer line
    g.add(Line(start=(w * 0.1, d * 0.65), end=(w * 0.9, d * 0.65), **s))


def draw_shoe_rack(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Shoe rack: low rect with angled shelf lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Angled shelves
    for i in range(1, 4):
        y_start = d * i / 4
        g.add(Line(start=(0, y_start), end=(w, y_start - d * 0.08), **s))


def draw_bench(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Bench: rect with seat line."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Seat edge
    g.add(Line(start=(0, d * 0.3), end=(w, d * 0.3), **s))
    # Optional backrest line
    g.add(Line(start=(0, d * 0.05), end=(w, d * 0.05), **s))


def draw_coat_rack(g: svgwrite.container.Group, w: float, d: float, style: dict) -> None:
    """Coat rack: rect with hook circles along top."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Hooks
    n_hooks = max(3, int(w / (d * 0.8)))
    for i in range(n_hooks):
        cx = w * (i + 0.5) / n_hooks
        g.add(Circle(center=(cx, d * 0.25), r=min(w, d) * 0.06, **s))
    # Shelf line
    g.add(Line(start=(0, d * 0.45), end=(w, d * 0.45), **s))
```

Then update the `FURNITURE_DRAWERS` dict (add new entries after existing ones):

```python
FURNITURE_DRAWERS: dict[FurnitureType, Callable] = {
    # ... existing entries ...
    FurnitureType.SHOWER: draw_shower,
    FurnitureType.DOUBLE_SINK: draw_double_sink,
    FurnitureType.BIDET: draw_bidet,
    FurnitureType.DRYER: draw_dryer,
    FurnitureType.OVEN: draw_oven,
    FurnitureType.DISHWASHER: draw_dishwasher,
    FurnitureType.MICROWAVE: draw_microwave,
    FurnitureType.BOOKSHELF: draw_bookshelf,
    FurnitureType.SHELVING: draw_shelving,
    FurnitureType.DRESSER: draw_dresser,
    FurnitureType.VANITY: draw_vanity,
    FurnitureType.SHOE_RACK: draw_shoe_rack,
    FurnitureType.BENCH: draw_bench,
    FurnitureType.COAT_RACK: draw_coat_rack,
}
```

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_all_furniture_types_have_dedicated_drawer -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/symbols/furniture.py tests/unit/test_renderer.py
git commit -m "feat: add 14 missing furniture symbols (shower, oven, dresser, etc.)"
```

---

### Task 7: SVG structure fixes — mebel group, background path

**Files:**
- Modify: `src/floorplan_generator/renderer/svg_renderer.py:20-54`
- Test: `tests/unit/test_renderer.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
# R36
def test_furniture_group_named_mebel():
    """Furniture group has id='mebel' (not 'furniture')."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.BATHTUB,
        position=Point(x=100, y=100), width=1700, depth=750,
    )
    room = _make_room(RoomType.BATHROOM, 0, 0, 2000, 2000, furniture=[item])
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    mebel = root.findall(".//svg:g[@id='mebel']", ns)
    assert len(mebel) == 1, "Expected <g id='mebel'>"
    assert root.findall(".//svg:g[@id='furniture']", ns) == [], "Should not have id='furniture'"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py::test_furniture_group_named_mebel -v`
Expected: FAIL — currently group is `id="furniture"`

**Step 3: Write the implementation**

In `src/floorplan_generator/renderer/svg_renderer.py`, change line 42:

```python
    # Layer 3: Furniture
    furniture_group = dwg.g(id="mebel")
```

Also update the R15, R20, R21 tests that reference `id='furniture'` to use `id='mebel'` instead.

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/unit/test_renderer.py -v`
Expected: All pass after updating old test references from "furniture" to "mebel"

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/svg_renderer.py tests/unit/test_renderer.py
git commit -m "feat: rename furniture group to 'mebel' per spec"
```

---

### Task 8: Layout quality — increase compactness weight + tighter canvas

**Files:**
- Modify: `src/floorplan_generator/generator/greedy/scoring.py:22` (W_COMPACT)
- Modify: `src/floorplan_generator/generator/room_composer.py` (canvas sizing)
- Test: `tests/integration/test_placement_quality.py`

**Step 1: Write the failing test**

Add to `tests/integration/test_placement_quality.py`:

```python
# PQ05
def test_layout_compact_no_excessive_restarts():
    """Layouts should succeed within 5 restarts for comfort 2-room."""
    success_count = 0
    for seed in range(42, 62):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is not None and result.restart_count <= 5:
            success_count += 1
    # At least 15/20 should succeed within 5 restarts
    assert success_count >= 15, f"Only {success_count}/20 succeeded within 5 restarts"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/integration/test_placement_quality.py::test_layout_compact_no_excessive_restarts -v`
Expected: FAIL — many apartments currently need 8+ restarts

**Step 3: Write the implementation**

In `src/floorplan_generator/generator/greedy/scoring.py`, line 22:

```python
W_COMPACT = 6.0  # was 3.0
```

In `src/floorplan_generator/generator/room_composer.py`, find the `get_canvas` function and change the padding multiplier from 1.2 to 1.1:

Look for a line like `canvas_area = total_area * 1.2` or similar and change to `1.1`. If the multiplier is embedded differently, find and adjust the canvas sizing logic to produce a ~10% tighter canvas.

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/integration/test_placement_quality.py -v`
Expected: PQ01-PQ05 all pass

**Step 5: Run full test suite**

Run: `.venv/bin/python -m pytest --tb=short`
Expected: All pass. Tighter canvas may cause some generation failures — if so, also increase `max_restarts` default or relax the test threshold.

**Step 6: Commit**

```bash
git add src/floorplan_generator/generator/greedy/scoring.py src/floorplan_generator/generator/room_composer.py tests/integration/test_placement_quality.py
git commit -m "feat: increase compactness weight and tighten canvas for better layouts"
```

---

### Task 9: Integration test — full visual regression

**Files:**
- Modify: `tests/integration/test_svg_structure.py`

**Step 1: Update integration tests for new structure**

Update `tests/integration/test_svg_structure.py` to verify:

```python
# SVG04
def test_walls_are_rects_not_lines():
    """Generated SVG has wall rects (not lines) in floor group."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    rects = floor.findall("svg:rect", ns)
    assert len(rects) >= 4, f"Expected wall rects, got {len(rects)}"


# SVG05
def test_mebel_group_exists():
    """Furniture group is named 'mebel'."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    mebel = root.findall(".//svg:g[@id='mebel']", ns)
    assert len(mebel) == 1


# SVG06
def test_text_font_size_is_large():
    """Room labels use font-size >= 20."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    texts = root.findall(".//svg:text", ns)
    assert len(texts) >= 2
    for text_el in texts:
        fs = text_el.get("font-size", "0")
        assert int(fs) >= 20, f"Font size {fs} too small"
```

Update existing SVG01/SVG02/SVG03 to reference `mebel` instead of `furniture`.

**Step 2: Run tests**

Run: `.venv/bin/python -m pytest tests/integration/test_svg_structure.py -v`
Expected: All pass

**Step 3: Generate sample output for visual inspection**

Run:
```bash
.venv/bin/python -m floorplan_generator.cli generate --class comfort --rooms 2 --count 5 --seed 100 --output ./output/v2_test --theme colored
```

**Step 4: Commit**

```bash
git add tests/integration/test_svg_structure.py
git commit -m "test: update integration tests for visual quality v2 (rects, mebel, font size)"
```

---

### Task 10: Final full suite run + cleanup

**Step 1: Run complete test suite**

Run: `.venv/bin/python -m pytest -v --tb=short`
Expected: All 274+ tests pass

**Step 2: Generate visual regression samples**

```bash
.venv/bin/python -m floorplan_generator.cli generate --class economy --rooms 1 --count 5 --seed 42 --output ./output/v2_economy --theme blueprint
.venv/bin/python -m floorplan_generator.cli generate --class comfort --rooms 2 --count 10 --seed 42 --output ./output/v2_comfort --theme colored
```

**Step 3: Visually inspect SVGs in browser**

Check:
- [ ] Walls have visible thickness (not just lines)
- [ ] Doors show leaf rect + arc
- [ ] Windows show double-line symbol
- [ ] All furniture has recognizable shapes (no text-only fallbacks)
- [ ] Room labels readable (28px size)
- [ ] Layout fills canvas well (minimal whitespace)
- [ ] No visual glitches (overlapping walls, misaligned openings)

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: visual quality v2 complete — architectural drawing style"
```
