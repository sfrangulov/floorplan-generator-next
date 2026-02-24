"""Planning rule validators (P01-P34)."""

from __future__ import annotations

from collections import defaultdict

from floorplan_generator.core.dimensions import (
    ADJACENCY_MATRIX,
    MIN_AREAS,
    MIN_WIDTHS,
    WINDOW_RATIOS,
)
from floorplan_generator.core.enums import (
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.models import Apartment, Door, Room
from floorplan_generator.rules.rule_engine import (
    MockAlwaysPassRule,
    RuleResult,
    RuleValidator,
)

# --- Helper to find rooms by type ---

def _rooms_of_type(apt: Apartment, *types: RoomType) -> list[Room]:
    return [r for r in apt.rooms if r.room_type in types]


def _all_doors(apt: Apartment):
    """Yield all (door, room) pairs."""
    for room in apt.rooms:
        for door in room.doors:
            yield door, room


# ========== Area rules (P01-P05) ==========

class P01LivingRoomArea1Room(RuleValidator):
    rule_id = "P01"
    name = "Min living room area (1-room)"
    description = "Living room area >= 14 m² in 1-room apartment"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.11"

    def validate(self, apartment: Apartment) -> RuleResult:
        if apartment.num_rooms != 1:
            return self._skip("Not a 1-room apartment")
        for room in _rooms_of_type(apartment, RoomType.LIVING_ROOM):
            if room.area_m2 < MIN_AREAS["living_room_1room"]:
                return self._fail(
                    f"Living room {room.area_m2:.1f} m² < 14 m²",
                    {"room_id": room.id, "area": room.area_m2},
                )
        return self._pass("Living room area OK")


class P02LivingRoomArea2Plus(RuleValidator):
    rule_id = "P02"
    name = "Min living room area (2+ rooms)"
    description = "Living room area >= 16 m² in 2+ room apartment"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.11"

    def validate(self, apartment: Apartment) -> RuleResult:
        if apartment.num_rooms < 2:
            return self._skip("Not a 2+ room apartment")
        for room in _rooms_of_type(apartment, RoomType.LIVING_ROOM):
            if room.area_m2 < MIN_AREAS["living_room_2plus"]:
                return self._fail(
                    f"Living room {room.area_m2:.1f} m² < 16 m²",
                    {"room_id": room.id, "area": room.area_m2},
                )
        return self._pass("Living room area OK")


class P03BedroomArea1Person(RuleValidator):
    rule_id = "P03"
    name = "Min bedroom area (1 person)"
    description = "Bedroom area >= 8 m²"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.11"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.BEDROOM,
            RoomType.CHILDREN, RoomType.CABINET,
        ):
            if room.area_m2 < MIN_AREAS["bedroom_1person"]:
                return self._fail(
                    f"Bedroom {room.area_m2:.1f} m² < 8 m²",
                    {"room_id": room.id, "area": room.area_m2},
                )
        return self._pass("Bedroom areas OK")


class P04BedroomArea2Person(RuleValidator):
    rule_id = "P04"
    name = "Min bedroom area (2 persons)"
    description = "Master bedroom area >= 10 m² in 2+ room apartment"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.11"

    def validate(self, apartment: Apartment) -> RuleResult:
        if apartment.num_rooms < 2:
            return self._skip("Not a 2+ room apartment")
        bedrooms = _rooms_of_type(apartment, RoomType.BEDROOM)
        if not bedrooms:
            return self._skip("No bedrooms found")
        largest = max(bedrooms, key=lambda r: r.area_m2)
        if largest.area_m2 < MIN_AREAS["bedroom_2person"]:
            return self._fail(
                f"Master bedroom {largest.area_m2:.1f} m² < 10 m²",
                {"room_id": largest.id, "area": largest.area_m2},
            )
        return self._pass("Master bedroom area OK")


