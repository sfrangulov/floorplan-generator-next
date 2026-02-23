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
    ) -> Door:
        return Door(
            id=_uid(),
            position=position or Point(x=0, y=0),
            width=width,
            door_type=door_type,
            swing=swing,
            room_from=room_from,
            room_to=room_to,
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
