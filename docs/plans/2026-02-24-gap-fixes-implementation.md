# Gap Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close all gaps identified in `docs/plans/2026-02-24-gap-analysis-report.md` between documentation and implementation.

**Architecture:** Nine sequential tasks ordered from simplest to most complex. Each task is self-contained with tests, touching minimal files. Tasks 1-5 are quick fixes (1-2 files each). Tasks 6-9 are larger features.

**Tech Stack:** Python 3.12+, Pydantic, Typer, svgwrite, pytest

---

### Task 1: Wire risers into GenerationResult

**Files:**
- Modify: `src/floorplan_generator/generator/layout_engine.py:88-90`
- Modify: `src/floorplan_generator/generator/csp/solver.py:100-107`
- Test: `tests/unit/test_csp.py` (existing, add case)

**Step 1: Fix CSP solver to return risers**

In `src/floorplan_generator/generator/csp/solver.py`, the `risers` variable from `place_risers()` on line 63 is computed but never included in `CSPResult`. Add a `risers` field to `CSPResult` and populate it.

First, add `risers` field to `CSPResult` in `src/floorplan_generator/generator/types.py`:

```python
class CSPResult(BaseModel):
    success: bool
    rooms: list[Room] = []
    risers: list["Riser"] = []  # ADD THIS LINE
    hard_violations: int = 0
    soft_violations: int = 0
    soft_details: list[str] = []
    reason: str = ""
```

Then in `src/floorplan_generator/generator/csp/solver.py`, line 101, add `risers=risers`:

```python
    return CSPResult(
        success=True,
        rooms=updated_rooms,
        risers=risers,          # ADD THIS LINE
        hard_violations=0,
        soft_violations=len(soft_details),
        soft_details=soft_details,
    )
```

**Step 2: Wire risers through layout_engine**

In `src/floorplan_generator/generator/layout_engine.py`, replace line 90 `risers=[]` with:

```python
        result = GenerationResult(
            apartment=apartment,
            risers=csp_result.risers,  # WAS: risers=[]
            restart_count=restart,
            seed_used=current_seed,
            recommended_violations=csp_result.soft_violations,
            violations=violations,
        )
```

**Step 3: Run existing tests**

Run: `pytest tests/ -x -q`
Expected: All existing tests still pass.

**Step 4: Commit**

```bash
git add src/floorplan_generator/generator/types.py src/floorplan_generator/generator/layout_engine.py src/floorplan_generator/generator/csp/solver.py
git commit -m "fix: wire riser placement results into GenerationResult"
```

---

### Task 2: Fix room ID prefix scheme

**Files:**
- Modify: `src/floorplan_generator/renderer/room_renderer.py:35-57`
- Test: `tests/unit/test_renderer.py` (add test case)

**Step 1: Write the failing test**

Add to `tests/unit/test_renderer.py`:

```python
from floorplan_generator.core.enums import RoomType
from floorplan_generator.renderer.room_renderer import _ROOM_PREFIX

def test_room_prefix_matches_spec():
    """Room ID prefixes must match functional-requirements.md section 6.2."""
    expected = {
        RoomType.BATHROOM: "b",
        RoomType.COMBINED_BATHROOM: "b",
        RoomType.BEDROOM: "s",
        RoomType.CHILDREN: "s",
        RoomType.LIVING_ROOM: "c",
        RoomType.CABINET: "c",
        RoomType.KITCHEN: "k",
        RoomType.KITCHEN_DINING: "k",
        RoomType.KITCHEN_NICHE: "k",
        RoomType.TOILET: "t",
        RoomType.WARDROBE: "w",
        RoomType.STORAGE: "l",
        RoomType.HALLWAY: "h",
        RoomType.HALL: "h",
        RoomType.CORRIDOR: "d",
        RoomType.LAUNDRY: "b",
        RoomType.BALCONY: "r",
    }
    for room_type, prefix in expected.items():
        assert _ROOM_PREFIX[room_type] == prefix, (
            f"{room_type}: expected '{prefix}', got '{_ROOM_PREFIX[room_type]}'"
        )
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_renderer.py::test_room_prefix_matches_spec -v`
Expected: FAIL

