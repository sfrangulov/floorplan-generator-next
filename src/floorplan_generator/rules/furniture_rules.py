"""Furniture rule validators (F01-F32)."""

from __future__ import annotations

from floorplan_generator.core.dimensions import (
    CLEARANCES,
    FURNITURE_SIZES,
    KITCHEN_TRIANGLE,
)
from floorplan_generator.core.enums import FurnitureType, RoomType
from floorplan_generator.core.geometry import min_distance_rect_to_segment
from floorplan_generator.core.models import Apartment, Room
from floorplan_generator.rules.geometry_helpers import (
    center_x_distance_to_nearest_wall,
    clearance_in_front,
    distance_between_items,
    items_of_type,
    kitchen_triangle_perimeter,
    nearest_wall_distance,
    wall_segments,
)
from floorplan_generator.rules.rule_engine import (
    RuleResult,
    RuleValidator,
)


def _rooms_of_type(
    apt: Apartment, *types: RoomType,
) -> list[Room]:
    return [r for r in apt.rooms if r.room_type in types]


# ========== Bathroom (F01-F05) ==========


class F01ToiletCenterFromWall(RuleValidator):
    rule_id = "F01"
    name = "Toilet center from wall"
    description = (
        "Toilet center axis >= 350 mm from nearest side wall"
    )
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_types = (
            RoomType.BATHROOM, RoomType.TOILET,
            RoomType.COMBINED_BATHROOM,
        )
        for room in _rooms_of_type(apartment, *bath_types):
            for toilet in items_of_type(
                room, FurnitureType.TOILET_BOWL,
            ):
                dist = center_x_distance_to_nearest_wall(
                    toilet, room,
                )
                if dist < CLEARANCES["toilet_center_from_wall"]:
                    return self._fail(
                        f"Toilet center {dist:.0f} mm "
                        f"from wall < 350 mm",
                        {"item_id": toilet.id, "distance": dist},
                    )
        return self._pass("Toilet center distance OK")


class F02ToiletFrontClearance(RuleValidator):
    rule_id = "F02"
    name = "Toilet front clearance"
    description = "Free space in front of toilet >= 600 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_types = (
            RoomType.BATHROOM, RoomType.TOILET,
            RoomType.COMBINED_BATHROOM,
        )
        for room in _rooms_of_type(apartment, *bath_types):
            for toilet in items_of_type(
                room, FurnitureType.TOILET_BOWL,
            ):
                cl = clearance_in_front(toilet, room)
                if cl < CLEARANCES["toilet_front"]:
                    return self._fail(
                        f"Toilet front clearance "
                        f"{cl:.0f} mm < 600 mm",
                        {"item_id": toilet.id, "clearance": cl},
                    )
        return self._pass("Toilet front clearance OK")


class F03SinkFrontClearance(RuleValidator):
    rule_id = "F03"
    name = "Sink front clearance"
    description = "Free space in front of sink >= 700 mm"
    is_mandatory = True
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_types = (
            RoomType.BATHROOM, RoomType.COMBINED_BATHROOM,
        )
        for room in _rooms_of_type(apartment, *bath_types):
            for sink in items_of_type(
                room, FurnitureType.SINK,
                FurnitureType.DOUBLE_SINK,
            ):
                cl = clearance_in_front(sink, room)
                if cl < CLEARANCES["sink_front"]:
                    return self._fail(
                        f"Sink front clearance "
                        f"{cl:.0f} mm < 700 mm",
                        {"item_id": sink.id, "clearance": cl},
                    )
        return self._pass("Sink front clearance OK")


class F04BathtubExitClearance(RuleValidator):
    rule_id = "F04"
    name = "Bathtub exit clearance"
    description = "Free zone for bathtub exit >= 550 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_types = (
            RoomType.BATHROOM, RoomType.COMBINED_BATHROOM,
        )
        for room in _rooms_of_type(apartment, *bath_types):
            for tub in items_of_type(
                room, FurnitureType.BATHTUB,
            ):
                cl = clearance_in_front(tub, room)
                if cl < CLEARANCES["bathtub_exit"]:
                    return self._fail(
                        f"Bathtub exit clearance "
                        f"{cl:.0f} mm < 550 mm",
                        {"item_id": tub.id, "clearance": cl},
                    )
        return self._pass("Bathtub exit clearance OK")


