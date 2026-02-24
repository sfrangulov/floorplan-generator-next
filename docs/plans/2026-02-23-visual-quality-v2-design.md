# Visual Quality V2 — Architectural Drawing Design

**Date:** 2026-02-23
**Problem:** SVG output still looks unprofessional despite Phase 1 fixes (wall_orientation, window thresholds, bezier arcs). Walls are thin lines, no door leaf, windows are single lines, 14 furniture types use fallback rectangles, text is too small, and layouts don't fill the canvas.

**Previous work:** `2026-02-23-visual-quality-design.md` and its implementation plan were partially executed. This document covers remaining gaps.

---

## Audit Summary: What Changed vs What Remains

| Item | Previous Plan Status | Still Needed |
|---|---|---|
| wall_orientation on Door | Done | — |
| Window thresholds lowered | Done | — |
| Bezier door arcs | Done | Door leaf rect missing |
| SVG structure (room groups) | Done (partially) | `furniture` → `mebel`, `rect` → `path` background |
| **Walls with real thickness** | **Not attempted** | **Full rewrite** |
| **Window double-line symbol** | **Not attempted** | **Full rewrite** |
| **14 missing furniture symbols** | **Not attempted** | **Draw all 14** |
| **Text size** | **Not changed** | **28px / 22px** |
| **Canvas fill / padding** | **Not changed** | **Reduce padding** |
| Layout quality (high restarts) | Partially | Scoring improvements |

---

## Section 1: Walls with Real Thickness

### Current
Walls are `<line>` elements with stroke-width 4px (outer) / 1.5px (inner). They look like thin outlines.

### Target
Walls are `<rect>` elements with real scaled thickness:
- External walls: 225mm → ~25px at typical scale
- Partition walls: 100mm → ~11px at typical scale
- Wall rects are filled solid (black in blueprint, dark gray in colored theme)
- Walls have gaps (openings) where doors and windows are placed
- Deduplication: shared wall between two rooms drawn once

### Implementation

**File: `wall_renderer.py` — full rewrite**

1. Collect all unique wall segments (deduplicate shared walls between rooms)
2. Classify each segment: outer (no neighbor room) → 225mm, inner (shared) → 100mm
3. For each segment, collect all openings (doors + windows on that wall)
4. Split segment into sub-segments around openings
5. For each sub-segment, render a `<rect>` with:
   - Position: offset perpendicular to wall by half-thickness
   - For horizontal wall: rect at (x, y - thickness/2, length, thickness)
   - For vertical wall: rect at (x - thickness/2, y, thickness, length)
6. Fill: solid color from theme (walls.fill — new theme field)

**File: `theme.py` — add wall fill**

```python
class WallTheme(BaseModel):
    outer_fill: str = "#000000"
    outer_thickness: float = 225.0  # mm
    inner_fill: str = "#000000"
    inner_thickness: float = 100.0  # mm
```

**File: `coordinate_mapper.py` — add thickness method**

```python
def scale_thickness(self, mm_thickness: float) -> float:
    return max(2.0, round(mm_thickness * self.scale, 1))
```

### Key complexity
Opening detection: for each wall segment, check if any door or window lies on it. A door on a vertical wall at (x, y) with width W creates a gap from y to y+W. The wall segment is split into [start..y] and [y+W..end].

---

## Section 2: Door Leaf + Arc

### Current
White gap rect + bezier arc (0.5px). Arc is nearly invisible. No door leaf (polotno).

### Target
- **Door leaf**: thin `<rect>` from hinge to door-end, rotated to match opening position (thickness ~30mm → ~3px)
- **Swing arc**: quarter-circle `<path>` with stroke 1.0px, dashed or thin solid
- **No gap rect needed**: the wall already has an opening from Section 1
- **Entrance door**: thicker leaf (double line)

### Implementation

**File: `door_renderer.py` — update**

After wall renderer creates gaps, door renderer draws:
1. Door leaf: `<rect>` at hinge position, width = door.width, height = 30mm scaled, with rotation matching swing direction
2. Arc: existing bezier path, but increase stroke to 1.0px

---

## Section 3: Window Double-Line Symbol

### Current
Single `<line>` on exterior wall.

