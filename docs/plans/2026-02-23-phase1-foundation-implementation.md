# Phase 1: Foundation — Implementation Plan

**Goal:** Implement the foundational data layer (enums, geometry, dimensions, domain models) with 32 passing tests for the floorplan generator.

**Architecture:** Bottom-up TDD — pure value types first (enums), then geometry primitives with tests, then constants, then domain models with tests. All geometric classes are frozen Pydantic BaseModel. Domain models use Pydantic v2 with @computed_field.

**Tech Stack:** Python 3.12+, uv, Pydantic v2, pytest, ruff

---

## Status: COMPLETED

**Executed:** 2026-02-23
**Result:** 32/32 tests passing, 91% coverage, 7 commits

### Deviations from plan
- All enums use `StrEnum` instead of `(str, Enum)` — ruff UP042 rule requires this for Python 3.12+ target.

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/floorplan_generator/__init__.py`
- Create: `src/floorplan_generator/cli.py`
- Create: `src/floorplan_generator/core/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "floorplan-generator"
version = "0.1.0"
description = "CLI tool for generating synthetic apartment floorplan datasets in SVG"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9",
    "lxml>=5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
]

[project.scripts]
floorplan = "floorplan_generator.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/floorplan_generator"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
src = ["src"]
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

**Step 2: Create package stubs**

`src/floorplan_generator/__init__.py`:
```python
"""Floorplan Generator — synthetic apartment floorplan dataset generator."""
```

`src/floorplan_generator/cli.py`:
```python
"""CLI entry point."""

import typer

app = typer.Typer(name="floorplan", help="Apartment floorplan generator")


@app.callback()
def main() -> None:
    """Generate synthetic apartment floorplan datasets in SVG format."""
```

`src/floorplan_generator/core/__init__.py`:
```python
"""Core domain models and utilities."""
```

`tests/__init__.py` and `tests/unit/__init__.py`: empty files.

**Step 3: Initialize project with uv**

Run: `cd /Users/sergeifrangulov/projects/floorplan-generator-next && uv venv && uv pip install -e ".[dev]"`
Expected: packages install successfully

**Step 4: Verify setup**

Run: `cd /Users/sergeifrangulov/projects/floorplan-generator-next && uv run pytest --co -q`
Expected: "no tests ran" (no test files yet)

Run: `uv run ruff check src/`
Expected: no errors

**Step 5: Commit**

```bash
git init
git add pyproject.toml src/ tests/
git commit -m "chore: initialize project structure with uv, pydantic, pytest, ruff"
```

---

### Task 2: Enumerations (enums.py)

**Files:**
- Create: `src/floorplan_generator/core/enums.py`

**Step 1: Write enums.py**

```python
"""Domain enumerations for the floorplan generator."""

from enum import StrEnum


class RoomType(StrEnum):
    """Type of room in an apartment."""

    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    CHILDREN = "children"
    CABINET = "cabinet"
    KITCHEN = "kitchen"
    KITCHEN_DINING = "kitchen_dining"
    KITCHEN_NICHE = "kitchen_niche"
    HALLWAY = "hallway"
    CORRIDOR = "corridor"
    HALL = "hall"
    BATHROOM = "bathroom"
    TOILET = "toilet"
    COMBINED_BATHROOM = "combined_bathroom"
    STORAGE = "storage"
    WARDROBE = "wardrobe"
    LAUNDRY = "laundry"
    BALCONY = "balcony"

    @property
    def is_wet_zone(self) -> bool:
        return self in _WET_ZONES

    @property
    def requires_window(self) -> bool:
        return self in _WINDOW_REQUIRED

    @property
    def is_living(self) -> bool:
        """True for rooms counted as 'living area' (жилая площадь)."""
        return self in _LIVING_ROOMS


_WET_ZONES = frozenset({
    RoomType.KITCHEN,
    RoomType.KITCHEN_DINING,
    RoomType.KITCHEN_NICHE,
    RoomType.BATHROOM,
    RoomType.TOILET,
    RoomType.COMBINED_BATHROOM,
    RoomType.LAUNDRY,
})

_WINDOW_REQUIRED = frozenset({
    RoomType.LIVING_ROOM,
    RoomType.BEDROOM,
    RoomType.CHILDREN,
    RoomType.CABINET,
    RoomType.KITCHEN,
    RoomType.KITCHEN_DINING,
})

_LIVING_ROOMS = frozenset({
    RoomType.LIVING_ROOM,
    RoomType.BEDROOM,
    RoomType.CHILDREN,
    RoomType.CABINET,
})


class ApartmentClass(StrEnum):
    """Housing class."""

    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"
    PREMIUM = "premium"


class DoorType(StrEnum):
    """Type of door."""

    ENTRANCE = "entrance"
    INTERIOR = "interior"
    INTERIOR_WIDE = "interior_wide"
    DOUBLE = "double"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    COMBINED_BATHROOM = "combined_bathroom"


class SwingDirection(StrEnum):
    """Door swing direction."""

    INWARD = "inward"
    OUTWARD = "outward"


class FurnitureType(StrEnum):
    """Type of furniture or equipment."""

    # Plumbing
    BATHTUB = "bathtub"
    SHOWER = "shower"
    SINK = "sink"
    DOUBLE_SINK = "double_sink"
    TOILET_BOWL = "toilet_bowl"
    BIDET = "bidet"
    WASHING_MACHINE = "washing_machine"
    DRYER = "dryer"
    # Kitchen
    STOVE = "stove"
    HOB = "hob"
    OVEN = "oven"
    FRIDGE = "fridge"
    FRIDGE_SIDE_BY_SIDE = "fridge_side_by_side"
    DISHWASHER = "dishwasher"
    KITCHEN_SINK = "kitchen_sink"
    HOOD = "hood"
    MICROWAVE = "microwave"
    # Living room
    SOFA_2 = "sofa_2"
    SOFA_3 = "sofa_3"
    SOFA_4 = "sofa_4"
    SOFA_CORNER = "sofa_corner"
    ARMCHAIR = "armchair"
    COFFEE_TABLE = "coffee_table"
    TV_STAND = "tv_stand"
    SHELVING = "shelving"
    # Bedroom
    BED_SINGLE = "bed_single"
    BED_DOUBLE = "bed_double"
    BED_KING = "bed_king"
    NIGHTSTAND = "nightstand"
    DRESSER = "dresser"
    WARDROBE_SLIDING = "wardrobe_sliding"
    WARDROBE_SWING = "wardrobe_swing"
    VANITY = "vanity"
    # Children
    CHILD_BED = "child_bed"
    CHILD_DESK = "child_desk"
    CHILD_WARDROBE = "child_wardrobe"
    # Hallway
    HALLWAY_WARDROBE = "hallway_wardrobe"
    SHOE_RACK = "shoe_rack"
    BENCH = "bench"
    COAT_RACK = "coat_rack"
    # General
    DINING_TABLE = "dining_table"
    DINING_CHAIR = "dining_chair"
    DESK = "desk"
    BOOKSHELF = "bookshelf"


class FunctionalZone(StrEnum):
    """Functional zone of the apartment."""

    ENTRY = "entry"
    DAY = "day"
    NIGHT = "night"


class LayoutType(StrEnum):
    """Furniture layout type in living room."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    CIRCULAR = "circular"


class KitchenLayoutType(StrEnum):
    """Kitchen layout type."""

    LINEAR = "linear"
    L_SHAPED = "l_shaped"
    U_SHAPED = "u_shaped"
    PARALLEL = "parallel"
    ISLAND = "island"
    PENINSULA = "peninsula"

    @property
    def min_area_m2(self) -> float:
        return _KITCHEN_MIN_AREAS[self]


_KITCHEN_MIN_AREAS = {
    KitchenLayoutType.LINEAR: 5.0,
    KitchenLayoutType.L_SHAPED: 7.0,
    KitchenLayoutType.U_SHAPED: 10.0,
    KitchenLayoutType.PARALLEL: 9.0,
    KitchenLayoutType.ISLAND: 15.0,
    KitchenLayoutType.PENINSULA: 12.0,
}
```

