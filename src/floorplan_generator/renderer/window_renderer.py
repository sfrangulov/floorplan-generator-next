"""Window rendering: simple line segments on exterior walls."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all windows as simple line segments."""
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
    """Render a single window as a line segment along its wall.

    For north/south walls the line is horizontal;
    for east/west walls the line is vertical.
    Uses a thicker stroke and round linecaps for clean appearance.
    """
    pos = mapper.to_svg(window.position)
    length = mapper.scale_length(window.width)

    if window.wall_side in ("north", "south"):
        # Horizontal line
        start = (pos[0], pos[1])
        end = (pos[0] + length, pos[1])
    else:
        # Vertical line (east/west)
        start = (pos[0], pos[1])
        end = (pos[0], pos[1] + length)

    group.add(dwg.line(
        start=start,
        end=end,
        stroke=theme.windows.stroke,
        stroke_width=theme.windows.stroke_width * 3,
        stroke_linecap="round",
    ))
