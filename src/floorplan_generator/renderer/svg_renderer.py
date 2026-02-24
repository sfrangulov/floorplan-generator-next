"""Main SVG renderer: orchestrates all sub-renderers."""
from __future__ import annotations

import svgwrite

from floorplan_generator.core.enums import SwingDirection
from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.door_renderer import render_doors
from floorplan_generator.renderer.furniture_renderer import render_furniture
from floorplan_generator.renderer.riser_renderer import render_risers
from floorplan_generator.renderer.room_renderer import (
    compute_room_group_ids,
    render_rooms,
)
from floorplan_generator.renderer.theme import Theme, get_default_theme
from floorplan_generator.renderer.wall_renderer import render_walls
from floorplan_generator.renderer.window_renderer import render_windows


def _compute_margin_mm(rooms: list, theme: Theme) -> float:
    """Compute mm margin to include outer walls and outward door arcs."""
    wall_t = theme.walls.outer_thickness
    # Find max outward-opening door width (entrance doors open outward)
    max_outward = 0.0
    for room in rooms:
        for door in room.doors:
            if door.swing == SwingDirection.OUTWARD:
                max_outward = max(max_outward, door.width)
    return wall_t + max_outward


def render_svg(
    result: GenerationResult, theme: Theme | None = None,
    *, show_dimensions: bool = False,
) -> str:
    if theme is None:
        theme = get_default_theme()

    rooms = result.apartment.rooms
    cw = theme.canvas.width
    ch = theme.canvas.height
    margin = _compute_margin_mm(rooms, theme)
    mapper = CoordinateMapper(rooms, cw, ch, margin_mm=margin)
    dwg = svgwrite.Drawing(size=(f"{cw}px", f"{ch}px"), viewBox=f"0 0 {cw} {ch}")

    # Layer 1: Background
    dwg.add(dwg.rect(
        insert=(0, 0), size=(cw, ch),
        fill=theme.canvas.background,
        id="background",
    ))

    # Layer 2: Per-room groups (h1, r1, s1, c1, ...) added directly to dwg
    room_ids = compute_room_group_ids(rooms)
    render_rooms(dwg, rooms, room_ids, mapper, theme)

    # Layer 3: Furniture
    furniture_group = dwg.g(id="mebel")
    render_furniture(dwg, furniture_group, rooms, mapper, theme)
    dwg.add(furniture_group)

    # Layer 4: Floor (walls + doors + windows + risers)
    floor_group = dwg.g(id="floor")
    render_walls(dwg, floor_group, rooms, mapper, theme)
    render_doors(dwg, floor_group, rooms, mapper, theme)
    render_windows(dwg, floor_group, rooms, mapper, theme)
    render_risers(dwg, floor_group, result.risers, mapper, theme)
    dwg.add(floor_group)

    # Layer 5: Dimension annotations
    if show_dimensions:
        from .dimension_renderer import render_dimensions
        render_dimensions(dwg, rooms, mapper, theme)

    return dwg.tostring()


def render_svg_to_file(
    result: GenerationResult, path: str, theme: Theme | None = None,
    *, show_dimensions: bool = False,
) -> None:
    svg_content = render_svg(result, theme, show_dimensions=show_dimensions)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)


def render_png(
    result: GenerationResult, theme: Theme | None = None,
    *, show_dimensions: bool = False,
) -> bytes:
    """Render a GenerationResult to PNG bytes via cairosvg."""
    import cairosvg

    if theme is None:
        theme = get_default_theme()

    svg_str = render_svg(result, theme, show_dimensions=show_dimensions)
    return cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        output_width=theme.canvas.width,
        output_height=theme.canvas.height,
    )


def render_png_to_file(
    result: GenerationResult, path: str, theme: Theme | None = None,
    *, show_dimensions: bool = False,
) -> None:
    """Render and save PNG to a file."""
    png_data = render_png(result, theme, show_dimensions=show_dimensions)
    with open(path, "wb") as f:
        f.write(png_data)
