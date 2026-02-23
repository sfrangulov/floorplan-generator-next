# Phase 4: SVG Renderer — Design

## Summary

Phase 4 implements the SVG rendering pipeline that converts `GenerationResult` (from Phase 3) into production-quality SVG floorplan files. Uses `svgwrite` library. Features a JSON-based theme system with two default themes (blueprint and colored). Furniture shapes are extracted from existing reference SVGs in `docs/svg/`. Adds CLI commands `generate` and `render`.

## Scope

### New files

```
src/floorplan_generator/renderer/
    __init__.py
    svg_renderer.py          # Main orchestrator: render(GenerationResult, theme) -> SVG string
    coordinate_mapper.py     # mm -> SVG unit conversion, centering, viewBox
    room_renderer.py         # Room boundary polygons + text labels
    wall_renderer.py         # Outer walls (thick) + inner partitions (thin)
    door_renderer.py         # Door opening gap + swing arc (quarter circle)
    window_renderer.py       # Window rect + crossing lines
    furniture_renderer.py    # Furniture symbol library + <use> placement with rotation
    stoyak_renderer.py       # Stoyak circle marker
    theme.py                 # Theme loading, validation, defaults
    themes/
        blueprint.json       # Black-on-white, matches existing SVG examples
        colored.json         # Room-type fill colors for visual distinction
    symbols/
        furniture.py         # SVG path data for each FurnitureType (from docs/svg/ examples)

tests/unit/
    test_renderer.py         # R01-R20: unit tests for renderer components
tests/integration/
    test_renderer_integration.py  # RI01-RI05: full pipeline SVG generation tests
```

### Modified files

- `src/floorplan_generator/cli.py` — add `generate` and `render` commands
- `src/floorplan_generator/generator/factory.py` — integrate SVG rendering into dataset generation
- `pyproject.toml` — add `svgwrite` dependency

## Architecture

### Rendering Pipeline

```
GenerationResult
    |
    v
CoordinateMapper (mm -> SVG units, fit to canvas, center)
    |
    v
SVG Drawing (svgwrite.Drawing, 2000x2000 viewBox)
    |
    ├── Layer 1: Background rect (theme.canvas.background)
    ├── Layer 2: Room fills (theme.rooms.fills[room_type]) -- only if theme has fills
    ├── Layer 3: Furniture group <g id="mebel"> (symbols + <use>)
    ├── Layer 4: Walls <g id="floor"> (outer thick + inner thin strokes)
    ├── Layer 5: Doors (opening gap + swing arc path)
    ├── Layer 6: Windows (rect + crossing lines)
    ├── Layer 7: Stoyaks (circle markers)
    └── Layer 8: Text labels (room names + areas at centroids)
    |
    v
SVG string / file
```

### Z-order matches existing examples

Furniture drawn BEFORE walls/doors so structural elements visually sit on top. This matches the Adobe Illustrator layer order in `docs/svg/` reference files.

### Coordinate Mapping

All internal geometry is in millimeters (mm). The mapper:
1. Computes bounding box of all room boundaries
2. Calculates scale factor to fit within canvas (2000x2000) with padding
3. Centers the floorplan on the canvas
4. Provides `to_svg(point_mm) -> (x_svg, y_svg)` conversion

```python
class CoordinateMapper:
    def __init__(self, rooms: list[Room], canvas_width=2000, canvas_height=2000, padding=100):
        ...
    def to_svg(self, point: Point) -> tuple[float, float]: ...
    def scale_length(self, mm_length: float) -> float: ...
```

### Theme System

