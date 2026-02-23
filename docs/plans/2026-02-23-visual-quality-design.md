# Floorplan Visual Quality Improvement Design

**Date:** 2026-02-23
**Problem:** Generated floorplans don't match the reference Illustrator SVGs in `docs/svg/`. Both placement correctness and visual rendering quality need improvement.

## Scope

Two phases, executed sequentially:
1. **Phase 1 — Placement bug fixes** (algorithm correctness)
2. **Phase 2 — Visual rendering improvements** (match reference SVG quality)

---

## Phase 1: Placement Bug Fixes

### 1.1 Windows Not Appearing

**Root cause:** `window_placer.py:_external_wall_segments()` requires wall length >= 900mm. Combined with 200mm margin check in the window sizing loop, most rooms get zero windows.

**Files:** `src/floorplan_generator/generator/csp/window_placer.py`

**Changes:**
- Lower minimum wall length threshold from 900mm to 600mm
- Add smaller window sizes to `_WINDOW_SIZES` (600mm, 700mm)
- Reduce margin from 200mm to 150mm (still safe per GOST)
- Add fallback: if no window fits, try longest external wall with minimal 600mm window

**Tests:**
- Rooms with short external walls (700mm, 800mm) still get windows
- Every room touching canvas boundary gets >= 1 window (except interior-only rooms)
- Integration: generate 10 apartments, assert all living rooms and kitchens have >= 1 window

### 1.2 Door Collision Detection

**Root cause:** `Door.swing_arc` computed property doesn't account for OUTWARD swing direction. Always positions arc at `door.position`, but OUTWARD swings extend in the opposite direction. Mismatch between placement-time calculation in `door_placer.py` and the `Door` model property.

**Files:**
- `src/floorplan_generator/core/models.py` — `Door.swing_arc` property
- `src/floorplan_generator/generator/csp/door_placer.py` — placement arc logic

**Changes:**
- Add `wall_normal` or `wall_orientation` field to `Door` model so `swing_arc` can compute the correct offset
- Update `Door.swing_arc` to shift the rectangle based on swing direction + wall orientation (matching door_placer.py lines 113-134)
- Ensure P22 rule and placement-time check use the same arc geometry

**Tests:**
- OUTWARD swing arcs offset correctly from door position
- P22 catches overlapping arcs that were previously missed
- Two doors on same wall with OUTWARD swings don't collide

### 1.3 Furniture Placement Quality

**Root cause:** Furniture placer doesn't properly check door swing arcs (same swing_arc bug), wall boundary checks may be incorrect, backtracking gives up and leaves items in invalid positions.

**Files:**
- `src/floorplan_generator/generator/csp/furniture_placer.py`
- `src/floorplan_generator/generator/csp/constraints.py`
- `src/floorplan_generator/rules/furniture_rules.py`

**Changes:**
- Strengthen clearance checks: furniture must not overlap door swing arcs, window zones, or stoyak zones
- Add wall-hugging preference for beds, wardrobes, desks (score wall-adjacent positions higher)
- Add entry clearance: no furniture within 600mm of door opening direction
- If placement fails after all retries, **omit the item** rather than placing it in an invalid position
- New validation rules:
  - Furniture must not overlap door swing arcs
  - Furniture must not block window access (min 300mm clearance)
- Strengthen F18 (minimum passage 700mm) enforcement during generation, not just post-validation

**Tests:**
- No furniture item overlaps any door swing arc
- Furniture items are within room boundaries (not crossing walls)
- Minimum passage width between furniture items
- Integration: generate apartments, assert zero furniture-door overlaps

---

## Phase 2: Visual Rendering Improvements

### 2.1 Furniture Symbol Library

**Problem:** Current furniture uses basic shapes (rect + circles). Reference Illustrator SVGs have detailed bezier-path furniture with recognizable features (pillows on beds, burner circles on stoves, basin shapes on sinks).

**Approach:** Parse the 66 reference SVGs in `docs/svg/` to extract `<g id="mebel">` furniture groups. Classify, normalize, and port as Python SVG-generating functions.

