"""Unit tests for planning rules (P01–P34)."""

from floorplan_generator.rules.planning_rules import (
    P01LivingRoomArea1Room,
    P02LivingRoomArea2Plus,
    P03BedroomArea1Person,
    P04BedroomArea2Person,
    P05KitchenArea,
    P06KitchenWidth,
    P07CorridorWidth,
    P08HallwayWidth,
    P09BathroomWidth,
    P10CombinedBathroomWidth,
    P11AspectRatio,
    P12WindowsInLivingRooms,
    P13WindowsInKitchen,
    P14WindowAreaRatio,
    P15ToiletNotFromKitchen,
    P16AdjacencyMatrix,
    P17NonPassthroughBedrooms,
    P18MandatoryComposition,
    P19ZoneSeparation,
    P20EntranceDoorWidth,
    P21BathroomDoorOutward,
    P22DoorsNotCollide,
    P23DoorWallGap,
    P24WetZonesGrouped,
    P25EnsuiteCondition,
    P26LivingRoomMinWidth,
    P27LivingRoomCentral,
    P28DiningNotFacingEntry,
    P29RoomHeight,
    P30CorridorHeight,
    P31SanitaryAboveLiving,
    P32Insolation,
    P33Waterproofing,
    P34Ventilation,
)

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point
from floorplan_generator.rules.rule_engine import RuleStatus

# --- P01: Min living room area (1-room) ---

def test_p01_living_room_14sqm_pass(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=3.5)  # 14 m²
    apt = make_apartment(ApartmentClass.ECONOMY, [living], num_rooms=1)
    result = P01LivingRoomArea1Room().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p01_living_room_13sqm_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=3.25, height_m=4.0)  # 13 m²
    apt = make_apartment(ApartmentClass.ECONOMY, [living], num_rooms=1)
    result = P01LivingRoomArea1Room().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p01_living_room_14sqm_in_2room_not_applied(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=3.5)  # 14 m²
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=2)
    result = P01LivingRoomArea1Room().validate(apt)
    assert result.status == RuleStatus.SKIP


# --- P02: Min living room area (2+ rooms) ---

def test_p02_living_room_16sqm_pass(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=4.0)  # 16 m²
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=2)
    result = P02LivingRoomArea2Plus().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p02_living_room_15sqm_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=3.1, height_m=5.0)  # 15.5 m²
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=2)
    result = P02LivingRoomArea2Plus().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P03: Min bedroom area (1 person) ---

def test_p03_bedroom_8sqm_pass(make_room, make_apartment):
    bedroom = make_room(RoomType.BEDROOM, width_m=2.0, height_m=4.0)  # 8 m²
    apt = make_apartment(ApartmentClass.COMFORT, [bedroom], num_rooms=1)
    result = P03BedroomArea1Person().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p03_bedroom_7sqm_fail(make_room, make_apartment):
    bedroom = make_room(RoomType.BEDROOM, width_m=2.5, height_m=3.0)  # 7.5 m²
    apt = make_apartment(ApartmentClass.COMFORT, [bedroom], num_rooms=1)
    result = P03BedroomArea1Person().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P04: Min bedroom area (2 persons) ---

def test_p04_bedroom_10sqm_pass(make_room, make_apartment):
    bedroom = make_room(RoomType.BEDROOM, width_m=2.5, height_m=4.0)  # 10 m²
    apt = make_apartment(ApartmentClass.COMFORT, [bedroom], num_rooms=2)
    result = P04BedroomArea2Person().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p04_bedroom_9sqm_fail(make_room, make_apartment):
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=3.0)  # 9 m²
    apt = make_apartment(ApartmentClass.COMFORT, [bedroom], num_rooms=2)
    result = P04BedroomArea2Person().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P05: Min kitchen area ---

def test_p05_kitchen_8sqm_pass(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=2.0, height_m=4.0)  # 8 m²
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=2)
    result = P05KitchenArea().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p05_kitchen_7sqm_fail(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=2.0, height_m=3.5)  # 7 m²
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=2)
    result = P05KitchenArea().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p05_kitchen_5sqm_1room_pass(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=2.5, height_m=2.0)  # 5 m²
    apt = make_apartment(ApartmentClass.ECONOMY, [kitchen], num_rooms=1)
    result = P05KitchenArea().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p05_kitchen_4sqm_1room_fail(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=2.0, height_m=2.0)  # 4 m²
    apt = make_apartment(ApartmentClass.ECONOMY, [kitchen], num_rooms=1)
    result = P05KitchenArea().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P06: Min kitchen width ---

