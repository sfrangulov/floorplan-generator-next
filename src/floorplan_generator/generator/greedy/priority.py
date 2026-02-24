"""Priority queue for room placement ordering."""

from __future__ import annotations

import random

from floorplan_generator.core.dimensions import ROOM_PLACEMENT_PRIORITY
from floorplan_generator.core.enums import RoomType
from floorplan_generator.generator.types import RoomSpec


def get_priority(room_type: RoomType) -> int:
    """Get placement priority for a room type (lower = earlier)."""
    return ROOM_PLACEMENT_PRIORITY.get(room_type, 9)


def build_priority_queue(
    specs: list[RoomSpec],
    rng: random.Random,
) -> list[RoomSpec]:
    """Sort room specs by priority, randomizing within same priority."""
    shuffled = list(specs)
    rng.shuffle(shuffled)
    return sorted(shuffled, key=lambda s: get_priority(s.room_type))
