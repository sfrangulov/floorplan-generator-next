# Phase 4: SVG Renderer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement SVG rendering pipeline that converts GenerationResult into production-quality SVG floorplan files with configurable JSON themes, furniture symbols extracted from reference SVGs, and CLI commands.

**Architecture:** Layered renderer using `svgwrite` library. CoordinateMapper converts mm→SVG units. Each element type (rooms, walls, doors, windows, furniture, stoyaks) has its own renderer module. JSON theme files control colors/strokes. Furniture shapes stored as normalized SVG path data in Python dict, rendered via `<symbol>` + `<use>`.

**Tech Stack:** Python 3.12+, svgwrite, pydantic v2, pytest, ruff, typer

---

### Task 1: Add svgwrite dependency + renderer package structure

**Files:**
- Modify: `pyproject.toml`
- Create: `src/floorplan_generator/renderer/__init__.py`
- Create: `src/floorplan_generator/renderer/themes/` (directory)
- Create: `src/floorplan_generator/renderer/symbols/` (directory)
- Create: `src/floorplan_generator/renderer/symbols/__init__.py`

**Step 1: Add svgwrite to pyproject.toml**

In `pyproject.toml`, add `"svgwrite>=1.4"` to the `dependencies` list:

```toml
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9",
    "lxml>=5.0",
    "svgwrite>=1.4",
]
```

**Step 2: Install dependency**

Run: `uv pip install -e ".[dev]"`
Expected: svgwrite installs successfully

**Step 3: Create package stubs**

`src/floorplan_generator/renderer/__init__.py`:
```python
"""SVG renderer for floorplan visualization."""
```

`src/floorplan_generator/renderer/symbols/__init__.py`:
```python
"""Furniture SVG symbol definitions."""
```

**Step 4: Verify**

Run: `uv run python -c "import svgwrite; print(svgwrite.version)"`
Expected: prints version number

**Step 5: Commit**

```bash
git add pyproject.toml src/floorplan_generator/renderer/
git commit -m "chore: add svgwrite dependency and renderer package structure"
```

---

### Task 2: Theme system

**Files:**
- Create: `src/floorplan_generator/renderer/theme.py`
- Create: `src/floorplan_generator/renderer/themes/blueprint.json`
- Create: `src/floorplan_generator/renderer/themes/colored.json`

**Step 1: Write theme.py**

```python
"""Theme loading and validation for SVG renderer."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

_THEMES_DIR = Path(__file__).parent / "themes"


class CanvasTheme(BaseModel):
    width: int = 2000
    height: int = 2000
    background: str = "#FFFFFF"


class WallTheme(BaseModel):
    outer_stroke: str = "#000000"
    outer_width: float = 4.0
    inner_stroke: str = "#000000"
    inner_width: float = 1.5


class RoomTheme(BaseModel):
    default_fill: str = "none"
    default_stroke: str = "#000000"
    stroke_width: float = 0.5
    fills: dict[str, str] = {}


class DoorTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 1.0
    arc_stroke: str = "#000000"
    arc_width: float = 0.5
    gap_fill: str = "#FFFFFF"


class WindowTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 1.0
    fill: str = "#FFFFFF"
    cross_stroke: str = "#000000"


class FurnitureTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 0.8
    fill: str = "none"


class StoyakTheme(BaseModel):
    stroke: str = "#000000"
    fill: str = "#000000"
    radius: float = 3.0


class TextTheme(BaseModel):
    font_family: str = "Arial, sans-serif"
    font_size: int = 14
    fill: str = "#333333"
    area_font_size: int = 11


class Theme(BaseModel):
    """Complete SVG rendering theme."""

    name: str = "default"
    canvas: CanvasTheme = CanvasTheme()
    walls: WallTheme = WallTheme()
    rooms: RoomTheme = RoomTheme()
    doors: DoorTheme = DoorTheme()
    windows: WindowTheme = WindowTheme()
    furniture: FurnitureTheme = FurnitureTheme()
    stoyak: StoyakTheme = StoyakTheme()
    text: TextTheme = TextTheme()


def load_theme(name_or_path: str) -> Theme:
    """Load a theme by name (built-in) or file path.

    Built-in themes: 'blueprint', 'colored'.
    Custom themes: pass a path to a JSON file.
    """
    # Try built-in theme first
    builtin_path = _THEMES_DIR / f"{name_or_path}.json"
    if builtin_path.exists():
        data = json.loads(builtin_path.read_text())
        return Theme(**data)

    # Try as file path
    custom_path = Path(name_or_path)
    if custom_path.exists():
        data = json.loads(custom_path.read_text())
        return Theme(**data)

    msg = f"Theme not found: {name_or_path}"
    raise FileNotFoundError(msg)


def get_default_theme() -> Theme:
    """Return the default blueprint theme."""
    return load_theme("blueprint")
```

**Step 2: Write blueprint.json**

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

**Step 3: Write colored.json**

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
    "inner_width": 1.5
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
  "stoyak": {
    "stroke": "#D32F2F",
    "fill": "#EF5350",
    "radius": 4.0
  },
  "text": {
    "font_family": "Arial, sans-serif",
    "font_size": 14,
    "fill": "#263238",
    "area_font_size": 11
  }
}
```

**Step 4: Lint check**

Run: `uv run ruff check src/floorplan_generator/renderer/theme.py`
Expected: no errors

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/theme.py src/floorplan_generator/renderer/themes/
git commit -m "feat: add theme system with blueprint and colored JSON themes"
```

---

### Task 3: Coordinate mapper

**Files:**
- Create: `src/floorplan_generator/renderer/coordinate_mapper.py`

**Step 1: Write coordinate_mapper.py**