def test_p06_kitchen_width_1700_pass(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=1.7, height_m=4.0)
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=1)
    result = P06KitchenWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p06_kitchen_width_1600_fail(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=1.6, height_m=4.0)
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=1)
    result = P06KitchenWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P07: Min corridor width ---

def test_p07_corridor_width_850_pass(make_room, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=0.85, height_m=1.4)
    apt = make_apartment(ApartmentClass.COMFORT, [corridor], num_rooms=1)
    result = P07CorridorWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p07_corridor_width_800_fail(make_room, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=0.8, height_m=1.4)
    apt = make_apartment(ApartmentClass.COMFORT, [corridor], num_rooms=1)
    result = P07CorridorWidth().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p07_corridor_long_1000_pass(make_room, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [corridor], num_rooms=1)
    result = P07CorridorWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p07_corridor_long_900_fail(make_room, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=0.9, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [corridor], num_rooms=1)
    result = P07CorridorWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P08: Min hallway width ---

def test_p08_hallway_1400_pass(make_room, make_apartment):
    hallway = make_room(RoomType.HALLWAY, width_m=1.4, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [hallway], num_rooms=1)
    result = P08HallwayWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p08_hallway_1300_fail(make_room, make_apartment):
    hallway = make_room(RoomType.HALLWAY, width_m=1.3, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [hallway], num_rooms=1)
    result = P08HallwayWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P09: Min bathroom width ---

def test_p09_bathroom_1500_pass(make_room, make_apartment):
    bathroom = make_room(RoomType.BATHROOM, width_m=1.5, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [bathroom], num_rooms=1)
    result = P09BathroomWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p09_bathroom_1400_fail(make_room, make_apartment):
    bathroom = make_room(RoomType.BATHROOM, width_m=1.4, height_m=2.0)
    apt = make_apartment(ApartmentClass.COMFORT, [bathroom], num_rooms=1)
    result = P09BathroomWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P10: Min combined bathroom width ---

def test_p10_combined_bath_1700_pass(make_room, make_apartment):
    bathroom = make_room(
        RoomType.COMBINED_BATHROOM, width_m=1.7, height_m=2.0,
    )
    apt = make_apartment(ApartmentClass.COMFORT, [bathroom], num_rooms=1)
    result = P10CombinedBathroomWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p10_combined_bath_1600_fail(make_room, make_apartment):
    bathroom = make_room(
        RoomType.COMBINED_BATHROOM, width_m=1.6, height_m=2.0,
    )
    apt = make_apartment(ApartmentClass.COMFORT, [bathroom], num_rooms=1)
    result = P10CombinedBathroomWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P11: Aspect ratio ---

def test_p11_aspect_ratio_1_5_pass(make_room, make_apartment):
    room = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=6.0)  # 1:1.5
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P11AspectRatio().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p11_aspect_ratio_2_5_fail(make_room, make_apartment):
    room = make_room(RoomType.LIVING_ROOM, width_m=3.0, height_m=7.5)  # 1:2.5
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P11AspectRatio().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p11_aspect_ratio_2_0_edge(make_room, make_apartment):
    room = make_room(RoomType.LIVING_ROOM, width_m=3.0, height_m=6.0)  # 1:2.0
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P11AspectRatio().validate(apt)
    assert result.status == RuleStatus.PASS  # edge case, 2.0 is allowed


# --- P12: Windows in living rooms ---

def test_p12_living_room_has_window_pass(
    make_room, make_window, make_apartment,
):
    living = make_room(
        RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0,
        windows=[make_window()],
    )
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P12WindowsInLivingRooms().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p12_living_room_no_window_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P12WindowsInLivingRooms().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p12_corridor_no_window_pass(make_room, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    apt = make_apartment(ApartmentClass.COMFORT, [corridor], num_rooms=1)
    result = P12WindowsInLivingRooms().validate(apt)
    assert result.status == RuleStatus.PASS


# --- P13: Windows in kitchen ---

def test_p13_kitchen_has_window_pass(
    make_room, make_window, make_apartment,
):
    kitchen = make_room(
        RoomType.KITCHEN, width_m=3.0, height_m=3.0,
        windows=[make_window()],
    )
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=1)
    result = P13WindowsInKitchen().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p13_kitchen_no_window_fail(make_room, make_apartment):
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    apt = make_apartment(ApartmentClass.COMFORT, [kitchen], num_rooms=1)
    result = P13WindowsInKitchen().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p13_kitchen_niche_no_window_pass(make_room, make_apartment):
    kitchen_niche = make_room(
        RoomType.KITCHEN_NICHE, width_m=2.0, height_m=2.5,
    )
    apt = make_apartment(ApartmentClass.ECONOMY, [kitchen_niche], num_rooms=1)
    result = P13WindowsInKitchen().validate(apt)
    assert result.status == RuleStatus.PASS