**Step 2: Lint check**

Run: `uv run ruff check src/floorplan_generator/core/enums.py`
Expected: no errors

**Step 3: Commit**

```bash
git add src/floorplan_generator/core/enums.py
git commit -m "feat: add domain enumerations (RoomType, ApartmentClass, DoorType, FurnitureType, etc.)"
```

---

### Task 3: Write geometry tests (RED)

**Files:**
- Create: `tests/unit/test_geometry.py`

**Step 1: Write all 18 geometry tests**

```python
"""Unit tests for geometric primitives (G01–G18)."""

import math

import pytest

from floorplan_generator.core.geometry import (
    Point,
    Polygon,
    Rectangle,
    Segment,
    distance,
    min_distance_rect_to_rect,
    point_in_polygon,
    rectangles_overlap,
    segments_intersect,
)


# G01
def test_point_distance():
    """Distance between two points."""
    a = Point(x=0, y=0)
    b = Point(x=3, y=4)
    assert a.distance_to(b) == pytest.approx(5.0)


# G02
def test_rectangle_area():
    """Area of a rectangle."""
    r = Rectangle(x=0, y=0, width=10, height=5)
    assert r.area == pytest.approx(50.0)


# G03
def test_rectangle_aspect_ratio():
    """Aspect ratio (max side / min side)."""
    r = Rectangle(x=0, y=0, width=4, height=8)
    assert r.aspect_ratio == pytest.approx(2.0)


# G04
def test_rectangle_contains_point():
    """Point inside rectangle."""
    r = Rectangle(x=0, y=0, width=10, height=10)
    assert r.contains(Point(x=5, y=5)) is True
    assert r.contains(Point(x=0, y=0)) is True  # corner
    assert r.contains(Point(x=11, y=5)) is False


# G05
def test_rectangle_overlap_true():
    """Two overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=5, y=5, width=10, height=10)
    assert r1.overlaps(r2) is True


# G06
def test_rectangle_overlap_false():
    """Two non-overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=20, y=20, width=10, height=10)
    assert r1.overlaps(r2) is False


# G07
def test_rectangle_overlap_edge():
    """Touching by edge — NOT overlapping (strict)."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=10, y=0, width=10, height=10)
    assert r1.overlaps(r2) is False


# G08
def test_polygon_area_square():
    """Area of a square as polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.area == pytest.approx(100.0)


# G09
def test_polygon_area_irregular():
    """Area of an irregular polygon (L-shape)."""
    # L-shape: 10x10 square minus 5x5 corner = 75
    poly = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=5),
        Point(x=5, y=5),
        Point(x=5, y=10),
        Point(x=0, y=10),
    ])
    assert poly.area == pytest.approx(75.0)


# G10
def test_polygon_contains_point_inside():
    """Point inside polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=5, y=5)) is True


# G11
def test_polygon_contains_point_outside():
    """Point outside polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=15, y=15)) is False


# G12
def test_polygon_contains_point_edge():
    """Point on edge of polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=5, y=0)) is True


# G13
def test_segment_intersection():
    """Two intersecting segments."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=10, y=10))
    s2 = Segment(start=Point(x=0, y=10), end=Point(x=10, y=0))
    assert s1.intersects(s2) is True


# G14
def test_segment_no_intersection():
    """Two non-intersecting segments."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=5, y=5))
    s2 = Segment(start=Point(x=6, y=6), end=Point(x=10, y=10))
    assert s1.intersects(s2) is False


# G15
def test_segment_parallel():
    """Parallel segments do not intersect."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=10, y=0))
    s2 = Segment(start=Point(x=0, y=1), end=Point(x=10, y=1))
    assert s1.intersects(s2) is False


# G16
def test_min_distance_rects():
    """Minimum distance between two non-overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=15, y=0, width=10, height=10)
    assert min_distance_rect_to_rect(r1, r2) == pytest.approx(5.0)


# G17
def test_polygon_bounding_box():
    """Bounding box of a polygon."""
    poly = Polygon(points=[
        Point(x=1, y=2),
        Point(x=5, y=1),
        Point(x=8, y=6),
        Point(x=3, y=9),
    ])
    bb = poly.bounding_box
    assert bb.x == pytest.approx(1.0)
    assert bb.y == pytest.approx(1.0)
    assert bb.width == pytest.approx(7.0)
    assert bb.height == pytest.approx(8.0)


# G18
def test_polygon_centroid():
    """Centroid of a square polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    c = square.centroid
    assert c.x == pytest.approx(5.0)
    assert c.y == pytest.approx(5.0)
```

