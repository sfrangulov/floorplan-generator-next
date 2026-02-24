# Wall, Window & Door Rendering Fix — Design

**Date:** 2026-02-24
**Status:** Approved

## Problem Statement

Current SVG rendering has several visual defects:
1. Exterior wall corners have gaps (rects don't join at L-shaped intersections)
2. Some exterior walls are misclassified as interior (shared-edge algorithm is flawed)
3. Interior partitions appear on the exterior perimeter
4. Windows are too thin (two 1.5px lines with 4px gap) — invisible at normal scale
5. No entrance door rendered
6. Windows don't match reference SVG style

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Exterior walls | Single filled polygon via Shapely | Eliminates corner gaps, matches reference SVGs |
| Interior walls | Same polygon approach via Shapely | Consistency, user preference |
| Wall thickness | Keep 225mm external, ~75mm internal | 225mm is SNiP standard; 75mm is ~3x thinner |
| Window style | Reference SVG style (opening rect + glass line + mullions) | Match etalon files |
| Entrance door | Same as interior door visually | Reference SVGs use same symbol on exterior wall |
| Polygon library | Shapely | Reliable for union/buffer/difference operations |
| Wall classification | Union-based (boundary = outer, interior = shared edges) | Replaces flawed edge-overlap algorithm |

## Architecture

### 1. Exterior Walls — Polygon Approach

```
rooms[] → Shapely Polygon each → unary_union() → inner_contour
inner_contour.buffer(225mm, join_style=mitre) → outer_contour
outer_contour.difference(inner_contour) → wall_ring
wall_ring.difference(window_openings + door_openings) → final_wall_polygon
polygon_to_svg_path(final_wall_polygon) → <path fill="#000000" fill-rule="evenodd">
```

### 2. Interior Walls — Polygon Approach

```
For each shared edge between rooms:
  Create thin rectangle (75mm wide) centered on the shared edge → Shapely box
unary_union(all_partition_boxes) → partition_polygon
partition_polygon.difference(door_openings) → final_partition_polygon
polygon_to_svg_path(final_partition_polygon) → <path fill="#000000">
```

### 3. Windows — Reference Style

Each window rendered as a group of SVG elements:

```
┌──────────────────────────────────┐
│     outer rect (opening)         │  stroke=black, fill=none
│                                  │  size = window_width × wall_thickness
├──────────────────────────────────┤  glass line (thin rect, ~14px height)
│ ██ │            │ ██ │      │ ██ │  mullion rects (~12×14 SVG units)
├──────────────────────────────────┤
│                                  │
└──────────────────────────────────┘
```

Components:
- **Opening rect**: `width=window_width`, `height=wall_thickness`, stroke=black, fill=none
- **Glass line**: thin rect at ~75% depth from outer edge, full width
- **Mullions**: small rects at window edges + every ~500-600mm spacing

### 4. Entrance Door

- Opening cut in exterior wall polygon (same as windows)
- Door rendered as standard leaf rect + swing arc
- Identified by `DoorType.ENTRANCE` or door on HALLWAY room at exterior boundary

## Files to Change

### New Files
- `src/floorplan_generator/renderer/outline.py` — Shapely-based wall polygon computation
  - `compute_outer_wall_polygon(rooms, thickness) → Polygon`
  - `compute_inner_wall_polygons(rooms, thickness) → Polygon`
  - `cut_openings(wall_poly, rooms) → Polygon`
  - `shapely_to_svg_path(poly, mapper) → str`

### Modified Files
- `wall_renderer.py` — Replace `_classify_edges` + rect rendering with outline.py polygon approach
- `window_renderer.py` — Rewrite `_render_single_window()` to reference SVG style
- `door_renderer.py` — Handle entrance door openings in exterior wall
- `svg_renderer.py` — Update render pipeline to use new wall renderer
- `pyproject.toml` — Add `shapely` dependency
- `renderer/themes/blueprint.json` — Update `inner_thickness` to 75.0mm

### Unchanged
- `coordinate_mapper.py` — No changes needed
- `core/models.py` — No changes needed
- `core/dimensions.py` — No changes needed (225mm stays)