class F05OutletFromWater(RuleValidator):
    rule_id = "F05"
    name = "Outlet distance from water"
    description = (
        "Electrical outlet >= 600 mm from bathtub/shower edge"
    )
    is_mandatory = True
    regulatory_basis = "GOST R 50571"

    def validate(self, apartment: Apartment) -> RuleResult:
        bath_types = (
            RoomType.BATHROOM, RoomType.COMBINED_BATHROOM,
        )
        water_types = (
            FurnitureType.BATHTUB, FurnitureType.SHOWER,
        )
        electric_types = (
            FurnitureType.WASHING_MACHINE, FurnitureType.DRYER,
        )
        for room in _rooms_of_type(apartment, *bath_types):
            water = items_of_type(room, *water_types)
            electric = items_of_type(room, *electric_types)
            for w in water:
                for e in electric:
                    dist = distance_between_items(w, e)
                    if dist < CLEARANCES["outlet_from_water"]:
                        return self._fail(
                            f"Outlet {dist:.0f} mm "
                            f"from water < 600 mm",
                            {
                                "water_id": w.id,
                                "electric_id": e.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Outlet distance OK")


# ========== Kitchen (F06-F13) ==========


class F06KitchenTriangle(RuleValidator):
    rule_id = "F06"
    name = "Kitchen work triangle"
    description = "Triangle perimeter 3500-8000 mm"
    is_mandatory = False
    regulatory_basis = "Neufert"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            perim = kitchen_triangle_perimeter(room)
            if perim is None:
                return self._skip(
                    "Missing sink, stove, or fridge",
                )
            mn = KITCHEN_TRIANGLE["perimeter_min"]
            mx = KITCHEN_TRIANGLE["perimeter_max"]
            if perim < mn:
                return self._fail(
                    f"Triangle perimeter "
                    f"{perim:.0f} mm < 3500 mm",
                    {"perimeter": perim},
                )
            if perim > mx:
                return self._fail(
                    f"Triangle perimeter "
                    f"{perim:.0f} mm > 8000 mm",
                    {"perimeter": perim},
                )
        return self._pass("Kitchen triangle OK")


class F07SinkStoveDistance(RuleValidator):
    rule_id = "F07"
    name = "Sink-stove distance"
    description = "Distance between sink and stove 800-2000 mm"
    is_mandatory = False
    regulatory_basis = "Neufert"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            sinks = items_of_type(
                room, FurnitureType.KITCHEN_SINK,
            )
            stoves = items_of_type(
                room, FurnitureType.STOVE, FurnitureType.HOB,
            )
            for s in sinks:
                for st in stoves:
                    sc = s.bounding_box.center
                    stc = st.bounding_box.center
                    dist = sc.distance_to(stc)
                    mn = KITCHEN_TRIANGLE["sink_stove_min"]
                    mx = KITCHEN_TRIANGLE["sink_stove_max"]
                    if dist < mn:
                        return self._fail(
                            f"Sink-stove {dist:.0f} mm "
                            f"< 800 mm",
                        )
                    if dist > mx:
                        return self._fail(
                            f"Sink-stove {dist:.0f} mm "
                            f"> 2000 mm",
                        )
        return self._pass("Sink-stove distance OK")


class F08StoveWallDistance(RuleValidator):
    rule_id = "F08"
    name = "Stove-wall distance"
    description = "Stove to side wall >= 200 mm"
    is_mandatory = False
    regulatory_basis = "Fire safety"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            for stove in items_of_type(
                room, FurnitureType.STOVE, FurnitureType.HOB,
            ):
                bb = stove.bounding_box
                room_bb = room.boundary.bounding_box
                left = bb.x - room_bb.x
                right = (
                    room_bb.x + room_bb.width
                ) - (bb.x + bb.width)
                dist = min(left, right)
                if dist < CLEARANCES["stove_side_wall"]:
                    return self._fail(
                        f"Stove-wall {dist:.0f} mm < 200 mm",
                        {
                            "item_id": stove.id,
                            "distance": dist,
                        },
                    )
        return self._pass("Stove-wall distance OK")


class F09StoveWindowDistance(RuleValidator):
    rule_id = "F09"
    name = "Stove-window distance"
    description = "Stove to window >= 450 mm"
    is_mandatory = True
    regulatory_basis = "Fire safety"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            stoves = items_of_type(
                room, FurnitureType.STOVE, FurnitureType.HOB,
            )
            for stove in stoves:
                sc = stove.bounding_box.center
                for window in room.windows:
                    dist = sc.distance_to(window.position)
                    if dist < CLEARANCES["stove_window"]:
                        return self._fail(
                            f"Stove-window "
                            f"{dist:.0f} mm < 450 mm",
                            {
                                "stove_id": stove.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Stove-window distance OK")


class F10HoodGasStove(RuleValidator):
    rule_id = "F10"
    name = "Hood height above gas stove"
    description = "Hood >= 750 mm above gas stove"
    is_mandatory = True
    regulatory_basis = "SP"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            stoves = items_of_type(
                room, FurnitureType.STOVE,
            )
            hoods = items_of_type(room, FurnitureType.HOOD)
            if not stoves or not hoods:
                return self._skip("No gas stove or hood")
        return self._pass("Hood-gas stove height OK")


class F11HoodElectricStove(RuleValidator):
    rule_id = "F11"
    name = "Hood height above electric stove"
    description = "Hood >= 650 mm above electric stove"
    is_mandatory = True
    regulatory_basis = "SP"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            hobs = items_of_type(room, FurnitureType.HOB)
            hoods = items_of_type(room, FurnitureType.HOOD)
            if not hobs or not hoods:
                return self._skip("No electric hob or hood")
        return self._pass("Hood-electric stove height OK")


class F12FridgeStoveDistance(RuleValidator):
    rule_id = "F12"
    name = "Fridge-stove distance"
    description = "Fridge to stove >= 300 mm"
    is_mandatory = False
    regulatory_basis = "Practice"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            fridges = items_of_type(
                room, FurnitureType.FRIDGE,
                FurnitureType.FRIDGE_SIDE_BY_SIDE,
            )
            stoves = items_of_type(
                room, FurnitureType.STOVE, FurnitureType.HOB,
            )
            for f in fridges:
                for s in stoves:
                    dist = distance_between_items(f, s)
                    if dist < CLEARANCES["fridge_stove"]:
                        return self._fail(
                            f"Fridge-stove "
                            f"{dist:.0f} mm < 300 mm",
                            {
                                "fridge_id": f.id,
                                "stove_id": s.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Fridge-stove distance OK")


class F13KitchenParallelRows(RuleValidator):
    rule_id = "F13"
    name = "Kitchen parallel rows"
    description = (
        "Distance between parallel kitchen rows >= 1200 mm"
    )
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        kitchen_items = (
            FurnitureType.KITCHEN_SINK, FurnitureType.STOVE,
            FurnitureType.HOB, FurnitureType.FRIDGE,
            FurnitureType.DISHWASHER, FurnitureType.OVEN,
        )
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            items = items_of_type(room, *kitchen_items)
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    dist = distance_between_items(
                        items[i], items[j],
                    )
                    mn = CLEARANCES["kitchen_rows_parallel"]
                    if 0 < dist < mn:
                        bb_i = items[i].bounding_box
                        bb_j = items[j].bounding_box
                        same_row = not (
                            bb_i.y + bb_i.height <= bb_j.y
                            or bb_j.y + bb_j.height <= bb_i.y
                        )
                        if same_row:
                            continue
                        return self._fail(
                            f"Kitchen rows "
                            f"{dist:.0f} mm apart < 1200 mm",
                            {"distance": dist},
                        )
        return self._pass("Kitchen parallel rows OK")


# ========== Bedroom (F14-F16) ==========


class F14BedPassage(RuleValidator):
    rule_id = "F14"
    name = "Bed passage"
    description = (
        "Passage around double bed >= 700 mm on 3 sides"
    )
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.BEDROOM, RoomType.CHILDREN,
        ):
            for bed in items_of_type(
                room, FurnitureType.BED_DOUBLE,
                FurnitureType.BED_KING,
            ):
                bb = bed.bounding_box
                dist = nearest_wall_distance(bb, room)
                mn = CLEARANCES["bed_passage_double"]
                if dist < mn:
                    return self._fail(
                        f"Bed passage "
                        f"{dist:.0f} mm < 700 mm",
                        {"bed_id": bed.id, "distance": dist},
                    )
            for bed in items_of_type(
                room, FurnitureType.BED_SINGLE,
            ):
                bb = bed.bounding_box
                room_w_mm = room.width_m * 1000
                left_gap = bb.x
                right_gap = room_w_mm - (bb.x + bb.width)
                mn = CLEARANCES["bed_passage_double"]
                if max(left_gap, right_gap) < mn:
                    return self._fail(
                        "Single bed no accessible side",
                        {"bed_id": bed.id},
                    )
        return self._pass("Bed passages OK")


class F15SwingWardrobeClearance(RuleValidator):
    rule_id = "F15"
    name = "Swing wardrobe clearance"
    description = (
        "Space in front of swing wardrobe >= 800 mm"
    )
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            for ward in items_of_type(
                room, FurnitureType.WARDROBE_SWING,
            ):
                cl = clearance_in_front(ward, room)
                mn = CLEARANCES["wardrobe_swing_front"]
                if cl < mn:
                    return self._fail(
                        f"Wardrobe clearance "
                        f"{cl:.0f} mm < 800 mm",
                        {"item_id": ward.id, "clearance": cl},
                    )
        return self._pass("Wardrobe clearance OK")


class F16DrawersClearance(RuleValidator):
    rule_id = "F16"
    name = "Drawers clearance"
    description = "Space in front of drawers >= 800 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            for dresser in items_of_type(
                room, FurnitureType.DRESSER,
            ):
                cl = clearance_in_front(dresser, room)
                if cl < CLEARANCES["drawers_front"]:
                    return self._fail(
                        f"Drawers clearance "
                        f"{cl:.0f} mm < 800 mm",
                        {
                            "item_id": dresser.id,
                            "clearance": cl,
                        },
                    )
        return self._pass("Drawers clearance OK")


# ========== Safety (F17-F18) ==========


class F17OvenClearance(RuleValidator):
    rule_id = "F17"
    name = "Oven clearance"
    description = "Space in front of oven >= 800 mm"
    is_mandatory = True
    regulatory_basis = "Safety"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.KITCHEN,
            RoomType.KITCHEN_DINING,
        ):
            for oven in items_of_type(
                room, FurnitureType.OVEN,
            ):
                cl = clearance_in_front(oven, room)
                if cl < CLEARANCES["oven_front"]:
                    return self._fail(
                        f"Oven clearance "
                        f"{cl:.0f} mm < 800 mm",
                        {"item_id": oven.id, "clearance": cl},
                    )
        return self._pass("Oven clearance OK")


class F18MinPassage(RuleValidator):
    rule_id = "F18"
    name = "Minimum passage"
    description = "Passage between furniture/wall >= 700 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        mn = CLEARANCES["passage_min"]
        for room in apartment.rooms:
            segs = wall_segments(room)
            for item in room.furniture:
                bb = item.bounding_box
                for seg in segs:
                    dist = min_distance_rect_to_segment(
                        bb, seg,
                    )
                    if 0 < dist < mn:
                        return self._fail(
                            f"Passage {dist:.0f} mm "
                            f"< 700 mm",
                            {
                                "item_id": item.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Passages OK")


# ========== Dining (F19-F20) ==========


class F19TableWallPassage(RuleValidator):
    rule_id = "F19"
    name = "Table-wall passage"
    description = "Behind chair to wall >= 900 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            for table in items_of_type(
                room, FurnitureType.DINING_TABLE,
            ):
                dist = nearest_wall_distance(
                    table.bounding_box, room,
                )
                if dist < CLEARANCES["table_wall_passage"]:
                    return self._fail(
                        f"Table-wall "
                        f"{dist:.0f} mm < 900 mm",
                        {
                            "table_id": table.id,
                            "distance": dist,
                        },
                    )
        return self._pass("Table-wall passages OK")


class F20ShelfHeight(RuleValidator):
    rule_id = "F20"
    name = "Shelf height"
    description = "Top shelf <= 1900 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        shelf_types = (
            FurnitureType.SHELVING, FurnitureType.BOOKSHELF,
        )
        for room in apartment.rooms:
            for shelf in items_of_type(room, *shelf_types):
                h = FURNITURE_SIZES.get(
                    shelf.furniture_type, (0, 0, 0),
                )[2]
                if h > CLEARANCES["shelf_max_height"]:
                    return self._fail(
                        f"Shelf height "
                        f"{h:.0f} mm > 1900 mm",
                        {"item_id": shelf.id, "height": h},
                    )
        return self._pass("Shelf heights OK")


# ========== Living room (F21-F29) ==========


class F21SofaArmchairDistance(RuleValidator):
    rule_id = "F21"
    name = "Sofa-armchair distance"
    description = "Distance sofa to armchair <= 2000 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        sofa_types = (
            FurnitureType.SOFA_2, FurnitureType.SOFA_3,
            FurnitureType.SOFA_4, FurnitureType.SOFA_CORNER,
        )
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            sofas = items_of_type(room, *sofa_types)
            chairs = items_of_type(
                room, FurnitureType.ARMCHAIR,
            )
            for s in sofas:
                for c in chairs:
                    dist = distance_between_items(s, c)
                    mx = CLEARANCES["sofa_armchair_max"]
                    if dist > mx:
                        return self._fail(
                            f"Sofa-armchair "
                            f"{dist:.0f} mm > 2000 mm",
                            {
                                "sofa_id": s.id,
                                "chair_id": c.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Sofa-armchair distance OK")


class F22ArmchairsApart(RuleValidator):
    rule_id = "F22"
    name = "Armchairs apart"
    description = "Distance between armchairs ~1050 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            chairs = items_of_type(
                room, FurnitureType.ARMCHAIR,
            )
            for i in range(len(chairs)):
                for j in range(i + 1, len(chairs)):
                    dist = distance_between_items(
                        chairs[i], chairs[j],
                    )
                    mn = CLEARANCES["armchairs_apart"]
                    if dist < mn:
                        return self._fail(
                            f"Armchairs "
                            f"{dist:.0f} mm apart "
                            f"< 1050 mm",
                            {"distance": dist},
                        )
        return self._pass("Armchairs spacing OK")


class F23WallFurnitureGap(RuleValidator):
    rule_id = "F23"
    name = "Wall-furniture gap"
    description = (
        "Non-perimeter furniture to wall >= 900 mm"
    )
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        non_wall_types = (
            FurnitureType.COFFEE_TABLE,
            FurnitureType.ARMCHAIR,
        )
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            for item in items_of_type(room, *non_wall_types):
                dist = nearest_wall_distance(
                    item.bounding_box, room,
                )
                mn = CLEARANCES["wall_furniture_not_perimeter"]
                if dist < mn:
                    return self._fail(
                        f"Wall-furniture "
                        f"{dist:.0f} mm < 900 mm",
                        {
                            "item_id": item.id,
                            "distance": dist,
                        },
                    )
        return self._pass("Wall-furniture gaps OK")


class F24CarpetWall(RuleValidator):
    rule_id = "F24"
    name = "Carpet-wall distance"
    description = "Carpet edge to wall >= 600 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            for item in items_of_type(
                room, FurnitureType.COFFEE_TABLE,
            ):
                dist = nearest_wall_distance(
                    item.bounding_box, room,
                )
                if dist < CLEARANCES["carpet_wall"]:
                    return self._fail(
                        f"Carpet-wall "
                        f"{dist:.0f} mm < 600 mm",
                        {
                            "item_id": item.id,
                            "distance": dist,
                        },
                    )
        return self._pass("Carpet-wall OK")


class F25ShelvingFurnitureGap(RuleValidator):
    rule_id = "F25"
    name = "Shelving-furniture gap"
    description = "Shelving to other furniture >= 800 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        shelf_types = (
            FurnitureType.SHELVING, FurnitureType.BOOKSHELF,
        )
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            shelves = items_of_type(room, *shelf_types)
            others = [
                f for f in room.furniture
                if f.furniture_type not in shelf_types
            ]
            for sh in shelves:
                for ot in others:
                    dist = distance_between_items(sh, ot)
                    mn = CLEARANCES[
                        "shelving_other_furniture"
                    ]
                    if dist < mn:
                        return self._fail(
                            f"Shelving-furniture "
                            f"{dist:.0f} mm < 800 mm",
                            {
                                "shelf_id": sh.id,
                                "other_id": ot.id,
                                "distance": dist,
                            },
                        )
        return self._pass("Shelving gaps OK")


class F26LivingRoomFurnitureRatio(RuleValidator):
    rule_id = "F26"
    name = "Living room furniture ratio"
    description = "Furniture area / room area <= 35%"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        max_ratio = CLEARANCES[
            "living_room_max_furniture_ratio"
        ]
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            if room.area_m2 == 0:
                continue
            ratio = 1.0 - room.free_area_ratio
            if ratio > max_ratio:
                return self._fail(
                    f"Furniture ratio "
                    f"{ratio:.0%} > {max_ratio:.0%}",
                    {"room_id": room.id, "ratio": ratio},
                )
        return self._pass("Furniture ratio OK")


class F27TVNotFacingWindow(RuleValidator):
    rule_id = "F27"
    name = "TV not facing window"
    description = "TV should not face window"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            tvs = items_of_type(room, FurnitureType.TV_STAND)
            for tv in tvs:
                tv_bb = tv.bounding_box
                room_h = room.height_m * 1000
                for window in room.windows:
                    tv_far = tv_bb.y > room_h * 0.7
                    win_near = window.position.y < room_h * 0.3
                    if tv_far and win_near:
                        return self._fail(
                            "TV faces window",
                            {"tv_id": tv.id},
                        )
        return self._pass("TV placement OK")


class F28SofaBedLength(RuleValidator):
    rule_id = "F28"
    name = "Sofa bed length"
    description = "Sofa bed sleeping area >= 2000 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        sofa_types = (
            FurnitureType.SOFA_2, FurnitureType.SOFA_3,
            FurnitureType.SOFA_4,
        )
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            for sofa in items_of_type(room, *sofa_types):
                if sofa.width < 2000:
                    return self._fail(
                        f"Sofa bed length "
                        f"{sofa.width:.0f} mm < 2000 mm",
                        {
                            "sofa_id": sofa.id,
                            "length": sofa.width,
                        },
                    )
        return self._pass("Sofa bed length OK")