```python
"""Coordinate mapping from mm (domain) to SVG units."""

from __future__ import annotations

from floorplan_generator.core.geometry import Point
from floorplan_generator.core.models import Room


class CoordinateMapper:
    """Maps millimeter coordinates to SVG canvas coordinates.

    Computes scale and offset to fit all rooms within the canvas
    with padding, preserving aspect ratio.
    """

    def __init__(
        self,
        rooms: list[Room],
        canvas_width: int = 2000,
        canvas_height: int = 2000,
        padding: int = 100,
    ) -> None:
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.padding = padding

        # Compute bounding box of all rooms in mm
        all_xs: list[float] = []
        all_ys: list[float] = []
        for room in rooms:
            for pt in room.boundary.points:
                all_xs.append(pt.x)
                all_ys.append(pt.y)

        if not all_xs:
            self.scale = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0
            self.mm_min_x = 0.0
            self.mm_min_y = 0.0
            return

        self.mm_min_x = min(all_xs)
        self.mm_min_y = min(all_ys)
        mm_max_x = max(all_xs)
        mm_max_y = max(all_ys)

        mm_width = mm_max_x - self.mm_min_x
        mm_height = mm_max_y - self.mm_min_y

        if mm_width == 0 or mm_height == 0:
            self.scale = 1.0
            self.offset_x = float(padding)
            self.offset_y = float(padding)
            return

        available_w = canvas_width - 2 * padding
        available_h = canvas_height - 2 * padding

        scale_x = available_w / mm_width
        scale_y = available_h / mm_height
        self.scale = min(scale_x, scale_y)

        # Center on canvas
        scaled_w = mm_width * self.scale
        scaled_h = mm_height * self.scale
        self.offset_x = (canvas_width - scaled_w) / 2
        self.offset_y = (canvas_height - scaled_h) / 2

    def to_svg(self, point: Point) -> tuple[float, float]:
        """Convert mm point to SVG coordinates."""
        x = (point.x - self.mm_min_x) * self.scale + self.offset_x
        y = (point.y - self.mm_min_y) * self.scale + self.offset_y
        return (round(x, 1), round(y, 1))

    def scale_length(self, mm_length: float) -> float:
        """Convert mm length to SVG length (no offset)."""
        return round(mm_length * self.scale, 1)
```

**Step 2: Lint check**

Run: `uv run ruff check src/floorplan_generator/renderer/coordinate_mapper.py`
Expected: no errors

**Step 3: Commit**

```bash
git add src/floorplan_generator/renderer/coordinate_mapper.py
git commit -m "feat: add coordinate mapper (mm to SVG units)"
```

---

### Task 4: Furniture SVG symbols

**Files:**
- Create: `src/floorplan_generator/renderer/symbols/furniture.py`

**Step 1: Write furniture.py**

This stores normalized SVG drawing instructions for each FurnitureType. Each entry is a function that draws the furniture at (0,0) at canonical size using svgwrite group.

