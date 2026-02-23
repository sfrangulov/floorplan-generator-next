"""Domain models for the floorplan generator."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from pydantic import BaseModel, computed_field

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point, Polygon, Rectangle


class Window(BaseModel):
    """Window in a room wall."""

    id: str
    position: Point
    width: float  # mm
    height: float  # mm
    wall_side: str

    @computed_field
    @property
    def area_m2(self) -> float:
        """Window area in square meters."""
        return (self.width * self.height) / 1_000_000


class Door(BaseModel):
    """Door connecting two rooms."""

    id: str
    position: Point
    width: float  # mm (door leaf width)
    door_type: DoorType
    swing: SwingDirection
    room_from: str
    room_to: str

    @computed_field
    @property
    def swing_arc(self) -> Rectangle:
        """Rectangle representing the door sweep area.

        The arc is a square with side = door width, positioned at the door.
        """
        return Rectangle(
            x=self.position.x,
            y=self.position.y,
            width=self.width,
            height=self.width,
        )


class FurnitureItem(BaseModel):
    """A piece of furniture or equipment placed in a room."""

    id: str
    furniture_type: FurnitureType
    position: Point  # top-left corner before rotation
    width: float  # mm
    depth: float  # mm
    rotation: float = 0.0  # degrees

    @computed_field
    @property
    def bounding_box(self) -> Rectangle:
        """Axis-aligned bounding box, accounting for rotation."""
        rad = math.radians(self.rotation)
        cos_a = abs(math.cos(rad))
        sin_a = abs(math.sin(rad))
        bb_w = self.width * cos_a + self.depth * sin_a
        bb_h = self.width * sin_a + self.depth * cos_a
        return Rectangle(
            x=self.position.x,
            y=self.position.y,
            width=bb_w,
            height=bb_h,
        )

    @computed_field
    @property
    def clearance_zone(self) -> Rectangle:
        """Access zone in front of the furniture item.

        By default, extends 600mm in the direction of depth (front).
        """
        clearance_depth = 600.0  # default clearance
        bb = self.bounding_box
        return Rectangle(
            x=bb.x,
            y=bb.y + bb.height,
            width=bb.width,
            height=clearance_depth,
        )


class Room(BaseModel):
    """A room in the apartment."""

    id: str
    room_type: RoomType
    boundary: Polygon
    doors: list[Door] = []
    windows: list[Window] = []
    furniture: list[FurnitureItem] = []

    @computed_field
    @property
    def area_m2(self) -> float:
        """Room area in m² (polygon area in mm² → m²)."""
        return self.boundary.area / 1_000_000

    @computed_field
    @property
    def width_m(self) -> float:
        """Minimum side of bounding box in meters."""
        bb = self.boundary.bounding_box
        return min(bb.width, bb.height) / 1000

    @computed_field
    @property
    def height_m(self) -> float:
        """Maximum side of bounding box in meters."""
        bb = self.boundary.bounding_box
        return max(bb.width, bb.height) / 1000

    @computed_field
    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio (max side / min side)."""
        if self.width_m == 0:
            return float("inf")
        return self.height_m / self.width_m

    @computed_field
    @property
    def is_wet_zone(self) -> bool:
        return self.room_type.is_wet_zone

    @computed_field
    @property
    def requires_window(self) -> bool:
        return self.room_type.requires_window

    @computed_field
    @property
    def free_area_ratio(self) -> float:
        """Ratio of free floor area (1 - furniture_area / room_area)."""
        if self.area_m2 == 0:
            return 0.0
        furniture_area_m2 = sum(
            (f.bounding_box.width * f.bounding_box.height) / 1_000_000
            for f in self.furniture
        )
        return 1.0 - furniture_area_m2 / self.area_m2


class Apartment(BaseModel):
    """An apartment consisting of multiple rooms."""

    id: str
    apartment_class: ApartmentClass
    rooms: list[Room]
    num_rooms: int  # number of living rooms (жилых комнат)

    @computed_field
    @property
    def total_area_m2(self) -> float:
        """Total area of all rooms."""
        return sum(r.area_m2 for r in self.rooms)

    @computed_field
    @property
    def living_area_m2(self) -> float:
        """Living area — only rooms with is_living=True."""
        return sum(r.area_m2 for r in self.rooms if r.room_type.is_living)

    @computed_field
    @property
    def adjacency_graph(self) -> dict[str, list[str]]:
        """Adjacency graph: room_id -> [connected_room_ids].

        Built from door connections (bidirectional).
        """
        graph: dict[str, list[str]] = defaultdict(list)
        for room in self.rooms:
            for door in room.doors:
                if door.room_to not in graph[door.room_from]:
                    graph[door.room_from].append(door.room_to)
                if door.room_from not in graph[door.room_to]:
                    graph[door.room_to].append(door.room_from)
        return dict(graph)

    @computed_field
    @property
    def room_composition(self) -> dict[RoomType, int]:
        """Count of rooms per type."""
        return dict(Counter(r.room_type for r in self.rooms))
