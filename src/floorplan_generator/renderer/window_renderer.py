"""Window rendering: double-line glazing symbol with optional mullion."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_MULLION_THRESHOLD_MM = 1200.0  # add mullion for windows wider than this
_GLASS_GAP_PX = 4.0  # gap between two parallel glass lines


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    for room in rooms:
        for window in room.windows:
            _render_single_window(dwg, group, window, mapper, theme)


def _render_single_window(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    window: Window,
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render a window as two parallel lines + optional mullion."""
    pos = mapper.to_svg(window.position)
    length = mapper.scale_length(window.width)
    gap = _GLASS_GAP_PX
    sw = max(1.5, theme.windows.stroke_width)
    color = theme.windows.stroke

    is_horizontal = window.wall_side in ("north", "south")

    if is_horizontal:
        y1 = pos[1] - gap / 2
        y2 = pos[1] + gap / 2
        group.add(dwg.line(
            start=(pos[0], y1), end=(pos[0] + length, y1),
            stroke=color, stroke_width=sw,
        ))
        group.add(dwg.line(
            start=(pos[0], y2), end=(pos[0] + length, y2),
            stroke=color, stroke_width=sw,
        ))
        if window.width > _MULLION_THRESHOLD_MM:
            mid_x = pos[0] + length / 2
            group.add(dwg.line(
                start=(mid_x, y1 - 2), end=(mid_x, y2 + 2),
                stroke=color, stroke_width=sw,
            ))
    else:
        x1 = pos[0] - gap / 2
        x2 = pos[0] + gap / 2
        group.add(dwg.line(
            start=(x1, pos[1]), end=(x1, pos[1] + length),
            stroke=color, stroke_width=sw,
        ))
        group.add(dwg.line(
            start=(x2, pos[1]), end=(x2, pos[1] + length),
            stroke=color, stroke_width=sw,
        ))
        if window.width > _MULLION_THRESHOLD_MM:
            mid_y = pos[1] + length / 2
            group.add(dwg.line(
                start=(x1 - 2, mid_y), end=(x2 + 2, mid_y),
                stroke=color, stroke_width=sw,
            ))
