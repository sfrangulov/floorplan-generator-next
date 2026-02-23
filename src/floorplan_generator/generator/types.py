"""Types for the generator engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from floorplan_generator.core.enums import (  # noqa: F401
    ApartmentClass,
    FurnitureType,
    RoomType,
)
from floorplan_generator.core.geometry import Point, Rectangle, Segment  # noqa: F401
from floorplan_generator.core.models import (  # noqa: F401
    Apartment,
    Door,
    FurnitureItem,
    Room,
    Window,
)


class Side(StrEnum):
    """Side of a rectangle for room attachment."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class Alignment(StrEnum):
    """Alignment when attaching a room to a side."""

    START = "start"
    CENTER = "center"
    END = "end"


class RoomSpec(BaseModel):
    """Specification for a room to be generated."""

    room_type: RoomType
    width: float  # mm
    height: float  # mm


class Slot(BaseModel):
    """A candidate position for placing a room."""

    position: Point
    target_room_id: str
    side: Side
    alignment: Alignment
    shared_wall: Segment
    score: float = 0.0


class SharedWall(BaseModel):
    """Shared wall between two adjacent rooms."""

    room_a_id: str
    room_b_id: str
    segment: Segment


class GreedyResult(BaseModel):
    """Result of greedy room placement."""

    success: bool
    rooms: list[Room] = []
    shared_walls: list[SharedWall] = []
    failed_room: RoomSpec | None = None


class CSPResult(BaseModel):
    """Result of CSP solving."""

    success: bool
    rooms: list[Room] = []
    hard_violations: int = 0
    soft_violations: int = 0
    soft_details: list[str] = []
    reason: str = ""


class Riser(BaseModel):
    """Water supply/drain riser (vertical pipe)."""

    id: str
    position: Point
    diameter: float = 100.0  # mm


class GenerationResult(BaseModel):
    """Complete result of a single apartment generation."""

    apartment: Apartment
    risers: list[Riser] = []
    restart_count: int
    seed_used: int
    recommended_violations: int
