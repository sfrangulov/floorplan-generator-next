"""Door rendering: opening gap + swing arc."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import SwingDirection
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
    """Render a single door: white gap rect + quarter-circle arc.

    The gap rectangle and swing arc are oriented based on the door's
    wall_orientation ("vertical" or "horizontal") and swing direction
    (INWARD or OUTWARD).
    """
    pos = mapper.to_svg(door.position)
    w = mapper.scale_length(door.width)
    hx, hy = pos
    arc_r = w
    gap_thickness = 4  # px

    orientation = getattr(door, "wall_orientation", "vertical")

    # --- Gap rectangle (covers wall line) ---
    if orientation == "vertical":
        # Vertical wall: gap is thin horizontally (4px), tall (w px)
        gap_w = gap_thickness
        gap_h = max(w, gap_thickness)
        insert_x = hx - gap_thickness / 2
        insert_y = hy
    else:
        # Horizontal wall: gap is wide (w px), thin vertically (4px)
        gap_w = max(w, gap_thickness)
        gap_h = gap_thickness
        insert_x = hx
        insert_y = hy - gap_thickness / 2

    group.add(dwg.rect(
        insert=(insert_x, insert_y),
        size=(gap_w, gap_h),
        fill=theme.doors.gap_fill,
        stroke="none",
    ))

    # --- Swing arc (quarter circle) ---
    # The arc is drawn from the hinge point: a line to the door-leaf tip,
    # then a quarter-circle arc to the fully-open position.
    #
    # Vertical wall + INWARD:  leaf tip at (hx + r, hy), arc to (hx, hy + r)
    # Vertical wall + OUTWARD: leaf tip at (hx - r, hy), arc to (hx, hy + r)
    # Horizontal wall + INWARD:  leaf tip at (hx, hy + r), arc to (hx + r, hy)
    # Horizontal wall + OUTWARD: leaf tip at (hx, hy - r), arc to (hx + r, hy)

    is_inward = door.swing == SwingDirection.INWARD

    if orientation == "vertical":
        if is_inward:
            # Leaf extends right from hinge, arc sweeps down
            tip_x, tip_y = hx + arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 1  # clockwise
        else:
            # Leaf extends left from hinge, arc sweeps down
            tip_x, tip_y = hx - arc_r, hy
            end_x, end_y = hx, hy + arc_r
            sweep = 0  # counter-clockwise
    else:  # horizontal
        if is_inward:
            # Leaf extends down from hinge, arc sweeps right
            tip_x, tip_y = hx, hy + arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 0  # counter-clockwise
        else:
            # Leaf extends up from hinge, arc sweeps right
            tip_x, tip_y = hx, hy - arc_r
            end_x, end_y = hx + arc_r, hy
            sweep = 1  # clockwise

    arc_path = (
        f"M {hx},{hy} "
        f"L {tip_x},{tip_y} "
        f"A {arc_r},{arc_r} 0 0,{sweep} {end_x},{end_y}"
    )

    group.add(dwg.path(
        d=arc_path,
        fill="none",
        stroke=theme.doors.arc_stroke,
        stroke_width=theme.doors.arc_width,
    ))