JSON theme files stored in `renderer/themes/`. Theme key passed via CLI (`--theme blueprint`).

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
    "inner_width": 1.5
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
  "stoyak": {
    "stroke": "#000000",
    "fill": "#000000",
    "radius": 3.0
  },
  "text": {
    "font_family": "Arial, sans-serif",
    "font_size": 14,
    "fill": "#333333",
    "area_font_size": 11
  }
}
```

Colored theme adds room fills:
```json
"fills": {
  "living_room": "#E3F2FD",
  "bedroom": "#E8EAF6",
  "children": "#F3E5F5",
  "cabinet": "#EDE7F6",
  "kitchen": "#FFF3E0",
  "kitchen_dining": "#FFF8E1",
  "kitchen_niche": "#FFF8E1",
  "hallway": "#F5F5F5",
  "corridor": "#EEEEEE",
  "hall": "#E0E0E0",
  "bathroom": "#E0F7FA",
  "toilet": "#E0F2F1",
  "combined_bathroom": "#E0F7FA",
  "storage": "#EFEBE9",
  "wardrobe": "#EFEBE9",
  "laundry": "#E0F7FA",
  "balcony": "#E8F5E9"
}
```

### Furniture Symbols

SVG path data extracted from `docs/svg/` reference files, normalized to (0,0) origin with canonical dimensions. Stored in `symbols/furniture.py` as a dict mapping `FurnitureType` to SVG element definitions.

Each symbol defined at canonical size (matching `FURNITURE_SIZES` from dimensions.py). At render time:
1. Define `<symbol id="furniture_{type}">` with the extracted paths
2. Place with `<use href="#furniture_{type}" x="..." y="..." transform="rotate(...)"/>`
3. Scale from canonical to actual size if needed

Furniture types with extracted shapes from reference SVGs:

| Type | Shape signature | Source |
|------|----------------|--------|
| BATHTUB | Rect body + rounded basin path + shelf rect | 84.5m2, 86.5m2, 90.7m2 |
| TOILET_BOWL | Oval paths + tank rect + flush circle | 84.5m2, 90.7m2 |
| SINK | Circle basin + faucet lever path | 84.5m2, 86.5m2 |
| WASHING_MACHINE | Large circle (drum) + 4 arm paths + inner detail circles | 86.5m2 |
| STOVE | Rect + 4 concentric circle pairs (burners) + handle details | 90.7m2 |
| FRIDGE | Polygon + cross lines + 4 polyline arrows (snowflake) | 84.5m2, 55.4m2 |
| BED_DOUBLE | Multi-panel rects (2 cols) + pillow paths at head | 86.5m2, 84.5m2 |
| BED_KING | 6 rect panels (3x2 grid) + pillow paths | 55.4m2 |
| SOFA | Capsule-shaped path with rounded ends | 90.7m2, 86.5m2 |
| WARDROBE_SLIDING | Rect + parallel line + division lines | 86.5m2 |
| WARDROBE_SWING | Rect + edge line + shelf division lines | 90.7m2 |
| NIGHTSTAND | Small rect + single vertical line | 86.5m2 |
| DINING_TABLE | Rect + polygon shelf + support rect | 90.7m2, 55.4m2 |
| DINING_CHAIR | Hexagonal polygon + circle + arm paths | 55.4m2 |
| TV_STAND / DESK | Wide rect + horizontal line + vertical divisions | 55.4m2, 90.7m2 |
| HOOD | 4 concentric circles + dial circle | 84.5m2 |

Furniture types without specific reference shapes use simplified rendering:
- Simple filled rect with type label for: SHOWER, DOUBLE_SINK, BIDET, DRYER, HOB, OVEN, DISHWASHER, KITCHEN_SINK, MICROWAVE, SOFA_2/4, SOFA_CORNER, ARMCHAIR, COFFEE_TABLE, SHELVING, BED_SINGLE, DRESSER, VANITY, CHILD_BED, CHILD_DESK, CHILD_WARDROBE, HALLWAY_WARDROBE, SHOE_RACK, BENCH, COAT_RACK, BOOKSHELF, FRIDGE_SIDE_BY_SIDE

### Wall Rendering

1. **Outer walls**: Detect room boundary edges that lie on the apartment's outer perimeter. Draw with thick stroke (theme.walls.outer_width).
2. **Inner walls**: Shared edges between rooms. Draw with thin stroke (theme.walls.inner_width).
3. Wall gaps left at door positions (no stroke where door opening is).

### Door Rendering

For each door:
1. Draw gap in wall (white rect at door position, width = door.width)
2. Draw swing arc: quarter-circle path from hinge point, radius = door.width
3. Swing direction (INWARD/OUTWARD) determines which side of the wall the arc appears

### Window Rendering

For each window:
1. Draw rect on wall at window position (width = window.width, depth = wall thickness)
2. Draw 3 parallel lines inside the rect (window pane divisions)
3. White fill behind to "cut" the wall

### CLI Commands

```bash
# Generate apartments and render to SVG in one step
floorplan generate --class comfort --rooms 2 --count 10 \
    --output ./dataset --theme colored --seed 42

