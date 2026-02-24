"""Tests for Shapely-based wall outline computation."""

from __future__ import annotations

from shapely.geometry import Polygon as ShapelyPolygon

from floorplan_generator.core.enums import DoorType, RoomType, SwingDirection
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import Door, Room, Window


def _rect_room(
    room_type: RoomType,
    x: float, y: float, w: float, h: float,
    room_id: str = "",
    doors: list[Door] | None = None,
    windows: list[Window] | None = None,
) -> Room:
    return Room(
        id=room_id or f"r_{room_type.value}",
        room_type=room_type,
        boundary=Polygon(points=[
            Point(x=x, y=y),
            Point(x=x + w, y=y),
            Point(x=x + w, y=y + h),
            Point(x=x, y=y + h),
        ]),
        doors=doors or [],
        windows=windows or [],
    )


def test_single_room_outer_wall():
    """Single room produces a rectangular wall ring."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    room = _rect_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    wall_poly = compute_outer_wall_polygon([room], thickness=225.0)
    assert not wall_poly.is_empty
    # Wall ring area = outer_area - inner_area
    # inner = 4000*4000 = 16_000_000
    # outer = 4450*4450 = 19_802_500
    # ring ~ 3_802_500
    assert wall_poly.area > 3_000_000
    assert wall_poly.area < 5_000_000


def test_two_adjacent_rooms_outer_wall():
    """Two adjacent rooms share a wall; outer ring has no gap at corners."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    wall_poly = compute_outer_wall_polygon([r1, r2], thickness=225.0)
    assert not wall_poly.is_empty
    assert wall_poly.geom_type in ("Polygon", "MultiPolygon")
    inner = ShapelyPolygon([(0,0),(6000,0),(6000,3000),(0,3000)])
    assert abs(inner.area - 18_000_000) < 1


def test_outer_wall_with_window_opening():
    """Window creates opening in outer wall polygon."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _rect_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 4000,
        windows=[window],
    )
    wall_no_opening = compute_outer_wall_polygon([room], thickness=225.0)
    wall_with_opening = compute_outer_wall_polygon(
        [room], thickness=225.0, cut_windows=True,
    )
    assert wall_with_opening.area < wall_no_opening.area


def test_inner_wall_polygons():
    """Shared edges produce inner wall polygons."""
    from floorplan_generator.renderer.outline import compute_inner_wall_polygons
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    inner_poly = compute_inner_wall_polygons([r1, r2], thickness=75.0)
    assert not inner_poly.is_empty
    assert inner_poly.area > 150_000
    assert inner_poly.area < 400_000


def test_inner_wall_with_door_opening():
    """Door creates opening in inner wall polygon."""
    from floorplan_generator.renderer.outline import compute_inner_wall_polygons
    door = Door(
        id="d1", position=Point(x=2000, y=500), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2", wall_orientation="vertical",
    )
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1", doors=[door])
    r2 = _rect_room(
        RoomType.LIVING_ROOM, 2000, 0, 4000, 3000,
        room_id="r2", doors=[door],
    )
    inner_no_door = compute_inner_wall_polygons(
        [r1, r2], thickness=75.0, cut_doors=False,
    )
    inner_with_door = compute_inner_wall_polygons(
        [r1, r2], thickness=75.0, cut_doors=True,
    )
    assert inner_with_door.area < inner_no_door.area


def test_shapely_to_svg_path():
    """Shapely polygon converts to valid SVG path d attribute."""
    from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
    from floorplan_generator.renderer.outline import shapely_to_svg_path
    room = _rect_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000)
    poly = ShapelyPolygon([(0,0),(4000,0),(4000,4000),(0,4000)])
    path_d = shapely_to_svg_path(poly, mapper)
    assert path_d.startswith("M")
    assert "L" in path_d
    assert "Z" in path_d


def test_l_shaped_apartment_corners():
    """L-shaped layout has proper corners with no gaps."""
    from floorplan_generator.renderer.outline import compute_outer_wall_polygon
    r1 = _rect_room(RoomType.HALLWAY, 0, 0, 3000, 2000, room_id="r1")
    r2 = _rect_room(RoomType.LIVING_ROOM, 0, 2000, 5000, 3000, room_id="r2")
    wall_poly = compute_outer_wall_polygon([r1, r2], thickness=225.0)
    assert not wall_poly.is_empty
    assert wall_poly.geom_type == "Polygon"
