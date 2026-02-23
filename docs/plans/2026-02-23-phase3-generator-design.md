# Phase 3: Generator (Greedy + CSP) — Design

## Summary

Phase 3 implements the two-level floorplan generator: a Greedy macro-level engine for room placement and a CSP micro-level solver for doors, windows, stoyaks, and furniture. Based on `docs/algorithm-greedy-csp.md`. Produces complete apartments that pass all 66 existing validators (P01-P34, F01-F32) with 45 new tests (18 greedy + 17 CSP + 10 integration).

## Scope

### New files

```
src/floorplan_generator/generator/
    __init__.py
    room_composer.py           # Room composition + size assignment
    greedy/
        __init__.py
        priority.py            # Priority queue for room ordering
        candidates.py          # Candidate slot generation (snap-to)
        scoring.py             # Scoring function + look-ahead
        engine.py              # Main greedy loop + restarts
    csp/
        __init__.py
        constraints.py         # Hard + soft constraint definitions
        door_placer.py         # Door placement on shared walls
        window_placer.py       # Window placement on external walls
        stoyak_placer.py       # Stoyak placement in wet zones
        furniture_placer.py    # Furniture backtracking placement
        solver.py              # CSP orchestrator
    layout_engine.py           # Orchestrator: Greedy -> CSP -> Validate
    factory.py                 # Dataset generation factory
tests/unit/
    test_greedy.py             # GR01-GR18
    test_csp.py                # CS01-CS17
tests/integration/
    __init__.py
    test_greedy_csp_integration.py  # GI01-GI10
```

### Modified files

- `src/floorplan_generator/core/models.py` — add `Stoyak` model, `RoomSpec` dataclass, `GenerationResult`
- `src/floorplan_generator/core/geometry.py` — add `shared_wall_length()`, `external_walls()`, `snap_to_edge()`
- `src/floorplan_generator/core/enums.py` — add `Side` enum (TOP, BOTTOM, LEFT, RIGHT), `Alignment` enum

## Architecture

### Two-level pipeline

```
RoomComposer (composition + sizes)
    |
    v
Greedy Engine (macro: room positions)
    |  Priority queue -> Candidate slots -> Score -> Softmax select
    |  Dead end? -> Restart with new seed
    v
CSP Solver (micro: doors, windows, stoyaks, furniture)
    |  Sequential: doors -> windows -> stoyaks -> furniture
    |  Hard constraints = backtrack, Soft constraints = warn
    |  CSP fail? -> Greedy restart
    v
Validation (P01-P34 + F01-F32)
    |  Mandatory violation? -> Restart
    v
Complete Apartment
```

### Greedy (macro-level)

**Priority queue** orders rooms from most constrained to least: hallway (edge anchor) -> corridor -> kitchen -> wet zones -> living room -> bedrooms -> storage. Within same priority, randomized via seed.

**Candidate slots** snap rooms to already-placed rooms: for each placed room x 4 sides x 3 alignments, filtered by: inside canvas, no overlap, shared wall >= door width, adjacency allowed (P16).

**Scoring function** with weighted criteria:

| Weight | Value | Controls |
|--------|-------|----------|
| W_WINDOW | 15.0 | External wall for windows (P12, P13) |
| W_CENTRAL | 12.0 | Living room centrality (P27) |
| W_ADJ | 10.0 | Adjacency matrix compliance (P16) |
| W_WET | 8.0 | Wet zone clustering (P24) |
| W_ZONE | 5.0 | Day/night zoning (P19) |
| W_BLOCK | 5.0 | Look-ahead blocking penalty |
| W_COMPACT | 3.0 | Bounding box compactness |

**Selection** via softmax top-K (K=3, temperature=0.5 default) for diversity.

**Look-ahead** checks if next 3 rooms can find at least 1 candidate after placement.

**Restarts** on dead end: seed + restart_num * 1000, up to 10 restarts.

### CSP (micro-level)

Solves sequentially: doors -> windows -> stoyaks -> furniture.

**Doors**: iterate shared walls, try positions at 50mm steps, check P21 (bathroom outward), P22 (no swing collision), P23 (wall gap >= 100mm), P15 (no kitchen->toilet).

**Windows**: for rooms requiring windows, place on external walls. Size chosen to satisfy P14 (area >= 1/8 floor area). Centered on wall.

**Stoyaks**: placed at corner of wet zone cluster, checking F32 (toilet <= 1000mm from stoyak).

**Furniture**: backtracking with forward checking + MRV. Large items first (bed, bathtub, sofa), then small. 50mm grid. Wall-snap heuristic. Hard constraints cause backtrack, soft constraints only warn.

### Hard vs Soft Constraints

**Hard (backtrack on violation):** no_overlap, inside_room, not_blocking_door, F01 toilet axis, F02 toilet front, F03 sink front, F04 bathtub exit, F05 outlet distance, F08-F11 stove/hood clearances, F17 oven front, F18 passage, F31 washer gap, F32 toilet-stoyak.

**Soft (warn only):** F06-F07 work triangle, F12-F16 kitchen/bedroom clearances, F19-F30 dining/living/entry rules, P28 dining entry.

## Design Decisions

1. **Frozen greedy output**: Once greedy places rooms, their positions are immutable. CSP only adds elements inside rooms.
2. **Room dimensions in mm**: All internal geometry stays in mm (matching existing codebase). Conversion to m^2 only at reporting.
3. **Reproducibility**: `random.Random(seed)` passed through entire pipeline. Same seed = same result.
4. **Slot as data class**: `Slot(position, target_room, side, alignment, shared_wall, score)` — lightweight, no mutation after creation.
5. **No spatial hash in v1**: Simple O(N) overlap checks sufficient for < 15 rooms. Spatial hash deferred to optimization phase.
6. **Furniture composition**: `room_composer.py` determines required + optional furniture based on room type and apartment class (table from algorithm doc section 5).

## Test Specification

18 greedy tests (GR01-GR18) + 17 CSP tests (CS01-CS17) + 10 integration tests (GI01-GI10) = 45 new tests. Test IDs and descriptions from `docs/algorithm-greedy-csp.md` section 8.2.

Combined with existing 181 tests: **226 total**.

## Sub-phases

- **3A: Greedy Layout** — room_composer, priority, candidates, scoring, engine (18 tests)
- **3B: CSP Solver** — constraints, door_placer, window_placer, stoyak_placer, furniture_placer, solver (17 tests)
- **3C: Integration** — layout_engine, factory (10 tests)

## Acceptance Criteria

- 45 new tests pass (226 total)
- `ruff check` passes
- Greedy success rate >= 95% with 10 restarts
- CSP success rate >= 90% on valid greedy topologies
- 0 mandatory rule violations in generated apartments
- Single layout generation <= 5 sec
- Same seed = identical output (reproducibility)