**Step 3: Fix the prefix mapping**

Replace `_ROOM_PREFIX` dict in `src/floorplan_generator/renderer/room_renderer.py:35-57` with:

```python
_ROOM_PREFIX: dict[RoomType, str] = {
    # b = bathroom/wet
    RoomType.BATHROOM: "b",
    RoomType.COMBINED_BATHROOM: "b",
    RoomType.LAUNDRY: "b",
    # s = sleep (bedroom, children)
    RoomType.BEDROOM: "s",
    RoomType.CHILDREN: "s",
    # c = living room, cabinet
    RoomType.LIVING_ROOM: "c",
    RoomType.CABINET: "c",
    # k = kitchen
    RoomType.KITCHEN: "k",
    RoomType.KITCHEN_DINING: "k",
    RoomType.KITCHEN_NICHE: "k",
    # t = toilet
    RoomType.TOILET: "t",
    # w = wardrobe
    RoomType.WARDROBE: "w",
    # l = storage/locker
    RoomType.STORAGE: "l",
    # h = hallway, hall
    RoomType.HALLWAY: "h",
    RoomType.HALL: "h",
    # d = corridor
    RoomType.CORRIDOR: "d",
    # r = other
    RoomType.BALCONY: "r",
}
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/floorplan_generator/renderer/room_renderer.py tests/unit/test_renderer.py
git commit -m "fix: room ID prefixes to match spec (b/s/c/k/t/w/l/h/d/r)"
```

---

### Task 3: Fix is_mandatory flags on furniture rules

**Files:**
- Modify: `src/floorplan_generator/rules/furniture_rules.py` (lines 43, 71, 123, 261, 566)

**Step 1: Write the failing test**

Add to `tests/unit/test_furniture_rules.py`:

```python
from floorplan_generator.rules.furniture_rules import (
    F01ToiletCenterFromWall,
    F02ToiletFrontClearance,
    F04BathtubExitClearance,
    F08StoveWallDistance,
    F18MinPassage,
)

def test_mandatory_flags_match_spec():
    """F01, F02, F04, F08, F18 must be mandatory per spec."""
    assert F01ToiletCenterFromWall.is_mandatory is True
    assert F02ToiletFrontClearance.is_mandatory is True
    assert F04BathtubExitClearance.is_mandatory is True
    assert F08StoveWallDistance.is_mandatory is True
    assert F18MinPassage.is_mandatory is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_furniture_rules.py::test_mandatory_flags_match_spec -v`
Expected: FAIL

**Step 3: Fix the flags**

In `src/floorplan_generator/rules/furniture_rules.py`, change `is_mandatory = False` to `is_mandatory = True` on these classes:
- `F01ToiletCenterFromWall` (line 43)
- `F02ToiletFrontClearance` (line 71)
- `F04BathtubExitClearance` (line 123)
- `F08StoveWallDistance` (line 261)
- `F18MinPassage` (line 566)

**Step 4: Run tests**

Run: `pytest tests/unit/test_furniture_rules.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/floorplan_generator/rules/furniture_rules.py tests/unit/test_furniture_rules.py
git commit -m "fix: F01/F02/F04/F08/F18 is_mandatory flags to match spec"
```

---

### Task 4: Complete ADJACENCY_MATRIX

**Files:**
- Modify: `src/floorplan_generator/core/dimensions.py:112-158`
- Test: `tests/unit/test_models.py` (add test)

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
from floorplan_generator.core.dimensions import ADJACENCY_MATRIX
from floorplan_generator.core.enums import RoomType