# Re-render from saved apartment data (JSON)
floorplan render --input ./dataset --output ./rendered --theme blueprint
```

The `generate` command:
1. Calls `generate_dataset()` from factory
2. Serializes each `GenerationResult` to JSON (for re-rendering)
3. Renders each to SVG using the specified theme
4. Saves SVG files + metadata.json

The `render` command:
1. Reads saved apartment JSON files
2. Re-renders with the specified theme

## Design Decisions

1. **svgwrite over lxml**: Cleaner API for SVG generation (`dwg.add(dwg.rect(...))` vs raw XML element manipulation). Already supports symbols, groups, transforms, paths.
2. **Normalized furniture symbols**: Path data normalized to (0,0) origin at canonical size. Placed via `<use>` with transform for position/rotation/scale. Keeps SVG files small.
3. **Theme as JSON**: Easy to create custom themes without code changes. Two built-in defaults.
4. **Layered rendering**: Each renderer is independent, receives the `Drawing` and `CoordinateMapper`. Easy to test in isolation.
5. **Fixed 2000x2000 canvas**: Matches reference SVGs. Scale factor computed per apartment to fit.
6. **Simplified fallback for rare furniture**: ~15 common types get detailed shapes from references. The rest get labeled rectangles. Avoids excessive symbol extraction work for items that rarely appear.

## Test Specification

### Unit tests (R01-R20)

| ID | Test | Description |
|----|------|-------------|
| R01 | test_coordinate_mapper_basic | mm point maps to correct SVG coords |
| R02 | test_coordinate_mapper_centering | Floorplan centered in canvas |
| R03 | test_coordinate_mapper_scale | Scale preserves aspect ratio |
| R04 | test_theme_load_blueprint | Load blueprint.json correctly |
| R05 | test_theme_load_colored | Load colored.json correctly |
| R06 | test_theme_custom_json | Load custom theme from file path |
| R07 | test_room_polygon_render | Room boundary renders as SVG polygon |
| R08 | test_room_label_render | Room label at centroid with name + area |
| R09 | test_wall_outer_thick | Outer walls drawn with thick stroke |
| R10 | test_wall_inner_thin | Inner walls drawn with thin stroke |
| R11 | test_door_gap | Door creates gap in wall |
| R12 | test_door_swing_arc | Swing arc is quarter circle, correct direction |
| R13 | test_window_rect | Window rect on external wall |
| R14 | test_window_panes | Window has pane division lines |
| R15 | test_furniture_symbol_defined | Furniture type creates <symbol> in defs |
| R16 | test_furniture_use_placement | <use> placed at correct position/rotation |
| R17 | test_furniture_rotation | Rotated furniture has correct transform |
| R18 | test_stoyak_circle | Stoyak renders as filled circle |
| R19 | test_full_render_produces_valid_svg | Full render returns valid SVG string |
| R20 | test_full_render_layers_order | Elements appear in correct z-order |

### Integration tests (RI01-RI05)

| ID | Test | Description |
|----|------|-------------|
| RI01 | test_generate_economy_svg | Generate economy 1-room, render SVG, check file exists + valid XML |
| RI02 | test_generate_with_themes | Same apartment renders differently with blueprint vs colored |
| RI03 | test_dataset_generation_svgs | generate_dataset produces SVG files + metadata |
| RI04 | test_svg_file_size_reasonable | SVG file size < 500KB for typical apartment |
| RI05 | test_render_from_json | Serialize apartment to JSON, reload, re-render matches |

Total: 25 new tests. Combined with existing 226: **251 total**.

## Acceptance Criteria

- 25 new tests pass (251 total)
- `ruff check` passes
- SVG output visually matches reference style from `docs/svg/`
- Two theme JSON files work correctly
- CLI `generate` and `render` commands functional
- Furniture rendered with detailed shapes for common types
- Same seed + same theme = identical SVG output (reproducibility)
