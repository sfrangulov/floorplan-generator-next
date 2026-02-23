"""Unit tests for domain models (M01–M14)."""

import pytest

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)


# M01
def test_room_area_calculation(make_room):
    """Room area in m² is computed correctly from boundary polygon."""
    room = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    assert room.area_m2 == pytest.approx(20.0)


# M02
def test_room_width_calculation(make_room):
    """Room width (min side of bounding box) in meters."""
    room = make_room(RoomType.BEDROOM, width_m=3.0, height_m=5.0)
    assert room.width_m == pytest.approx(3.0)


# M03
def test_room_aspect_ratio(make_room):
    """Room aspect ratio = max side / min side."""
    room = make_room(RoomType.BEDROOM, width_m=3.0, height_m=6.0)
    assert room.aspect_ratio == pytest.approx(2.0)


# M04
def test_room_is_wet_zone(make_room):
    """Wet zone determined by room type."""
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    assert bathroom.is_wet_zone is True
    assert bedroom.is_wet_zone is False


# M05
def test_room_requires_window(make_room):
    """Window requirement determined by room type."""
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    assert living.requires_window is True
    assert corridor.requires_window is False


# M06
def test_door_swing_arc(make_door):
    """Door swing arc returns a Rectangle representing the sweep area."""
    door = make_door(
        door_type=DoorType.INTERIOR,
        width=800.0,
        swing=SwingDirection.INWARD,
    )
    arc = door.swing_arc
    # Arc should be a square with side = door width
    assert arc.width == pytest.approx(800.0)
    assert arc.height == pytest.approx(800.0)


# M07
def test_window_area(make_window):
    """Window area in m²."""
    window = make_window(width=1500.0, height=1500.0)
    assert window.area_m2 == pytest.approx(2.25)


# M08
def test_furniture_bounding_box(make_furniture):
    """Bounding box of furniture item accounts for rotation."""
    # No rotation — simple bbox
    item = make_furniture(FurnitureType.SOFA_3, x=100, y=200, width=2100, depth=950, rotation=0)
    bb = item.bounding_box
    assert bb.x == pytest.approx(100.0)
    assert bb.y == pytest.approx(200.0)
    assert bb.width == pytest.approx(2100.0)
    assert bb.height == pytest.approx(950.0)

    # 90-degree rotation — width and depth swap
    item90 = make_furniture(FurnitureType.SOFA_3, x=100, y=200, width=2100, depth=950, rotation=90)
    bb90 = item90.bounding_box
    assert bb90.width == pytest.approx(950.0, abs=1.0)
    assert bb90.height == pytest.approx(2100.0, abs=1.0)


# M09
def test_furniture_clearance_zone(make_furniture):
    """Clearance zone extends in front of furniture."""
    item = make_furniture(FurnitureType.TOILET_BOWL, x=0, y=0, width=650, depth=375, rotation=0)
    cz = item.clearance_zone
    # Clearance zone should be a rectangle in front (positive y direction by default)
    assert cz is not None
    assert cz.width > 0
    assert cz.height > 0


# M10
def test_apartment_total_area(make_room, make_apartment):
    """Total apartment area = sum of all room areas."""
    r1 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)  # 20
    r2 = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)  # 9
    r3 = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)  # 4
    apt = make_apartment(ApartmentClass.COMFORT, [r1, r2, r3], num_rooms=1)
    assert apt.total_area_m2 == pytest.approx(33.0)


# M11
def test_apartment_living_area(make_room, make_apartment):
    """Living area = sum of only living rooms (гостиная, спальня, детская, кабинет)."""
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)  # 20
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)  # 12
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)  # 9 (not counted)
    apt = make_apartment(ApartmentClass.COMFORT, [living, bedroom, kitchen], num_rooms=2)
    assert apt.living_area_m2 == pytest.approx(32.0)


# M12
def test_apartment_adjacency_graph(make_room, make_door, make_apartment):
    """Adjacency graph built from door connections."""
    r1 = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    r2 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    door = make_door(room_from=r1.id, room_to=r2.id)
    r1_with_door = r1.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [r1_with_door, r2], num_rooms=1)
    graph = apt.adjacency_graph
    assert r2.id in graph[r1_with_door.id]
    assert r1_with_door.id in graph[r2.id]


# M13
def test_apartment_room_composition(make_room, make_apartment):
    """Room composition returns count per room type."""
    r1 = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    r2 = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    r3 = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    r4 = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    apt = make_apartment(ApartmentClass.COMFORT, [r1, r2, r3, r4], num_rooms=2)
    comp = apt.room_composition
    assert comp[RoomType.LIVING_ROOM] == 1
    assert comp[RoomType.BEDROOM] == 2
    assert comp[RoomType.KITCHEN] == 1


# M14
def test_room_free_area_ratio(make_room, make_furniture):
    """Free area ratio = 1 - (furniture area / room area)."""
    furniture = make_furniture(
        FurnitureType.BED_DOUBLE,
        x=500, y=500, width=1600, depth=2000, rotation=0,
    )
    room = make_room(
        RoomType.BEDROOM, width_m=4.0, height_m=5.0, furniture=[furniture],
    )
    # Room = 4*5 = 20 m², furniture = 1.6*2.0 = 3.2 m²
    # Free ratio = 1 - 3.2/20 = 0.84
    assert room.free_area_ratio == pytest.approx(0.84)