def test_adjacency_matrix_covers_all_room_types():
    """Every RoomType must have a row in ADJACENCY_MATRIX."""
    for rt in RoomType:
        assert rt in ADJACENCY_MATRIX, f"{rt} missing from ADJACENCY_MATRIX"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_adjacency_matrix_covers_all_room_types -v`
Expected: FAIL (8 missing room types)

**Step 3: Add missing rows**

In `src/floorplan_generator/core/dimensions.py`, add to `ADJACENCY_MATRIX` after the `STORAGE` row (line 157):

```python
    RoomType.KITCHEN_NICHE: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "-", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.KITCHEN_DINING: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "-", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.CHILDREN: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "+", RoomType.KITCHEN: "-", RoomType.BATHROOM: "(у)",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "(у)", RoomType.STORAGE: "+",
    },
    RoomType.CABINET: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "+", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.WARDROBE: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.BEDROOM: "+",
        RoomType.LIVING_ROOM: "+", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.LAUNDRY: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.BATHROOM: "+",
        RoomType.COMBINED_BATHROOM: "+", RoomType.KITCHEN: "-", RoomType.BEDROOM: "-",
        RoomType.LIVING_ROOM: "-", RoomType.TOILET: "-", RoomType.STORAGE: "+",
    },
    RoomType.BALCONY: {
        RoomType.LIVING_ROOM: "+", RoomType.BEDROOM: "+", RoomType.CHILDREN: "+",
        RoomType.CABINET: "+", RoomType.KITCHEN: "+", RoomType.KITCHEN_DINING: "+",
    },
    RoomType.HALL: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "+", RoomType.KITCHEN: "+", RoomType.BATHROOM: "+",
        RoomType.TOILET: "+", RoomType.COMBINED_BATHROOM: "+", RoomType.STORAGE: "+",
    },
```

**Step 4: Run tests**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/floorplan_generator/core/dimensions.py tests/unit/test_models.py
git commit -m "fix: complete ADJACENCY_MATRIX for all 17 room types"
```

---

### Task 5: Add Apartment.functional_zones and metadata room_composition

**Files:**
- Modify: `src/floorplan_generator/core/models.py:177-217`
- Modify: `src/floorplan_generator/generator/factory.py:94-106`
- Test: `tests/unit/test_models.py` (add test)

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
from floorplan_generator.core.enums import FunctionalZone

def test_apartment_functional_zones(economy_1room):
    """Apartment.functional_zones groups rooms by zone."""
    zones = economy_1room.functional_zones
    assert FunctionalZone.LIVING in zones
    assert FunctionalZone.WET in zones
    assert FunctionalZone.TRANSIT in zones
    # living room should be in LIVING zone
    living_ids = {r.id for r in zones[FunctionalZone.LIVING]}
    living_rooms = [r for r in economy_1room.rooms if r.room_type.is_living]
    assert all(r.id in living_ids for r in living_rooms)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_apartment_functional_zones -v`
Expected: FAIL (AttributeError: functional_zones)

**Step 3: Add functional_zones computed property**

In `src/floorplan_generator/core/models.py`, add to `Apartment` class after `room_composition`:

```python
    @computed_field
    @property
    def functional_zones(self) -> dict[str, list[str]]:
        """Group room IDs by functional zone."""
        from floorplan_generator.core.enums import FunctionalZone
        zones: dict[str, list[str]] = {
            FunctionalZone.LIVING: [],
            FunctionalZone.WET: [],
            FunctionalZone.TRANSIT: [],
        }
        for room in self.rooms:
            if room.room_type.is_wet_zone:
                zones[FunctionalZone.WET].append(room.id)
            elif room.room_type.is_living:
                zones[FunctionalZone.LIVING].append(room.id)
            else:
                zones[FunctionalZone.TRANSIT].append(room.id)
        return zones
```

**Step 4: Add room_composition to metadata**

In `src/floorplan_generator/generator/factory.py`, add to the `entry` dict (after line 104):

```python
            "room_composition": {
                rt.value: count
                for rt, count in result.apartment.room_composition.items()
            },
```

**Step 5: Run tests**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/floorplan_generator/core/models.py src/floorplan_generator/generator/factory.py tests/unit/test_models.py
git commit -m "feat: add Apartment.functional_zones and room_composition to metadata"
```

---

### Task 6: SVG structure fixes (room IDs, mebel variants)

**Files:**
- Modify: `src/floorplan_generator/renderer/room_renderer.py:90-126`
- Modify: `src/floorplan_generator/renderer/svg_renderer.py:33-79`
- Modify: `src/floorplan_generator/cli.py` (add `--variants` option)
- Test: `tests/unit/test_renderer.py` (add tests)

**Step 1: Write failing tests for room child element IDs**

Add to `tests/unit/test_renderer.py`:

