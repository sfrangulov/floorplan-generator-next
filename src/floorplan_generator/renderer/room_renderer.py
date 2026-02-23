"""Room boundary and label rendering."""
from __future__ import annotations

from collections import defaultdict

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_ROOM_NAMES: dict[RoomType, str] = {
    RoomType.LIVING_ROOM: "Гостиная",
    RoomType.BEDROOM: "Спальня",
    RoomType.CHILDREN: "Детская",
    RoomType.CABINET: "Кабинет",
    RoomType.KITCHEN: "Кухня",
    RoomType.KITCHEN_DINING: "Кухня-столовая",
    RoomType.KITCHEN_NICHE: "Кухня-ниша",
    RoomType.HALLWAY: "Прихожая",
    RoomType.CORRIDOR: "Коридор",
    RoomType.HALL: "Холл",
    RoomType.BATHROOM: "Ванная",
    RoomType.TOILET: "Туалет",
    RoomType.COMBINED_BATHROOM: "Санузел",
    RoomType.STORAGE: "Кладовая",
    RoomType.WARDROBE: "Гардероб",
    RoomType.LAUNDRY: "Постирочная",
    RoomType.BALCONY: "Балкон",
}

_ROOM_PREFIX: dict[RoomType, str] = {
    # h = hallway, corridor, hall
    RoomType.HALLWAY: "h",
    RoomType.CORRIDOR: "h",
    RoomType.HALL: "h",
    # r = living_room, bedroom, children, cabinet
    RoomType.LIVING_ROOM: "r",
    RoomType.BEDROOM: "r",
    RoomType.CHILDREN: "r",
    RoomType.CABINET: "r",
    # s = bathroom, toilet, combined_bathroom, laundry
    RoomType.BATHROOM: "s",
    RoomType.TOILET: "s",
    RoomType.COMBINED_BATHROOM: "s",
    RoomType.LAUNDRY: "s",
    # c = kitchen, kitchen_dining, kitchen_niche, storage, wardrobe, balcony
    RoomType.KITCHEN: "c",
    RoomType.KITCHEN_DINING: "c",
    RoomType.KITCHEN_NICHE: "c",
    RoomType.STORAGE: "c",
    RoomType.WARDROBE: "c",
    RoomType.BALCONY: "c",
}


def compute_room_group_ids(rooms: list[Room]) -> dict[str, str]:
    """Compute type-prefixed group IDs for each room.

    Returns a mapping from room.id to a short ID like "h1", "r1", "s1", "c1".
    Counters are per-prefix and increment in room list order.
    """
    counters: dict[str, int] = defaultdict(int)
    result: dict[str, str] = {}
    for room in rooms:
        prefix = _ROOM_PREFIX.get(room.room_type, "c")
        counters[prefix] += 1
        result[room.id] = f"{prefix}{counters[prefix]}"
    return result


def render_rooms(
    dwg: svgwrite.drawing.Drawing,
    rooms: list[Room],
    room_ids: dict[str, str],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render room fill polygons and text labels, each in its own <g> group.

    Each room gets a <g id="h1">, <g id="r1">, etc. group added directly to dwg.
    """
    for room in rooms:
        group_id = room_ids.get(room.id, room.id)
        group = dwg.g(id=group_id)

        points = [mapper.to_svg(pt) for pt in room.boundary.points]
        fill = theme.rooms.fills.get(room.room_type.value, theme.rooms.default_fill)
        group.add(dwg.polygon(
            points=points,
            fill=fill,
            stroke=theme.rooms.default_stroke,
            stroke_width=theme.rooms.stroke_width,
        ))

        centroid = room.boundary.centroid
        cx, cy = mapper.to_svg(centroid)
        name = _ROOM_NAMES.get(room.room_type, room.room_type.value)
        area = f"{room.area_m2:.1f} м²"
        group.add(dwg.text(
            name,
            insert=(cx, cy - 6),
            text_anchor="middle",
            font_family=theme.text.font_family,
            font_size=theme.text.font_size,
            fill=theme.text.fill,
        ))
        group.add(dwg.text(
            area,
            insert=(cx, cy + 10),
            text_anchor="middle",
            font_family=theme.text.font_family,
            font_size=theme.text.area_font_size,
            fill=theme.text.fill,
        ))

        dwg.add(group)