# --- P14: Window area ratio ---

def test_p14_window_area_ratio_pass(
    make_room, make_window, make_apartment,
):
    # Window 2.5 m² in room 18 m² -> 1/7.2 > 1/8
    window = make_window(width=1667.0, height=1500.0)  # ~2.5 m²
    room = make_room(
        RoomType.LIVING_ROOM, width_m=4.5, height_m=4.0,
        windows=[window],
    )
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P14WindowAreaRatio().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p14_window_area_ratio_fail(
    make_room, make_window, make_apartment,
):
    # Window 1.5 m² in room 18 m² -> 1/12 < 1/8
    window = make_window(width=1000.0, height=1500.0)  # 1.5 m²
    room = make_room(
        RoomType.LIVING_ROOM, width_m=4.5, height_m=4.0,
        windows=[window],
    )
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P14WindowAreaRatio().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p14_multiple_windows_sum(
    make_room, make_window, make_apartment,
):
    # Two windows of 1.3 m² each = 2.6 m² in room 18 m² -> 1/6.9 > 1/8
    w1 = make_window(width=1000.0, height=1300.0)  # 1.3 m²
    w2 = make_window(width=1000.0, height=1300.0)  # 1.3 m²
    room = make_room(
        RoomType.LIVING_ROOM, width_m=4.5, height_m=4.0,
        windows=[w1, w2],
    )
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P14WindowAreaRatio().validate(apt)
    assert result.status == RuleStatus.PASS


# --- P15: Toilet not from kitchen ---

def test_p15_toilet_from_corridor_pass(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    toilet = make_room(RoomType.TOILET, width_m=1.0, height_m=1.5)
    door = make_door(room_from=corridor.id, room_to=toilet.id)
    corridor = corridor.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, toilet], num_rooms=1,
    )
    result = P15ToiletNotFromKitchen().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p15_toilet_from_kitchen_fail(
    make_room, make_door, make_apartment,
):
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    toilet = make_room(RoomType.TOILET, width_m=1.0, height_m=1.5)
    door = make_door(room_from=kitchen.id, room_to=toilet.id)
    kitchen = kitchen.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [kitchen, toilet], num_rooms=1,
    )
    result = P15ToiletNotFromKitchen().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P16: Adjacency matrix ---

def test_p16_hallway_to_corridor_pass(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    door = make_door(room_from=hallway.id, room_to=corridor.id)
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [hallway, corridor], num_rooms=1,
    )
    result = P16AdjacencyMatrix().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p16_bedroom_to_kitchen_fail(
    make_room, make_door, make_apartment,
):
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    door = make_door(room_from=bedroom.id, room_to=kitchen.id)
    bedroom = bedroom.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [bedroom, kitchen], num_rooms=1,
    )
    result = P16AdjacencyMatrix().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p16_bedroom_to_bathroom_conditional(
    make_room, make_door, make_apartment,
):
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    bath1 = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bath2 = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    d1 = make_door(room_from=bedroom.id, room_to=bath1.id)
    d2 = make_door(room_from=corridor.id, room_to=bath2.id)
    bedroom = bedroom.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [bedroom, bath1, corridor, bath2],
        num_rooms=1,
    )
    result = P16AdjacencyMatrix().validate(apt)
    assert result.status == RuleStatus.PASS


# --- P17: Non-passthrough bedrooms ---

