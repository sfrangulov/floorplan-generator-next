# Gap Analysis: Documentation vs Implementation

**Date:** 2026-02-24
**Scope:** All documentation files compared against actual codebase

## Summary

| Area | Implemented | Partial | Not Implemented |
|------|:-----------:|:-------:|:---------------:|
| Enums (8 enums, 57 values) | 57 | 0 | 0 |
| Geometry primitives | 9/9 | 0 | 0 |
| Dimension constants | 8/9 | 1 | 0 |
| Domain models | 23/25 | 2 | 0 |
| Planning rules P01-P28 | 23/28 | 5 | 0 |
| Planning mock rules P29-P34 | 6/6 | 0 | 0 |
| Furniture rules F01-F32 | 28/32 | 4 | 0 |
| CLI commands | 1/4 | 0 | 3 |
| Generation pipeline steps | 6/9 | 3 | 0 |
| SVG structure requirements | 7/15 | 5 | 3 |
| SVG room ID prefixes | 2/10 | 0 | 8 |
| furniture_library.json | 0/1 | 0 | 1 |
| Test files (unit) | 3/3 | 0 | 0 |
| Test files (integration) | 0/2 | 0 | 2 |
| Test files (SVG) | 0/1 | 0 | 1 |
| conftest.py fixtures | 7/8 | 0 | 1 |

---

## 1. NOT IMPLEMENTED (Critical Gaps)

### 1.1 Missing CLI Commands (Section 9)

Three of four specified CLI commands are absent from `cli.py`:

| Command | Description |
|---------|-------------|
| `floorplan validate ./plan.svg [--rules all\|mandatory\|recommended] [--format text\|json]` | Validate existing SVG against rules |
| `floorplan rules [--list] [--id P01] [--type mandatory\|recommended]` | List/query validation rules |
| `floorplan extract-furniture ./plan_example.svg --output ./data/furniture_library.json` | Extract furniture SVG snippets |

**Note:** Two undocumented commands were added: `render` and `random-generate`.

### 1.2 `--variants` CLI Option and `mebel_1`/`mebel_2` SVG Structure (Sections 6.1, 8.1)

- The `generate` command does not support `--variants 1|2`
- SVG output produces single `<g id="mebel">` instead of `<g id="mebel_1" style="display:inline;">` / `<g id="mebel_2" style="display:none;">`

### 1.3 Risers Discarded (Section 8, Step 6)

`riser_placer.py` exists and places risers, but `layout_engine.py:90` hardcodes `risers=[]`, discarding the result. No riser markers (`u1`, `u2`) appear in SVG output.

### 1.4 `data/furniture_library.json` (Section 7)

The JSON file with SVG snippets, sizes, and clearances does not exist. No extraction pipeline is implemented.

### 1.5 Room ID Prefix Scheme (Section 6.2)

| Spec Prefix | Room Type | Code Uses |
|:-----------:|-----------|:---------:|
| b | BATHROOM | s |
| s | BEDROOM | r |
| c | LIVING_ROOM | r |
| k | KITCHEN | c |
| t | TOILET | s |
| w | WARDROBE | c |
| l | STORAGE | c |
| d | CORRIDOR | h |
| h | HALLWAY | h |
| r | generic room | r |

Only `h` (hallway) matches. All other prefixes are incorrect.

### 1.6 Missing Test Files (Section 10)

| File | Tests |
|------|:-----:|
| `tests/integration/test_generation.py` (I01-I10) | 10 |
| `tests/integration/test_validation.py` (V01-V04) | 4 |
| `tests/svg/test_svg_output.py` (S01-S15) | 15 |
| **Total missing tests** | **29** |

### 1.7 SVG Font

Spec requires `GraphikLCG-Regular` at 40px. Code uses `Arial, sans-serif` at 28px.

---

## 2. PARTIALLY IMPLEMENTED

### 2.1 ADJACENCY_MATRIX (dimensions.py)

Only 9 of 17 RoomType values have adjacency rows. Missing: KITCHEN_NICHE, KITCHEN_DINING, CHILDREN, CABINET, WARDROBE, LAUNDRY, BALCONY, HALL. This causes P16 (forbidden adjacencies) to silently allow any connection involving these types.

### 2.2 Apartment.functional_zones

Computed property specified in Section 4.4 is absent from the Apartment model.

### 2.3 Planning Rules with Issues

| Rule | Issue |
|------|-------|
| P16 | Incomplete ADJACENCY_MATRIX means forbidden pairs with missing room types are never checked |
| P19 | Simplified heuristic instead of graph-path analysis for transit through night zone |
| P23 | Measures distance from door to nearest polygon vertex (corner), not to nearest wall edge |
| P24 | Checks reachability through dry zones instead of requiring direct wall adjacency for wet zone grouping |
| P28 | Proximity heuristic (dx<500, dy<1000) is approximate |