```python
import svgwrite
from floorplan_generator.renderer.room_renderer import render_rooms, compute_room_group_ids
from floorplan_generator.renderer.theme import get_default_theme
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import Room

def test_room_group_has_path_and_text_ids():
    """Room group must contain elements with {group_id}_path and {group_id}_text IDs."""
    room = Room(
        id="test1",
        room_type=RoomType.LIVING_ROOM,
        boundary=Polygon(points=[
            Point(x=0, y=0), Point(x=4000, y=0),
            Point(x=4000, y=4000), Point(x=0, y=4000),
        ]),
    )
    theme = get_default_theme()
    mapper = CoordinateMapper([room], 2000, 2000)
    dwg = svgwrite.Drawing(size=("2000px", "2000px"))
    room_ids = compute_room_group_ids([room])
    render_rooms(dwg, [room], room_ids, mapper, theme)
    svg = dwg.tostring()
    gid = room_ids["test1"]
    assert f'id="{gid}_path"' in svg
    assert f'id="{gid}_text"' in svg
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_renderer.py::test_room_group_has_path_and_text_ids -v`
Expected: FAIL

**Step 3: Add IDs to room polygon and text elements**

In `src/floorplan_generator/renderer/room_renderer.py`, modify `render_rooms()`. Add `id=f"{group_id}_path"` to the polygon and `id=f"{group_id}_text"` to the first text element:

```python
        group.add(dwg.polygon(
            points=points,
            fill=fill,
            stroke=theme.rooms.default_stroke,
            stroke_width=theme.rooms.stroke_width,
            id=f"{group_id}_path",
        ))

        if show_labels:
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
                id=f"{group_id}_text",
            ))
```

**Step 4: Write failing test for mebel_1 structure**

```python
from floorplan_generator.renderer.svg_renderer import render_svg
from floorplan_generator.generator.types import GenerationResult, Riser
from floorplan_generator.core.models import Apartment

def test_svg_has_mebel_1_group(economy_1room):
    """SVG must contain <g id="mebel_1"> instead of <g id="mebel">."""
    result = GenerationResult(
        apartment=economy_1room,
        risers=[],
        restart_count=0,
        seed_used=42,
        recommended_violations=0,
    )
    svg = render_svg(result)
    assert 'id="mebel_1"' in svg
```

**Step 5: Rename mebel group to mebel_1 in svg_renderer**

In `src/floorplan_generator/renderer/svg_renderer.py`, change line 62:
```python
    furniture_group = dwg.g(id="mebel_1", style="display:inline")
```

**Step 6: Add --variants option to generate command**

In `src/floorplan_generator/cli.py`, add to `generate` function parameters:
```python
    variants: int = typer.Option(1, "--variants", help="Number of furniture variants (1 or 2)"),
```

Pass `variants` through to `generate_dataset` and `render_svg_to_file`. For now, variant 2 generates an empty hidden group since the doc says `display:none`. In `svg_renderer.py`, add `variants` parameter to `render_svg`:

```python
def render_svg(
    result: GenerationResult, theme: Theme | None = None,
    *, show_dimensions: bool = False, show_labels: bool = True,
    variants: int = 1,
) -> str:
```

After the mebel_1 group, add:
```python
    if variants >= 2:
        furniture_group_2 = dwg.g(id="mebel_2", style="display:none")
        dwg.add(furniture_group_2)
```

**Step 7: Run tests**

Run: `pytest tests/unit/test_renderer.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add src/floorplan_generator/renderer/room_renderer.py src/floorplan_generator/renderer/svg_renderer.py src/floorplan_generator/cli.py tests/unit/test_renderer.py
git commit -m "feat: add room element IDs, mebel_1/mebel_2 SVG structure, --variants CLI option"
```

---

### Task 7: Add missing CLI commands (validate, rules, extract-furniture)

**Files:**
- Modify: `src/floorplan_generator/cli.py`
- Test: `tests/unit/test_cli.py` (new file)

**Step 1: Write the failing tests**

Create `tests/unit/test_cli.py`:

