"""Furniture rendering using symbol library."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.models import FurnitureItem, Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.symbols.furniture import get_drawer
from floorplan_generator.renderer.theme import Theme


def render_furniture(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render all furniture items in all rooms."""
    style = {
        "stroke": theme.furniture.stroke,
        "fill": theme.furniture.fill,
        "stroke_width": theme.furniture.stroke_width,
    }
    for room in rooms:
        for item in room.furniture:
            _render_item(dwg, group, item, mapper, style)


def _render_item(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    item: FurnitureItem,
    mapper: CoordinateMapper,
    style: dict,
) -> None:
    """Render a single furniture item at its position with rotation."""
    pos = mapper.to_svg(item.position)
    w = mapper.scale_length(item.width)
    d = mapper.scale_length(item.depth)

    # Create group with transform
    transform = f"translate({pos[0]},{pos[1]})"
    if item.rotation != 0:
        transform += f" rotate({item.rotation},{w / 2},{d / 2})"

    item_group = dwg.g(transform=transform)

    drawer = get_drawer(item.furniture_type)
    if getattr(drawer, "is_fallback", False):
        drawer(item_group, w, d, style, label=item.furniture_type.value)
    else:
        drawer(item_group, w, d, style)

    group.add(item_group)