### Target
Standard architectural window symbol: two parallel lines with a gap between them:
```
Wall ━━━━┃          ┃━━━━ Wall
         ┃──────────┃  (outer line)
         ┃          ┃  (gap ~2px)
         ┃──────────┃  (inner line)
Wall ━━━━┃          ┃━━━━ Wall
```

For windows > 1200mm: add a vertical mullion (impost) in the center.

### Implementation

**File: `window_renderer.py` — rewrite**

For each window:
1. The wall already has a gap (Section 1)
2. Inside the gap, draw:
   - Two parallel lines (offset ±2px from wall centerline)
   - For wide windows: a short perpendicular line at center (mullion)
3. Color: theme.windows.stroke (blue in colored theme)

---

## Section 4: Missing Furniture Symbols (14 types)

### Types needing dedicated draw functions:

| Type | Symbol Description |
|---|---|
| SHOWER | Square with diagonal hatch lines + drain circle |
| DOUBLE_SINK | Two oval basins side by side in a rect |
| BIDET | Small oval bowl (like toilet without tank) |
| DRYER | Rect + circle (like washing machine but with vent circle) |
| OVEN | Rect with inner rect (door) + circle (window) |
| DISHWASHER | Rect with horizontal rack lines |
| MICROWAVE | Rect with rounded inner rect (door) + control panel |
| BOOKSHELF | Rect with 4-5 horizontal shelf lines |
| SHELVING | Rect with horizontal + vertical divisions (grid) |
| DRESSER | Rect with 3-4 horizontal drawer lines + small handle circles |
| VANITY | Rect table + oval mirror circle above |
| SHOE_RACK | Low rect with 2-3 angled shelf lines |
| BENCH | Rect with seat line + optional backrest |
| COAT_RACK | Rect with hook circles along top |

### Implementation

**File: `symbols/furniture.py` — add 14 functions**

Each follows the same pattern: `draw_xxx(g, w, d, style) -> None`

Also add to `FURNITURE_DRAWERS` registry dict.

---

## Section 5: Text and Scale

### Changes:
1. **Font size**: 14px → 28px (room name), 11px → 22px (area)
2. **Padding**: 100px → 50px in CoordinateMapper
3. **Furniture group ID**: `"furniture"` → `"mebel"` (match spec)
4. **Background**: `<rect>` → `<path>` tracing exterior polygon

### Files:
- `theme.py` / `blueprint.json` / `colored.json`: update font sizes
- `coordinate_mapper.py`: reduce default padding
- `svg_renderer.py`: rename furniture group, compute exterior polygon for background

---

## Section 6: Layout Quality Improvements

### Problems:
- restart_count up to 8/10 — generator often fails to place rooms
- Corridor doesn't always connect all rooms
- Rooms sometimes leave large gaps

### Changes:
1. **Increase W_COMPACT** from 3.0 → 6.0 (penalize sprawling layouts more)
2. **Add gap penalty**: score_slot checks for empty rectangular gaps between placed rooms
3. **Hallway placement**: ensure hallway is placed adjacent to at least one external wall AND corridor
4. **Canvas sizing**: tighten canvas to 1.1× apartment area instead of 1.2× (room_composer.py)

### Files:
- `greedy/scoring.py`: W_COMPACT increase, gap penalty
- `room_composer.py`: tighter canvas

---

## Testing Strategy

### Unit tests:
- Wall renderer: verify rect count, opening gaps, deduplication
- Door renderer: verify leaf rect + arc path
- Window renderer: verify double-line output
- Each new furniture symbol: verify element count and key shapes

### Integration tests:
- Generate apartments, render SVG, parse XML:
  - Walls are `<rect>` not `<line>` in floor group
  - Doors have both rect (leaf) and path (arc)
  - Windows have 2+ lines per window
  - All furniture types produce non-fallback output
  - Text font-size matches theme
  - Background is `<path>` element

### Visual regression:
- Generate fixed-seed apartments before/after
- Compare in browser

---

## Implementation Order (recommended)

1. **Wall renderer rewrite** (biggest impact, prerequisite for doors/windows)
2. **Door renderer update** (leaf + arc, depends on wall gaps)
3. **Window renderer update** (double-line, depends on wall gaps)
4. **14 missing furniture symbols**
5. **Text size + padding + SVG structure fixes**
6. **Layout quality scoring improvements**
7. **Theme file updates** (blueprint.json, colored.json)
8. **Integration tests + visual regression**
