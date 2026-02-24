"""Segmentation mask renderer for floorplan ML datasets.

Produces a flat-color SVG/PNG where each pixel encodes the semantic class
of the underlying element (room type, wall, door, window, furniture type).
"""

from __future__ import annotations

import svgwrite

from floorplan_generator.core.enums import FurnitureType, RoomType
from floorplan_generator.core.models import Room
from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.outline import (
    compute_inner_wall_polygons,
    compute_outer_wall_polygon,
    shapely_to_svg_path,
)
from floorplan_generator.renderer.svg_renderer import _compute_margin_mm
from floorplan_generator.renderer.theme import Theme, get_default_theme

# ---------------------------------------------------------------------------
# Semantic class palette
# ---------------------------------------------------------------------------
# class_id -> (label, hex_color)
# 0 = background, 1-17 = room types, 18-19 = walls, 20 = door, 21 = window,
# 22+ = furniture types

_ROOM_COLORS: dict[RoomType, str] = {
    RoomType.LIVING_ROOM: "#78B4F0",
    RoomType.BEDROOM: "#9696DC",
    RoomType.CHILDREN: "#C896DC",
    RoomType.CABINET: "#B4AADC",
    RoomType.KITCHEN: "#F0C878",
    RoomType.KITCHEN_DINING: "#F0D28C",
    RoomType.KITCHEN_NICHE: "#F0DCA0",
    RoomType.HALLWAY: "#B4BEC8",
    RoomType.CORRIDOR: "#AAB4BE",
    RoomType.HALL: "#A0AAB4",
    RoomType.BATHROOM: "#78D2DC",
    RoomType.TOILET: "#82C8C8",
    RoomType.COMBINED_BATHROOM: "#8CD2D2",
    RoomType.STORAGE: "#C8B4A0",
    RoomType.WARDROBE: "#BEAA96",
    RoomType.LAUNDRY: "#96C8D2",
    RoomType.BALCONY: "#A0DCAA",
}

_FURNITURE_COLORS: dict[FurnitureType, str] = {
    # Plumbing
    FurnitureType.BATHTUB: "#1E90FF",
    FurnitureType.SHOWER: "#1C86EE",
    FurnitureType.SINK: "#1874CD",
    FurnitureType.DOUBLE_SINK: "#1662B0",
    FurnitureType.TOILET_BOWL: "#104E8B",
    FurnitureType.BIDET: "#0E4682",
    FurnitureType.WASHING_MACHINE: "#6495ED",
    FurnitureType.DRYER: "#5B8BD6",
    FurnitureType.WASHER_DRYER: "#5A8FD6",
    # Kitchen
    FurnitureType.STOVE: "#FF8C00",
    FurnitureType.HOB: "#EE8200",
    FurnitureType.OVEN: "#CD7000",
    FurnitureType.FRIDGE: "#FFA500",
    FurnitureType.FRIDGE_SIDE_BY_SIDE: "#EE9A00",
    FurnitureType.DISHWASHER: "#CD8500",
    FurnitureType.KITCHEN_SINK: "#FFB732",
    FurnitureType.HOOD: "#E6A020",
    FurnitureType.MICROWAVE: "#CC8800",
    # Living room
    FurnitureType.SOFA_2: "#32CD32",
    FurnitureType.SOFA_3: "#2DB82D",
    FurnitureType.SOFA_4: "#28A428",
    FurnitureType.SOFA_CORNER: "#228B22",
    FurnitureType.ARMCHAIR: "#3CB371",
    FurnitureType.COFFEE_TABLE: "#66CDAA",
    FurnitureType.TV_STAND: "#20B2AA",
    FurnitureType.SHELVING: "#5F9EA0",
    # Bedroom
    FurnitureType.BED_SINGLE: "#DC143C",
    FurnitureType.BED_DOUBLE: "#CD1236",
    FurnitureType.BED_KING: "#B22222",
    FurnitureType.NIGHTSTAND: "#E06060",
    FurnitureType.DRESSER: "#C45050",
    FurnitureType.WARDROBE_SLIDING: "#A52A2A",
    FurnitureType.WARDROBE_SWING: "#8B2323",
    FurnitureType.VANITY: "#D46A6A",
    # Children
    FurnitureType.CHILD_BED: "#FF69B4",
    FurnitureType.CHILD_DESK: "#EE6AA7",
    FurnitureType.CHILD_WARDROBE: "#CD6090",
    # Hallway
    FurnitureType.HALLWAY_WARDROBE: "#8B6914",
    FurnitureType.SHOE_RACK: "#A0822B",
    FurnitureType.BENCH: "#B8993C",
    FurnitureType.COAT_RACK: "#C8A94E",
    # General
    FurnitureType.DINING_TABLE: "#DAA520",
    FurnitureType.DINING_CHAIR: "#CD9B1D",
    FurnitureType.DESK: "#B8860B",
    FurnitureType.BOOKSHELF: "#8B7500",
}