**Step 2: Run tests to verify they fail (RED)**

Run: `uv run pytest tests/unit/test_geometry.py -v 2>&1 | head -30`
Expected: ImportError or ModuleNotFoundError — geometry module doesn't exist yet

**Step 3: Commit red tests**

```bash
git add tests/unit/test_geometry.py
git commit -m "test: add 18 geometry tests (RED) — G01-G18"
```

---

### Task 4: Implement geometry.py (GREEN)

**Files:**
- Create: `src/floorplan_generator/core/geometry.py`

**Step 1: Write geometry.py**

```python
"""Geometric primitives for 2D floorplan operations."""

from __future__ import annotations

import math

from pydantic import BaseModel, model_validator


class Point(BaseModel, frozen=True):
    """2D point."""

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Segment(BaseModel, frozen=True):
    """Line segment between two points."""

    start: Point
    end: Point

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point:
        return Point(
            x=(self.start.x + self.end.x) / 2,
            y=(self.start.y + self.end.y) / 2,
        )

    def intersects(self, other: Segment) -> bool:
        return segments_intersect(self, other)


class Rectangle(BaseModel, frozen=True):
    """Axis-aligned rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Point:
        return Point(x=self.x + self.width / 2, y=self.y + self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        sides = sorted([self.width, self.height])
        if sides[0] == 0:
            return float("inf")
        return sides[1] / sides[0]

    @property
    def corners(self) -> list[Point]:
        return [
            Point(x=self.x, y=self.y),
            Point(x=self.x + self.width, y=self.y),
            Point(x=self.x + self.width, y=self.y + self.height),
            Point(x=self.x, y=self.y + self.height),
        ]

    def contains(self, point: Point) -> bool:
        return (
            self.x <= point.x <= self.x + self.width
            and self.y <= point.y <= self.y + self.height
        )

    def overlaps(self, other: Rectangle) -> bool:
        """Strict overlap — touching edges do NOT count."""
        return rectangles_overlap(self, other)

    def distance_to(self, other: Rectangle) -> float:
        return min_distance_rect_to_rect(self, other)


class Polygon(BaseModel, frozen=True):
    """Arbitrary polygon defined by ordered vertices."""

    points: list[Point]

    @model_validator(mode="after")
    def _check_min_points(self) -> Polygon:
        if len(self.points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        return self

    @property
    def area(self) -> float:
        """Shoelace formula (absolute value)."""
        n = len(self.points)
        s = 0.0
        for i in range(n):
            j = (i + 1) % n
            s += self.points[i].x * self.points[j].y
            s -= self.points[j].x * self.points[i].y
        return abs(s) / 2.0

    @property
    def perimeter(self) -> float:
        n = len(self.points)
        return sum(
            self.points[i].distance_to(self.points[(i + 1) % n]) for i in range(n)
        )

    @property
    def bounding_box(self) -> Rectangle:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return Rectangle(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)

    @property
    def centroid(self) -> Point:
        """Centroid via the shoelace-based formula."""
        n = len(self.points)
        signed_area = 0.0
        cx = 0.0
        cy = 0.0
        for i in range(n):
            j = (i + 1) % n
            cross = (
                self.points[i].x * self.points[j].y
                - self.points[j].x * self.points[i].y
            )
            signed_area += cross
            cx += (self.points[i].x + self.points[j].x) * cross
            cy += (self.points[i].y + self.points[j].y) * cross
        signed_area /= 2.0
        if signed_area == 0:
            # Degenerate — return average
            avg_x = sum(p.x for p in self.points) / n
            avg_y = sum(p.y for p in self.points) / n
            return Point(x=avg_x, y=avg_y)
        cx /= 6.0 * signed_area
        cy /= 6.0 * signed_area
        return Point(x=cx, y=cy)

    def contains(self, point: Point) -> bool:
        return point_in_polygon(point, self)


# --- Module-level functions ---


def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    return a.distance_to(b)


def _cross(o: Point, a: Point, b: Point) -> float:
    """Cross product of vectors OA and OB."""
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """Check if point q lies on segment pr."""
    return (
        min(p.x, r.x) <= q.x <= max(p.x, r.x)
        and min(p.y, r.y) <= q.y <= max(p.y, r.y)
    )


def segments_intersect(s1: Segment, s2: Segment) -> bool:
    """Check if two segments intersect (proper or endpoint touch)."""
    p1, q1 = s1.start, s1.end
    p2, q2 = s2.start, s2.end

    d1 = _cross(p2, q2, p1)
    d2 = _cross(p2, q2, q1)
    d3 = _cross(p1, q1, p2)
    d4 = _cross(p1, q1, q2)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
        (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
    ):
        return True

    if d1 == 0 and _on_segment(p2, p1, q2):
        return True
    if d2 == 0 and _on_segment(p2, q1, q2):
        return True
    if d3 == 0 and _on_segment(p1, p2, q1):
        return True
    if d4 == 0 and _on_segment(p1, q2, q1):
        return True

    return False


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """Ray casting algorithm. Points on edge return True."""
    pts = polygon.points
    n = len(pts)
    # First check if on any edge
    for i in range(n):
        j = (i + 1) % n
        p1, p2 = pts[i], pts[j]
        # Check collinearity and within bounds
        cross = (point.y - p1.y) * (p2.x - p1.x) - (point.x - p1.x) * (p2.y - p1.y)
        if abs(cross) < 1e-10:
            if _on_segment(p1, point, p2):
                return True

    # Ray casting
    inside = False
    j = n - 1
    for i in range(n):
        yi, yj = pts[i].y, pts[j].y
        xi, xj = pts[i].x, pts[j].x
        if (yi > point.y) != (yj > point.y):
            x_intersect = (xj - xi) * (point.y - yi) / (yj - yi) + xi
            if point.x < x_intersect:
                inside = not inside
        j = i
    return inside


def rectangles_overlap(r1: Rectangle, r2: Rectangle) -> bool:
    """Strict overlap — touching edges do NOT count."""
    return not (
        r1.x + r1.width <= r2.x
        or r2.x + r2.width <= r1.x
        or r1.y + r1.height <= r2.y
        or r2.y + r2.height <= r1.y
    )


def min_distance_rect_to_rect(r1: Rectangle, r2: Rectangle) -> float:
    """Minimum distance between two axis-aligned rectangles."""
    # Horizontal gap
    dx = max(0.0, max(r2.x - (r1.x + r1.width), r1.x - (r2.x + r2.width)))
    # Vertical gap
    dy = max(0.0, max(r2.y - (r1.y + r1.height), r1.y - (r2.y + r2.height)))
    return math.sqrt(dx * dx + dy * dy)
```

