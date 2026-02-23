"""Door rendering: opening gap + swing arc."""

from __future__ import annotations

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