class P05KitchenArea(RuleValidator):
    rule_id = "P05"
    name = "Min kitchen area"
    description = "Kitchen >= 8 m² (or >= 5 m² in 1-room)"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.11"

    def validate(self, apartment: Apartment) -> RuleResult:
        min_area = (
            MIN_AREAS["kitchen_1room"]
            if apartment.num_rooms == 1
            else MIN_AREAS["kitchen"]
        )
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN, RoomType.KITCHEN_DINING,
        ):
            if room.area_m2 < min_area:
                return self._fail(
                    f"Kitchen {room.area_m2:.1f} m² < {min_area} m²",
                    {"room_id": room.id, "area": room.area_m2},
                )
        return self._pass("Kitchen area OK")


# ========== Width rules (P06-P10) ==========

class P06KitchenWidth(RuleValidator):
    rule_id = "P06"
    name = "Min kitchen width"
    description = "Kitchen width >= 1700 mm"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN, RoomType.KITCHEN_DINING,
        ):
            if room.width_m < MIN_WIDTHS["kitchen"] / 1000:
                return self._fail(
                    f"Kitchen width {room.width_m:.2f} m < 1.7 m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Kitchen width OK")


class P07CorridorWidth(RuleValidator):
    rule_id = "P07"
    name = "Min corridor width"
    description = (
        "Corridor width >= 850 mm (or >= 1000 mm if length > 1500 mm)"
    )
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(apartment, RoomType.CORRIDOR):
            length_mm = room.height_m * 1000  # height_m is max side
            min_w = MIN_WIDTHS["corridor"] / 1000
            if length_mm > MIN_WIDTHS["corridor_long_threshold"]:
                min_w = MIN_WIDTHS["corridor_long"] / 1000
            if room.width_m < min_w:
                return self._fail(
                    f"Corridor width {room.width_m:.2f} m < {min_w} m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Corridor width OK")


class P08HallwayWidth(RuleValidator):
    rule_id = "P08"
    name = "Min hallway width"
    description = "Hallway width >= 1400 mm"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(apartment, RoomType.HALLWAY):
            if room.width_m < MIN_WIDTHS["hallway"] / 1000:
                return self._fail(
                    f"Hallway width {room.width_m:.2f} m < 1.4 m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Hallway width OK")


class P09BathroomWidth(RuleValidator):
    rule_id = "P09"
    name = "Min bathroom width"
    description = "Bathroom width >= 1500 mm"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(apartment, RoomType.BATHROOM):
            if room.width_m < MIN_WIDTHS["bathroom"] / 1000:
                return self._fail(
                    f"Bathroom width {room.width_m:.2f} m < 1.5 m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Bathroom width OK")


class P10CombinedBathroomWidth(RuleValidator):
    rule_id = "P10"
    name = "Min combined bathroom width"
    description = "Combined bathroom width >= 1700 mm"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.COMBINED_BATHROOM,
        ):
            if room.width_m < MIN_WIDTHS["combined_bathroom"] / 1000:
                return self._fail(
                    f"Combined bathroom width "
                    f"{room.width_m:.2f} m < 1.7 m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Combined bathroom width OK")


# ========== Proportion (P11) ==========

class P11AspectRatio(RuleValidator):
    rule_id = "P11"
    name = "Living room aspect ratio"
    description = "Aspect ratio of living rooms <= 1:2"
    is_mandatory = False
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM, RoomType.BEDROOM,
            RoomType.CHILDREN, RoomType.CABINET,
        ):
            if room.aspect_ratio > 2.0:
                return self._fail(
                    f"Room aspect ratio {room.aspect_ratio:.1f} > 2.0",
                    {
                        "room_id": room.id,
                        "aspect_ratio": room.aspect_ratio,
                    },
                )
        return self._pass("Aspect ratios OK")


# ========== Window rules (P12-P14) ==========

class P12WindowsInLivingRooms(RuleValidator):
    rule_id = "P12"
    name = "Windows in living rooms"
    description = "Living rooms must have at least one window"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            if room.requires_window and len(room.windows) == 0:
                return self._fail(
                    f"Room {room.room_type.value} has no windows",
                    {
                        "room_id": room.id,
                        "room_type": room.room_type.value,
                    },
                )
        return self._pass("All rooms requiring windows have windows")