```python
"""CLI command tests."""
from typer.testing import CliRunner
from floorplan_generator.cli import app

runner = CliRunner()

def test_rules_list():
    """'rules --list' must output rule IDs."""
    result = runner.invoke(app, ["rules", "--list"])
    assert result.exit_code == 0
    assert "P01" in result.output
    assert "F01" in result.output

def test_rules_by_id():
    """'rules --id P01' shows a single rule."""
    result = runner.invoke(app, ["rules", "--id", "P01"])
    assert result.exit_code == 0
    assert "P01" in result.output

def test_rules_by_type_mandatory():
    """'rules --type mandatory' filters to mandatory rules."""
    result = runner.invoke(app, ["rules", "--type", "mandatory"])
    assert result.exit_code == 0
    assert "P01" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_cli.py -v`
Expected: FAIL (no 'rules' command)

**Step 3: Implement the `rules` command**

Add to `src/floorplan_generator/cli.py`:

```python
@app.command()
def rules(
    list_all: bool = typer.Option(False, "--list", help="List all rules"),
    rule_id: str | None = typer.Option(None, "--id", help="Show specific rule by ID"),
    rule_type: str | None = typer.Option(None, "--type", help="Filter: mandatory|recommended"),
) -> None:
    """List and query validation rules."""
    from floorplan_generator.rules.registry import create_default_registry

    registry = create_default_registry()

    if rule_id:
        rule = registry.get(rule_id)
        mandatory = "mandatory" if rule.is_mandatory else "recommended"
        typer.echo(f"{rule.rule_id}: {rule.name} [{mandatory}]")
        typer.echo(f"  {rule.description}")
        typer.echo(f"  Basis: {rule.regulatory_basis}")
        return

    if rule_type == "mandatory":
        rules_list = registry.mandatory_rules()
    elif rule_type == "recommended":
        rules_list = registry.recommended_rules()
    else:
        rules_list = registry.all_rules()

    for rule in rules_list:
        mandatory = "mandatory" if rule.is_mandatory else "recommended"
        typer.echo(f"{rule.rule_id}: {rule.name} [{mandatory}]")
```

**Step 4: Implement the `validate` command**

```python
@app.command()
def validate(
    svg_path: Path = typer.Argument(..., help="Path to apartment JSON file"),
    rules_filter: str = typer.Option("all", "--rules", help="all|mandatory|recommended"),
    format_output: str = typer.Option("text", "--format", help="text|json"),
) -> None:
    """Validate an apartment JSON file against rules."""
    import json as _json
    from floorplan_generator.generator.types import GenerationResult
    from floorplan_generator.rules.registry import create_default_registry
    from floorplan_generator.rules.rule_engine import RuleStatus

    result = GenerationResult.model_validate_json(svg_path.read_text())
    registry = create_default_registry()

    if rules_filter == "mandatory":
        validators = registry.mandatory_rules()
    elif rules_filter == "recommended":
        validators = registry.recommended_rules()
    else:
        validators = registry.all_rules()

    results = [v.validate(result.apartment) for v in validators]

    if format_output == "json":
        data = [r.model_dump() for r in results]
        typer.echo(_json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for r in results:
            icon = {"pass": "OK", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}[r.status]
            typer.echo(f"[{icon}] {r.rule_id}: {r.message}")
        fails = sum(1 for r in results if r.status == RuleStatus.FAIL)
        typer.echo(f"\n{fails} failures out of {len(results)} rules checked")
```

**Step 5: Implement the `extract-furniture` command**

```python
@app.command(name="extract-furniture")
def extract_furniture(
    svg_path: Path = typer.Argument(..., help="Path to SVG plan file"),
    output_path: Path = typer.Option(
        Path("./data/furniture_library.json"), "--output", "-o", help="Output JSON path",
    ),
) -> None:
    """Extract furniture definitions to a JSON library."""
    import json as _json
    from floorplan_generator.core.dimensions import CLEARANCES, FURNITURE_SIZES
    from floorplan_generator.core.enums import FurnitureType

    library = {}
    for ft in FurnitureType:
        size = FURNITURE_SIZES.get(ft)
        if size is None:
            continue
        library[ft.value] = {
            "width": size[0],
            "depth": size[1],
            "height": size[2],
            "clearance": 600.0,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_json.dumps(library, indent=2, ensure_ascii=False))
    typer.echo(f"Extracted {len(library)} furniture items to {output_path}")
```