**Step 2: Run tests to verify they pass (GREEN)**

Run: `uv run pytest tests/unit/test_geometry.py -v`
Expected: 18 passed

**Step 3: Lint check**

Run: `uv run ruff check src/floorplan_generator/core/geometry.py`
Expected: no errors

**Step 4: Commit**

```bash
git add src/floorplan_generator/core/geometry.py
git commit -m "feat: implement geometry primitives (Point, Segment, Rectangle, Polygon) — 18 tests GREEN"
```

---

### Task 5: Dimension constants (dimensions.py)

**Files:**
- Create: `src/floorplan_generator/core/dimensions.py`

**Step 1: Write dimensions.py**

All values from `docs/apartment-planning-rules.md` and `docs/equipment-furniture-rules.md`.

```python
"""Dimension constants from Russian building codes and ergonomic standards.

All lengths in millimeters (mm). All areas in square meters (m²).
Sources: СП 54.13330.2022, СНиП 31-01-2003, ГОСТ 13025, Нойферт.
"""

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
)

# --- Minimum areas (m²) ---

MIN_AREAS: dict[str, float] = {
    "living_room_1room": 14.0,
    "living_room_2plus": 16.0,
    "bedroom_1person": 8.0,
    "bedroom_2person": 10.0,
    "kitchen": 8.0,
    "kitchen_1room": 5.0,
    "kitchen_zone_dining": 6.0,
    "kitchen_niche": 5.0,
}

# Total apartment area ranges by class and room count (m²): (min, max)
APARTMENT_AREAS: dict[ApartmentClass, dict[int, tuple[float, float]]] = {
    ApartmentClass.ECONOMY: {
        1: (28.0, 38.0),
        2: (44.0, 53.0),
        3: (56.0, 65.0),
        4: (70.0, 80.0),
    },
    ApartmentClass.COMFORT: {
        1: (38.0, 50.0),
        2: (53.0, 75.0),
        3: (65.0, 90.0),
        4: (80.0, 110.0),
    },
    ApartmentClass.BUSINESS: {
        1: (45.0, 65.0),
        2: (70.0, 100.0),
        3: (90.0, 140.0),
        4: (110.0, 180.0),
    },
    ApartmentClass.PREMIUM: {
        1: (60.0, 120.0),
        2: (100.0, 200.0),
        3: (150.0, 300.0),
        4: (200.0, 400.0),
    },
}

# --- Minimum widths (mm) ---

MIN_WIDTHS: dict[str, float] = {
    "kitchen": 1700.0,
    "hallway": 1400.0,
    "corridor": 850.0,
    "corridor_long": 1000.0,  # corridor longer than 1500 mm
    "corridor_long_threshold": 1500.0,
    "bathroom": 1500.0,
    "combined_bathroom": 1700.0,
    "toilet": 800.0,
    "living_room": 3200.0,
    "living_room_min": 2400.0,
}

# --- Minimum heights (mm) ---

MIN_HEIGHTS: dict[str, float] = {
    "living_rooms_standard": 2500.0,
    "living_rooms_cold_climate": 2700.0,
    "corridors": 2100.0,
}

# Ceiling heights by class (mm)
CEILING_HEIGHTS: dict[ApartmentClass, tuple[float, float]] = {
    ApartmentClass.ECONOMY: (2500.0, 2600.0),
    ApartmentClass.COMFORT: (2600.0, 2800.0),
    ApartmentClass.BUSINESS: (3000.0, 3500.0),
    ApartmentClass.PREMIUM: (3000.0, 4000.0),
}

# --- Door sizes (mm): (width_min, width_max, height) ---

DOOR_SIZES: dict[DoorType, tuple[float, float, float]] = {
    DoorType.ENTRANCE: (860.0, 960.0, 2050.0),
    DoorType.INTERIOR: (800.0, 800.0, 2000.0),
    DoorType.INTERIOR_WIDE: (800.0, 900.0, 2000.0),
    DoorType.DOUBLE: (1300.0, 1500.0, 2000.0),
    DoorType.KITCHEN: (700.0, 800.0, 2000.0),
    DoorType.BATHROOM: (600.0, 600.0, 2000.0),
    DoorType.COMBINED_BATHROOM: (600.0, 700.0, 2000.0),
}

# --- Window ratios ---

WINDOW_RATIOS: dict[str, float] = {
    "min_ratio": 1.0 / 8.0,       # min window area / floor area
    "recommended_ratio": 1.0 / 6.0,
    "sill_height": 800.0,          # mm from floor
    "min_side_gap": 250.0,         # mm from window to side wall
    "max_room_depth": 6000.0,      # mm for one-sided illumination
}

# --- Adjacency matrix ---
# +: allowed, -: forbidden, (у): conditional
# Rows and columns indexed by RoomType values

ADJACENCY_MATRIX: dict[RoomType, dict[RoomType, str]] = {
    RoomType.HALLWAY: {
        RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "+", RoomType.TOILET: "+",
        RoomType.COMBINED_BATHROOM: "+", RoomType.STORAGE: "+",
    },
    RoomType.CORRIDOR: {
        RoomType.HALLWAY: "+", RoomType.LIVING_ROOM: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "+", RoomType.TOILET: "+",
        RoomType.COMBINED_BATHROOM: "+", RoomType.STORAGE: "+",
    },
    RoomType.LIVING_ROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "(у)", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "(у)", RoomType.STORAGE: "+",
    },
    RoomType.BEDROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.KITCHEN: "-", RoomType.BATHROOM: "(у)", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "(у)", RoomType.STORAGE: "+",
    },
    RoomType.KITCHEN: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "-", RoomType.BATHROOM: "-", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.BATHROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "(у)",
        RoomType.BEDROOM: "(у)", RoomType.KITCHEN: "-", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "-",
    },
    RoomType.TOILET: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "-",
        RoomType.BEDROOM: "-", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "-",
    },
    RoomType.COMBINED_BATHROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "(у)",
        RoomType.BEDROOM: "(у)", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.STORAGE: "-",
    },
    RoomType.STORAGE: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "+", RoomType.KITCHEN: "+", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-",
    },
}

# --- Furniture sizes (mm): (width, depth, height) ---

FURNITURE_SIZES: dict[FurnitureType, tuple[float, float, float]] = {
    # Plumbing
    FurnitureType.BATHTUB: (1700.0, 750.0, 600.0),
    FurnitureType.SHOWER: (900.0, 900.0, 2100.0),
    FurnitureType.SINK: (600.0, 500.0, 850.0),
    FurnitureType.DOUBLE_SINK: (1350.0, 500.0, 850.0),
    FurnitureType.TOILET_BOWL: (650.0, 375.0, 420.0),
    FurnitureType.BIDET: (580.0, 375.0, 400.0),
    FurnitureType.WASHING_MACHINE: (600.0, 500.0, 850.0),
    FurnitureType.DRYER: (600.0, 550.0, 850.0),
    # Kitchen
    FurnitureType.STOVE: (600.0, 600.0, 850.0),
    FurnitureType.HOB: (590.0, 520.0, 50.0),
    FurnitureType.OVEN: (580.0, 575.0, 595.0),
    FurnitureType.FRIDGE: (600.0, 600.0, 1800.0),
    FurnitureType.FRIDGE_SIDE_BY_SIDE: (900.0, 725.0, 1800.0),
    FurnitureType.DISHWASHER: (600.0, 575.0, 820.0),
    FurnitureType.KITCHEN_SINK: (600.0, 550.0, 200.0),
    FurnitureType.HOOD: (600.0, 400.0, 100.0),
    FurnitureType.MICROWAVE: (525.0, 350.0, 320.0),
    # Living room
    FurnitureType.SOFA_2: (1750.0, 950.0, 770.0),
    FurnitureType.SOFA_3: (2300.0, 950.0, 770.0),
    FurnitureType.SOFA_4: (2500.0, 950.0, 770.0),
    FurnitureType.SOFA_CORNER: (2750.0, 1750.0, 800.0),
    FurnitureType.ARMCHAIR: (850.0, 850.0, 770.0),
    FurnitureType.COFFEE_TABLE: (1000.0, 600.0, 400.0),
    FurnitureType.TV_STAND: (1500.0, 425.0, 500.0),
    FurnitureType.SHELVING: (1200.0, 375.0, 2000.0),
    # Bedroom
    FurnitureType.BED_SINGLE: (900.0, 2000.0, 500.0),
    FurnitureType.BED_DOUBLE: (1600.0, 2000.0, 500.0),
    FurnitureType.BED_KING: (1800.0, 2100.0, 500.0),
    FurnitureType.NIGHTSTAND: (500.0, 425.0, 600.0),
    FurnitureType.DRESSER: (1000.0, 450.0, 1000.0),
    FurnitureType.WARDROBE_SLIDING: (2000.0, 625.0, 2300.0),
    FurnitureType.WARDROBE_SWING: (1600.0, 575.0, 2100.0),
    FurnitureType.VANITY: (1000.0, 450.0, 750.0),
    # Children
    FurnitureType.CHILD_BED: (1700.0, 800.0, 400.0),
    FurnitureType.CHILD_DESK: (1100.0, 600.0, 640.0),
    FurnitureType.CHILD_WARDROBE: (1000.0, 500.0, 1650.0),
    # Hallway
    FurnitureType.HALLWAY_WARDROBE: (1800.0, 500.0, 2250.0),
    FurnitureType.SHOE_RACK: (800.0, 325.0, 750.0),
    FurnitureType.BENCH: (900.0, 375.0, 475.0),
    FurnitureType.COAT_RACK: (900.0, 275.0, 1600.0),
    # General
    FurnitureType.DINING_TABLE: (1350.0, 850.0, 760.0),
    FurnitureType.DINING_CHAIR: (450.0, 450.0, 440.0),
    FurnitureType.DESK: (1200.0, 600.0, 750.0),
    FurnitureType.BOOKSHELF: (900.0, 300.0, 2000.0),
}

# --- Clearance zones (mm, distance in front of furniture) ---

CLEARANCES: dict[str, float] = {
    # Bathroom
    "toilet_center_from_wall": 350.0,
    "toilet_front": 600.0,
    "toilet_front_optimal": 750.0,
    "sink_front": 700.0,
    "sink_front_optimal": 800.0,
    "bathtub_exit": 550.0,
    "bathtub_exit_optimal": 750.0,
    "outlet_from_water": 600.0,
    # Kitchen
    "stove_side_wall": 200.0,
    "stove_window": 450.0,
    "hood_gas_stove": 750.0,
    "hood_electric_stove": 650.0,
    "fridge_stove": 300.0,
    "kitchen_rows_parallel": 1200.0,
    "kitchen_passage": 900.0,
    # Bedroom
    "bed_passage_double": 700.0,
    "bed_passage_double_optimal": 900.0,
    "wardrobe_swing_front": 800.0,
    "wardrobe_sliding_front": 700.0,
    "drawers_front": 800.0,
    # Safety
    "oven_front": 800.0,
    "passage_min": 700.0,
    "passage_two_people": 1100.0,
    # Dining
    "table_wall_passage": 900.0,
    "table_wall_no_passage": 600.0,
    "shelf_max_height": 1900.0,
    # Living room
    "sofa_armchair_max": 2000.0,
    "armchairs_apart": 1050.0,
    "wall_furniture_not_perimeter": 900.0,
    "carpet_wall": 600.0,
    "shelving_other_furniture": 800.0,
    "living_room_max_furniture_ratio": 0.35,
    # Hallway
    "entry_zone_width": 600.0,
    "entry_zone_depth": 800.0,
    # Appliances
    "washer_back_gap": 50.0,
    "toilet_stoyak_max": 1000.0,
}

# --- Kitchen triangle (mm) ---

KITCHEN_TRIANGLE: dict[str, float] = {
    "perimeter_min": 3500.0,
    "perimeter_max": 8000.0,
    "perimeter_optimal_min": 4000.0,
    "perimeter_optimal_max": 6000.0,
    "sink_stove_min": 800.0,
    "sink_stove_max": 2000.0,
    "fridge_stove_min": 350.0,
    "sink_fridge_max": 2500.0,
}

# --- Wall thicknesses (mm) ---

WALL_THICKNESS: dict[str, float] = {
    "external": 225.0,
    "internal_partition": 100.0,
    "load_bearing": 290.0,
}
```