class F29ArmchairSeatWidth(RuleValidator):
    rule_id = "F29"
    name = "Armchair seat width"
    description = "Armchair seat width >= 480 mm"
    is_mandatory = False
    regulatory_basis = "rules.docx"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            for chair in items_of_type(
                room, FurnitureType.ARMCHAIR,
            ):
                seat_width = chair.width * 0.6
                if seat_width < 480:
                    return self._fail(
                        f"Armchair seat "
                        f"{seat_width:.0f} mm < 480 mm",
                        {
                            "chair_id": chair.id,
                            "seat_width": seat_width,
                        },
                    )
        return self._pass("Armchair seats OK")


# ========== Entry/utility (F30-F32) ==========


class F30EntryZone(RuleValidator):
    rule_id = "F30"
    name = "Entry zone"
    description = "Free zone at entrance >= 600x800 mm"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    def validate(self, apartment: Apartment) -> RuleResult:
        from floorplan_generator.core.enums import DoorType

        for room in _rooms_of_type(
            apartment, RoomType.HALLWAY, RoomType.HALL,
        ):
            has_entry = any(
                d.door_type == DoorType.ENTRANCE
                for d in room.doors
            )
            if not has_entry:
                continue
            bb = room.boundary.bounding_box
            room_w = bb.width
            room_h = bb.height
            min_w = CLEARANCES["entry_zone_width"]
            min_d = CLEARANCES["entry_zone_depth"]
            if room_w < min_w or room_h < min_d:
                return self._fail(
                    f"Entry zone too small "
                    f"({room_w:.0f}x{room_h:.0f} mm)",
                    {"width": room_w, "height": room_h},
                )
        return self._pass("Entry zone OK")