**Files:**
- `src/floorplan_generator/renderer/symbols/furniture.py` — rewrite with detailed symbols
- Potentially split into sub-modules: `symbols/beds.py`, `symbols/kitchen.py`, `symbols/bathroom.py`, `symbols/living.py`

**Symbol categories:**
- Beds: single, double, with pillows and headboard detail
- Sofas: 2-seat, 3-seat, L-shaped with cushion lines
- Kitchen: stove (concentric burner circles), fridge (compartment lines), sink (oval basin + faucet), hood
- Bathroom: toilet (oval bowl + tank), bathtub (rounded rect + drain), shower, washing machine (drum circle)
- Tables: round dining with chairs, rectangular, desk with drawer line
- Storage: wardrobe (door lines), nightstand (drawer), shelf (horizontal divisions)

**Design decision:** Symbols remain as Python functions generating SVG elements (self-contained, no external template files).

### 2.2 SVG Structure Overhaul

**Problem:** Generated SVG layer structure doesn't match reference.

**Reference structure:**
```xml
<svg viewBox="0 0 2000 2000">
    <path id="background" fill="#FFFFFF" d="..."/>  <!-- apartment exterior polygon -->
    <g id="h1"><path/><text/></g>                    <!-- room groups -->
    <g id="c1"><path/><text/></g>
    <g id="s1"><path/><text/></g>
    <g id="r1"><path/><text/></g>
    <g id="mebel">...</g>                            <!-- all furniture -->
    <g id="floor">                                   <!-- walls, doors, windows -->
        <polygon points="..."/>                       <!-- exterior boundary -->
        <g id="LINE_..."><line .../></g>             <!-- individual wall lines -->
        <g id="LWPOLYLINE_..."><rect .../></g>       <!-- door gaps -->
        <g id="ARC_..."><path .../></g>              <!-- door swing arcs -->
    </g>
</svg>
```

**Files:** `src/floorplan_generator/renderer/svg_renderer.py` and all sub-renderers

**Changes:**
1. **Background:** Single `<path id="background">` tracing apartment exterior polygon with `fill:#FFFFFF`
2. **Room groups:** Each room gets `<g id="XX">` with room-type prefix (h=hallway, c=common, s=sanitary, r=room) + `<path>` boundary + `<text>` label
3. **Furniture:** Single `<g id="mebel">` wrapping all furniture
4. **Floor group:** Single `<g id="floor">` containing:
   - Exterior boundary polygon
   - Wall segments as individual `<line>` elements
   - Door gaps as `<rect>` + swing arcs as bezier `<path>`
   - Window line segments

### 2.3 Wall Rendering

**Change:** Keep stroke-based lines (reference also uses lines). Render each wall segment as individual `<line>` in the floor group. Adjust stroke widths for better visual weight matching reference.

### 2.4 Door Rendering

**Change:** Small `<rect>` for gap (matching reference LWPOLYLINE pattern). Bezier curve `<path>` for swing arc (matching reference ARC pattern) instead of current simple polygon.

### 2.5 Window Rendering

**Change:** Simple `<line>` segments on exterior walls (matching reference) instead of rectangles with pane divisions.

---

## Testing Strategy

### Unit tests per fix:
- Window placement with various wall lengths
- Door swing_arc geometry for all swing directions
- Furniture boundary/clearance checks

### Integration tests:
- Generate N apartments, assert:
  - All living rooms and kitchens have windows
  - Zero door arc collisions
  - Zero furniture-door overlaps
  - Zero furniture items outside room boundaries
- Render SVG, parse XML, assert correct structure (background, room groups, mebel, floor)

### Visual regression:
- Generate a fixed-seed apartment before/after each phase
- Compare SVG outputs manually to verify improvement

---

## Implementation Order

1. Fix `Door.swing_arc` (models.py) — unblocks door and furniture fixes
2. Fix window placement thresholds (window_placer.py)
3. Fix furniture clearance checks (furniture_placer.py)
4. Add/update tests for all three fixes
5. Extract furniture symbols from reference SVGs
6. Restructure SVG renderer output
7. Update door/window renderers
8. Add rendering structure tests