class P13WindowsInKitchen(RuleValidator):
    rule_id = "P13"
    name = "Windows in kitchen"
    description = "Kitchen must have a window (except kitchen niche)"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN, RoomType.KITCHEN_DINING,
        ):
            if len(room.windows) == 0:
                return self._fail(
                    "Kitchen has no windows",
                    {"room_id": room.id},
                )
        # Kitchen niche does not require a window
        return self._pass("Kitchen windows OK")


class P14WindowAreaRatio(RuleValidator):
    rule_id = "P14"
    name = "Window area ratio"
    description = "Total window area >= 1/8 of floor area"
    is_mandatory = True
    regulatory_basis = "SNiP 23-05"

    def validate(self, apartment: Apartment) -> RuleResult:
        min_ratio = WINDOW_RATIOS["min_ratio"]
        for room in apartment.rooms:
            if not room.requires_window:
                continue
            if not room.windows:
                continue  # P12/P13 handles missing windows
            window_area = sum(w.area_m2 for w in room.windows)
            ratio = window_area / room.area_m2 if room.area_m2 > 0 else 0
            if ratio < min_ratio:
                return self._fail(
                    f"Window area ratio {ratio:.3f} < {min_ratio:.3f}",
                    {
                        "room_id": room.id,
                        "window_area": window_area,
                        "floor_area": room.area_m2,
                    },
                )
        return self._pass("Window area ratios OK")


# ========== Adjacency/connectivity (P15-P19) ==========

class P15ToiletNotFromKitchen(RuleValidator):
    rule_id = "P15"
    name = "No toilet from kitchen"
    description = "No door from kitchen to toilet"
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.12"

    def validate(self, apartment: Apartment) -> RuleResult:
        room_map = {r.id: r for r in apartment.rooms}
        kitchen_types = {RoomType.KITCHEN, RoomType.KITCHEN_DINING}
        toilet_types = {RoomType.TOILET, RoomType.COMBINED_BATHROOM}
        for door, room in _all_doors(apartment):
            from_room = room_map.get(door.room_from)
            to_room = room_map.get(door.room_to)
            if from_room is None or to_room is None:
                continue
            ft = from_room.room_type
            tt = to_room.room_type
            if (ft in kitchen_types and tt in toilet_types) or (
                ft in toilet_types and tt in kitchen_types
            ):
                return self._fail("Door connects kitchen to toilet")
        return self._pass("No kitchen-toilet door connection")


class P16AdjacencyMatrix(RuleValidator):
    rule_id = "P16"
    name = "Adjacency matrix"
    description = "All door connections match the adjacency matrix"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        room_map = {r.id: r for r in apartment.rooms}
        for door, _room in _all_doors(apartment):
            from_room = room_map.get(door.room_from)
            to_room = room_map.get(door.room_to)
            if from_room is None or to_room is None:
                continue
            ft = from_room.room_type
            tt = to_room.room_type
            if ft in ADJACENCY_MATRIX and tt in ADJACENCY_MATRIX.get(
                ft, {},
            ):
                allowed = ADJACENCY_MATRIX[ft][tt]
                if allowed == "-":
                    return self._fail(
                        f"Forbidden adjacency: "
                        f"{ft.value} -> {tt.value}",
                        {"from": ft.value, "to": tt.value},
                    )
            # If not in matrix, allow by default
        return self._pass("All adjacencies OK")


class P17NonPassthroughBedrooms(RuleValidator):
    rule_id = "P17"
    name = "Non-passthrough bedrooms"
    description = (
        "Bedrooms should not be passthrough in 2+ room apartments"
    )
    is_mandatory = True
    regulatory_basis = "SNiP 31-01"

    def validate(self, apartment: Apartment) -> RuleResult:
        if apartment.num_rooms < 2:
            return self._skip("Single-room apartment")
        for room in _rooms_of_type(apartment, RoomType.BEDROOM):
            door_count = len(room.doors)
            if door_count > 1:
                return self._fail(
                    f"Bedroom is passthrough ({door_count} doors)",
                    {"room_id": room.id, "door_count": door_count},
                )
        return self._pass("No passthrough bedrooms")


