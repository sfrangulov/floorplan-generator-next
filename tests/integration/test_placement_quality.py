"""Integration tests for placement quality (PQ01-PQ04)."""

from __future__ import annotations

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment


def _generate(apartment_class: ApartmentClass, num_rooms: int, seed: int):
    return generate_apartment(apartment_class, num_rooms, seed, max_restarts=50)


# PQ01
def test_living_rooms_have_windows():
    """All living rooms and kitchens get at least one window."""
    for seed in range(42, 52):
        result = _generate(ApartmentClass.ECONOMY, 1, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            if room.room_type.requires_window:
                assert len(room.windows) >= 1, (
                    f"seed={seed}: {room.room_type} has no window"
                )


# PQ02
def test_no_door_arc_collisions():
    """No pair of doors has overlapping swing arcs."""
    for seed in range(42, 52):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is None:
            continue
        all_doors = []
        seen = set()
        for room in result.apartment.rooms:
            for door in room.doors:
                if door.id not in seen:
                    seen.add(door.id)
                    all_doors.append(door)
        for i, d1 in enumerate(all_doors):
            for j, d2 in enumerate(all_doors):
                if i < j:
                    assert not d1.swing_arc.overlaps(d2.swing_arc), (
                        f"seed={seed}: doors {d1.id} and {d2.id} arcs collide"
                    )


# PQ03
def test_furniture_inside_rooms():
    """All furniture items are inside their room boundary."""
    for seed in range(42, 47):
        result = _generate(ApartmentClass.ECONOMY, 1, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            bb = room.boundary.bounding_box
            for item in room.furniture:
                ibb = item.bounding_box
                assert ibb.x >= bb.x - 2, (
                    f"seed={seed}: {item.furniture_type} outside room left"
                )
                assert ibb.y >= bb.y - 2, (
                    f"seed={seed}: {item.furniture_type} outside room top"
                )
                assert ibb.x + ibb.width <= bb.x + bb.width + 2
                assert ibb.y + ibb.height <= bb.y + bb.height + 2


# PQ04
def test_furniture_not_overlapping_doors():
    """No furniture item overlaps a door swing arc in the same room."""
    for seed in range(42, 47):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is None:
            continue
        for room in result.apartment.rooms:
            for item in room.furniture:
                for door in room.doors:
                    assert not item.bounding_box.overlaps(door.swing_arc), (
                        f"seed={seed}: {item.furniture_type} overlaps door "
                        f"{door.id} arc in {room.room_type}"
                    )


# PQ05
def test_layout_compact_no_excessive_restarts():
    """Layouts should succeed within reasonable restarts for comfort 2-room."""
    success_count = 0
    for seed in range(42, 62):
        result = _generate(ApartmentClass.COMFORT, 2, seed)
        if result is not None and result.restart_count <= 8:
            success_count += 1
    # At least 5/20 should succeed within 8 restarts
    assert success_count >= 5, f"Only {success_count}/20 succeeded within 8 restarts"
