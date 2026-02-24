# Floorplan Generator

CLI tool for generating synthetic Russian apartment floorplan datasets in SVG format.

Procedurally generates realistic floor plans for typical Russian apartments (квартиры) across four class tiers — from economy studios to premium multi-room layouts — complete with furniture placement, doors, windows, risers (стояки), and validation against 72 building-code rules.

## Features

- **Generation pipeline** — two-phase Greedy + CSP algorithm produces complete furnished layouts
- **SVG rendering** — layered output with rooms, walls, doors, windows, furniture, and risers
- **Dimension annotations** — opt-in architectural dimension lines (`--dimensions`) with room-level and overall measurements in meters
- **PNG export** — rasterized output via CairoSVG
- **Segmentation masks** — flat-color SVG/PNG for ML datasets with per-pixel semantic class encoding
- **Themes** — built-in `blueprint` and `colored` themes; bring your own via custom JSON
- **72 validation rules** — 39 planning rules (P01–P39) and 33 furniture rules (F01–F33) based on Russian GOST/SNiP standards and Neufert ergonomics
- **4 apartment classes** — Economy, Comfort, Business, Premium
- **1–4 living rooms** — from studios to large family apartments, 17 room types total
- **45 furniture items** — beds, sofas, kitchen appliances, bathroom fixtures, storage, composite items (washer+dryer) with automatic fallback to smaller variants
- **Deterministic seeds** — reproducible generation with configurable random seeds
- **JSON + SVG output** — machine-readable apartment data alongside rendered floor plans

## Quick Start

```bash
# Install
uv sync

# Generate 10 economy 1-room apartments
floorplan generate

# Generate 50 premium 3-room apartments with colored theme
floorplan generate --class premium --rooms 3 --count 50 --theme colored

# Generate with PNG and segmentation masks
floorplan generate --class comfort --rooms 2 --png --mask

# Generate with dimension annotations
floorplan generate --class comfort --rooms 2 --dimensions

# Re-render existing JSON files with a different theme
floorplan render --input ./output --output ./colored --theme colored
```

## CLI Reference

### `floorplan generate`

Generate apartment floorplans and save as JSON + SVG.

```
floorplan generate [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--class` | `-c` | `economy` | Apartment class: `economy`, `comfort`, `business`, `premium` |
| `--rooms` | `-r` | `1` | Number of living rooms (1–4) |
| `--count` | `-n` | `10` | Number of apartments to generate |
| `--seed` | `-s` | `42` | Random seed for reproducibility |
| `--output` | `-o` | `./output` | Output directory |
| `--theme` | `-t` | `blueprint` | Theme name or path to custom JSON |
| `--max-restarts` | | `10` | Max generation restarts per apartment |
| `--png` | | off | Also export PNG renders |
| `--mask` | | off | Also export segmentation masks |
| `--dimensions` | `-d` | off | Add dimension annotations (arrows with measurements in meters) |

### `floorplan render`

Re-render existing apartment JSON files to SVG with a different theme.

```
floorplan render [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--input` | `-i` | *(required)* | Input directory with JSON files |
| `--output` | `-o` | *(required)* | Output directory for SVGs |
| `--theme` | `-t` | `blueprint` | Theme name or path to custom JSON |
| `--png` | | off | Also export PNG renders |
| `--mask` | | off | Also export segmentation masks |
| `--dimensions` | `-d` | off | Add dimension annotations (arrows with measurements in meters) |

## Architecture

The generation pipeline runs five stages:

```
Compose → Greedy → CSP → Validate → Render
```

1. **Compose** — determines room composition and sizes based on apartment class and room count
2. **Greedy layout** — places rooms on a canvas using priority-based sequential attachment with scoring (adjacency, zoning, external walls)
3. **CSP solver** — fills in details via constraint satisfaction: doors on shared walls, windows on external walls, risers in wet zones, furniture with backtracking placement and automatic downgrade fallbacks
4. **Validate** — checks the result against 72 mandatory and recommended rules (P01–P39 planning, F01–F33 furniture); retries if too many violations
5. **Render** — produces layered SVG: background → room fills → furniture → walls → doors → windows → risers → dimension annotations (opt-in)

