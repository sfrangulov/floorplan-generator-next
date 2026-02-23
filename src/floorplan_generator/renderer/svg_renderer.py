"""Main SVG renderer: orchestrates all sub-renderers."""
from __future__ import annotations

import svgwrite

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


def render_svg(result: GenerationResult, theme: Theme | None = None) -> str:
    if theme is None:
        theme = get_default_theme()

    rooms = result.apartment.rooms
    cw = theme.canvas.width
    ch = theme.canvas.height
    mapper = CoordinateMapper(rooms, cw, ch)
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

    return dwg.tostring()


def render_svg_to_file(
    result: GenerationResult, path: str, theme: Theme | None = None,
) -> None:
    svg_content = render_svg(result, theme)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
