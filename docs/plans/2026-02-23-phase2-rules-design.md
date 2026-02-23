# Phase 2: Rule Engine & Validators — Design

## Summary

Phase 2 implements the validation layer: a rule engine with 60 validators (28 planning + 6 mock + 32 furniture) and 141 tests (73 planning + 68 furniture). Rules follow Russian building codes (SP 54.13330, SNiP 31-01, GOST 13025) and ergonomic standards (Neufert).

## Scope

- `src/floorplan_generator/rules/__init__.py` — package init
- `src/floorplan_generator/rules/rule_engine.py` — base classes (RuleValidator ABC, RuleResult, RuleStatus, MockAlwaysPassRule)
- `src/floorplan_generator/rules/geometry_helpers.py` — spatial helper functions for distance calculations
- `src/floorplan_generator/rules/planning_rules.py` — 28 real planning validators (P01-P28) + 6 mock rules (P29-P34)
- `src/floorplan_generator/rules/furniture_rules.py` — 32 furniture validators (F01-F32)
- `src/floorplan_generator/rules/registry.py` — RuleRegistry with create_default_registry()
- `src/floorplan_generator/core/geometry.py` — update: add min_distance_point_to_segment, min_distance_rect_to_segment
- `tests/conftest.py` — update: add apartment fixtures (economy_1room, comfort_2room, etc.)
- `tests/unit/test_planning_rules.py` — 73 tests
- `tests/unit/test_furniture_rules.py` — 68 tests

## Approach

Strict TDD (matching Phase 1 pattern): write all tests RED per category, then implement to GREEN.

## Design Decisions

### Rule Engine (rule_engine.py)

```python
class RuleStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"

class RuleResult(BaseModel):
    rule_id: str
    status: RuleStatus
    message: str
    details: dict | None = None

class RuleValidator(ABC):
    rule_id: str
    name: str
    description: str
    is_mandatory: bool
    regulatory_basis: str

    @abstractmethod
    def validate(self, apartment: Apartment) -> RuleResult: ...

    def _pass(self, msg: str) -> RuleResult: ...
    def _fail(self, msg: str, details: dict | None = None) -> RuleResult: ...
    def _skip(self, msg: str) -> RuleResult: ...

class MockAlwaysPassRule(RuleValidator):
    """Base for P29-P34. Always returns PASS with 'mock' in message."""
    is_mandatory = False
    def validate(self, apartment: Apartment) -> RuleResult:
        return self._pass(f"{self.name}: mock — always PASS")
```

### Geometry Helpers

Wall distances use room boundary polygon segments (not explicit Wall model):

- `min_distance_point_to_segment(point, segment) -> float`
- `min_distance_rect_to_segment(rect, segment) -> float`
- `nearest_wall_distance(item_bbox, room) -> float`
- `distance_to_window(item_bbox, window, room) -> float`
- `clearance_in_front(item, room) -> float`
- `items_of_type(room, *types) -> list[FurnitureItem]`
- `kitchen_triangle_perimeter(room) -> float | None`

### Planning Rules (P01-P34)

28 real + 6 mock. Categories:

- **Area rules (P01-P05):** room.area_m2 vs thresholds from dimensions.py
- **Width rules (P06-P10):** room.width_m vs MIN_WIDTHS
- **Proportion (P11):** room.aspect_ratio <= 2.0 for living rooms
- **Window rules (P12-P14):** window count and area ratio
- **Adjacency/connectivity (P15-P19):** door connections, adjacency matrix, passthrough check, zone separation
- **Door rules (P20-P23):** entrance width, swing direction, collision, wall gap
- **Wet zone rules (P24-P25):** connected component, ensuite condition
- **Recommendations (P26-P28):** living room width, central position, dining table placement
- **Mock rules (P29-P34):** always PASS (3D/multi-floor/insolation concerns)

### Furniture Rules (F01-F32)

32 validators. Categories:

- **Bathroom (F01-F05):** toilet axis from wall, clearances in front of toilet/sink/bathtub, outlet distance
- **Kitchen (F06-F13):** work triangle, sink-stove distance, stove-wall/window gaps, hood height, fridge-stove, parallel rows
- **Bedroom (F14-F16):** bed passage, wardrobe clearance, drawer clearance
- **Safety (F17-F18):** oven clearance, minimum passage
- **Dining (F19-F20):** table-wall passage, shelf height
- **Living room (F21-F29):** sofa-armchair distance, armchair spacing, wall-furniture gap, carpet-wall, shelving clearance, furniture load ratio, TV placement, sofa bed length, armchair seat width
- **Entry/utility (F30-F32):** entry zone, washer gap, toilet-stoyak distance

### Registry (registry.py)

```python
class RuleRegistry:
    def register(self, rule: RuleValidator) -> None: ...
    def get(self, rule_id: str) -> RuleValidator: ...
    def all_rules(self) -> list[RuleValidator]: ...
    def mandatory_rules(self) -> list[RuleValidator]: ...
    def recommended_rules(self) -> list[RuleValidator]: ...
    def validate_all(self, apartment: Apartment) -> list[RuleResult]: ...

def create_default_registry() -> RuleRegistry:
    """Instantiate and register all P01-P34 and F01-F32 rules."""
```

### Test Fixtures (conftest.py)

New ready-made apartment fixtures:

- `economy_1room()` — 1-room economy apartment with rooms, doors, windows
- `comfort_2room()` — 2-room comfort apartment
- `comfort_3room()` — 3-room comfort apartment
- `business_3room()` — 3-room business apartment

## Test Specification

73 planning tests + 68 furniture tests = 141 total. All test IDs and scenarios are defined in functional-requirements.md sections 10.5 and 10.6.

## Acceptance Criteria

- All 141 new tests pass (+ 32 existing = 173 total)
- `ruff check` passes with no errors
- Each rule class has rule_id, name, description, is_mandatory, regulatory_basis
- Mock rules (P29-P34) always return PASS with "mock" in message
- Registry contains all 66 rules (34 planning + 32 furniture)