**Step 2: Lint check**

Run: `uv run ruff check src/floorplan_generator/core/dimensions.py`
Expected: no errors

**Step 3: Commit**

```bash
git add src/floorplan_generator/core/dimensions.py
git commit -m "feat: add dimension constants from building codes and ergonomic standards"
```

---

### Task 6: Write model tests (RED) + conftest fixtures

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/unit/test_models.py`

**Step 1: Write conftest.py with fixtures**

```python
"""Shared test fixtures."""

from __future__ import annotations

import uuid

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


def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def make_room():
    """Factory fixture: creates a rectangular Room.

    Width and height in meters. Converts to mm-based polygon internally.
    """

    def _factory(
        room_type: RoomType,
        width_m: float,
        height_m: float,
        *,
        doors: list[Door] | None = None,
        windows: list[Window] | None = None,
        furniture: list[FurnitureItem] | None = None,
    ) -> Room:
        w = width_m * 1000  # mm
        h = height_m * 1000  # mm
        boundary = Polygon(points=[
            Point(x=0, y=0),
            Point(x=w, y=0),
            Point(x=w, y=h),
            Point(x=0, y=h),
        ])
        return Room(
            id=_uid(),
            room_type=room_type,
            boundary=boundary,
            doors=doors or [],
            windows=windows or [],
            furniture=furniture or [],
        )

    return _factory


