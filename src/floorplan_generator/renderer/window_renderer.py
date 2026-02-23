"""Window rendering: rect + pane division lines."""

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
    """Render all windows with rect and pane lines."""
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
    """Render a single window: filled rect + 3 pane lines."""
    pos = mapper.to_svg(window.position)
    w = mapper.scale_length(window.width)
    wall_depth = 6.0  # visual wall thickness in SVG units

    # Window rect
    group.add(dwg.rect(
        insert=(pos[0], pos[1] - wall_depth / 2),
        size=(w, wall_depth),
        fill=theme.windows.fill,
        stroke=theme.windows.stroke,
        stroke_width=theme.windows.stroke_width,
    ))

    # Pane division lines (3 lines inside)
    for frac in [0.25, 0.5, 0.75]:
        lx = pos[0] + w * frac
        group.add(dwg.line(
            start=(lx, pos[1] - wall_depth / 2),
            end=(lx, pos[1] + wall_depth / 2),
            stroke=theme.windows.cross_stroke,
            stroke_width=theme.windows.stroke_width * 0.5,
        ))
