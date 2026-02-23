"""Room boundary and label rendering."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.enums import RoomType
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

# Human-readable room names (Russian)
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


def render_rooms(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render room fill polygons and text labels."""
    for room in rooms:
        points = [mapper.to_svg(pt) for pt in room.boundary.points]
        fill = theme.rooms.fills.get(room.room_type.value, theme.rooms.default_fill)

        # Room fill polygon
        group.add(dwg.polygon(
            points=points,
            fill=fill,
            stroke=theme.rooms.default_stroke,
            stroke_width=theme.rooms.stroke_width,
        ))

        # Label at centroid
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