@pytest.fixture
def make_apartment():
    """Factory fixture: creates an Apartment from a list of rooms."""

    def _factory(
        apartment_class: ApartmentClass,
        rooms: list[Room],
        num_rooms: int,
    ) -> Apartment:
        return Apartment(
            id=_uid(),
            apartment_class=apartment_class,
            rooms=rooms,
            num_rooms=num_rooms,
        )

    return _factory


@pytest.fixture
def make_door():
    """Factory fixture: creates a Door."""

    def _factory(
        door_type: DoorType = DoorType.INTERIOR,
        width: float = 800.0,
        swing: SwingDirection = SwingDirection.INWARD,
        room_from: str = "room_a",
        room_to: str = "room_b",
        position: Point | None = None,
    ) -> Door:
        return Door(
            id=_uid(),
            position=position or Point(x=0, y=0),
            width=width,
            door_type=door_type,
            swing=swing,
            room_from=room_from,
            room_to=room_to,
        )

    return _factory


@pytest.fixture
def make_window():
    """Factory fixture: creates a Window."""

    def _factory(
        width: float = 1500.0,
        height: float = 1500.0,
        wall_side: str = "north",
    ) -> Window:
        return Window(
            id=_uid(),
            position=Point(x=0, y=0),
            width=width,
            height=height,
            wall_side=wall_side,
        )

    return _factory


@pytest.fixture
def make_furniture():
    """Factory fixture: creates a FurnitureItem."""

    def _factory(
        furniture_type: FurnitureType,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 600.0,
        depth: float = 400.0,
        rotation: float = 0.0,
    ) -> FurnitureItem:
        return FurnitureItem(
            id=_uid(),
            furniture_type=furniture_type,
            position=Point(x=x, y=y),
            width=width,
            depth=depth,
            rotation=rotation,
        )

    return _factory
```

**Step 2: Write all 14 model tests**

```python
"""Unit tests for domain models (M01–M14)."""

import pytest

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)


# M01
def test_room_area_calculation(make_room):
    """Room area in m² is computed correctly from boundary polygon."""
    room = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    assert room.area_m2 == pytest.approx(20.0)