WALL_COLOR = "#323232"
DOOR_COLOR = "#DC6464"
WINDOW_COLOR = "#6496DC"
BACKGROUND_COLOR = "#000000"

# Build complete class_id -> (label, color) map for external tools
SEGMENTATION_PALETTE: dict[int, tuple[str, str]] = {0: ("background", BACKGROUND_COLOR)}
_id = 1
for _rt in RoomType:
    SEGMENTATION_PALETTE[_id] = (_rt.value, _ROOM_COLORS.get(_rt, "#808080"))
    _id += 1
SEGMENTATION_PALETTE[_id] = ("outer_wall", WALL_COLOR)
_id += 1
SEGMENTATION_PALETTE[_id] = ("inner_wall", WALL_COLOR)
_id += 1
SEGMENTATION_PALETTE[_id] = ("door", DOOR_COLOR)
_id += 1
SEGMENTATION_PALETTE[_id] = ("window", WINDOW_COLOR)
_id += 1
for _ft in FurnitureType:
    SEGMENTATION_PALETTE[_id] = (_ft.value, _FURNITURE_COLORS.get(_ft, "#808080"))
    _id += 1


# ---------------------------------------------------------------------------
# Mask SVG rendering
# ---------------------------------------------------------------------------


def _render_room_masks(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
) -> None:
    """Render room polygons as flat fills."""
    for room in rooms:
        color = _ROOM_COLORS.get(room.room_type, "#808080")
        points = [mapper.to_svg(pt) for pt in room.boundary.points]
        dwg.add(dwg.polygon(points=points, fill=color, stroke="none"))