```python
"""SVG symbol definitions for furniture types.

Each function draws the furniture shape into an svgwrite group at (0,0)
with the given width and depth. Shapes are extracted from reference SVGs
in docs/svg/ and simplified for programmatic generation.

All drawing functions have signature:
    def draw_xxx(group, w, d, style) -> None
where w=width, d=depth (in SVG units), style=dict with stroke/fill.
"""

from __future__ import annotations

import math

import svgwrite.container
import svgwrite.drawing


def _style(s: dict) -> dict:
    """Convert style dict to svgwrite kwargs."""
    return {
        "stroke": s.get("stroke", "#000000"),
        "fill": s.get("fill", "none"),
        "stroke_width": s.get("stroke_width", 0.8),
        "stroke_linecap": "round",
        "stroke_linejoin": "round",
    }


def draw_bathtub(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bathtub: outer rect + inner rounded basin + shelf strip."""
    s = _style(style)
    # Shelf strip at top
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, d * 0.04), **s,
    ))
    # Main body
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, d * 0.04), size=(w, d * 0.96), **s,
    ))
    # Inner basin (inset rect with rounded corners)
    inset = w * 0.08
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(inset, d * 0.15),
        size=(w - 2 * inset, d * 0.78),
        rx=w * 0.05, ry=d * 0.05,
        **s,
    ))
    # Drain circle
    g.add(svgwrite.drawing.Drawing().circle(
        center=(w * 0.5, d * 0.85), r=w * 0.025, **s,
    ))


def draw_toilet(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Toilet: tank rect + oval bowl."""
    s = _style(style)
    tank_h = d * 0.35
    # Tank
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, tank_h), **s,
    ))
    # Bowl (ellipse)
    g.add(svgwrite.drawing.Drawing().ellipse(
        center=(w / 2, tank_h + (d - tank_h) / 2),
        r=(w * 0.42, (d - tank_h) * 0.48),
        **s,
    ))
    # Inner bowl
    g.add(svgwrite.drawing.Drawing().ellipse(
        center=(w / 2, tank_h + (d - tank_h) * 0.55),
        r=(w * 0.28, (d - tank_h) * 0.3),
        **s,
    ))


def draw_sink(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Sink: rect body + inner oval basin."""
    s = _style(style)
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, d), **s,
    ))
    # Basin oval
    g.add(svgwrite.drawing.Drawing().ellipse(
        center=(w / 2, d * 0.55), r=(w * 0.35, d * 0.3), **s,
    ))
    # Faucet circle
    g.add(svgwrite.drawing.Drawing().circle(
        center=(w / 2, d * 0.15), r=w * 0.05, **s,
    ))


def draw_washing_machine(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Washing machine: rect + large drum circle + inner circles."""
    s = _style(style)
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, d), **s,
    ))
    r_drum = min(w, d) * 0.38
    cx, cy = w / 2, d / 2
    g.add(svgwrite.drawing.Drawing().circle(
        center=(cx, cy), r=r_drum, **s,
    ))
    g.add(svgwrite.drawing.Drawing().circle(
        center=(cx, cy), r=r_drum * 0.25, **s,
    ))


def draw_stove(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Stove/cooktop: rect body + 4 burner circles (2x2 grid)."""
    s = _style(style)
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, d), rx=2, ry=2, **s,
    ))
    burner_r = min(w, d) * 0.12
    inner_r = burner_r * 0.57
    positions = [
        (w * 0.3, d * 0.3), (w * 0.7, d * 0.3),
        (w * 0.3, d * 0.7), (w * 0.7, d * 0.7),
    ]
    for bx, by in positions:
        g.add(svgwrite.drawing.Drawing().circle(
            center=(bx, by), r=burner_r, **s,
        ))
        g.add(svgwrite.drawing.Drawing().circle(
            center=(bx, by), r=inner_r, **s,
        ))


def draw_fridge(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Fridge: rect + snowflake cross pattern."""
    s = _style(style)
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, d), **s,
    ))
    cx, cy = w / 2, d / 2
    arm = min(w, d) * 0.25
    # Cross lines
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.line(
        start=(cx - arm, cy), end=(cx + arm, cy), **s,
    ))
    g.add(dwg.line(
        start=(cx, cy - arm), end=(cx, cy + arm), **s,
    ))
    # Arrow tips (4 V-shapes)
    tip = arm * 0.4
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        ex, ey = cx + dx * arm, cy + dy * arm
        g.add(dwg.line(
            start=(ex, ey),
            end=(ex - dy * tip * 0.5 - dx * tip, ey - dx * tip * 0.5 - dy * tip),
            **s,
        ))
        g.add(dwg.line(
            start=(ex, ey),
            end=(ex + dy * tip * 0.5 - dx * tip, ey + dx * tip * 0.5 - dy * tip),
            **s,
        ))


def draw_bed(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bed: headboard rect + mattress rect + pillow section paths."""
    s = _style(style)
    head_h = d * 0.04
    # Headboard
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, head_h), **s,
    ))
    # Mattress body
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, head_h), size=(w, d - head_h), **s,
    ))
    # Pillow area (two pillows side by side)
    pillow_h = d * 0.15
    pillow_w = w * 0.45
    gap = w * 0.05
    for px in [gap, w - gap - pillow_w]:
        g.add(svgwrite.drawing.Drawing().rect(
            insert=(px, head_h + d * 0.02),
            size=(pillow_w, pillow_h),
            rx=pillow_h * 0.3, ry=pillow_h * 0.3,
            **s,
        ))


def draw_sofa(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Sofa: seat cushion (rounded rect) + backrest."""
    s = _style(style)
    back_d = d * 0.25
    # Backrest
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, 0), size=(w, back_d), **s,
    ))
    # Seat (rounded rect)
    g.add(svgwrite.drawing.Drawing().rect(
        insert=(0, back_d), size=(w, d - back_d),
        rx=d * 0.08, ry=d * 0.08, **s,
    ))


def draw_wardrobe(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Wardrobe: rect + door division line + shelf lines."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    # Door edge line (near front)
    g.add(dwg.line(start=(0, d * 0.95), end=(w, d * 0.95), **s))
    # Shelf divisions
    g.add(dwg.line(start=(0, d * 0.33), end=(w, d * 0.33), **s))
    g.add(dwg.line(start=(0, d * 0.66), end=(w, d * 0.66), **s))


def draw_nightstand(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Nightstand: rect + single drawer line."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    g.add(dwg.line(start=(w * 0.05, d * 0.5), end=(w, d * 0.5), **s))


def draw_table(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Dining/coffee table: rect with inset line."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    inset = min(w, d) * 0.08
    g.add(dwg.rect(
        insert=(inset, inset), size=(w - 2 * inset, d - 2 * inset), **s,
    ))


def draw_chair(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Chair: seat square + backrest line."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, d * 0.2), size=(w, d * 0.8), **s))
    # Backrest
    g.add(dwg.rect(insert=(0, 0), size=(w, d * 0.2), **s))


def draw_desk(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Desk: rect + front edge line."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    g.add(dwg.line(start=(0, d * 0.92), end=(w, d * 0.92), **s))


def draw_tv_stand(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """TV stand: wide rect + shelf divisions."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    g.add(dwg.line(start=(0, d * 0.9), end=(w, d * 0.9), **s))
    g.add(dwg.line(start=(w * 0.33, 0), end=(w * 0.33, d), **s))
    g.add(dwg.line(start=(w * 0.66, 0), end=(w * 0.66, d), **s))


def draw_hood(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Range hood: 4 concentric circles."""
    s = _style(style)
    cx, cy = w / 2, d / 2
    r_max = min(w, d) * 0.45
    for frac in [1.0, 0.73, 0.47, 0.2]:
        g.add(svgwrite.drawing.Drawing().circle(
            center=(cx, cy), r=r_max * frac, **s,
        ))


def draw_rect_fallback(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
    label: str = "",
) -> None:
    """Fallback: simple rect with optional type label."""
    s = _style(style)
    dwg = svgwrite.drawing.Drawing()
    g.add(dwg.rect(insert=(0, 0), size=(w, d), **s))
    if label:
        g.add(dwg.text(
            label,
            insert=(w / 2, d / 2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=max(6, min(w, d) * 0.15),
            font_family="Arial, sans-serif",
            fill=s.get("stroke", "#000000"),
        ))


# --- Registry mapping FurnitureType -> draw function ---

from floorplan_generator.core.enums import FurnitureType  # noqa: E402

FURNITURE_DRAWERS: dict[FurnitureType, callable] = {
    FurnitureType.BATHTUB: draw_bathtub,
    FurnitureType.TOILET_BOWL: draw_toilet,
    FurnitureType.SINK: draw_sink,
    FurnitureType.KITCHEN_SINK: draw_sink,
    FurnitureType.WASHING_MACHINE: draw_washing_machine,
    FurnitureType.STOVE: draw_stove,
    FurnitureType.HOB: draw_stove,
    FurnitureType.FRIDGE: draw_fridge,
    FurnitureType.FRIDGE_SIDE_BY_SIDE: draw_fridge,
    FurnitureType.BED_SINGLE: draw_bed,
    FurnitureType.BED_DOUBLE: draw_bed,
    FurnitureType.BED_KING: draw_bed,
    FurnitureType.CHILD_BED: draw_bed,
    FurnitureType.SOFA_2: draw_sofa,
    FurnitureType.SOFA_3: draw_sofa,
    FurnitureType.SOFA_4: draw_sofa,
    FurnitureType.SOFA_CORNER: draw_sofa,
    FurnitureType.ARMCHAIR: draw_sofa,
    FurnitureType.WARDROBE_SLIDING: draw_wardrobe,
    FurnitureType.WARDROBE_SWING: draw_wardrobe,
    FurnitureType.HALLWAY_WARDROBE: draw_wardrobe,
    FurnitureType.CHILD_WARDROBE: draw_wardrobe,
    FurnitureType.NIGHTSTAND: draw_nightstand,
    FurnitureType.DINING_TABLE: draw_table,
    FurnitureType.COFFEE_TABLE: draw_table,
    FurnitureType.DINING_CHAIR: draw_chair,
    FurnitureType.DESK: draw_desk,
    FurnitureType.CHILD_DESK: draw_desk,
    FurnitureType.TV_STAND: draw_tv_stand,
    FurnitureType.HOOD: draw_hood,
}


def get_drawer(ft: FurnitureType) -> callable:
    """Get the draw function for a furniture type."""
    return FURNITURE_DRAWERS.get(ft, draw_rect_fallback)
```

**Step 2: Lint check**

Run: `uv run ruff check src/floorplan_generator/renderer/symbols/furniture.py`
Expected: no errors

**Step 3: Commit**

```bash
git add src/floorplan_generator/renderer/symbols/furniture.py
git commit -m "feat: add furniture SVG symbol drawing functions (16 detailed + fallback)"
```

