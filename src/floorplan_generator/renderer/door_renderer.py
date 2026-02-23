"""Door rendering: door leaf rect + swing arc."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import SwingDirection
from floorplan_generator.core.models import Door, Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_LEAF_THICKNESS_MM = 40.0  # door leaf thickness in mm


def render_doors(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all doors with leaf rect and swing arc."""
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
    """Render a single door: thin leaf rect + quarter-circle swing arc."""
    pos = mapper.to_svg(door.position)
    w = mapper.scale_length(door.width)
    leaf_t = max(2.0, mapper.scale_thickness(_LEAF_THICKNESS_MM))
    hx, hy = pos
    arc_r = w
    is_inward = door.swing == SwingDirection.INWARD
    orientation = getattr(door, "wall_orientation", "vertical")

    # --- Door leaf rect ---
    if orientation == "vertical":
        if is_inward:
            group.add(dwg.rect(
                insert=(hx, hy), size=(w, leaf_t),
                fill=theme.doors.stroke, stroke="none",
            ))
        else:
            group.add(dwg.rect(
                insert=(hx - w, hy), size=(w, leaf_t),
                fill=theme.doors.stroke, stroke="none",
            ))
    else:  # horizontal
        if is_inward:
            group.add(dwg.rect(
                insert=(hx, hy), size=(leaf_t, w),
                fill=theme.doors.stroke, stroke="none",
            ))
        else:
            group.add(dwg.rect(
                insert=(hx, hy - w), size=(leaf_t, w),
                fill=theme.doors.stroke, stroke="none",
            ))

    # --- Swing arc (quarter circle) ---
    if orientation == "vertical":
        if is_inward:
            tip_x, tip_y = hx + arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 1
        else:
            tip_x, tip_y = hx - arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 0
    else:
        if is_inward:
            tip_x, tip_y = hx, hy + arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 0
        else:
            tip_x, tip_y = hx, hy - arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 1

    arc_path = (
        f"M {hx},{hy} "
        f"L {tip_x},{tip_y} "
        f"A {arc_r},{arc_r} 0 0,{sweep} {end_x},{end_y}"
    )

    group.add(dwg.path(
        d=arc_path,
        fill="none",
        stroke=theme.doors.arc_stroke,
        stroke_width=max(1.0, theme.doors.arc_width),
    ))