class P18MandatoryComposition(RuleValidator):
    rule_id = "P18"
    name = "Mandatory composition"
    description = (
        "Apartment must have living room + kitchen + bathroom + hallway"
    )
    is_mandatory = True
    regulatory_basis = "SP 54, p.5.3"

    def validate(self, apartment: Apartment) -> RuleResult:
        types = {r.room_type for r in apartment.rooms}
        living_types = {
            RoomType.LIVING_ROOM, RoomType.BEDROOM,
            RoomType.CHILDREN, RoomType.CABINET,
        }
        kitchen_types = {
            RoomType.KITCHEN, RoomType.KITCHEN_DINING,
            RoomType.KITCHEN_NICHE,
        }
        bath_types = {
            RoomType.BATHROOM, RoomType.TOILET,
            RoomType.COMBINED_BATHROOM,
        }
        entry_types = {RoomType.HALLWAY, RoomType.HALL}

        if not types & living_types:
            return self._fail("No living room")
        if not types & kitchen_types:
            return self._fail("No kitchen")
        if not types & bath_types:
            return self._fail("No bathroom/toilet")
        if not types & entry_types:
            return self._fail("No hallway/hall")
        return self._pass("Mandatory composition OK")


class P19ZoneSeparation(RuleValidator):
    rule_id = "P19"
    name = "Zone separation"
    description = (
        "Day and night zones should not be mixed by transit"
    )
    is_mandatory = False
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        night_types = {
            RoomType.BEDROOM, RoomType.CHILDREN, RoomType.CABINET,
        }
        day_types = {
            RoomType.KITCHEN, RoomType.KITCHEN_DINING,
            RoomType.LIVING_ROOM,
        }
        room_map = {r.id: r for r in apartment.rooms}
        graph = apartment.adjacency_graph

        for room in apartment.rooms:
            if room.room_type not in night_types:
                continue
            neighbors = graph.get(room.id, [])
            neighbor_types = [
                room_map[n].room_type
                for n in neighbors if n in room_map
            ]
            has_day = any(t in day_types for t in neighbor_types)
            if has_day and len(neighbors) > 1:
                return self._fail(
                    f"Night zone {room.room_type.value} used as transit",
                    {"room_id": room.id},
                )
        return self._pass("Zone separation OK")


# ========== Door rules (P20-P23) ==========

class P20EntranceDoorWidth(RuleValidator):
    rule_id = "P20"
    name = "Min entrance door width"
    description = "Entrance door width >= 800 mm"
    is_mandatory = True
    regulatory_basis = "SP 3.13130"

    def validate(self, apartment: Apartment) -> RuleResult:
        for door, _ in _all_doors(apartment):
            if door.door_type == DoorType.ENTRANCE:
                if door.width < 800:
                    return self._fail(
                        f"Entrance door width {door.width} mm < 800 mm",
                        {"door_id": door.id, "width": door.width},
                    )
        return self._pass("Entrance door width OK")


class P21BathroomDoorOutward(RuleValidator):
    rule_id = "P21"
    name = "Bathroom doors open outward"
    description = "Bathroom and toilet doors must swing outward"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_door_types = {
            DoorType.BATHROOM, DoorType.COMBINED_BATHROOM,
        }
        for door, _ in _all_doors(apartment):
            if door.door_type in bath_door_types:
                if door.swing != SwingDirection.OUTWARD:
                    return self._fail(
                        "Bathroom door swings inward",
                        {"door_id": door.id},
                    )
        return self._pass("Bathroom doors swing outward")


class P22DoorsNotCollide(RuleValidator):
    rule_id = "P22"
    name = "Doors do not collide"
    description = "Door swing arcs must not overlap"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        # Deduplicate doors (same door appears in both room_from and room_to)
        seen: dict[str, Door] = {}
        for door, _room in _all_doors(apartment):
            if door.id not in seen:
                seen[door.id] = door
        unique_doors = list(seen.values())
        for i in range(len(unique_doors)):
            for j in range(i + 1, len(unique_doors)):
                d1 = unique_doors[i]
                d2 = unique_doors[j]
                if d1.swing_arc.overlaps(d2.swing_arc):
                    return self._fail(
                        "Door swing arcs collide",
                        {"door1": d1.id, "door2": d2.id},
                    )
        return self._pass("No door collisions")