---

### Task 5: Room, wall, door, window, stoyak renderers

**Files:**
- Create: `src/floorplan_generator/renderer/room_renderer.py`
- Create: `src/floorplan_generator/renderer/wall_renderer.py`
- Create: `src/floorplan_generator/renderer/door_renderer.py`
- Create: `src/floorplan_generator/renderer/window_renderer.py`
- Create: `src/floorplan_generator/renderer/furniture_renderer.py`
- Create: `src/floorplan_generator/renderer/stoyak_renderer.py`

**Step 1: Write room_renderer.py**

```python
"""Room boundary and label rendering."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

# Human-readable room names (Russian)
_ROOM_NAMES: dict[RoomType, str] = {
    RoomType.LIVING_ROOM: "Гостиная",
    RoomType.BEDROOM: "Спальня",
    RoomType.CHILDREN: "Детская",
    RoomType.CABINET: "Кабинет",
    RoomType.KITCHEN: "Кухня",
    RoomType.KITCHEN_DINING: "Кухня-столовая",
    RoomType.KITCHEN_NICHE: "Кухня-ниша",
    RoomType.HALLWAY: "Прихожая",
    RoomType.CORRIDOR: "Коридор",
    RoomType.HALL: "Холл",
    RoomType.BATHROOM: "Ванная",
    RoomType.TOILET: "Туалет",
    RoomType.COMBINED_BATHROOM: "Санузел",
    RoomType.STORAGE: "Кладовая",
    RoomType.WARDROBE: "Гардероб",
    RoomType.LAUNDRY: "Постирочная",
    RoomType.BALCONY: "Балкон",
}


def render_rooms(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render room fill polygons and text labels."""
    for room in rooms:
        points = [mapper.to_svg(pt) for pt in room.boundary.points]
        fill = theme.rooms.fills.get(room.room_type.value, theme.rooms.default_fill)

        # Room fill polygon
        group.add(dwg.polygon(
            points=points,
            fill=fill,
            stroke=theme.rooms.default_stroke,
            stroke_width=theme.rooms.stroke_width,
        ))

        # Label at centroid
        centroid = room.boundary.centroid
        cx, cy = mapper.to_svg(centroid)
        name = _ROOM_NAMES.get(room.room_type, room.room_type.value)
        area = f"{room.area_m2:.1f} м²"

        group.add(dwg.text(
            name,
            insert=(cx, cy - 6),
            text_anchor="middle",
            font_family=theme.text.font_family,
            font_size=theme.text.font_size,
            fill=theme.text.fill,
        ))
        group.add(dwg.text(
            area,
            insert=(cx, cy + 10),
            text_anchor="middle",
            font_family=theme.text.font_family,
            font_size=theme.text.area_font_size,
            fill=theme.text.fill,
        ))
```

**Step 2: Write wall_renderer.py**

```python
"""Wall rendering: outer perimeter (thick) + inner partitions (thin)."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.geometry import Point, Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_EDGE_EPS = 1.0  # mm tolerance for shared edge detection


def _room_edges(room: Room) -> list[Segment]:
    """Get all edges of a room boundary as segments."""
    pts = room.boundary.points
    n = len(pts)
    return [
        Segment(start=pts[i], end=pts[(i + 1) % n])
        for i in range(n)
    ]


def _segments_overlap(a: Segment, b: Segment, eps: float = _EDGE_EPS) -> bool:
    """Check if two segments share a collinear overlap (shared wall)."""
    # Both must be axis-aligned for simple check
    a_horiz = abs(a.start.y - a.end.y) < eps
    b_horiz = abs(b.start.y - b.end.y) < eps
    a_vert = abs(a.start.x - a.end.x) < eps
    b_vert = abs(b.start.x - b.end.x) < eps

    if a_horiz and b_horiz and abs(a.start.y - b.start.y) < eps:
        a_min = min(a.start.x, a.end.x)
        a_max = max(a.start.x, a.end.x)
        b_min = min(b.start.x, b.end.x)
        b_max = max(b.start.x, b.end.x)
        return a_min < b_max - eps and b_min < a_max - eps

    if a_vert and b_vert and abs(a.start.x - b.start.x) < eps:
        a_min = min(a.start.y, a.end.y)
        a_max = max(a.start.y, a.end.y)
        b_min = min(b.start.y, b.end.y)
        b_max = max(b.start.y, b.end.y)
        return a_min < b_max - eps and b_min < a_max - eps

    return False


def _classify_edges(
    rooms: list[Room],
) -> tuple[list[Segment], list[Segment]]:
    """Classify room edges as outer or inner walls.

    An edge is inner if it overlaps with an edge of another room.
    Otherwise it's outer (perimeter).
    """
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


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render outer walls (thick) and inner walls (thin)."""
    outer, inner = _classify_edges(rooms)

    for seg in outer:
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(
            start=start, end=end,
            stroke=theme.walls.outer_stroke,
            stroke_width=theme.walls.outer_width,
            stroke_linecap="round",
        ))

    for seg in inner:
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(
            start=start, end=end,
            stroke=theme.walls.inner_stroke,
            stroke_width=theme.walls.inner_width,
            stroke_linecap="round",
        ))
```

**Step 3: Write door_renderer.py**

```python
"""Door rendering: opening gap + swing arc."""

from __future__ import annotations

import math

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Door, Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_doors(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all doors with opening gap and swing arc."""
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
    """Render a single door: white gap rect + quarter-circle arc."""
    pos = mapper.to_svg(door.position)
    w = mapper.scale_length(door.width)

    # Gap rectangle (covers wall line)
    gap_size = max(w, 4)
    group.add(dwg.rect(
        insert=(pos[0], pos[1] - 2),
        size=(gap_size, 4),
        fill=theme.doors.gap_fill,
        stroke="none",
    ))

    # Swing arc (quarter circle)
    arc_r = w
    # Arc from hinge point
    hx, hy = pos
    # Draw quarter circle arc using SVG path
    # Arc sweeps 90 degrees from the door position
    end_x = hx + arc_r
    end_y = hy - arc_r
    arc_path = f"M {hx},{hy} L {end_x},{hy} A {arc_r},{arc_r} 0 0,0 {hx},{end_y}"

    group.add(dwg.path(
        d=arc_path,
        fill="none",
        stroke=theme.doors.arc_stroke,
        stroke_width=theme.doors.arc_width,
    ))
```

**Step 4: Write window_renderer.py**