# M02
def test_room_width_calculation(make_room):
    """Room width (min side of bounding box) in meters."""
    room = make_room(RoomType.BEDROOM, width_m=3.0, height_m=5.0)
    assert room.width_m == pytest.approx(3.0)


# M03
def test_room_aspect_ratio(make_room):
    """Room aspect ratio = max side / min side."""
    room = make_room(RoomType.BEDROOM, width_m=3.0, height_m=6.0)
    assert room.aspect_ratio == pytest.approx(2.0)


# M04
def test_room_is_wet_zone(make_room):
    """Wet zone determined by room type."""
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    assert bathroom.is_wet_zone is True
    assert bedroom.is_wet_zone is False


# M05
def test_room_requires_window(make_room):
    """Window requirement determined by room type."""
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    assert living.requires_window is True
    assert corridor.requires_window is False


# M06
def test_door_swing_arc(make_door):
    """Door swing arc returns a Rectangle representing the sweep area."""
    door = make_door(
        door_type=DoorType.INTERIOR,
        width=800.0,
        swing=SwingDirection.INWARD,
    )
    arc = door.swing_arc
    # Arc should be a square with side = door width
    assert arc.width == pytest.approx(800.0)
    assert arc.height == pytest.approx(800.0)


# M07
def test_window_area(make_window):
    """Window area in m²."""
    window = make_window(width=1500.0, height=1500.0)
    assert window.area_m2 == pytest.approx(2.25)


# M08
def test_furniture_bounding_box(make_furniture):
    """Bounding box of furniture item accounts for rotation."""
    # No rotation — simple bbox
    item = make_furniture(FurnitureType.SOFA_3, x=100, y=200, width=2100, depth=950, rotation=0)
    bb = item.bounding_box
    assert bb.x == pytest.approx(100.0)
    assert bb.y == pytest.approx(200.0)
    assert bb.width == pytest.approx(2100.0)
    assert bb.height == pytest.approx(950.0)

    # 90-degree rotation — width and depth swap
    item90 = make_furniture(FurnitureType.SOFA_3, x=100, y=200, width=2100, depth=950, rotation=90)
    bb90 = item90.bounding_box
    assert bb90.width == pytest.approx(950.0, abs=1.0)
    assert bb90.height == pytest.approx(2100.0, abs=1.0)


# M09
def test_furniture_clearance_zone(make_furniture):
    """Clearance zone extends in front of furniture."""
    item = make_furniture(FurnitureType.TOILET_BOWL, x=0, y=0, width=650, depth=375, rotation=0)
    cz = item.clearance_zone
    # Clearance zone should be a rectangle in front (positive y direction by default)
    assert cz is not None
    assert cz.width > 0
    assert cz.height > 0


# M10
def test_apartment_total_area(make_room, make_apartment):
    """Total apartment area = sum of all room areas."""
    r1 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)  # 20
    r2 = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)  # 9
    r3 = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)  # 4
    apt = make_apartment(ApartmentClass.COMFORT, [r1, r2, r3], num_rooms=1)
    assert apt.total_area_m2 == pytest.approx(33.0)


# M11
def test_apartment_living_area(make_room, make_apartment):
    """Living area = sum of only living rooms (гостиная, спальня, детская, кабинет)."""
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)  # 20
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)  # 12
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)  # 9 (not counted)
    apt = make_apartment(ApartmentClass.COMFORT, [living, bedroom, kitchen], num_rooms=2)
    assert apt.living_area_m2 == pytest.approx(32.0)


# M12
def test_apartment_adjacency_graph(make_room, make_door, make_apartment):
    """Adjacency graph built from door connections."""
    r1 = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    r2 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    door = make_door(room_from=r1.id, room_to=r2.id)
    r1_with_door = r1.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [r1_with_door, r2], num_rooms=1)
    graph = apt.adjacency_graph
    assert r2.id in graph[r1_with_door.id]
    assert r1_with_door.id in graph[r2.id]


# M13
def test_apartment_room_composition(make_room, make_apartment):
    """Room composition returns count per room type."""
    r1 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    r2 = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    r3 = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    r4 = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    apt = make_apartment(ApartmentClass.COMFORT, [r1, r2, r3, r4], num_rooms=2)
    comp = apt.room_composition
    assert comp[RoomType.LIVING_ROOM] == 1
    assert comp[RoomType.BEDROOM] == 2
    assert comp[RoomType.KITCHEN] == 1


# M14
def test_room_free_area_ratio(make_room, make_furniture):
    """Free area ratio = 1 - (furniture area / room area)."""
    furniture = make_furniture(
        FurnitureType.BED_DOUBLE,
        x=500, y=500, width=1600, depth=2000, rotation=0,
    )
    room = make_room(
        RoomType.BEDROOM, width_m=4.0, height_m=5.0, furniture=[furniture],
    )
    # Room = 4*5 = 20 m², furniture = 1.6*2.0 = 3.2 m²
    # Free ratio = 1 - 3.2/20 = 0.84
    assert room.free_area_ratio == pytest.approx(0.84)