def _render_wall_masks(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render wall polygons (outer + inner) as flat fills."""
    outer_poly = compute_outer_wall_polygon(
        rooms, thickness=theme.walls.outer_thickness,
        cut_windows=True, cut_doors=True,
    )
    if not outer_poly.is_empty:
        path_d = shapely_to_svg_path(outer_poly, mapper)
        if path_d:
            dwg.add(dwg.path(d=path_d, fill=WALL_COLOR, stroke="none",
                             fill_rule="evenodd"))

    inner_poly = compute_inner_wall_polygons(
        rooms, thickness=theme.walls.inner_thickness, cut_doors=True,
    )
    if not inner_poly.is_empty:
        path_d = shapely_to_svg_path(inner_poly, mapper)
        if path_d:
            dwg.add(dwg.path(d=path_d, fill=WALL_COLOR, stroke="none",
                             fill_rule="evenodd"))


def _render_furniture_masks(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
) -> None:
    """Render furniture as flat-filled axis-aligned bounding boxes."""
    for room in rooms:
        for item in room.furniture:
            color = _FURNITURE_COLORS.get(item.furniture_type, "#808080")
            bb = item.bounding_box
            x, y = mapper.to_svg(bb.center)
            w = mapper.scale_length(bb.width)
            h = mapper.scale_length(bb.height)
            dwg.add(dwg.rect(
                insert=(x - w / 2, y - h / 2), size=(w, h),
                fill=color, stroke="none",
            ))


def _render_door_masks(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render doors as flat-filled rectangles covering the door opening."""
    seen: set[str] = set()
    wall_t = theme.walls.outer_thickness
    for room in rooms:
        for door in room.doors:
            if door.id in seen:
                continue
            seen.add(door.id)

            pos = mapper.to_svg(door.position)
            w = mapper.scale_length(door.width)
            t = mapper.scale_length(wall_t)
            orientation = getattr(door, "wall_orientation", "vertical")

            if orientation == "vertical":
                dwg.add(dwg.rect(
                    insert=(pos[0], pos[1] - t / 2), size=(w, t),
                    fill=DOOR_COLOR, stroke="none",
                ))
            else:
                dwg.add(dwg.rect(
                    insert=(pos[0] - t / 2, pos[1]), size=(t, w),
                    fill=DOOR_COLOR, stroke="none",
                ))


def _render_window_masks(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render windows as flat-filled rectangles in the wall opening."""
    wall_t = theme.walls.outer_thickness
    for room in rooms:
        for window in room.windows:
            pos = mapper.to_svg(window.position)
            w_len = mapper.scale_length(window.width)
            w_thick = mapper.scale_length(wall_t)
            is_horiz = window.wall_side in ("north", "south")

            if is_horiz:
                if window.wall_side == "north":
                    ox, oy = pos[0], pos[1] - w_thick
                else:
                    ox, oy = pos[0], pos[1]
                dwg.add(dwg.rect(
                    insert=(ox, oy), size=(w_len, w_thick),
                    fill=WINDOW_COLOR, stroke="none",
                ))
            else:
                if window.wall_side == "west":
                    ox, oy = pos[0] - w_thick, pos[1]
                else:
                    ox, oy = pos[0], pos[1]
                dwg.add(dwg.rect(
                    insert=(ox, oy), size=(w_thick, w_len),
                    fill=WINDOW_COLOR, stroke="none",
                ))


def render_mask_svg(
    result: GenerationResult,
    theme: Theme | None = None,
) -> str:
    """Render a segmentation mask as a flat-color SVG string.

    Layer order (back to front):
    background -> rooms -> furniture -> walls -> doors -> windows
    """
    if theme is None:
        theme = get_default_theme()

    rooms = result.apartment.rooms
    cw = theme.canvas.width
    ch = theme.canvas.height
    margin = _compute_margin_mm(rooms, theme)
    mapper = CoordinateMapper(rooms, cw, ch, margin_mm=margin)

    dwg = svgwrite.Drawing(
        size=(f"{cw}px", f"{ch}px"),
        viewBox=f"0 0 {cw} {ch}",
    )
    dwg.add(dwg.rect(
        insert=(0, 0), size=(cw, ch),
        fill=BACKGROUND_COLOR, stroke="none",
    ))

    _render_room_masks(dwg, rooms, mapper)
    _render_furniture_masks(dwg, rooms, mapper)
    _render_wall_masks(dwg, rooms, mapper, theme)
    _render_door_masks(dwg, rooms, mapper, theme)
    _render_window_masks(dwg, rooms, mapper, theme)

    return dwg.tostring()


def render_mask_png(
    result: GenerationResult,
    theme: Theme | None = None,
) -> bytes:
    """Render segmentation mask as PNG bytes."""
    import cairosvg

    if theme is None:
        theme = get_default_theme()

    svg_str = render_mask_svg(result, theme)
    return cairosvg.svg2png(
        bytestring=svg_str.encode("utf-8"),
        output_width=theme.canvas.width,
        output_height=theme.canvas.height,
    )


def render_mask_to_file(
    result: GenerationResult,
    path: str,
    theme: Theme | None = None,
) -> None:
    """Render segmentation mask and save as PNG file."""
    png_data = render_mask_png(result, theme)
    with open(path, "wb") as f:
        f.write(png_data)