```python
"""Window rendering: rect + pane division lines."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all windows with rect and pane lines."""
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
    """Render a single window: filled rect + 3 pane lines."""
    pos = mapper.to_svg(window.position)
    w = mapper.scale_length(window.width)
    wall_depth = 6.0  # visual wall thickness in SVG units

    # Window rect
    group.add(dwg.rect(
        insert=(pos[0], pos[1] - wall_depth / 2),
        size=(w, wall_depth),
        fill=theme.windows.fill,
        stroke=theme.windows.stroke,
        stroke_width=theme.windows.stroke_width,
    ))

    # Pane division lines (3 lines inside)
    for frac in [0.25, 0.5, 0.75]:
        lx = pos[0] + w * frac
        group.add(dwg.line(
            start=(lx, pos[1] - wall_depth / 2),
            end=(lx, pos[1] + wall_depth / 2),
            stroke=theme.windows.cross_stroke,
            stroke_width=theme.windows.stroke_width * 0.5,
        ))
```

**Step 5: Write furniture_renderer.py**

```python
"""Furniture rendering using symbol library."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import FurnitureItem, Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.symbols.furniture import get_drawer
from floorplan_generator.renderer.theme import Theme


def render_furniture(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all furniture items in all rooms."""
    style = {
        "stroke": theme.furniture.stroke,
        "fill": theme.furniture.fill,
        "stroke_width": theme.furniture.stroke_width,
    }
    for room in rooms:
        for item in room.furniture:
            _render_item(dwg, group, item, mapper, style)


def _render_item(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    item: FurnitureItem,
    mapper: CoordinateMapper,
    style: dict,
) -> None:
    """Render a single furniture item at its position with rotation."""
    pos = mapper.to_svg(item.position)
    w = mapper.scale_length(item.width)
    d = mapper.scale_length(item.depth)

    # Create group with transform
    transform = f"translate({pos[0]},{pos[1]})"
    if item.rotation != 0:
        transform += f" rotate({item.rotation},{w / 2},{d / 2})"

    item_group = dwg.g(transform=transform)

    drawer = get_drawer(item.furniture_type)
    if drawer.__name__ == "draw_rect_fallback":
        drawer(item_group, w, d, style, label=item.furniture_type.value)
    else:
        drawer(item_group, w, d, style)

    group.add(item_group)
```

**Step 6: Write stoyak_renderer.py**

```python
"""Stoyak (vertical pipe) rendering."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.generator.types import Stoyak
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_stoyaks(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    stoyaks: list[Stoyak],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render stoyak pipe markers as filled circles."""
    for stoyak in stoyaks:
        pos = mapper.to_svg(stoyak.position)
        group.add(dwg.circle(
            center=pos,
            r=theme.stoyak.radius,
            fill=theme.stoyak.fill,
            stroke=theme.stoyak.stroke,
            stroke_width=1.0,
        ))
```

**Step 7: Lint check all files**

Run: `uv run ruff check src/floorplan_generator/renderer/`
Expected: no errors

**Step 8: Commit**

```bash
git add src/floorplan_generator/renderer/room_renderer.py src/floorplan_generator/renderer/wall_renderer.py src/floorplan_generator/renderer/door_renderer.py src/floorplan_generator/renderer/window_renderer.py src/floorplan_generator/renderer/furniture_renderer.py src/floorplan_generator/renderer/stoyak_renderer.py
git commit -m "feat: add room, wall, door, window, furniture, stoyak renderers"
```

---

### Task 6: Main SVG renderer orchestrator

**Files:**
- Create: `src/floorplan_generator/renderer/svg_renderer.py`

**Step 1: Write svg_renderer.py**

```python
"""Main SVG renderer: orchestrates all sub-renderers."""

from __future__ import annotations

import svgwrite

from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.door_renderer import render_doors
from floorplan_generator.renderer.furniture_renderer import render_furniture
from floorplan_generator.renderer.room_renderer import render_rooms
from floorplan_generator.renderer.stoyak_renderer import render_stoyaks
from floorplan_generator.renderer.theme import Theme, get_default_theme
from floorplan_generator.renderer.wall_renderer import render_walls
from floorplan_generator.renderer.window_renderer import render_windows


def render_svg(
    result: GenerationResult,
    theme: Theme | None = None,
) -> str:
    """Render a GenerationResult to an SVG string.

    Args:
        result: Complete generation result with apartment and stoyaks.
        theme: Rendering theme. Uses blueprint if None.

    Returns:
        SVG content as a string.
    """
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

    # Layer 1: Background
    dwg.add(dwg.rect(
        insert=(0, 0), size=(cw, ch),
        fill=theme.canvas.background,
    ))

    # Layer 2: Room fills + labels
    rooms_group = dwg.g(id="rooms")
    render_rooms(dwg, rooms_group, rooms, mapper, theme)
    dwg.add(rooms_group)

    # Layer 3: Furniture (drawn before walls, matching reference SVGs)
    furniture_group = dwg.g(id="mebel")
    render_furniture(dwg, furniture_group, rooms, mapper, theme)
    dwg.add(furniture_group)

    # Layer 4: Walls (on top of furniture)
    walls_group = dwg.g(id="floor")
    render_walls(dwg, walls_group, rooms, mapper, theme)
    dwg.add(walls_group)

    # Layer 5: Doors
    doors_group = dwg.g(id="doors")
    render_doors(dwg, doors_group, rooms, mapper, theme)
    dwg.add(doors_group)

    # Layer 6: Windows
    windows_group = dwg.g(id="windows")
    render_windows(dwg, windows_group, rooms, mapper, theme)
    dwg.add(windows_group)

    # Layer 7: Stoyaks
    stoyaks_group = dwg.g(id="stoyaks")
    render_stoyaks(dwg, stoyaks_group, result.stoyaks, mapper, theme)
    dwg.add(stoyaks_group)

    return dwg.tostring()


def render_svg_to_file(
    result: GenerationResult,
    path: str,
    theme: Theme | None = None,
) -> None:
    """Render and save SVG to a file."""
    svg_content = render_svg(result, theme)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
```

**Step 2: Lint check**

Run: `uv run ruff check src/floorplan_generator/renderer/svg_renderer.py`
Expected: no errors

**Step 3: Commit**

```bash
git add src/floorplan_generator/renderer/svg_renderer.py
git commit -m "feat: add main SVG renderer orchestrator"
```

---

### Task 7: Write unit tests (RED)

**Files:**
- Create: `tests/unit/test_renderer.py`

**Step 1: Write all 20 unit tests**

