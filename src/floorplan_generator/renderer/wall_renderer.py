"""Wall rendering: Shapely-based polygon outlines for outer and inner walls."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.outline import (
    compute_inner_wall_polygons,
    compute_outer_wall_polygon,
    shapely_to_svg_path,
)
from floorplan_generator.renderer.theme import Theme


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render walls as Shapely-computed polygon paths."""
    outer_t = theme.walls.outer_thickness
    inner_t = theme.walls.inner_thickness

    # Outer walls: polygon ring with window/entrance-door openings
    outer_poly = compute_outer_wall_polygon(
        rooms, thickness=outer_t, cut_windows=True, cut_doors=True,
    )
    if not outer_poly.is_empty:
        path_d = shapely_to_svg_path(outer_poly, mapper)
        if path_d:
            group.add(dwg.path(
                d=path_d,
                fill=theme.walls.outer_fill,
                stroke="none",
                fill_rule="evenodd",
            ))

    # Inner walls: thin polygons on shared edges with door openings
    inner_poly = compute_inner_wall_polygons(
        rooms, thickness=inner_t, cut_doors=True,
        outer_thickness=outer_t,
    )
    if not inner_poly.is_empty:
        path_d = shapely_to_svg_path(inner_poly, mapper)
        if path_d:
            group.add(dwg.path(
                d=path_d,
                fill=theme.walls.inner_fill,
                stroke="none",
                fill_rule="evenodd",
            ))
