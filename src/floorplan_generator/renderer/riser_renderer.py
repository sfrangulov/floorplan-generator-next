"""Riser (vertical pipe) rendering."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.generator.types import Riser
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme


def render_risers(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    risers: list[Riser],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render riser pipe markers as filled circles."""
    for riser in risers:
        pos = mapper.to_svg(riser.position)
        group.add(dwg.circle(
            center=pos,
            r=theme.riser.radius,
            fill=theme.riser.fill,
            stroke=theme.riser.stroke,
            stroke_width=1.0,
        ))
