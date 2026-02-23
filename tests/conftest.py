"""Shared test fixtures."""

from __future__ import annotations

import uuid

import pytest

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import (
    Apartment,
    Door,
    FurnitureItem,
    Room,
    Window,
)


def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def make_room():
    """Factory fixture: creates a rectangular Room.

    Width and height in meters. Converts to mm-based polygon internally.
    """

    def _factory(
        room_type: RoomType,
        width_m: float,
        height_m: float,
        *,
        doors: list[Door] | None = None,
        windows: list[Window] | None = None,
        furniture: list[FurnitureItem] | None = None,
    ) -> Room:
        w = width_m * 1000  # mm
        h = height_m * 1000  # mm
        boundary = Polygon(points=[
            Point(x=0, y=0),
            Point(x=w, y=0),
            Point(x=w, y=h),
            Point(x=0, y=h),
        ])
        return Room(
            id=_uid(),
            room_type=room_type,
            boundary=boundary,
            doors=doors or [],
            windows=windows or [],
            furniture=furniture or [],
        )

    return _factory


@pytest.fixture
def make_apartment():
    """Factory fixture: creates an Apartment from a list of rooms."""

    def _factory(
        apartment_class: ApartmentClass,
        rooms: list[Room],
        num_rooms: int,
    ) -> Apartment:
        return Apartment(
            id=_uid(),
            apartment_class=apartment_class,
            rooms=rooms,
            num_rooms=num_rooms,
        )

    return _factory


@pytest.fixture
def make_door():
    """Factory fixture: creates a Door."""

    def _factory(
        door_type: DoorType = DoorType.INTERIOR,
        width: float = 800.0,
        swing: SwingDirection = SwingDirection.INWARD,
        room_from: str = "room_a",
        room_to: str = "room_b",
        position: Point | None = None,
        wall_orientation: str = "vertical",
    ) -> Door:
        return Door(
            id=_uid(),
            position=position or Point(x=0, y=0),
            width=width,
            door_type=door_type,
            swing=swing,
            room_from=room_from,
            room_to=room_to,
            wall_orientation=wall_orientation,
        )

    return _factory


@pytest.fixture
def make_window():
    """Factory fixture: creates a Window."""

    def _factory(
        width: float = 1500.0,
        height: float = 1500.0,
        wall_side: str = "north",
    ) -> Window:
        return Window(
            id=_uid(),
            position=Point(x=0, y=0),
            width=width,
            height=height,
            wall_side=wall_side,
        )

    return _factory


@pytest.fixture
def make_furniture():
    """Factory fixture: creates a FurnitureItem."""

    def _factory(
        furniture_type: FurnitureType,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 600.0,
        depth: float = 400.0,
        rotation: float = 0.0,
    ) -> FurnitureItem:
        return FurnitureItem(
            id=_uid(),
            furniture_type=furniture_type,
            position=Point(x=x, y=y),
            width=width,
            depth=depth,
            rotation=rotation,
        )

    return _factory


@pytest.fixture
def economy_1room(
    make_room, make_door, make_window, make_furniture, make_apartment,
):
    """1-room economy apartment with rooms, doors, windows, furniture."""
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=1.6)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    living = make_room(
        RoomType.LIVING_ROOM, width_m=4.0, height_m=4.0,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    kitchen = make_room(
        RoomType.KITCHEN, width_m=3.0, height_m=3.0,
        windows=[make_window(width=1200.0, height=1500.0)],
    )
    bathroom = make_room(
        RoomType.COMBINED_BATHROOM, width_m=2.0, height_m=2.0,
    )

    d1 = make_door(
        door_type=DoorType.ENTRANCE, width=860.0,
        room_from=hallway.id, room_to=corridor.id,
    )
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(
        door_type=DoorType.KITCHEN, width=700.0,
        room_from=corridor.id, room_to=kitchen.id,
    )
    d4 = make_door(
        door_type=DoorType.COMBINED_BATHROOM, width=600.0,
        swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=bathroom.id,
    )

    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2, d3, d4]})

    return make_apartment(
        ApartmentClass.ECONOMY,
        [hallway, corridor, living, kitchen, bathroom],
        num_rooms=1,
    )


@pytest.fixture
def comfort_2room(
    make_room, make_door, make_window, make_furniture, make_apartment,
):
    """2-room comfort apartment."""
    hallway = make_room(RoomType.HALLWAY, width_m=2.5, height_m=1.8)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.2, height_m=4.0)
    living = make_room(
        RoomType.LIVING_ROOM, width_m=4.5, height_m=4.5,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    bedroom = make_room(
        RoomType.BEDROOM, width_m=3.5, height_m=4.0,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    kitchen = make_room(
        RoomType.KITCHEN, width_m=3.5, height_m=3.5,
        windows=[make_window(width=1200.0, height=1500.0)],
    )
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    toilet = make_room(RoomType.TOILET, width_m=1.0, height_m=1.5)

    d1 = make_door(
        door_type=DoorType.ENTRANCE, width=860.0,
        room_from=hallway.id, room_to=corridor.id,
    )
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(room_from=corridor.id, room_to=bedroom.id)
    d4 = make_door(
        door_type=DoorType.KITCHEN, width=700.0,
        room_from=corridor.id, room_to=kitchen.id,
    )
    d5 = make_door(
        door_type=DoorType.BATHROOM, width=600.0,
        swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=bathroom.id,
    )
    d6 = make_door(
        door_type=DoorType.BATHROOM, width=600.0,
        swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=toilet.id,
    )

    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(
        update={"doors": [d2, d3, d4, d5, d6]},
    )

    return make_apartment(
        ApartmentClass.COMFORT,
        [hallway, corridor, living, bedroom, kitchen, bathroom, toilet],
        num_rooms=2,
    )


@pytest.fixture
def comfort_3room(make_room, make_door, make_window, make_apartment):
    """3-room comfort apartment."""
    hallway = make_room(RoomType.HALLWAY, width_m=2.5, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.2, height_m=5.0)
    living = make_room(
        RoomType.LIVING_ROOM, width_m=5.0, height_m=4.5,
        windows=[make_window(width=1800.0, height=1500.0)],
    )
    bed1 = make_room(
        RoomType.BEDROOM, width_m=3.5, height_m=4.0,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    bed2 = make_room(
        RoomType.BEDROOM, width_m=3.0, height_m=3.5,
        windows=[make_window(width=1500.0, height=1500.0)],
    )
    kitchen = make_room(
        RoomType.KITCHEN, width_m=4.0, height_m=3.5,
        windows=[make_window(width=1200.0, height=1500.0)],
    )
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    toilet = make_room(RoomType.TOILET, width_m=1.0, height_m=1.5)

    d1 = make_door(
        door_type=DoorType.ENTRANCE, width=860.0,
        room_from=hallway.id, room_to=corridor.id,
    )
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(room_from=corridor.id, room_to=bed1.id)
    d4 = make_door(room_from=corridor.id, room_to=bed2.id)
    d5 = make_door(
        door_type=DoorType.KITCHEN, width=700.0,
        room_from=corridor.id, room_to=kitchen.id,
    )
    d6 = make_door(
        door_type=DoorType.BATHROOM, width=600.0,
        swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=bathroom.id,
    )
    d7 = make_door(
        door_type=DoorType.BATHROOM, width=600.0,
        swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=toilet.id,
    )

    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(
        update={"doors": [d2, d3, d4, d5, d6, d7]},
    )

    return make_apartment(
        ApartmentClass.COMFORT,
        [hallway, corridor, living, bed1, bed2, kitchen, bathroom, toilet],
        num_rooms=3,
    )
