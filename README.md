# Floorplan Generator

CLI tool for generating synthetic Russian apartment floorplan datasets in SVG format.

Procedurally generates realistic floor plans for typical Russian apartments (квартиры) across four class tiers — from economy studios to premium multi-room layouts — complete with furniture placement, doors, windows, and validation against 66 building-code rules.

## Features

- **Generation pipeline** — two-phase Greedy + CSP algorithm produces complete furnished layouts
- **SVG rendering** — layered output with rooms, walls, doors, windows, furniture, and risers (стояки)
- **Themes** — built-in `blueprint` and `colored` themes; bring your own via custom JSON
- **66 validation rules** — 34 planning rules (P01–P34) and 32 furniture rules (F01–F32) based on Russian GOST/SNiP standards and Neufert ergonomics
- **4 apartment classes** — Economy (экономкласс), Comfort (комфорт), Business (бизнес), Premium (премиум)
- **1–4 living rooms** — from studios to large family apartments, 16 room types total
- **60+ furniture items** — beds, sofas, kitchen appliances, bathroom fixtures, storage
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

## Architecture

The generation pipeline runs four stages:

```
Compose → Greedy → CSP → Validate → Render
```

1. **Compose** — determines room composition and sizes based on apartment class and room count
2. **Greedy layout** — places rooms on a canvas using priority-based sequential attachment with scoring (adjacency, zoning, external walls)
3. **CSP solver** — fills in details via constraint satisfaction: doors on shared walls, windows on external walls, risers in wet zones, furniture with backtracking placement
4. **Validate** — checks the result against 66 mandatory and recommended rules (P01–P34 planning, F01–F32 furniture); retries if too many violations
5. **Render** — produces layered SVG: background → room fills → furniture → walls → doors → windows → risers

## Project Structure

```
src/floorplan_generator/
├── cli.py                    # Typer CLI entry point
├── core/
│   ├── enums.py              # RoomType, ApartmentClass, DoorType
│   ├── models.py             # Apartment, Room, Door, Window, FurnitureItem
│   ├── dimensions.py         # Russian building codes & furniture sizes
│   └── geometry.py           # Point, Polygon, Rectangle, Segment
├── rules/
│   ├── registry.py           # Rule registry (P01–P34, F01–F32)
│   ├── rule_engine.py        # RuleValidator base class
│   ├── planning_rules.py     # 34 planning validators
│   ├── furniture_rules.py    # 32 furniture validators
│   └── geometry_helpers.py   # Geometry utilities for rules
├── generator/
│   ├── layout_engine.py      # Orchestrator: Compose → Greedy → CSP
│   ├── factory.py            # generate_dataset, generate_single
│   ├── room_composer.py      # Room composition & sizing
│   ├── types.py              # RoomSpec, GreedyResult, CSPResult
│   ├── greedy/
│   │   ├── engine.py         # Greedy layout with restarts
│   │   ├── priority.py       # Room placement priority queue
│   │   ├── candidates.py     # Candidate slot generation
│   │   └── scoring.py        # Slot scoring function
│   └── csp/
│       ├── solver.py         # CSP orchestrator
│       ├── door_placer.py    # Door placement on shared walls
│       ├── window_placer.py  # Window placement on external walls
│       ├── riser_placer.py  # Riser placement
│       ├── furniture_placer.py # Furniture with backtracking
│       └── constraints.py    # CSP constraint definitions
└── renderer/
    ├── svg_renderer.py       # render_svg, render_svg_to_file
    ├── theme.py              # Theme model & loader
    ├── coordinate_mapper.py  # Canvas → SVG coordinate transform
    ├── room_renderer.py      # Room fills & labels
    ├── wall_renderer.py      # Outer & inner walls
    ├── door_renderer.py      # Doors with swing arcs
    ├── window_renderer.py    # Window markers
    ├── furniture_renderer.py # Furniture shapes
    ├── riser_renderer.py    # Riser pipe circles
    └── themes/
        ├── blueprint.json    # Black & white architectural style
        └── colored.json      # Material Design colors per room type
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
  "riser": { "stroke": "#000000", "fill": "#000000", "radius": 3.0 }
}
```

The `rooms.fills` object maps room types to colors (e.g. `"living_room": "#E3F2FD"`).

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
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
- **lxml** >= 5.0 — XML processing
- **pytest** >= 8.0 — testing
- **ruff** >= 0.4 — linting and formatting
- **uv** — package management
- **hatchling** — build backend