**Step 6: Run tests**

Run: `pytest tests/unit/test_cli.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/floorplan_generator/cli.py tests/unit/test_cli.py
git commit -m "feat: add validate, rules, extract-furniture CLI commands"
```

---

### Task 8: Add missing test fixtures and test files

**Files:**
- Modify: `tests/conftest.py` (add `business_3room` fixture)
- Create: `tests/integration/test_generation.py`
- Create: `tests/integration/test_validation.py`
- Create: `tests/svg/test_svg_output.py`

**Step 1: Add business_3room fixture**

Add to `tests/conftest.py`:

```python
@pytest.fixture
def business_3room(make_room, make_door, make_window, make_apartment):
    """3-room business apartment."""
    hallway = make_room(RoomType.HALLWAY, width_m=3.0, height_m=2.5)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.5, height_m=6.0)
    living = make_room(
        RoomType.LIVING_ROOM, width_m=6.0, height_m=5.0,
        windows=[make_window(width=2000.0, height=1500.0)],
    )
    bed1 = make_room(
        RoomType.BEDROOM, width_m=4.5, height_m=4.5,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    bed2 = make_room(
        RoomType.BEDROOM, width_m=4.0, height_m=4.0,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    kitchen = make_room(
        RoomType.KITCHEN, width_m=5.0, height_m=4.0,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    bathroom = make_room(RoomType.BATHROOM, width_m=2.5, height_m=2.5)
    toilet = make_room(RoomType.TOILET, width_m=1.2, height_m=1.8)
    storage = make_room(RoomType.STORAGE, width_m=1.5, height_m=1.5)

    d1 = make_door(door_type=DoorType.ENTRANCE, width=960.0,
                    room_from=hallway.id, room_to=corridor.id)
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(room_from=corridor.id, room_to=bed1.id)
    d4 = make_door(room_from=corridor.id, room_to=bed2.id)
    d5 = make_door(door_type=DoorType.KITCHEN, width=800.0,
                    room_from=corridor.id, room_to=kitchen.id)
    d6 = make_door(door_type=DoorType.BATHROOM, width=600.0,
                    swing=SwingDirection.OUTWARD,
                    room_from=corridor.id, room_to=bathroom.id)
    d7 = make_door(door_type=DoorType.BATHROOM, width=600.0,
                    swing=SwingDirection.OUTWARD,
                    room_from=corridor.id, room_to=toilet.id)

    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2, d3, d4, d5, d6, d7]})

    return make_apartment(
        ApartmentClass.BUSINESS,
        [hallway, corridor, living, bed1, bed2, kitchen, bathroom, toilet, storage],
        num_rooms=3,
    )
```

**Step 2: Create tests/integration/test_generation.py**

Create `tests/integration/test_generation.py` with tests I01-I10:

```python
"""Integration tests: generation pipeline (I01-I10)."""
import pytest
from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment

@pytest.mark.parametrize("cls,rooms", [
    (ApartmentClass.ECONOMY, 1),
    (ApartmentClass.ECONOMY, 2),
    (ApartmentClass.COMFORT, 1),
    (ApartmentClass.COMFORT, 2),
    (ApartmentClass.COMFORT, 3),
    (ApartmentClass.BUSINESS, 2),
    (ApartmentClass.BUSINESS, 3),
])
def test_generate_apartment_succeeds(cls, rooms):
    """I01-I07: Generation pipeline produces a valid apartment."""
    result = generate_apartment(cls, rooms, seed=42, max_restarts=20)
    assert result is not None
    assert result.apartment is not None
    assert len(result.apartment.rooms) >= rooms + 2  # living + kitchen + bath + transit

def test_generate_has_doors():
    """I08: Every room in generated apartment has at least one door."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    for room in result.apartment.rooms:
        assert len(room.doors) >= 1, f"{room.room_type} has no doors"

def test_generate_has_windows_where_required():
    """I09: Rooms requiring windows have at least one window."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42, max_restarts=20)
    assert result is not None
    for room in result.apartment.rooms:
        if room.requires_window:
            assert len(room.windows) >= 1, f"{room.room_type} missing window"

def test_generate_deterministic():
    """I10: Same seed produces same layout."""
    r1 = generate_apartment(ApartmentClass.ECONOMY, 1, seed=100, max_restarts=20)
    r2 = generate_apartment(ApartmentClass.ECONOMY, 1, seed=100, max_restarts=20)
    assert r1 is not None and r2 is not None
    assert r1.apartment.total_area_m2 == r2.apartment.total_area_m2
    assert len(r1.apartment.rooms) == len(r2.apartment.rooms)
```

