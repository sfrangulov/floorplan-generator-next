"""Main SVG renderer: orchestrates all sub-renderers."""

from __future__ import annotations

import svgwrite

from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.door_renderer import render_doors
from floorplan_generator.renderer.furniture_renderer import render_furniture
from floorplan_generator.renderer.room_renderer import render_rooms
from floorplan_generator.renderer.stoyak_renderer import render_stoyaks
from floorplan_generator.renderer.theme import Theme, get_default_theme
from floorplan_generator.renderer.wall_renderer import render_walls
from floorplan_generator.renderer.window_renderer import render_windows


def render_svg(
    result: GenerationResult,
    theme: Theme | None = None,
) -> str:
    """Render a GenerationResult to an SVG string.

    Args:
        result: Complete generation result with apartment and stoyaks.
        theme: Rendering theme. Uses blueprint if None.

    Returns:
        SVG content as a string.
    """
    if theme is None:
        theme = get_default_theme()

    rooms = result.apartment.rooms
    cw = theme.canvas.width
    ch = theme.canvas.height

    mapper = CoordinateMapper(rooms, cw, ch)

    dwg = svgwrite.Drawing(
        size=(f"{cw}px", f"{ch}px"),
        viewBox=f"0 0 {cw} {ch}",
    )

    # Layer 1: Background
    dwg.add(dwg.rect(
        insert=(0, 0), size=(cw, ch),
        fill=theme.canvas.background,
    ))

    # Layer 2: Room fills + labels
    rooms_group = dwg.g(id="rooms")
    render_rooms(dwg, rooms_group, rooms, mapper, theme)
    dwg.add(rooms_group)

    # Layer 3: Furniture (drawn before walls, matching reference SVGs)
    furniture_group = dwg.g(id="mebel")
    render_furniture(dwg, furniture_group, rooms, mapper, theme)
    dwg.add(furniture_group)

    # Layer 4: Walls (on top of furniture)
    walls_group = dwg.g(id="floor")
    render_walls(dwg, walls_group, rooms, mapper, theme)
    dwg.add(walls_group)

    # Layer 5: Doors
    doors_group = dwg.g(id="doors")
    render_doors(dwg, doors_group, rooms, mapper, theme)
    dwg.add(doors_group)

    # Layer 6: Windows
    windows_group = dwg.g(id="windows")
    render_windows(dwg, windows_group, rooms, mapper, theme)
    dwg.add(windows_group)

    # Layer 7: Stoyaks
    stoyaks_group = dwg.g(id="stoyaks")
    render_stoyaks(dwg, stoyaks_group, result.stoyaks, mapper, theme)
    dwg.add(stoyaks_group)

    return dwg.tostring()


def render_svg_to_file(
    result: GenerationResult,
    path: str,
    theme: Theme | None = None,
) -> None:
    """Render and save SVG to a file."""
    svg_content = render_svg(result, theme)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_content)