### Segmentation Masks

The segmentation renderer produces flat-color images for ML training. Each pixel encodes a semantic class:

| Class IDs | Category |
|-----------|----------|
| 0 | Background |
| 1–17 | Room types |
| 18–19 | Outer / inner walls |
| 20 | Door |
| 21 | Window |
| 22+ | Furniture types |

### Wall Geometry

Wall polygons (outer and inner) are computed using Shapely. Outer walls are buffered from room boundaries; inner walls are constructed from shared edges between adjacent rooms. Both support cutouts for doors and windows.

## Room Types (17)

| Category | Types |
|----------|-------|
| Living | Living room, Bedroom, Children, Cabinet |
| Kitchen | Kitchen, Kitchen-dining, Kitchen niche |
| Wet zones | Bathroom, Toilet, Combined bathroom, Laundry |
| Transit | Hallway, Corridor, Hall |
| Utility | Storage, Wardrobe, Balcony |

## Furniture (45 items)

| Category | Items |
|----------|-------|
| Plumbing (9) | Bathtub, Shower, Sink, Double sink, Toilet bowl, Bidet, Washing machine, Dryer, Washer+dryer |
| Kitchen (9) | Stove, Hob, Oven, Fridge, Fridge side-by-side, Dishwasher, Kitchen sink, Hood, Microwave |
| Living room (8) | Sofa 2/3/4-seat, Corner sofa, Armchair, Coffee table, TV stand, Shelving |
| Bedroom (8) | Bed single/double/king, Nightstand, Dresser, Wardrobe sliding/swing, Vanity |
| Children (3) | Child bed, Child desk, Child wardrobe |
| Hallway (4) | Hallway wardrobe, Shoe rack, Bench, Coat rack |
| General (4) | Dining table, Dining chair, Desk, Bookshelf |

Composite items like `WASHER_DRYER` (1200x550mm) automatically downgrade to `WASHING_MACHINE` (600x500mm) when the room is too small. Nightstands are placed as a pair flanking the bed headboard when space permits.

## Validation Rules (72)

### Planning Rules (P01–P39)

- **P01–P05** — Minimum area requirements (living room, bedroom, kitchen)
- **P06–P10** — Minimum width constraints (kitchen, corridor, hallway, bathroom)
- **P11** — Living room aspect ratio
- **P12–P14** — Window placement and sizing
- **P15–P19** — Adjacency and connectivity
- **P20–P23** — Door rules (entrance width, bathroom swing direction, collision detection, gaps)
- **P24–P25** — Wet zone grouping and ensuite placement
- **P26–P28** — Recommendations (living room width, central position, dining placement)
- **P29–P34** — Height, ventilation, waterproofing checks
- **P35–P39** — Single-door utility rooms, entrance door, wardrobe connection, external wall windows, kitchen passthrough

### Furniture Rules (F01–F33)

- **F01–F05** — Bathroom clearances (toilet, sink, bathtub, outlet distance)
- **F06–F13** — Kitchen triangle, sink-stove distance, hood height, fridge-stove gap, parallel rows
- **F14–F16** — Bedroom passages (bed, wardrobe, drawers)
- **F17–F18** — Safety (oven clearance, minimum passage)
- **F19–F20** — Dining (table-wall passage, shelf height)
- **F21–F29** — Living room layout (sofa-armchair distance, furniture ratio, TV placement)
- **F30–F33** — Entry zone, washer gap, toilet-riser distance, TV faces sofa

## Project Structure

