"""Priority queue for room placement ordering."""

from __future__ import annotations

import random

from floorplan_generator.core.enums import RoomType
from floorplan_generator.generator.types import RoomSpec

_PRIORITY_MAP: dict[RoomType, int] = {
    RoomType.HALLWAY: 1,
    RoomType.CORRIDOR: 2,
    RoomType.HALL: 2,
    RoomType.KITCHEN: 3,
    RoomType.KITCHEN_DINING: 3,
    RoomType.KITCHEN_NICHE: 3,
    RoomType.BATHROOM: 4,
    RoomType.TOILET: 4,
    RoomType.COMBINED_BATHROOM: 4,
    RoomType.LAUNDRY: 4,
    RoomType.LIVING_ROOM: 5,
    RoomType.BEDROOM: 6,
    RoomType.CHILDREN: 7,
    RoomType.CABINET: 7,
    RoomType.STORAGE: 8,
    RoomType.WARDROBE: 8,
    RoomType.BALCONY: 9,
}


def get_priority(room_type: RoomType) -> int:
    """Get placement priority for a room type (lower = earlier)."""
    return _PRIORITY_MAP.get(room_type, 9)


def build_priority_queue(
    specs: list[RoomSpec],
    rng: random.Random,
) -> list[RoomSpec]:
    """Sort room specs by priority, randomizing within same priority."""
    shuffled = list(specs)
    rng.shuffle(shuffled)
    return sorted(shuffled, key=lambda s: get_priority(s.room_type))