class P23DoorWallGap(RuleValidator):
    rule_id = "P23"
    name = "Door-wall gap"
    description = "Distance from door to adjacent wall >= 100 mm"
    is_mandatory = True
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            pts = room.boundary.points
            for door in room.doors:
                # Distance from door position to nearest wall corner
                min_dist = min(
                    door.position.distance_to(pt) for pt in pts
                )
                if min_dist < 100:
                    return self._fail(
                        f"Door-wall gap {min_dist:.0f} mm < 100 mm",
                        {"door_id": door.id, "distance": min_dist},
                    )
        return self._pass("Door-wall gaps OK")


# ========== Wet zone rules (P24-P25) ==========

class P24WetZonesGrouped(RuleValidator):
    rule_id = "P24"
    name = "Wet zones grouped"
    description = (
        "All wet zones must be adjacent (connected component)"
    )
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        wet_rooms = [r for r in apartment.rooms if r.is_wet_zone]
        if len(wet_rooms) <= 1:
            return self._pass("Single or no wet zone — OK")

        wet_ids = {r.id for r in wet_rooms}
        graph = apartment.adjacency_graph
        adj: dict[str, set[str]] = defaultdict(set)

        for wid in wet_ids:
            for neighbor in graph.get(wid, []):
                if neighbor in wet_ids:
                    adj[wid].add(neighbor)
                else:
                    for nn in graph.get(neighbor, []):
                        if nn in wet_ids and nn != wid:
                            adj[wid].add(nn)
                            adj[nn].add(wid)

        # BFS to check connectivity
        visited: set[str] = set()
        queue = [next(iter(wet_ids))]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            queue.extend(adj.get(curr, set()) - visited)

        if visited != wet_ids:
            return self._fail(
                f"Wet zones not fully connected: "
                f"{len(visited)}/{len(wet_ids)}",
                {
                    "connected": list(visited),
                    "all": list(wet_ids),
                },
            )
        return self._pass("Wet zones grouped OK")


class P25EnsuiteCondition(RuleValidator):
    rule_id = "P25"
    name = "Ensuite condition"
    description = (
        "Ensuite bathroom requires second bathroom from corridor"
    )
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        room_map = {r.id: r for r in apartment.rooms}
        bath_types = {
            RoomType.BATHROOM, RoomType.COMBINED_BATHROOM,
            RoomType.TOILET,
        }
        bedroom_types = {
            RoomType.BEDROOM, RoomType.CHILDREN, RoomType.CABINET,
        }
        corridor_types = {
            RoomType.CORRIDOR, RoomType.HALLWAY, RoomType.HALL,
        }

        has_ensuite = False
        has_corridor_bath = False

        for door, _room in _all_doors(apartment):
            from_room = room_map.get(door.room_from)
            to_room = room_map.get(door.room_to)
            if from_room is None or to_room is None:
                continue

            ft = from_room.room_type
            tt = to_room.room_type

            if (ft in bedroom_types and tt in bath_types) or (
                tt in bedroom_types and ft in bath_types
            ):
                has_ensuite = True

            if (ft in corridor_types and tt in bath_types) or (
                tt in corridor_types and ft in bath_types
            ):
                has_corridor_bath = True

        if has_ensuite and not has_corridor_bath:
            return self._fail(
                "Ensuite without second bathroom from corridor",
            )
        return self._pass("Ensuite condition OK")


# ========== Recommendations (P26-P28) ==========

class P26LivingRoomMinWidth(RuleValidator):
    rule_id = "P26"
    name = "Living room min width"
    description = "Living room width >= 3200 mm"
    is_mandatory = False
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(apartment, RoomType.LIVING_ROOM):
            if room.width_m < MIN_WIDTHS["living_room"] / 1000:
                return self._fail(
                    f"Living room width {room.width_m:.2f} m < 3.2 m",
                    {"room_id": room.id, "width": room.width_m},
                )
        return self._pass("Living room width OK")