```python
"""Unit tests for SVG renderer (R01-R20)."""

from __future__ import annotations

from xml.etree import ElementTree

import pytest

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import (
    Apartment,
    Door,
    FurnitureItem,
    Room,
    Window,
)
from floorplan_generator.generator.types import GenerationResult, Stoyak
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.svg_renderer import render_svg
from floorplan_generator.renderer.theme import Theme, load_theme


def _make_room(
    room_type: RoomType,
    x: float, y: float, w: float, h: float,
    *,
    room_id: str = "",
    doors: list[Door] | None = None,
    windows: list[Window] | None = None,
    furniture: list[FurnitureItem] | None = None,
) -> Room:
    """Helper: create a rectangular room at (x,y) with size (w,h) in mm."""
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
        furniture=furniture or [],
    )


def _make_result(rooms: list[Room], stoyaks: list[Stoyak] | None = None) -> GenerationResult:
    """Helper: wrap rooms into a GenerationResult."""
    apt = Apartment(
        id="test_apt",
        apartment_class=ApartmentClass.ECONOMY,
        rooms=rooms,
        num_rooms=1,
    )
    return GenerationResult(
        apartment=apt,
        stoyaks=stoyaks or [],
        restart_count=0,
        seed_used=42,
        recommended_violations=0,
    )


def _parse_svg(svg_str: str) -> ElementTree.Element:
    """Parse SVG string to XML element tree."""
    return ElementTree.fromstring(svg_str)


# R01
def test_coordinate_mapper_basic():
    """mm point maps to correct SVG coords."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    # Origin should map near padding area
    x, y = mapper.to_svg(Point(x=0, y=0))
    assert 50 < x < 500
    assert 50 < y < 200
    # Far corner
    x2, y2 = mapper.to_svg(Point(x=4000, y=5000))
    assert x2 > 1500
    assert y2 > 1800


# R02
def test_coordinate_mapper_centering():
    """Floorplan centered in canvas."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    center_mm = Point(x=2000, y=2000)
    cx, cy = mapper.to_svg(center_mm)
    # Should be near canvas center (1000, 1000)
    assert 900 < cx < 1100
    assert 900 < cy < 1100


# R03
def test_coordinate_mapper_scale():
    """Scale preserves aspect ratio."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 8000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    # Width is double height in mm; in SVG should maintain ratio
    w_svg = mapper.scale_length(8000)
    h_svg = mapper.scale_length(4000)
    assert abs(w_svg / h_svg - 2.0) < 0.01


# R04
def test_theme_load_blueprint():
    """Load blueprint.json correctly."""
    theme = load_theme("blueprint")
    assert theme.name == "blueprint"
    assert theme.canvas.background == "#FFFFFF"
    assert theme.walls.outer_width == 4.0
    assert theme.rooms.default_fill == "none"


# R05
def test_theme_load_colored():
    """Load colored.json correctly."""
    theme = load_theme("colored")
    assert theme.name == "colored"
    assert theme.rooms.fills.get("living_room") == "#E3F2FD"
    assert theme.rooms.fills.get("kitchen") == "#FFF3E0"
    assert theme.rooms.fills.get("bathroom") == "#E0F7FA"


# R06
def test_theme_custom_json(tmp_path):
    """Load custom theme from file path."""
    custom = tmp_path / "custom.json"
    custom.write_text('{"name": "custom", "canvas": {"background": "#FF0000"}}')
    theme = load_theme(str(custom))
    assert theme.name == "custom"
    assert theme.canvas.background == "#FF0000"


# R07
def test_room_polygon_render():
    """Room boundary renders as SVG polygon."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    polygons = root.findall(".//svg:g[@id='rooms']/svg:polygon", ns)
    assert len(polygons) >= 1


# R08
def test_room_label_render():
    """Room label at centroid with name + area."""
    room = _make_room(RoomType.KITCHEN, 0, 0, 3000, 3000)
    result = _make_result([room])
    svg = render_svg(result)
    assert "Кухня" in svg
    assert "9.0 м²" in svg


# R09
def test_wall_outer_thick():
    """Outer walls drawn with thick stroke."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    result = _make_result([room])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    # Should contain stroke-width matching outer_width
    assert f'stroke-width="{int(theme.walls.outer_width)}"' in svg or \
           f"stroke-width=\"{theme.walls.outer_width}\"" in svg


# R10
def test_wall_inner_thin():
    """Inner walls drawn with thin stroke when rooms share edge."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    result = _make_result([r1, r2])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    lines = root.findall(".//svg:g[@id='floor']/svg:line", ns)
    # Should have both outer and inner wall lines
    assert len(lines) >= 4


# R11
def test_door_gap():
    """Door creates visual element in SVG."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    room = _make_room(
        RoomType.HALLWAY, 0, 0, 2000, 3000,
        room_id="r1", doors=[door],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    door_group = root.findall(".//svg:g[@id='doors']", ns)
    assert len(door_group) == 1
    # Should have children (rect + path)
    assert len(list(door_group[0])) >= 1


# R12
def test_door_swing_arc():
    """Swing arc is quarter circle path."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    room = _make_room(
        RoomType.HALLWAY, 0, 0, 2000, 3000,
        room_id="r1", doors=[door],
    )
    result = _make_result([room])
    svg = render_svg(result)
    # Arc path should contain SVG arc command 'A'
    assert " A " in svg


# R13
def test_window_rect():
    """Window rect on external wall."""
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
    win_group = root.findall(".//svg:g[@id='windows']", ns)
    assert len(win_group) == 1
    assert len(list(win_group[0])) >= 1


# R14
def test_window_panes():
    """Window has pane division lines."""
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
    win_group = root.findall(".//svg:g[@id='windows']", ns)[0]
    lines = win_group.findall("svg:line", ns)
    assert len(lines) >= 3  # 3 pane division lines


# R15
def test_furniture_rendered():
    """Furniture item creates elements in mebel group."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.BATHTUB,
        position=Point(x=100, y=100), width=1700, depth=750,
    )
    room = _make_room(
        RoomType.BATHROOM, 0, 0, 2000, 2000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    mebel = root.findall(".//svg:g[@id='mebel']", ns)
    assert len(mebel) == 1
    assert len(list(mebel[0])) >= 1


# R16
def test_furniture_placement_position():
    """Furniture placed at correct SVG position via transform."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.STOVE,
        position=Point(x=500, y=500), width=600, depth=600,
    )
    room = _make_room(
        RoomType.KITCHEN, 0, 0, 3000, 3000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    assert "translate(" in svg


# R17
def test_furniture_rotation():
    """Rotated furniture has correct transform."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.BED_DOUBLE,
        position=Point(x=500, y=500), width=1600, depth=2000,
        rotation=90.0,
    )
    room = _make_room(
        RoomType.BEDROOM, 0, 0, 4000, 4000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    assert "rotate(90" in svg


# R18
def test_stoyak_circle():
    """Stoyak renders as filled circle."""
    room = _make_room(RoomType.BATHROOM, 0, 0, 2000, 2000)
    stoyak = Stoyak(id="s1", position=Point(x=100, y=100))
    result = _make_result([room], stoyaks=[stoyak])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    stoyak_group = root.findall(".//svg:g[@id='stoyaks']", ns)
    assert len(stoyak_group) == 1
    circles = stoyak_group[0].findall("svg:circle", ns)
    assert len(circles) == 1


# R19
def test_full_render_produces_valid_svg():
    """Full render returns valid SVG string with correct root element."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    result = _make_result([room])
    svg = render_svg(result)
    assert svg.startswith("<?xml") or "<svg" in svg[:200]
    root = _parse_svg(svg)
    assert root.tag.endswith("svg")


# R20
def test_full_render_layers_order():
    """Elements appear in correct z-order: rooms, mebel, floor, doors, windows."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    window = Window(
        id="w1", position=Point(x=500, y=0),
        width=1200.0, height=1500.0, wall_side="north",
    )
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.SOFA_3,
        position=Point(x=500, y=500), width=2300, depth=950,
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        room_id="r1",
        doors=[door], windows=[window], furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    # Check layer order by finding group IDs in SVG string
    rooms_pos = svg.find('id="rooms"')
    mebel_pos = svg.find('id="mebel"')
    floor_pos = svg.find('id="floor"')
    doors_pos = svg.find('id="doors"')
    windows_pos = svg.find('id="windows"')
    assert rooms_pos < mebel_pos < floor_pos < doors_pos < windows_pos
```