class F31WasherBackGap(RuleValidator):
    rule_id = "F31"
    name = "Washer back gap"
    description = "Gap behind washing machine >= 50 mm"
    is_mandatory = True
    regulatory_basis = "Technical"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in apartment.rooms:
            for washer in items_of_type(
                room, FurnitureType.WASHING_MACHINE,
            ):
                bb = washer.bounding_box
                back_dist = bb.y
                if back_dist < CLEARANCES["washer_back_gap"]:
                    return self._fail(
                        f"Washer back gap "
                        f"{back_dist:.0f} mm < 50 mm",
                        {
                            "washer_id": washer.id,
                            "gap": back_dist,
                        },
                    )
        return self._pass("Washer gap OK")


class F32ToiletRiserDistance(RuleValidator):
    rule_id = "F32"
    name = "Toilet-riser distance"
    description = "Toilet to riser <= 1000 mm"
    is_mandatory = True
    regulatory_basis = "SP"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.TOILET,
            RoomType.BATHROOM,
            RoomType.COMBINED_BATHROOM,
        ):
            for toilet in items_of_type(
                room, FurnitureType.TOILET_BOWL,
            ):
                riser = room.boundary.points[0]
                tc = toilet.bounding_box.center
                dist = tc.distance_to(riser)
                mx = CLEARANCES["toilet_riser_max"]
                if dist > mx:
                    return self._fail(
                        f"Toilet-riser "
                        f"{dist:.0f} mm > 1000 mm",
                        {
                            "toilet_id": toilet.id,
                            "distance": dist,
                        },
                    )
        return self._pass("Toilet-riser OK")