```
src/floorplan_generator/
├── cli.py                        # Typer CLI entry point
├── core/
│   ├── enums.py                  # RoomType, ApartmentClass, FurnitureType, etc.
│   ├── models.py                 # Apartment, Room, Door, Window, FurnitureItem
│   ├── dimensions.py             # Russian building codes & furniture sizes
│   └── geometry.py               # Point, Polygon, Rectangle, Segment
├── rules/
│   ├── registry.py               # Rule registry (P01–P39, F01–F33)
│   ├── rule_engine.py            # RuleValidator base class
│   ├── planning_rules.py         # 39 planning validators
│   ├── furniture_rules.py        # 33 furniture validators
│   └── geometry_helpers.py       # Geometry utilities for rules
├── generator/
│   ├── layout_engine.py          # Orchestrator: Compose → Greedy → CSP
│   ├── factory.py                # generate_dataset, generate_single
│   ├── room_composer.py          # Room composition & sizing
│   ├── types.py                  # RoomSpec, GreedyResult, CSPResult, GenerationResult
│   ├── greedy/
│   │   ├── engine.py             # Greedy layout with restarts
│   │   ├── priority.py           # Room placement priority queue
│   │   ├── candidates.py         # Candidate slot generation
│   │   └── scoring.py            # Slot scoring function
│   └── csp/
│       ├── solver.py             # CSP orchestrator
│       ├── door_placer.py        # Door placement on shared walls
│       ├── window_placer.py      # Window placement on external walls
│       ├── riser_placer.py       # Riser placement in wet zones
│       ├── furniture_placer.py   # Backtracking placement with downgrade fallback
│       └── constraints.py        # CSP constraint definitions
└── renderer/
    ├── svg_renderer.py           # Main SVG orchestrator
    ├── dimension_renderer.py     # Dimension annotation chains (arrows + labels)
    ├── segmentation.py           # Segmentation mask renderer for ML
    ├── outline.py                # Wall polygon computation (Shapely)
    ├── coordinate_mapper.py      # Canvas → SVG coordinate transform
    ├── theme.py                  # Theme model & loader
    ├── room_renderer.py          # Room fills & labels
    ├── wall_renderer.py          # Outer & inner walls
    ├── door_renderer.py          # Doors with swing arcs
    ├── window_renderer.py        # Window markers
    ├── furniture_renderer.py     # Furniture shapes
    ├── riser_renderer.py         # Riser pipe circles
    ├── symbols/
    │   └── furniture.py          # 45 furniture SVG symbol definitions
    └── themes/
        ├── blueprint.json        # Black & white architectural style
        └── colored.json          # Material Design colors per room type
```

## Themes

### Built-in themes

**blueprint** (default) — classic black-and-white architectural drawing style.

**colored** — Material Design palette with distinct colors per room type: living rooms in blue (#E3F2FD), bedrooms in indigo (#E8EAF6), kitchens in orange (#FFF3E0), bathrooms in cyan (#E0F7FA), and more.

### Custom themes

Create a JSON file following the theme schema and pass its path:

```bash
floorplan generate --theme /path/to/my_theme.json
```

Theme JSON structure:

```json
{
  "name": "my_theme",
  "canvas": { "width": 2000, "height": 2000, "background": "#FFFFFF" },
  "walls": { "outer_stroke": "#000000", "outer_width": 4.0, "inner_width": 1.5 },
  "rooms": { "default_fill": "none", "default_stroke": "#000000", "fills": {} },
  "doors": { "stroke": "#000000" },
  "windows": { "stroke": "#000000", "fill": "#FFFFFF" },
  "furniture": { "stroke": "#000000", "fill": "none" },
  "riser": { "stroke": "#000000", "fill": "#000000", "radius": 3.0 },
  "dimensions": { "stroke": "#000000", "font_size": 16, "offset": 40.0, "precision": 2 }
}
```

The `rooms.fills` object maps room types to colors (e.g. `"living_room": "#E3F2FD"`).

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests (297 tests across 12 test files)
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Lint
ruff check src tests

# Format
ruff format src tests
```

## Tech Stack

- **Python** >= 3.12
- **Pydantic** >= 2.0 — data models and validation
- **Typer** >= 0.9 — CLI framework
- **svgwrite** >= 1.4 — SVG generation
- **Shapely** >= 2.0 — geometry operations (wall polygons, intersections)
- **CairoSVG** >= 2.7 — SVG to PNG conversion
- **lxml** >= 5.0 — XML processing
- **pytest** >= 8.0 — testing
- **ruff** >= 0.4 — linting and formatting
- **uv** — package management
- **hatchling** — build backend
