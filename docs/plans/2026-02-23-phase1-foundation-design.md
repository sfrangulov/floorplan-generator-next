# Phase 1: Foundation Design

## Summary

Phase 1 implements the foundational data layer for the floorplan generator: enumerations, geometric primitives, dimension constants, and domain models. This phase produces 32 passing tests (18 geometry + 14 models) and establishes the project infrastructure (pyproject.toml, uv, pytest, ruff).

## Scope

- `src/floorplan_generator/core/enums.py` — 7 enumerations
- `src/floorplan_generator/core/geometry.py` — 4 geometric classes + 5 utility functions
- `src/floorplan_generator/core/dimensions.py` — all numeric constants from building codes
- `src/floorplan_generator/core/models.py` — 5 Pydantic domain models
- `tests/unit/test_geometry.py` — 18 tests (G01–G18)
- `tests/unit/test_models.py` — 14 tests (M01–M14)
- `tests/conftest.py` — shared fixtures
- `pyproject.toml` — project configuration
- `src/floorplan_generator/__init__.py`, `cli.py` — stubs

## Approach

Bottom-up, strict TDD:

1. Project setup (pyproject.toml, directories, uv)
2. `enums.py` (no tests — pure definitions)
3. `test_geometry.py` — 18 red tests
4. `geometry.py` — implementation until green
5. `dimensions.py` (no tests — pure constants)
6. `conftest.py` + `test_models.py` — 14 red tests
7. `models.py` — implementation until green

## Design Decisions

### enums.py

All enums inherit `str, Enum` for JSON serialization.

- `RoomType`: 17 values. Custom properties `is_wet_zone` and `requires_window` derived from mapping dicts.
- `ApartmentClass`: ECONOMY, COMFORT, BUSINESS, PREMIUM
- `DoorType`: 7 types with default width via class method
- `SwingDirection`: INWARD, OUTWARD
- `FurnitureType`: ~40 values grouped by room category
- `FunctionalZone`: ENTRY, DAY, NIGHT
- `LayoutType`: SYMMETRIC, ASYMMETRIC, CIRCULAR
- `KitchenLayoutType`: 6 types with `min_area` property

### geometry.py

All classes are frozen Pydantic BaseModel (immutable value objects).

- `Point(x, y)`: distance_to(other)
- `Segment(start, end)`: length, midpoint, intersects(other)
- `Rectangle(x, y, width, height)`: center, area, aspect_ratio, corners, contains(point), overlaps(other), distance_to(other)
- `Polygon(points: list[Point])`: area (Shoelace formula), perimeter, bounding_box, centroid, contains(point) (ray casting)

Functions: `distance()`, `segments_intersect()`, `point_in_polygon()`, `rectangles_overlap()`, `min_distance_rect_to_rect()`

Edge cases:
- Rectangle overlap: touching edges = NOT overlapping (strict overlap)
- Polygon contains point on edge: returns True
- Parallel segments: never intersect

### dimensions.py

Named constants organized as module-level dicts/dataclasses. All lengths in mm, areas in m². Values sourced from apartment-planning-rules.md and equipment-furniture-rules.md.

Groups: MIN_AREAS, MIN_WIDTHS, MIN_HEIGHTS, DOOR_SIZES, WINDOW_RATIOS, ADJACENCY_MATRIX, FURNITURE_SIZES, CLEARANCES, KITCHEN_TRIANGLE.

### models.py

Pydantic v2 BaseModel with computed fields (@computed_field).

- `Window`: area_m2 = width * height / 1_000_000
- `Door`: swing_arc returns Rectangle representing the door sweep area
- `FurnitureItem`: bounding_box accounts for rotation; clearance_zone extends in front direction
- `Room`: area_m2 from boundary.area / 1_000_000; width_m and height_m from bounding_box; is_wet_zone and requires_window delegate to RoomType
- `Apartment`: total_area_m2 sums rooms; living_area_m2 sums only living rooms; adjacency_graph built from door connections

## Test Specification

### test_geometry.py (18 tests)

G01–G18 as specified in functional-requirements.md section 10.3.

### test_models.py (14 tests)

M01–M14 as specified in functional-requirements.md section 10.4.

### conftest.py fixtures

- `make_room(room_type, width, height, **kwargs)` — rectangular room
- `make_apartment(cls, rooms_spec)` — apartment from spec
- `make_door(type, width, swing, from_room, to_room)` — door
- `make_window(width, height)` — window
- `make_furniture(type, x, y, w, d, rotation)` — furniture item

## Acceptance Criteria

- All 32 tests pass
- `ruff check` passes with no errors
- Project installable via `uv pip install -e .`
- All types properly annotated