class F33TVFacesSofa(RuleValidator):
    rule_id = "F33"
    name = "TV faces sofa"
    description = "TV stand should be on the wall opposite the sofa"
    is_mandatory = False
    regulatory_basis = "Ergonomics"

    _SOFA_TYPES = (
        FurnitureType.SOFA_2, FurnitureType.SOFA_3,
        FurnitureType.SOFA_4, FurnitureType.SOFA_CORNER,
    )

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment, RoomType.LIVING_ROOM,
        ):
            tvs = items_of_type(
                room, FurnitureType.TV_STAND,
            )
            sofas = items_of_type(room, *self._SOFA_TYPES)
            if not tvs or not sofas:
                continue
            for tv in tvs:
                facing = any(
                    abs(tv.rotation - s.rotation) == 180
                    for s in sofas
                )
                if not facing:
                    return self._fail(
                        "TV not facing sofa",
                        {"tv_id": tv.id},
                    )
        return self._pass("TV faces sofa OK")


# ========== Bathroom essentials (F34) ==========

# Required fixtures per bathroom room type.
_BATHROOM_ESSENTIALS: dict[
    RoomType, list[tuple[str, tuple[FurnitureType, ...]]],
] = {
    RoomType.BATHROOM: [
        ("bathtub/shower", (
            FurnitureType.BATHTUB, FurnitureType.SHOWER,
        )),
        ("sink", (
            FurnitureType.SINK, FurnitureType.DOUBLE_SINK,
        )),
    ],
    RoomType.COMBINED_BATHROOM: [
        ("bathtub/shower", (
            FurnitureType.BATHTUB, FurnitureType.SHOWER,
        )),
        ("sink", (
            FurnitureType.SINK, FurnitureType.DOUBLE_SINK,
        )),
        ("toilet", (FurnitureType.TOILET_BOWL,)),
    ],
    RoomType.TOILET: [
        ("toilet", (FurnitureType.TOILET_BOWL,)),
    ],
}


class F34BathroomEssentials(RuleValidator):
    rule_id = "F34"
    name = "Bathroom essential fixtures"
    description = (
        "Bathrooms must contain essential plumbing: "
        "bathtub/shower + sink; combined bathroom adds toilet"
    )
    is_mandatory = True
    regulatory_basis = "SP 54.13330"

    def validate(self, apartment: Apartment) -> RuleResult:
        for room in _rooms_of_type(
            apartment,
            RoomType.BATHROOM,
            RoomType.COMBINED_BATHROOM,
            RoomType.TOILET,
        ):
            reqs = _BATHROOM_ESSENTIALS.get(room.room_type, [])
            for label, types in reqs:
                if not items_of_type(room, *types):
                    return self._fail(
                        f"{room.room_type.value} missing {label}",
                        {"room_id": room.id},
                    )
        return self._pass("Bathroom essentials OK")