**Step 3: Create tests/integration/test_validation.py**

Create `tests/integration/test_validation.py` with tests V01-V04:

```python
"""Integration tests: validation pipeline (V01-V04)."""
import pytest
from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.rules.registry import create_default_registry
from floorplan_generator.rules.rule_engine import RuleStatus

def _gen(cls, rooms, seed=42):
    return generate_apartment(cls, rooms, seed=seed, max_restarts=20)

def test_validate_all_rules_run():
    """V01: All registered rules execute without error."""
    result = _gen(ApartmentClass.ECONOMY, 1)
    assert result is not None
    registry = create_default_registry()
    results = registry.validate_all(result.apartment)
    assert len(results) > 0
    for r in results:
        assert r.status in (RuleStatus.PASS, RuleStatus.FAIL, RuleStatus.WARN, RuleStatus.SKIP)

def test_validate_mandatory_subset():
    """V02: Mandatory rules are a subset of all rules."""
    registry = create_default_registry()
    mandatory = registry.mandatory_rules()
    all_rules = registry.all_rules()
    mandatory_ids = {r.rule_id for r in mandatory}
    all_ids = {r.rule_id for r in all_rules}
    assert mandatory_ids.issubset(all_ids)

def test_validate_recommended_subset():
    """V03: Recommended rules are a subset of all rules."""
    registry = create_default_registry()
    recommended = registry.recommended_rules()
    all_rules = registry.all_rules()
    recommended_ids = {r.rule_id for r in recommended}
    all_ids = {r.rule_id for r in all_rules}
    assert recommended_ids.issubset(all_ids)

def test_validate_no_overlap():
    """V04: Mandatory and recommended are disjoint."""
    registry = create_default_registry()
    mandatory_ids = {r.rule_id for r in registry.mandatory_rules()}
    recommended_ids = {r.rule_id for r in registry.recommended_rules()}
    assert mandatory_ids.isdisjoint(recommended_ids)
```

**Step 4: Create tests/svg/ directory and test file**

Create `tests/svg/__init__.py` (empty) and `tests/svg/test_svg_output.py`:

```python
"""SVG output structure tests (S01-S15)."""
import pytest
from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.renderer.svg_renderer import render_svg
from floorplan_generator.renderer.theme import get_default_theme

@pytest.fixture
def generated_svg():
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    return render_svg(result)

def test_svg_has_background(generated_svg):
    """S01: SVG contains background rect."""
    assert 'id="background"' in generated_svg

def test_svg_has_floor_group(generated_svg):
    """S02: SVG contains floor group."""
    assert 'id="floor"' in generated_svg

def test_svg_has_mebel_group(generated_svg):
    """S03: SVG contains mebel_1 group."""
    assert 'id="mebel_1"' in generated_svg

def test_svg_has_room_groups(generated_svg):
    """S04: SVG contains room groups with correct prefixes."""
    assert 'id="h1"' in generated_svg or 'id="d1"' in generated_svg

def test_svg_has_viewbox(generated_svg):
    """S05: SVG has viewBox."""
    assert 'viewBox="0 0 2000 2000"' in generated_svg

def test_svg_has_room_path_ids(generated_svg):
    """S06: Room groups contain _path elements."""
    assert '_path"' in generated_svg

def test_svg_has_room_text_ids(generated_svg):
    """S07: Room groups contain _text elements."""
    assert '_text"' in generated_svg

def test_svg_has_doors(generated_svg):
    """S08: SVG contains door elements."""
    # Doors rendered as lines/arcs inside floor group
    assert '<line' in generated_svg or '<path' in generated_svg

def test_svg_has_windows(generated_svg):
    """S09: SVG contains window rectangles."""
    assert '<rect' in generated_svg

def test_svg_valid_xml(generated_svg):
    """S10: SVG is valid XML."""
    from xml.etree import ElementTree
    ElementTree.fromstring(generated_svg)

def test_svg_dimensions_option():
    """S11: Dimensions show when enabled."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg = render_svg(result, show_dimensions=True)
    # Dimension lines are rendered as additional elements
    assert len(svg) > len(render_svg(result, show_dimensions=False))

def test_svg_no_labels_option():
    """S12: Labels hidden when disabled."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_with = render_svg(result, show_labels=True)
    svg_without = render_svg(result, show_labels=False)
    assert "Гостиная" in svg_with or "Прихожая" in svg_with
    assert "м²" not in svg_without

def test_svg_theme_applied():
    """S13: Custom theme colors appear in SVG."""
    from floorplan_generator.renderer.theme import load_theme
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    dark = load_theme("dark")
    svg = render_svg(result, dark)
    assert dark.canvas.background in svg

def test_svg_canvas_size():
    """S14: Canvas size matches theme."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg = render_svg(result)
    assert '2000px' in svg

def test_svg_multiple_rooms():
    """S15: Multi-room apartment renders all rooms."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42, max_restarts=20)
    assert result is not None
    svg = render_svg(result)
    # Should have multiple room groups
    room_count = sum(1 for r in result.apartment.rooms if True)
    # At least one group per room type prefix appears
    assert svg.count('id="') >= room_count
```

**Step 5: Run all new tests**

Run: `pytest tests/integration/ tests/svg/ -v`
Expected: PASS

**Step 6: Commit**

```bash
git add tests/conftest.py tests/integration/test_generation.py tests/integration/test_validation.py tests/svg/__init__.py tests/svg/test_svg_output.py
git commit -m "feat: add business_3room fixture, integration tests, SVG output tests"
```

---

### Task 9: Generate data/furniture_library.json

**Files:**
- Create: `data/furniture_library.json`

**Step 1: Generate the library file**

Run: `cd /Users/sergeifrangulov/projects/floorplan-generator-next && python -m floorplan_generator.cli extract-furniture docs/plan-example.svg --output data/furniture_library.json`

If CLI not installed as entry point, use:
```bash
python -c "
from floorplan_generator.cli import app
from typer.testing import CliRunner
runner = CliRunner()
runner.invoke(app, ['extract-furniture', 'docs/plan-example.svg', '--output', 'data/furniture_library.json'])
"
```

**Step 2: Verify file exists and is valid JSON**

```bash
python -c "import json; data = json.load(open('data/furniture_library.json')); print(f'{len(data)} items')"
```
Expected: `45 items` (or similar count)

**Step 3: Commit**

```bash
git add data/furniture_library.json
git commit -m "feat: generate data/furniture_library.json with all furniture definitions"
```

---

## Summary of all tasks

| Task | What | Files changed | Estimated complexity |
|------|------|---------------|---------------------|
| 1 | Wire risers into GenerationResult | 3 files, ~5 lines | Trivial |
| 2 | Fix room ID prefixes | 1 file + test | Simple |
| 3 | Fix is_mandatory flags | 1 file + test | Trivial |
| 4 | Complete ADJACENCY_MATRIX | 1 file + test | Simple |
| 5 | Add functional_zones + metadata | 2 files + test | Simple |
| 6 | SVG structure (IDs, mebel variants) | 3 files + tests | Medium |
| 7 | CLI commands (validate, rules, extract) | 1 file + tests | Medium |
| 8 | Missing test files + fixtures | 5 new files | Medium |
| 9 | Generate furniture_library.json | 1 file | Trivial |

**Not included** (deferred as separate projects):
- Room placement algorithm (Greedy -> CSP): Major architectural change
- P19/P23/P24 logic fixes: Require algorithm rework
- SVG font (GraphikLCG-Regular): Requires font file availability
- F10/F11 height checks: 2D model limitation
- F32 riser distance: Depends on Task 1 (risers) being verified