```

**Step 3: Run tests to verify they fail (RED)**

Run: `uv run pytest tests/unit/test_models.py -v 2>&1 | head -10`
Expected: ImportError — models module doesn't exist yet

**Step 4: Commit red tests**

```bash
git add tests/conftest.py tests/unit/test_models.py
git commit -m "test: add conftest fixtures + 14 model tests (RED) — M01-M14"
```

---

### Task 7: Implement models.py (GREEN)

**Files:**
- Create: `src/floorplan_generator/core/models.py`

**Step 1: Write models.py**

```python
"""Domain models for the floorplan generator."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from pydantic import BaseModel, computed_field

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point, Polygon, Rectangle


class Window(BaseModel):
    """Window in a room wall."""

    id: str
    position: Point
    width: float  # mm
    height: float  # mm
    wall_side: str

    @computed_field
    @property
    def area_m2(self) -> float:
        """Window area in square meters."""
        return (self.width * self.height) / 1_000_000


class Door(BaseModel):
    """Door connecting two rooms."""

    id: str
    position: Point
    width: float  # mm (door leaf width)
    door_type: DoorType
    swing: SwingDirection
    room_from: str
    room_to: str

    @computed_field
    @property
    def swing_arc(self) -> Rectangle:
        """Rectangle representing the door sweep area.

        The arc is a square with side = door width, positioned at the door.
        """
        return Rectangle(
            x=self.position.x,
            y=self.position.y,
            width=self.width,
            height=self.width,
        )


class FurnitureItem(BaseModel):
    """A piece of furniture or equipment placed in a room."""

    id: str
    furniture_type: FurnitureType
    position: Point  # top-left corner before rotation
    width: float  # mm
    depth: float  # mm
    rotation: float = 0.0  # degrees

    @computed_field
    @property
    def bounding_box(self) -> Rectangle:
        """Axis-aligned bounding box, accounting for rotation."""
        rad = math.radians(self.rotation)
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))
        bb_w = self.width * cos_a + self.depth * sin_a
        bb_h = self.width * sin_a + self.depth * cos_a
        return Rectangle(
            x=self.position.x,
            y=self.position.y,
            width=bb_w,
            height=bb_h,
        )

    @computed_field
    @property
    def clearance_zone(self) -> Rectangle:
        """Access zone in front of the furniture item.

        By default, extends 600mm in the direction of depth (front).
        """
        clearance_depth = 600.0  # default clearance
        bb = self.bounding_box
        return Rectangle(
            x=bb.x,
            y=bb.y + bb.height,
            width=bb.width,
            height=clearance_depth,
        )


class Room(BaseModel):
    """A room in the apartment."""

    id: str
    room_type: RoomType
    boundary: Polygon
    doors: list[Door] = []
    windows: list[Window] = []
    furniture: list[FurnitureItem] = []

    @computed_field
    @property
    def area_m2(self) -> float:
        """Room area in m² (polygon area in mm² → m²)."""
        return self.boundary.area / 1_000_000

    @computed_field
    @property
    def width_m(self) -> float:
        """Minimum side of bounding box in meters."""
        bb = self.boundary.bounding_box
        return min(bb.width, bb.height) / 1000

    @computed_field
    @property
    def height_m(self) -> float:
        """Maximum side of bounding box in meters."""
        bb = self.boundary.bounding_box
        return max(bb.width, bb.height) / 1000

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio (max side / min side)."""
        if self.width_m == 0:
            return float("inf")
        return self.height_m / self.width_m

    @computed_field
    @property
    def is_wet_zone(self) -> bool:
        return self.room_type.is_wet_zone

    @computed_field
    @property
    def requires_window(self) -> bool:
        return self.room_type.requires_window

    @computed_field
    @property
    def free_area_ratio(self) -> float:
        """Ratio of free floor area (1 - furniture_area / room_area)."""
        if self.area_m2 == 0:
            return 0.0
        furniture_area_m2 = sum(
            (f.bounding_box.width * f.bounding_box.height) / 1_000_000
            for f in self.furniture
        )
        return 1.0 - furniture_area_m2 / self.area_m2


class Apartment(BaseModel):
    """An apartment consisting of multiple rooms."""

    id: str
    apartment_class: ApartmentClass
    rooms: list[Room]
    num_rooms: int  # number of living rooms (жилых комнат)

    @computed_field
    @property
    def total_area_m2(self) -> float:
        """Total area of all rooms."""
        return sum(r.area_m2 for r in self.rooms)

    @computed_field
    @property
    def living_area_m2(self) -> float:
        """Living area — only rooms with is_living=True."""
        return sum(r.area_m2 for r in self.rooms if r.room_type.is_living)

    @computed_field
    @property
    def adjacency_graph(self) -> dict[str, list[str]]:
        """Adjacency graph: room_id -> [connected_room_ids].

        Built from door connections (bidirectional).
        """
        graph: dict[str, list[str]] = defaultdict(list)
        for room in self.rooms:
            for door in room.doors:
                if door.room_to not in graph[door.room_from]:
                    graph[door.room_from].append(door.room_to)
                if door.room_from not in graph[door.room_to]:
                    graph[door.room_to].append(door.room_from)
        return dict(graph)

    @computed_field
    @property
    def room_composition(self) -> dict[RoomType, int]:
        """Count of rooms per type."""
        return dict(Counter(r.room_type for r in self.rooms))
```

**Step 2: Run tests to verify they pass (GREEN)**

Run: `uv run pytest tests/ -v`
Expected: 32 passed (18 geometry + 14 models)

**Step 3: Run full lint check**

Run: `uv run ruff check src/`
Expected: no errors

**Step 4: Run coverage**

Run: `uv run pytest tests/ --cov=floorplan_generator --cov-report=term-missing`
Expected: high coverage for core modules

**Step 5: Commit**

```bash
git add src/floorplan_generator/core/models.py
git commit -m "feat: implement domain models (Window, Door, FurnitureItem, Room, Apartment) — 32 tests GREEN"
```

---

## Summary

| Task | Files | Tests | Status |
|------|-------|-------|--------|
| 1. Project setup | pyproject.toml, stubs | 0 | Done |
| 2. Enums | enums.py | 0 | Done |
| 3. Geometry tests | test_geometry.py | 18 RED | Done |
| 4. Geometry impl | geometry.py | 18 GREEN | Done |
| 5. Dimensions | dimensions.py | 0 | Done |
| 6. Model tests | conftest.py, test_models.py | 14 RED | Done |
| 7. Models impl | models.py | 14 GREEN | Done |

**Total: 7 tasks, 32 tests, 7 commits**
**Coverage: 91% overall (enums 99%, geometry 88%, models 98%)**