def test_p17_bedroom_not_passthrough_pass(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    door = make_door(room_from=corridor.id, room_to=bedroom.id)
    corridor = corridor.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, bedroom], num_rooms=2,
    )
    result = P17NonPassthroughBedrooms().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p17_bedroom_passthrough_fail(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    d1 = make_door(room_from=corridor.id, room_to=bedroom.id)
    d2 = make_door(room_from=bedroom.id, room_to=living.id)
    corridor = corridor.model_copy(update={"doors": [d1]})
    bedroom = bedroom.model_copy(update={"doors": [d1, d2]})
    living = living.model_copy(update={"doors": [d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, bedroom, living], num_rooms=2,
    )
    result = P17NonPassthroughBedrooms().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p17_living_room_passthrough_ok(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    d1 = make_door(room_from=corridor.id, room_to=living.id)
    d2 = make_door(room_from=living.id, room_to=bedroom.id)
    corridor = corridor.model_copy(update={"doors": [d1]})
    living = living.model_copy(update={"doors": [d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, living, bedroom], num_rooms=2,
    )
    result = P17NonPassthroughBedrooms().validate(apt)
    assert result.status == RuleStatus.PASS


# --- P18: Mandatory composition ---

def test_p18_full_composition_pass(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [living, kitchen, bathroom, hallway],
        num_rooms=1,
    )
    result = P18MandatoryComposition().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p18_no_kitchen_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    apt = make_apartment(
        ApartmentClass.COMFORT, [living, bathroom, hallway], num_rooms=1,
    )
    result = P18MandatoryComposition().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p18_no_bathroom_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    apt = make_apartment(
        ApartmentClass.COMFORT, [living, kitchen, hallway], num_rooms=1,
    )
    result = P18MandatoryComposition().validate(apt)
    assert result.status == RuleStatus.FAIL

def test_p18_no_hallway_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    apt = make_apartment(
        ApartmentClass.COMFORT, [living, kitchen, bathroom], num_rooms=1,
    )
    result = P18MandatoryComposition().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P19: Zone separation ---

def test_p19_zones_separated_pass(make_room, make_door, make_apartment):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    d1 = make_door(room_from=hallway.id, room_to=corridor.id)
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(room_from=corridor.id, room_to=bedroom.id)
    d4 = make_door(room_from=corridor.id, room_to=kitchen.id)
    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2, d3, d4]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [hallway, corridor, living, bedroom, kitchen],
        num_rooms=2,
    )
    result = P19ZoneSeparation().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p19_transit_through_night_fail(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    d1 = make_door(room_from=hallway.id, room_to=bedroom.id)
    d2 = make_door(room_from=bedroom.id, room_to=kitchen.id)
    hallway = hallway.model_copy(update={"doors": [d1]})
    bedroom = bedroom.model_copy(update={"doors": [d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [hallway, bedroom, kitchen],
        num_rooms=2,
    )
    result = P19ZoneSeparation().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P20: Entrance door width ---

def test_p20_entrance_door_800_pass(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    door = make_door(
        door_type=DoorType.ENTRANCE, width=860.0,
        room_from="outside", room_to=hallway.id,
    )
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [hallway], num_rooms=1)
    result = P20EntranceDoorWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p20_entrance_door_700_fail(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    door = make_door(
        door_type=DoorType.ENTRANCE, width=700.0,
        room_from="outside", room_to=hallway.id,
    )
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [hallway], num_rooms=1)
    result = P20EntranceDoorWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P21: Bathroom door outward ---

def test_p21_bathroom_door_outward_pass(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    door = make_door(
        door_type=DoorType.BATHROOM, swing=SwingDirection.OUTWARD,
        room_from=corridor.id, room_to=bathroom.id,
    )
    corridor = corridor.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, bathroom], num_rooms=1,
    )
    result = P21BathroomDoorOutward().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p21_bathroom_door_inward_fail(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    door = make_door(
        door_type=DoorType.BATHROOM, swing=SwingDirection.INWARD,
        room_from=corridor.id, room_to=bathroom.id,
    )
    corridor = corridor.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [corridor, bathroom], num_rooms=1,
    )
    result = P21BathroomDoorOutward().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P22: Doors not collide ---

def test_p22_doors_not_collide_pass(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=3.0, height_m=3.0)
    room_a = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    room_b = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    d1 = make_door(
        position=Point(x=0, y=0),
        room_from=corridor.id, room_to=room_a.id,
    )
    d2 = make_door(
        position=Point(x=2000, y=0),
        room_from=corridor.id, room_to=room_b.id,
    )
    corridor = corridor.model_copy(update={"doors": [d1, d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [corridor, room_a, room_b],
        num_rooms=2,
    )
    result = P22DoorsNotCollide().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p22_doors_collide_fail(make_room, make_door, make_apartment):
    corridor = make_room(RoomType.CORRIDOR, width_m=3.0, height_m=3.0)
    room_a = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    room_b = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    d1 = make_door(
        position=Point(x=0, y=0),
        room_from=corridor.id, room_to=room_a.id,
    )
    d2 = make_door(
        position=Point(x=100, y=0),
        room_from=corridor.id, room_to=room_b.id,
    )
    corridor = corridor.model_copy(update={"doors": [d1, d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [corridor, room_a, room_b],
        num_rooms=2,
    )
    result = P22DoorsNotCollide().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P23: Door wall gap ---

def test_p23_door_wall_gap_100_pass(
    make_room, make_door, make_apartment,
):
    room = make_room(RoomType.CORRIDOR, width_m=3.0, height_m=3.0)
    door = make_door(
        position=Point(x=100, y=0),
        room_from=room.id, room_to="other",
    )
    room = room.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P23DoorWallGap().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p23_door_wall_gap_50_fail(
    make_room, make_door, make_apartment,
):
    room = make_room(RoomType.CORRIDOR, width_m=3.0, height_m=3.0)
    door = make_door(
        position=Point(x=50, y=0),
        room_from=room.id, room_to="other",
    )
    room = room.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [room], num_rooms=1)
    result = P23DoorWallGap().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P24: Wet zones grouped ---

def test_p24_wet_zones_grouped_pass(
    make_room, make_door, make_apartment,
):
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    d1 = make_door(room_from=corridor.id, room_to=kitchen.id)
    d2 = make_door(room_from=corridor.id, room_to=bathroom.id)
    corridor = corridor.model_copy(update={"doors": [d1, d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [kitchen, bathroom, corridor],
        num_rooms=1,
    )
    result = P24WetZonesGrouped().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p24_wet_zones_scattered_fail(
    make_room, make_door, make_apartment,
):
    kitchen = make_room(RoomType.KITCHEN, width_m=3.0, height_m=3.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    # kitchen connected to corridor, bathroom connected to living
    d1 = make_door(room_from=corridor.id, room_to=kitchen.id)
    d2 = make_door(room_from=corridor.id, room_to=living.id)
    d3 = make_door(room_from=living.id, room_to=bathroom.id)
    corridor = corridor.model_copy(update={"doors": [d1, d2]})
    living = living.model_copy(update={"doors": [d3]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [kitchen, bathroom, living, corridor],
        num_rooms=1,
    )
    result = P24WetZonesGrouped().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P25: Ensuite condition ---

def test_p25_ensuite_with_second_bathroom_pass(
    make_room, make_door, make_apartment,
):
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    bath1 = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    bath2 = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    d1 = make_door(
        room_from=bedroom.id, room_to=bath1.id,
        swing=SwingDirection.OUTWARD,
    )
    d2 = make_door(
        room_from=corridor.id, room_to=bath2.id,
        swing=SwingDirection.OUTWARD,
    )
    d3 = make_door(room_from=corridor.id, room_to=bedroom.id)
    bedroom = bedroom.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2, d3]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [corridor, bedroom, bath1, bath2],
        num_rooms=2,
    )
    result = P25EnsuiteCondition().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p25_ensuite_without_second_fail(
    make_room, make_door, make_apartment,
):
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    bathroom = make_room(RoomType.BATHROOM, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    d1 = make_door(
        room_from=bedroom.id, room_to=bathroom.id,
        swing=SwingDirection.OUTWARD,
    )
    d2 = make_door(room_from=corridor.id, room_to=bedroom.id)
    bedroom = bedroom.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [corridor, bedroom, bathroom],
        num_rooms=2,
    )
    result = P25EnsuiteCondition().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P26: Living room min width (recommended) ---

def test_p26_living_room_width_3200_pass(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=3.2, height_m=5.0)
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P26LivingRoomMinWidth().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p26_living_room_width_2800_fail(make_room, make_apartment):
    living = make_room(RoomType.LIVING_ROOM, width_m=2.8, height_m=5.0)
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P26LivingRoomMinWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P27: Living room central position ---

def test_p27_living_room_central_pass(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    door = make_door(room_from=hallway.id, room_to=living.id)
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(
        ApartmentClass.COMFORT, [hallway, living], num_rooms=1,
    )
    result = P27LivingRoomCentral().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p27_living_room_isolated_fail(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RoomType.HALLWAY, width_m=2.0, height_m=2.0)
    corridor = make_room(RoomType.CORRIDOR, width_m=1.0, height_m=3.0)
    bedroom = make_room(RoomType.BEDROOM, width_m=3.0, height_m=4.0)
    living = make_room(RoomType.LIVING_ROOM, width_m=4.0, height_m=5.0)
    d1 = make_door(room_from=hallway.id, room_to=corridor.id)
    d2 = make_door(room_from=corridor.id, room_to=bedroom.id)
    d3 = make_door(room_from=bedroom.id, room_to=living.id)
    hallway = hallway.model_copy(update={"doors": [d1]})
    corridor = corridor.model_copy(update={"doors": [d2]})
    bedroom = bedroom.model_copy(update={"doors": [d3]})
    apt = make_apartment(
        ApartmentClass.COMFORT,
        [hallway, corridor, bedroom, living],
        num_rooms=2,
    )
    result = P27LivingRoomCentral().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- P28: Dining not facing entry ---

def test_p28_dining_not_facing_entry_pass(
    make_room, make_door, make_furniture, make_apartment,
):
    living = make_room(
        RoomType.LIVING_ROOM, width_m=5.0, height_m=5.0,
        furniture=[
            make_furniture(FurnitureType.DINING_TABLE, x=3000, y=3000),
        ],
    )
    door = make_door(
        position=Point(x=0, y=0),
        room_from="corridor", room_to=living.id,
    )
    living = living.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P28DiningNotFacingEntry().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p28_dining_facing_entry_fail(
    make_room, make_door, make_furniture, make_apartment,
):
    living = make_room(
        RoomType.LIVING_ROOM, width_m=5.0, height_m=5.0,
        furniture=[
            make_furniture(
                FurnitureType.DINING_TABLE,
                x=0, y=100, width=1350, depth=850,
            ),
        ],
    )
    door = make_door(
        position=Point(x=0, y=0),
        room_from="corridor", room_to=living.id,
    )
    living = living.model_copy(update={"doors": [door]})
    apt = make_apartment(ApartmentClass.COMFORT, [living], num_rooms=1)
    result = P28DiningNotFacingEntry().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- Mock rules (P29-P34) ---

def test_p29_room_height_always_pass(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.LIVING_ROOM, 4.0, 5.0)],
        num_rooms=1,
    )
    result = P29RoomHeight().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p29_room_height_returns_mock_message(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.LIVING_ROOM, 4.0, 5.0)],
        num_rooms=1,
    )
    result = P29RoomHeight().validate(apt)
    assert "mock" in result.message.lower()

def test_p30_corridor_height_always_pass(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.CORRIDOR, 1.0, 3.0)],
        num_rooms=1,
    )
    result = P30CorridorHeight().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p30_corridor_height_returns_mock_message(
    make_room, make_apartment,
):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.CORRIDOR, 1.0, 3.0)],
        num_rooms=1,
    )
    result = P30CorridorHeight().validate(apt)
    assert "mock" in result.message.lower()

def test_p31_sanitary_above_living_always_pass(
    make_room, make_apartment,
):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.BATHROOM, 2.0, 2.0)],
        num_rooms=1,
    )
    result = P31SanitaryAboveLiving().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p31_sanitary_above_living_returns_mock_message(
    make_room, make_apartment,
):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.BATHROOM, 2.0, 2.0)],
        num_rooms=1,
    )
    result = P31SanitaryAboveLiving().validate(apt)
    assert "mock" in result.message.lower()

