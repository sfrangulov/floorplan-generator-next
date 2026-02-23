"""Spatial helper functions for rule validators.

These operate on Room boundary polygon segments (not explicit Wall models).
"""

from __future__ import annotations

from floorplan_generator.core.enums import FurnitureType
from floorplan_generator.core.geometry import (
    Point,
    Rectangle,
    Segment,
    min_distance_point_to_segment,
    min_distance_rect_to_segment,
)
from floorplan_generator.core.models import FurnitureItem, Room


def wall_segments(room: Room) -> list[Segment]:
    """Return wall segments from a room's boundary polygon."""
    pts = room.boundary.points
    n = len(pts)
    return [
        Segment(start=pts[i], end=pts[(i + 1) % n])
        for i in range(n)
    ]


def nearest_wall_distance(item_bbox: Rectangle, room: Room) -> float:
    """Minimum distance from a furniture bounding box to any wall segment."""
    segs = wall_segments(room)
    if not segs:
        return float("inf")
    return min(min_distance_rect_to_segment(item_bbox, s) for s in segs)


def distance_to_window(item_bbox: Rectangle, window_pos: Point, room: Room) -> float:
    """Distance from furniture bbox center to window position."""
    center = item_bbox.center
    return center.distance_to(window_pos)


def clearance_in_front(item: FurnitureItem, room: Room) -> float:
    """Distance from front edge of furniture to far wall or furniture ahead.

    Measures in the +y direction from the front edge of the item
    to the opposite wall (room bounding box top) or to furniture ahead.
    """
    bb = item.bounding_box
    front_y = bb.y + bb.height
    # Distance to the far wall (top of room bounding box)
    room_bb = room.boundary.bounding_box
    min_d = (room_bb.y + room_bb.height) - front_y
    # Distance to other furniture in front
    for other in room.furniture:
        if other.id == item.id:
            continue
        other_bb = other.bounding_box
        # Only count items in front direction (higher y)
        if other_bb.y >= front_y - 1:
            d = other_bb.y - front_y
            if d >= 0:
                min_d = min(min_d, d)
    return min_d


def items_of_type(room: Room, *types: FurnitureType) -> list[FurnitureItem]:
    """Return all furniture items of given type(s) in a room."""
    return [f for f in room.furniture if f.furniture_type in types]


def kitchen_triangle_perimeter(room: Room) -> float | None:
    """Calculate the kitchen work triangle perimeter (sink-stove-fridge).

    Returns None if any of the three items is missing.
    """
    sinks = items_of_type(room, FurnitureType.KITCHEN_SINK)
    stoves = items_of_type(room, FurnitureType.STOVE, FurnitureType.HOB)
    fridges = items_of_type(
        room, FurnitureType.FRIDGE, FurnitureType.FRIDGE_SIDE_BY_SIDE,
    )

    if not sinks or not stoves or not fridges:
        return None

    sink_c = sinks[0].bounding_box.center
    stove_c = stoves[0].bounding_box.center
    fridge_c = fridges[0].bounding_box.center

    return (
        sink_c.distance_to(stove_c)
        + stove_c.distance_to(fridge_c)
        + fridge_c.distance_to(sink_c)
    )


def center_x_distance_to_nearest_wall(item: FurnitureItem, room: Room) -> float:
    """Distance from item's center X axis to the nearest side wall segment."""
    bb = item.bounding_box
    center = Point(x=bb.x + bb.width / 2, y=bb.y + bb.height / 2)
    segs = wall_segments(room)
    if not segs:
        return float("inf")
    return min(min_distance_point_to_segment(center, s) for s in segs)


def distance_between_items(a: FurnitureItem, b: FurnitureItem) -> float:
    """Minimum distance between bounding boxes of two furniture items."""
    return a.bounding_box.distance_to(b.bounding_box)
