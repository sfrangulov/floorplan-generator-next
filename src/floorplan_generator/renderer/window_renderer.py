"""Window rendering: reference-style opening rect + glass line + mullions."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import Room, Window
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_MULLION_SPACING_MM = 600.0
_GLASS_POSITION_RATIO = 0.75


def render_windows(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    wall_thickness = theme.walls.outer_thickness
    for room in rooms:
        for window in room.windows:
            _render_single_window(dwg, group, window, mapper, theme, wall_thickness)


def _render_single_window(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    window: Window,
    mapper: CoordinateMapper,
    theme: Theme,
    wall_thickness: float,
) -> None:
    """Render window as: opening rect + glass line + mullion rects."""
    pos = mapper.to_svg(window.position)
    w_len = mapper.scale_length(window.width)
    w_thick = mapper.scale_length(wall_thickness)
    sw = max(1.0, theme.windows.stroke_width)
    color = theme.windows.stroke

    glass_height = max(4.0, w_thick * 0.2)
    glass_offset = w_thick * _GLASS_POSITION_RATIO

    mullion_w = max(3.0, w_thick * 0.15)
    mullion_h = glass_height

    is_horizontal = window.wall_side in ("north", "south")

    if is_horizontal:
        ox, oy = pos[0], pos[1] - w_thick / 2
        group.add(dwg.rect(
            insert=(ox, oy), size=(w_len, w_thick),
            fill="none", stroke=color, stroke_width=sw,
        ))

        gy = oy + glass_offset - glass_height / 2
        group.add(dwg.rect(
            insert=(ox, gy), size=(w_len, glass_height),
            fill="none", stroke=color, stroke_width=sw,
        ))

        mull_pos = _compute_mullion_positions(
            window.width, _MULLION_SPACING_MM,
        )
        for mp in mull_pos:
            mx = ox + mapper.scale_length(mp) - mullion_w / 2
            group.add(dwg.rect(
                insert=(mx, gy), size=(mullion_w, mullion_h),
                fill="none", stroke=color, stroke_width=sw,
            ))
    else:
        ox, oy = pos[0] - w_thick / 2, pos[1]
        group.add(dwg.rect(
            insert=(ox, oy), size=(w_thick, w_len),
            fill="none", stroke=color, stroke_width=sw,
        ))

        gx = ox + glass_offset - glass_height / 2
        group.add(dwg.rect(
            insert=(gx, oy), size=(glass_height, w_len),
            fill="none", stroke=color, stroke_width=sw,
        ))

        mull_pos = _compute_mullion_positions(
            window.width, _MULLION_SPACING_MM,
        )
        for mp in mull_pos:
            my = oy + mapper.scale_length(mp) - mullion_w / 2
            group.add(dwg.rect(
                insert=(gx, my), size=(mullion_h, mullion_w),
                fill="none", stroke=color, stroke_width=sw,
            ))


def _compute_mullion_positions(
    window_width_mm: float, spacing_mm: float,
) -> list[float]:
    """Compute mullion positions along window width.

    Always includes edge mullions (at 0 and window_width).
    For wide windows, adds intermediate mullions every ~spacing_mm.
    """
    positions = [0.0, window_width_mm]

    if window_width_mm > spacing_mm * 1.5:
        n_sections = max(2, round(window_width_mm / spacing_mm))
        step = window_width_mm / n_sections
        for i in range(1, n_sections):
            positions.append(step * i)

    return sorted(set(positions))