class P27LivingRoomCentral(RuleValidator):
    rule_id = "P27"
    name = "Living room central position"
    description = "Living room should be adjacent to hallway/hall"
    is_mandatory = False
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        living_rooms = _rooms_of_type(apartment, RoomType.LIVING_ROOM)
        if not living_rooms:
            return self._skip("No living room")
        entry_types = {RoomType.HALLWAY, RoomType.HALL}
        graph = apartment.adjacency_graph
        room_map = {r.id: r for r in apartment.rooms}

        for lr in living_rooms:
            neighbors = graph.get(lr.id, [])
            if any(
                room_map.get(n) and room_map[n].room_type in entry_types
                for n in neighbors
            ):
                return self._pass(
                    "Living room adjacent to entry zone",
                )
        return self._fail("Living room not connected to entry zone")


class P28DiningNotFacingEntry(RuleValidator):
    rule_id = "P28"
    name = "Dining not facing entry"
    description = "Dining table should not face the entry door"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            tables = [
                f for f in room.furniture
                if f.furniture_type == FurnitureType.DINING_TABLE
            ]
            if not tables or not room.doors:
                continue
            for table in tables:
                tb = table.bounding_box
                for door in room.doors:
                    dp = door.position
                    dx = abs(tb.x - dp.x)
                    dy = abs(tb.y - dp.y)
                    if dx < 500 and dy < 1000:
                        return self._fail(
                            "Dining table faces entry door",
                            {
                                "table_id": table.id,
                                "door_id": door.id,
                            },
                        )
        return self._pass("Dining placement OK")


# ========== Mock rules (P29-P34) ==========

class P36WindowsOnExternalWalls(RuleValidator):
    rule_id = "P36"
    name = "Windows on external walls only"
    description = "Windows must be placed on external (perimeter) walls"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        if not apartment.rooms:
            return self._skip("No rooms")

        # Compute building footprint as bounding box of all rooms
        all_bbs = [r.boundary.bounding_box for r in apartment.rooms]
        min_x = min(bb.x for bb in all_bbs)
        min_y = min(bb.y for bb in all_bbs)
        max_x = max(bb.x + bb.width for bb in all_bbs)
        max_y = max(bb.y + bb.height for bb in all_bbs)

        eps = 250.0  # same tolerance as window_placer

        for room in apartment.rooms:
            for window in room.windows:
                wp = window.position
                side = window.wall_side
                on_perimeter = (
                    (side == "west" and abs(wp.x - min_x) < eps)
                    or (side == "east" and abs(wp.x - max_x) < eps)
                    or (side == "north" and abs(wp.y - min_y) < eps)
                    or (side == "south" and abs(wp.y - max_y) < eps)
                )
                if not on_perimeter:
                    return self._fail(
                        f"Window on internal wall in {room.room_type.value}",
                        {
                            "room_id": room.id,
                            "window_id": window.id,
                            "wall_side": side,
                        },
                    )
        return self._pass("All windows on external walls")


class P37KitchenNotPassthrough(RuleValidator):
    rule_id = "P37"
    name = "Kitchen not passthrough to living areas"
    description = (
        "Kitchen must not serve as a passthrough between "
        "living room and bedroom"
    )
    is_mandatory = True
    regulatory_basis = "SP 54"

    _LIVING_TYPES = {
        RoomType.LIVING_ROOM,
        RoomType.BEDROOM,
        RoomType.CHILDREN,
        RoomType.CABINET,
    }

    def validate(self, apartment: Apartment) -> RuleResult:
        room_map = {r.id: r for r in apartment.rooms}
        kitchen_types = {RoomType.KITCHEN, RoomType.KITCHEN_DINING}

        for room in apartment.rooms:
            if room.room_type not in kitchen_types:
                continue
            # Collect living-area neighbors via doors
            living_neighbors = set()
            for door in room.doors:
                other_id = (
                    door.room_to if door.room_from == room.id
                    else door.room_from
                )
                other = room_map.get(other_id)
                if other and other.room_type in self._LIVING_TYPES:
                    living_neighbors.add(other_id)
            if len(living_neighbors) >= 2:
                return self._fail(
                    f"Kitchen is passthrough to {len(living_neighbors)} "
                    f"living areas",
                    {
                        "room_id": room.id,
                        "living_neighbors": list(living_neighbors),
                    },
                )
        return self._pass("Kitchen not passthrough")