### 2.4 Furniture Rules with Issues

| Rule | Issue |
|------|-------|
| F01 | `is_mandatory=False` but spec says "Обяз." (mandatory) |
| F02 | `is_mandatory=False` but spec says "Обяз." (mandatory) |
| F04 | `is_mandatory=False` but spec says "Обяз." (mandatory) |
| F08 | `is_mandatory=False` but spec says "Обяз." (mandatory) |
| F10 | Always SKIP — 2D model has no height data |
| F11 | Always SKIP — 2D model has no height data |
| F18 | `is_mandatory=False` but spec says "Обяз." (mandatory) |
| F32 | Stub logic: uses first polygon vertex as riser position |

### 2.5 Generation Pipeline

| Step | Issue |
|------|-------|
| Step 3 (Room placement) | Uses Greedy algorithm, not Backtracking CSP as spec requires. `generator/solver.py` does not exist. |
| Step 6 (Riser placement) | Risers placed but result discarded |
| Step 8 (Validation + backtrack) | Full restart instead of step-level backtracking |

### 2.6 SVG Structure

| Requirement | Issue |
|-------------|-------|
| Room child IDs `{room_id}_path`, `{room_id}_text` | Generated elements have no IDs |
| Inline styles only (no `<defs>`) | Pattern fills use `<defs>` |
| Walls as `<rect>` | Walls rendered as `<path>` via Shapely polygons |
| Door Bezier arc format | May not match exact 4-control-point cubic Bezier from spec |
| Furniture `transform="matrix(a b c d e f)"` | Uses svgwrite transforms, format may differ |

### 2.7 Missing Test Fixture

`business_3room` fixture is absent from `conftest.py`.

### 2.8 Metadata

`room_composition` field missing from `metadata.json` output (required by Section 8).

---

## 3. FULLY IMPLEMENTED (No Issues)

- All enums: RoomType (17), ApartmentClass (4), DoorType (7), SwingDirection (2), FurnitureType (45+1), FunctionalZone (3), LayoutType (3), KitchenLayoutType (6)
- All geometry: Point, Rectangle, Polygon, Segment, distance functions
- Dimension constants: MIN_AREAS, MIN_WIDTHS, MIN_HEIGHTS, DOOR_SIZES, WINDOW_RATIOS, FURNITURE_SIZES, CLEARANCES, KITCHEN_TRIANGLE
- Core models: Room, Door, Window, FurnitureItem (basic structure)
- Planning rules: P01-P15, P17-P18, P20-P22, P25-P27, P29-P34
- Furniture rules: F03, F05-F07, F09, F12-F17, F19-F31
- CLI `generate` command (core options)
- SVG rendering: themes (12), dimension annotations, segmentation masks, PNG export
- Unit tests: test_geometry, test_models, test_planning_rules, test_furniture_rules

---

## 4. Undocumented Additions (Extra Features)

These exist in code but are NOT in the spec:

| Feature | Description |
|---------|-------------|
| CLI `render` command | Re-render JSON to SVG with different theme |
| CLI `random-generate` command | Random class/rooms/theme generation |
| Rules P35-P39 | Single door utility, external wall windows, kitchen passthrough, entrance door, wardrobe connection |
| Rules F33-F34 | TV faces sofa, bathroom essentials |
| WASHER_DRYER enum value | Extra FurnitureType not in spec |
| 12 built-in themes | Spec mentions only blueprint; 11 extra themes added |
| Pattern fills | SVG hatch, crosshatch, brick, tile, wood, dots |
| `--png`, `--mask`, `--dimensions`, `--labels` CLI options | Not in spec |

---

## 5. Priority Recommendations

If implementing gaps, recommended order:

1. **Risers fix** — Simplest: just wire `riser_placer` results into `GenerationResult`
2. **Room ID prefixes** — Localized change in `room_renderer.py`
3. **is_mandatory flags** — 5 one-line fixes in `furniture_rules.py`
4. **ADJACENCY_MATRIX** — Add missing 8 room type rows in `dimensions.py`
5. **Apartment.functional_zones** — Add computed property to model
6. **SVG structure** — Add `_path`/`_text` IDs, `mebel_1`/`mebel_2` groups
7. **Missing CLI commands** — `validate`, `rules`, `extract-furniture`
8. **Missing test files** — 29 tests across 3 files
9. **Room placement algorithm** — Greedy vs CSP (major architectural change)