**Step 2: Run tests to verify they fail (RED)**

Run: `uv run pytest tests/unit/test_renderer.py -v 2>&1 | tail -30`
Expected: Some tests may pass (theme, coord mapper), others may fail if imports or rendering have issues.

**Step 3: Commit**

```bash
git add tests/unit/test_renderer.py
git commit -m "test: add 20 SVG renderer unit tests (R01-R20)"
```

---

### Task 8: Fix issues and make tests GREEN

**Files:**
- Modify: any renderer files that need fixes based on test failures

**Step 1: Run tests and fix all issues**

Run: `uv run pytest tests/unit/test_renderer.py -v`

Fix any issues discovered: import errors, svgwrite API mismatches, incorrect SVG output format, etc.

The most likely issues will be:
1. `svgwrite.drawing.Drawing().rect(...)` pattern — svgwrite elements need to be created from the drawing, not a throwaway instance. Fix by passing `dwg` to furniture draw functions, or by using `svgwrite.shapes` directly.
2. SVG namespace in XML parsing — may need to handle `{http://www.w3.org/2000/svg}` prefix.

**Step 2: Run full test suite**

Run: `uv run pytest tests/ --tb=short -q`
Expected: 246 passed (226 + 20)

**Step 3: Lint check**

Run: `uv run ruff check src/floorplan_generator/renderer/`
Expected: no errors

**Step 4: Commit**

```bash
git add -A
git commit -m "fix: resolve renderer test failures — 20 tests GREEN"
```

---

### Task 9: Integration tests

**Files:**
- Create: `tests/integration/test_renderer_integration.py`

**Step 1: Write 5 integration tests**

```python
"""Integration tests for SVG renderer (RI01-RI05)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from xml.etree import ElementTree

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.renderer.svg_renderer import render_svg, render_svg_to_file
from floorplan_generator.renderer.theme import load_theme


# RI01
def test_generate_economy_svg():
    """Generate economy 1-room, render SVG, check valid XML."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    svg = render_svg(result)
    assert len(svg) > 100
    # Valid XML
    root = ElementTree.fromstring(svg)
    assert root.tag.endswith("svg")


# RI02
def test_generate_with_themes():
    """Same apartment renders differently with blueprint vs colored."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    bp = render_svg(result, load_theme("blueprint"))
    col = render_svg(result, load_theme("colored"))
    assert bp != col
    # Colored should have room fill colors
    assert "#E3F2FD" in col or "#FFF3E0" in col or "#E0F7FA" in col


# RI03
def test_svg_file_output():
    """render_svg_to_file produces a valid SVG file."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.svg"
        render_svg_to_file(result, str(path))
        assert path.exists()
        content = path.read_text()
        assert "<svg" in content
        assert len(content) > 500


# RI04
def test_svg_file_size_reasonable():
    """SVG file size < 500KB for typical apartment."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42)
    assert result is not None
    svg = render_svg(result)
    assert len(svg) < 500_000


# RI05
def test_comfort_2room_all_layers():
    """Comfort 2-room SVG has all expected layer groups."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42)
    assert result is not None
    svg = render_svg(result)
    for layer_id in ["rooms", "mebel", "floor", "doors", "windows"]:
        assert f'id="{layer_id}"' in svg
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/integration/test_renderer_integration.py -v`
Expected: 5 passed

**Step 3: Run full test suite**

Run: `uv run pytest tests/ --tb=short -q`
Expected: 251 passed (226 + 20 + 5)

**Step 4: Commit**

```bash
git add tests/integration/test_renderer_integration.py
git commit -m "test: add 5 SVG renderer integration tests (RI01-RI05)"
```

---

### Task 10: CLI commands (generate + render)

**Files:**
- Modify: `src/floorplan_generator/cli.py`
- Modify: `src/floorplan_generator/generator/factory.py`

**Step 1: Update factory.py to support SVG rendering**

Add SVG rendering to `generate_dataset`:

```python
"""Dataset generation factory."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.svg_renderer import render_svg_to_file
from floorplan_generator.renderer.theme import Theme, load_theme

logger = logging.getLogger(__name__)


def generate_single(
    apartment_class: ApartmentClass,
    num_rooms: int,
    seed: int,
    max_restarts: int = 10,
) -> GenerationResult | None:
    """Generate a single apartment."""
    return generate_apartment(
        apartment_class, num_rooms, seed, max_restarts,
    )


def generate_dataset(
    apartment_class: ApartmentClass,
    num_rooms: int,
    count: int,
    seed: int,
    output: Path,
    max_restarts: int = 10,
    theme: Theme | None = None,
) -> list[dict]:
    """Generate a dataset of apartments and save SVG + metadata.

    Returns metadata list.
    """
    output.mkdir(parents=True, exist_ok=True)
    if theme is None:
        theme = load_theme("blueprint")
    metadata = []

    for i in range(count):
        result = generate_single(
            apartment_class, num_rooms,
            seed=seed + i,
            max_restarts=max_restarts,
        )

        if result is None:
            logger.warning("Failed to generate #%d", i)
            continue

        filename = f"{apartment_class.value}_{num_rooms}r_{i:04d}"

        # Save SVG
        svg_path = output / f"{filename}.svg"
        render_svg_to_file(result, str(svg_path), theme)

        # Save apartment JSON for re-rendering
        json_path = output / f"{filename}.json"
        json_path.write_text(result.model_dump_json(indent=2))

        entry = {
            "index": i,
            "filename": filename,
            "class": apartment_class.value,
            "rooms": num_rooms,
            "total_area_m2": round(result.apartment.total_area_m2, 1),
            "room_count": len(result.apartment.rooms),
            "restart_count": result.restart_count,
            "seed_used": result.seed_used,
            "recommended_violations": result.recommended_violations,
        }
        metadata.append(entry)

    # Save metadata
    meta_path = output / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return metadata
```

**Step 2: Update cli.py with generate and render commands**

```python
"""CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from floorplan_generator.core.enums import ApartmentClass

app = typer.Typer(name="floorplan", help="Apartment floorplan generator")


@app.callback()
def main() -> None:
    """Generate synthetic apartment floorplan datasets in SVG format."""


@app.command()
def generate(
    apartment_class: ApartmentClass = typer.Option(
        ApartmentClass.ECONOMY, "--class", "-c", help="Apartment class",
    ),
    rooms: int = typer.Option(1, "--rooms", "-r", help="Number of living rooms"),
    count: int = typer.Option(10, "--count", "-n", help="Number of apartments"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output dir"),
    theme: str = typer.Option("blueprint", "--theme", "-t", help="Theme name or path"),
    max_restarts: int = typer.Option(10, "--max-restarts", help="Max restarts"),
) -> None:
    """Generate apartment floorplans and save as SVG."""
    from floorplan_generator.generator.factory import generate_dataset
    from floorplan_generator.renderer.theme import load_theme

    theme_obj = load_theme(theme)
    metadata = generate_dataset(
        apartment_class, rooms, count, seed, output,
        max_restarts=max_restarts,
        theme=theme_obj,
    )
    typer.echo(f"Generated {len(metadata)} apartments in {output}")


@app.command()
def render(
    input_dir: Path = typer.Option(..., "--input", "-i", help="Input dir with JSON files"),
    output_dir: Path = typer.Option(..., "--output", "-o", help="Output dir for SVGs"),
    theme: str = typer.Option("blueprint", "--theme", "-t", help="Theme name or path"),
) -> None:
    """Re-render apartment JSON files to SVG with a different theme."""
    from floorplan_generator.generator.types import GenerationResult
    from floorplan_generator.renderer.svg_renderer import render_svg_to_file
    from floorplan_generator.renderer.theme import load_theme

    theme_obj = load_theme(theme)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "metadata.json"]

    rendered = 0
    for json_file in json_files:
        result = GenerationResult.model_validate_json(json_file.read_text())
        svg_path = output_dir / f"{json_file.stem}.svg"
        render_svg_to_file(result, str(svg_path), theme_obj)
        rendered += 1

    typer.echo(f"Rendered {rendered} SVG files to {output_dir}")
```

**Step 3: Lint check**

Run: `uv run ruff check src/floorplan_generator/cli.py src/floorplan_generator/generator/factory.py`
Expected: no errors

**Step 4: Run full test suite (factory changes may affect integration tests)**

Run: `uv run pytest tests/ --tb=short -q`
Expected: 251 passed

**Step 5: Quick CLI smoke test**

Run: `uv run floorplan generate --class economy --rooms 1 --count 2 --seed 42 --output /tmp/floorplan_test --theme blueprint`
Expected: "Generated 2 apartments in /tmp/floorplan_test"

Run: `ls /tmp/floorplan_test/`
Expected: SVG files, JSON files, metadata.json

Run: `uv run floorplan render --input /tmp/floorplan_test --output /tmp/floorplan_colored --theme colored`
Expected: "Rendered 2 SVG files to /tmp/floorplan_colored"

**Step 6: Commit**

```bash
git add src/floorplan_generator/cli.py src/floorplan_generator/generator/factory.py
git commit -m "feat: add CLI generate + render commands with SVG output"
```

---

### Task 11: Final verification + lint + update integration test for factory changes

**Files:**
- Modify: `tests/integration/test_greedy_csp_integration.py` (if GI10 breaks due to factory signature change)

**Step 1: Run full test suite**

Run: `uv run pytest tests/ --tb=short -v 2>&1 | tail -40`

If GI10 (`test_metadata_json_correct`) fails because `generate_dataset` now has a `theme` parameter, the existing test should still work since `theme` has a default value. If it fails for another reason (e.g., extra files in output), fix accordingly.

**Step 2: Run ruff on everything**

Run: `uv run ruff check src/ tests/`
Expected: no errors

**Step 3: Final count**

Run: `uv run pytest tests/ --tb=short -q`
Expected: 251 passed (226 existing + 20 renderer unit + 5 renderer integration)

**Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve any remaining test/lint issues for Phase 4"
```

---

## Summary

| Task | Files | Tests | Description |
|------|-------|-------|-------------|
| 1 | pyproject.toml, renderer/__init__.py, symbols/__init__.py | 0 | Package structure + svgwrite dep |
| 2 | theme.py, blueprint.json, colored.json | 0 | Theme system |
| 3 | coordinate_mapper.py | 0 | mm → SVG coordinate mapping |
| 4 | symbols/furniture.py | 0 | Furniture SVG drawing functions |
| 5 | room/wall/door/window/furniture/stoyak_renderer.py | 0 | 6 sub-renderers |
| 6 | svg_renderer.py | 0 | Main orchestrator |
| 7 | test_renderer.py | 20 | Unit tests R01-R20 |
| 8 | (fixes) | 20 GREEN | Fix test failures |
| 9 | test_renderer_integration.py | 5 | Integration tests RI01-RI05 |
| 10 | cli.py, factory.py | 0 | CLI commands |
| 11 | (fixes) | 0 | Final verification |

**Total: 11 tasks, 25 new tests, 251 total, ~11 commits**