class P35SingleDoorUtilityRooms(RuleValidator):
    rule_id = "P35"
    name = "Single door in utility rooms"
    description = (
        "Storage, bathroom, and toilet must have exactly one door"
    )
    is_mandatory = True
    regulatory_basis = "SP 54"

    _SINGLE_DOOR_TYPES = {
        RoomType.STORAGE,
        RoomType.WARDROBE,
        RoomType.BATHROOM,
        RoomType.TOILET,
        RoomType.COMBINED_BATHROOM,
        RoomType.LAUNDRY,
    }

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            if room.room_type not in self._SINGLE_DOOR_TYPES:
                continue
            door_count = len(room.doors)
            if door_count != 1:
                return self._fail(
                    f"{room.room_type.value} has {door_count} doors, expected 1",
                    {"room_id": room.id, "door_count": door_count},
                )
        return self._pass("Utility rooms have single doors")


class P38EntranceDoorExists(RuleValidator):
    rule_id = "P38"
    name = "Entrance door exists"
    description = "Apartment must have at least one entrance door"
    is_mandatory = True
    regulatory_basis = "SP 54"

    def validate(self, apartment: Apartment) -> RuleResult:
        for door, _ in _all_doors(apartment):
            if door.door_type == DoorType.ENTRANCE:
                return self._pass("Entrance door found")
        return self._fail("No entrance door in the apartment")


class P39WardrobeConnection(RuleValidator):
    rule_id = "P39"
    name = "Wardrobe connected to bedroom or hallway"
    description = (
        "Wardrobe must be connected to a bedroom or hallway"
    )
    is_mandatory = True
    regulatory_basis = "Practice"

    _ALLOWED_NEIGHBORS = {
        RoomType.BEDROOM,
        RoomType.CHILDREN,
        RoomType.CABINET,
        RoomType.HALLWAY,
        RoomType.CORRIDOR,
        RoomType.HALL,
    }

    def validate(self, apartment: Apartment) -> RuleResult:
        room_map = {r.id: r for r in apartment.rooms}
        for room in apartment.rooms:
            if room.room_type != RoomType.WARDROBE:
                continue
            if not room.doors:
                return self._fail(
                    "Wardrobe has no doors",
                    {"room_id": room.id},
                )
            for door in room.doors:
                other_id = (
                    door.room_to if door.room_from == room.id
                    else door.room_from
                )
                other = room_map.get(other_id)
                if other and other.room_type in self._ALLOWED_NEIGHBORS:
                    break
            else:
                return self._fail(
                    "Wardrobe not connected to bedroom or hallway",
                    {"room_id": room.id},
                )
        return self._pass("Wardrobe connections OK")


class P29RoomHeight(MockAlwaysPassRule):
    rule_id = "P29"
    name = "Min room height"
    description = (
        "Living room/kitchen height >= 2500 mm (3D parameter)"
    )
    regulatory_basis = "SP 54, p.5.8"


class P30CorridorHeight(MockAlwaysPassRule):
    rule_id = "P30"
    name = "Min corridor height"
    description = "Corridor/hall height >= 2100 mm (3D parameter)"
    regulatory_basis = "SP 54, p.5.8"


class P31SanitaryAboveLiving(MockAlwaysPassRule):
    rule_id = "P31"
    name = "Sanitary not above living"
    description = "Bathrooms not above living rooms (multi-floor)"
    regulatory_basis = "SP 54, p.5.12"


class P32Insolation(MockAlwaysPassRule):
    rule_id = "P32"
    name = "Insolation >= 2 hours"
    description = "Continuous insolation >= 2 hours/day"
    regulatory_basis = "SanPiN 2.2.1/2.1.1.1076"


class P33Waterproofing(MockAlwaysPassRule):
    rule_id = "P33"
    name = "Waterproofing"
    description = "Wet zone floors have waterproofing"
    regulatory_basis = "SP 29.13330"


class P34Ventilation(MockAlwaysPassRule):
    rule_id = "P34"
    name = "Exhaust ventilation"
    description = (
        "Kitchen, bathroom, toilet have exhaust ventilation"
    )
    regulatory_basis = "SP 54, p.5.8"
