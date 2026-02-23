"""Stoyak (vertical pipe) rendering."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.generator.types import Stoyak
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_stoyaks(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    stoyaks: list[Stoyak],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render stoyak pipe markers as filled circles."""
    for stoyak in stoyaks:
        pos = mapper.to_svg(stoyak.position)
        group.add(dwg.circle(
            center=pos,
            r=theme.stoyak.radius,
            fill=theme.stoyak.fill,
            stroke=theme.stoyak.stroke,
            stroke_width=1.0,
        ))