def test_p32_insolation_always_pass(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.LIVING_ROOM, 4.0, 5.0)],
        num_rooms=1,
    )
    result = P32Insolation().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p32_insolation_returns_mock_message(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.LIVING_ROOM, 4.0, 5.0)],
        num_rooms=1,
    )
    result = P32Insolation().validate(apt)
    assert "mock" in result.message.lower()

def test_p33_waterproofing_always_pass(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.BATHROOM, 2.0, 2.0)],
        num_rooms=1,
    )
    result = P33Waterproofing().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p33_waterproofing_returns_mock_message(
    make_room, make_apartment,
):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.BATHROOM, 2.0, 2.0)],
        num_rooms=1,
    )
    result = P33Waterproofing().validate(apt)
    assert "mock" in result.message.lower()

def test_p34_ventilation_always_pass(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.KITCHEN, 3.0, 3.0)],
        num_rooms=1,
    )
    result = P34Ventilation().validate(apt)
    assert result.status == RuleStatus.PASS

def test_p34_ventilation_returns_mock_message(make_room, make_apartment):
    apt = make_apartment(
        ApartmentClass.ECONOMY,
        [make_room(RoomType.KITCHEN, 3.0, 3.0)],
        num_rooms=1,
    )
    result = P34Ventilation().validate(apt)
    assert "mock" in result.message.lower()
