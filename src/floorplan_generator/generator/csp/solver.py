"""CSP solver orchestrator: doors -> windows -> risers -> furniture."""

from __future__ import annotations

import random

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.core.geometry import Rectangle
from floorplan_generator.core.models import Room
from floorplan_generator.generator.csp.door_placer import place_doors
from floorplan_generator.generator.csp.furniture_placer import place_furniture
from floorplan_generator.generator.csp.riser_placer import place_risers
from floorplan_generator.generator.csp.window_placer import place_windows
from floorplan_generator.generator.room_composer import get_furniture_list
from floorplan_generator.generator.types import CSPResult, SharedWall


def csp_solve(
    rooms: list[Room],
    shared_walls: list[SharedWall],
    canvas: Rectangle,
    apartment_class: ApartmentClass,
    rng: random.Random,
) -> CSPResult:
    """Run CSP solver: doors -> windows -> risers -> furniture."""
    # Step 1: Place doors
    door_results = place_doors(rooms, shared_walls, rng)

    # Assign doors to rooms
    room_doors: dict[str, list] = {r.id: [] for r in rooms}
    for dr in door_results:
        door = dr["door"]
        if door.room_from in room_doors:
            room_doors[door.room_from].append(door)
        if door.room_to in room_doors:
            room_doors[door.room_to].append(door)

    # Step 2: Place windows
    window_results = place_windows(rooms, canvas, rng)
    room_windows: dict[str, list] = {r.id: [] for r in rooms}
    for wr in window_results:
        rid = wr["room"].id
        if rid in room_windows:
            room_windows[rid].append(wr["window"])

    # Step 3: Place risers
    risers = place_risers(rooms, canvas, rng)

    # Step 4: Place furniture in each room
    updated_rooms = []
    soft_details: list[str] = []

    for room in rooms:
        furniture_list = get_furniture_list(
            room.room_type, apartment_class, room.area_m2, rng,
        )

        doors_for_room = room_doors.get(room.id, [])
        furniture = place_furniture(
            room, furniture_list, doors_for_room, risers, rng,
        )

        if furniture is None:
            return CSPResult(
                success=False,
                reason=f"furniture_fail:{room.room_type}",
            )

        # Check that required furniture was mostly placed
        # (fail if room needed furniture but got none)
        if furniture_list and not furniture:
            return CSPResult(
                success=False,
                reason=f"furniture_fail:{room.room_type}",
            )

        # Update room with doors, windows, furniture
        updated = room.model_copy(update={
            "doors": doors_for_room,
            "windows": room_windows.get(room.id, []),
            "furniture": furniture,
        })
        updated_rooms.append(updated)

    return CSPResult(
        success=True,
        rooms=updated_rooms,
        hard_violations=0,
        soft_violations=len(soft_details),
        soft_details=soft_details,
    )
