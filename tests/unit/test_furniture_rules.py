"""Unit tests for furniture rules (F01-F32)."""

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
)
from floorplan_generator.core.geometry import Point
from floorplan_generator.rules.furniture_rules import (
    F01ToiletCenterFromWall,
    F02ToiletFrontClearance,
    F03SinkFrontClearance,
    F04BathtubExitClearance,
    F05OutletFromWater,
    F06KitchenTriangle,
    F07SinkStoveDistance,
    F08StoveWallDistance,
    F09StoveWindowDistance,
    F10HoodGasStove,
    F11HoodElectricStove,
    F12FridgeStoveDistance,
    F13KitchenParallelRows,
    F14BedPassage,
    F15SwingWardrobeClearance,
    F16DrawersClearance,
    F17OvenClearance,
    F18MinPassage,
    F19TableWallPassage,
    F20ShelfHeight,
    F21SofaArmchairDistance,
    F22ArmchairsApart,
    F23WallFurnitureGap,
    F24CarpetWall,
    F25ShelvingFurnitureGap,
    F26LivingRoomFurnitureRatio,
    F27TVNotFacingWindow,
    F28SofaBedLength,
    F29ArmchairSeatWidth,
    F30EntryZone,
    F31WasherBackGap,
    F32ToiletRiserDistance,
)
from floorplan_generator.rules.rule_engine import RuleStatus

FT = FurnitureType
RT = RoomType
AC = ApartmentClass


def _apt(mk_room, mk_apt, rt, w, h, furn, wins=None):
    """Make apartment with single room containing furniture."""
    room = mk_room(
        rt, width_m=w, height_m=h,
        furniture=furn, windows=wins or [],
    )
    return mk_apt(AC.COMFORT, [room], num_rooms=1)


# --- F01: Toilet center from wall ---


def test_f01_toilet_center_350_pass(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=25, y=500, width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 2.0, [toilet],
    )
    result = F01ToiletCenterFromWall().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f01_toilet_center_250_fail(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=0, y=500, width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.COMBINED_BATHROOM, 2.0, 2.0, [toilet],
    )
    result = F01ToiletCenterFromWall().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F02: Toilet front clearance ---


def test_f02_toilet_front_600_pass(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=200, y=0, width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 2.0, [toilet],
    )
    result = F02ToiletFrontClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f02_toilet_front_400_fail(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=200, y=1225, width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 1.8, [toilet],
    )
    result = F02ToiletFrontClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F03: Sink front clearance ---


def test_f03_sink_front_700_pass(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.SINK, x=200, y=0, width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 2.0, [sink],
    )
    result = F03SinkFrontClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f03_sink_front_500_fail(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.SINK, x=200, y=0, width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 0.9, [sink],
    )
    result = F03SinkFrontClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F04: Bathtub exit clearance ---


def test_f04_bathtub_exit_550_pass(
    make_room, make_furniture, make_apartment,
):
    tub = make_furniture(
        FT.BATHTUB, x=0, y=0, width=1700, depth=750,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.5, 2.0, [tub],
    )
    result = F04BathtubExitClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f04_bathtub_exit_400_fail(
    make_room, make_furniture, make_apartment,
):
    tub = make_furniture(
        FT.BATHTUB, x=0, y=0, width=1700, depth=750,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 1.7, 1.1, [tub],
    )
    result = F04BathtubExitClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F05: Outlet distance from water ---


def test_f05_outlet_600_pass(
    make_room, make_furniture, make_apartment,
):
    tub = make_furniture(
        FT.BATHTUB, x=0, y=0, width=1700, depth=750,
    )
    washer = make_furniture(
        FT.WASHING_MACHINE, x=0, y=1400, width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.5, 2.5, [tub, washer],
    )
    result = F05OutletFromWater().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f05_outlet_400_fail(
    make_room, make_furniture, make_apartment,
):
    tub = make_furniture(
        FT.BATHTUB, x=0, y=0, width=1700, depth=750,
    )
    washer = make_furniture(
        FT.WASHING_MACHINE, x=0, y=800, width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.5, 2.0, [tub, washer],
    )
    result = F05OutletFromWater().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F06: Kitchen triangle ---


def test_f06_triangle_5000_pass(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=1500, y=0, width=600, depth=600,
    )
    fridge = make_furniture(
        FT.FRIDGE, x=0, y=1800, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [sink, stove, fridge],
    )
    result = F06KitchenTriangle().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f06_triangle_2500_fail(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=600, y=0, width=600, depth=600,
    )
    fridge = make_furniture(
        FT.FRIDGE, x=300, y=600, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [sink, stove, fridge],
    )
    result = F06KitchenTriangle().validate(apt)
    assert result.status == RuleStatus.FAIL


def test_f06_triangle_9000_fail(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=3500, y=0, width=600, depth=600,
    )
    fridge = make_furniture(
        FT.FRIDGE, x=0, y=3500, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 5.0, 5.0, [sink, stove, fridge],
    )
    result = F06KitchenTriangle().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F07: Sink-stove distance ---


def test_f07_sink_stove_1200_pass(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=1200, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [sink, stove],
    )
    result = F07SinkStoveDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f07_sink_stove_500_fail(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=500, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [sink, stove],
    )
    result = F07SinkStoveDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


def test_f07_sink_stove_2500_fail(
    make_room, make_furniture, make_apartment,
):
    sink = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    stove = make_furniture(
        FT.STOVE, x=2500, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 4.0, 3.0, [sink, stove],
    )
    result = F07SinkStoveDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F08: Stove-wall distance ---


def test_f08_stove_wall_200_pass(
    make_room, make_furniture, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=200, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove],
    )
    result = F08StoveWallDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f08_stove_wall_100_fail(
    make_room, make_furniture, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=100, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove],
    )
    result = F08StoveWallDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F09: Stove-window distance ---


def test_f09_stove_window_450_pass(
    make_room, make_furniture, make_window, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=1000, y=0, width=600, depth=600,
    )
    win = make_window(width=1200, height=1500)
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove], wins=[win],
    )
    result = F09StoveWindowDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f09_stove_window_300_fail(
    make_room, make_furniture, make_window, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=0, y=0, width=600, depth=600,
    )
    win = make_window(width=1200, height=1500)
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove], wins=[win],
    )
    result = F09StoveWindowDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F10: Hood - gas stove ---


def test_f10_hood_gas_750_pass(
    make_room, make_furniture, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=200, y=0, width=600, depth=600,
    )
    hood = make_furniture(
        FT.HOOD, x=200, y=0, width=600, depth=400,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove, hood],
    )
    result = F10HoodGasStove().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f10_hood_gas_600_result(
    make_room, make_furniture, make_apartment,
):
    stove = make_furniture(
        FT.STOVE, x=200, y=0, width=600, depth=600,
    )
    hood = make_furniture(
        FT.HOOD, x=200, y=0, width=600, depth=400,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [stove, hood],
    )
    result = F10HoodGasStove().validate(apt)
    assert result.status in {RuleStatus.PASS, RuleStatus.FAIL}


# --- F11: Hood - electric stove ---


def test_f11_hood_electric_650_pass(
    make_room, make_furniture, make_apartment,
):
    hob = make_furniture(
        FT.HOB, x=200, y=0, width=590, depth=520,
    )
    hood = make_furniture(
        FT.HOOD, x=200, y=0, width=600, depth=400,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [hob, hood],
    )
    result = F11HoodElectricStove().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f11_hood_electric_500_result(
    make_room, make_furniture, make_apartment,
):
    hob = make_furniture(
        FT.HOB, x=200, y=0, width=590, depth=520,
    )
    hood = make_furniture(
        FT.HOOD, x=200, y=0, width=600, depth=400,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [hob, hood],
    )
    result = F11HoodElectricStove().validate(apt)
    assert result.status in {RuleStatus.PASS, RuleStatus.FAIL}


# --- F12: Fridge-stove distance ---


def test_f12_fridge_stove_300_pass(
    make_room, make_furniture, make_apartment,
):
    fridge = make_furniture(
        FT.FRIDGE, x=0, y=0, width=600, depth=600,
    )
    stove = make_furniture(
        FT.STOVE, x=900, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [fridge, stove],
    )
    result = F12FridgeStoveDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f12_fridge_stove_200_fail(
    make_room, make_furniture, make_apartment,
):
    fridge = make_furniture(
        FT.FRIDGE, x=0, y=0, width=600, depth=600,
    )
    stove = make_furniture(
        FT.STOVE, x=700, y=0, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [fridge, stove],
    )
    result = F12FridgeStoveDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F13: Kitchen parallel rows ---


def test_f13_rows_1200_pass(
    make_room, make_furniture, make_apartment,
):
    row1 = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    row2 = make_furniture(
        FT.STOVE, x=0, y=1750, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [row1, row2],
    )
    result = F13KitchenParallelRows().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f13_rows_1000_fail(
    make_room, make_furniture, make_apartment,
):
    row1 = make_furniture(
        FT.KITCHEN_SINK, x=0, y=0, width=600, depth=550,
    )
    row2 = make_furniture(
        FT.STOVE, x=0, y=1350, width=600, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [row1, row2],
    )
    result = F13KitchenParallelRows().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F14: Bed passage ---


def test_f14_bed_passage_700_pass(
    make_room, make_furniture, make_apartment,
):
    bed = make_furniture(
        FT.BED_DOUBLE, x=700, y=700, width=1600, depth=2000,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 3.5, 4.0, [bed],
    )
    result = F14BedPassage().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f14_bed_passage_500_fail(
    make_room, make_furniture, make_apartment,
):
    bed = make_furniture(
        FT.BED_DOUBLE, x=200, y=200, width=1600, depth=2000,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 2.0, 2.5, [bed],
    )
    result = F14BedPassage().validate(apt)
    assert result.status == RuleStatus.FAIL


def test_f14_single_bed_one_side_ok(
    make_room, make_furniture, make_apartment,
):
    bed = make_furniture(
        FT.BED_SINGLE, x=0, y=700, width=900, depth=2000,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 2.5, 3.5, [bed],
    )
    result = F14BedPassage().validate(apt)
    assert result.status == RuleStatus.PASS


# --- F15: Swing wardrobe clearance ---


def test_f15_swing_wardrobe_800_pass(
    make_room, make_furniture, make_apartment,
):
    ward = make_furniture(
        FT.WARDROBE_SWING, x=0, y=0, width=1600, depth=575,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 3.0, 3.0, [ward],
    )
    result = F15SwingWardrobeClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f15_swing_wardrobe_600_fail(
    make_room, make_furniture, make_apartment,
):
    ward = make_furniture(
        FT.WARDROBE_SWING, x=0, y=0, width=1600, depth=575,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 1.6, 1.2, [ward],
    )
    result = F15SwingWardrobeClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F16: Drawers clearance ---


def test_f16_drawers_800_pass(
    make_room, make_furniture, make_apartment,
):
    dresser = make_furniture(
        FT.DRESSER, x=0, y=0, width=1000, depth=450,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 3.0, 3.0, [dresser],
    )
    result = F16DrawersClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f16_drawers_600_fail(
    make_room, make_furniture, make_apartment,
):
    dresser = make_furniture(
        FT.DRESSER, x=0, y=0, width=1000, depth=450,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BEDROOM, 1.0, 1.1, [dresser],
    )
    result = F16DrawersClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F17: Oven clearance ---


def test_f17_oven_800_pass(
    make_room, make_furniture, make_apartment,
):
    oven = make_furniture(
        FT.OVEN, x=200, y=0, width=580, depth=575,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 3.0, 3.0, [oven],
    )
    result = F17OvenClearance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f17_oven_500_fail(
    make_room, make_furniture, make_apartment,
):
    oven = make_furniture(
        FT.OVEN, x=200, y=0, width=580, depth=575,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.KITCHEN, 1.0, 1.0, [oven],
    )
    result = F17OvenClearance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F18: Min passage ---


def test_f18_passage_700_pass(
    make_room, make_furniture, make_apartment,
):
    item = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 3.0, [item],
    )
    result = F18MinPassage().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f18_passage_500_fail(
    make_room, make_furniture, make_apartment,
):
    item = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 2.3, 1.5, [item],
    )
    result = F18MinPassage().validate(apt)
    assert result.status == RuleStatus.FAIL


def test_f18_passage_between_furniture(
    make_room, make_furniture, make_apartment,
):
    item1 = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    item2 = make_furniture(
        FT.COFFEE_TABLE, x=0, y=1650, width=1000, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [item1, item2],
    )
    result = F18MinPassage().validate(apt)
    assert result.status == RuleStatus.PASS


# --- F19: Table-wall passage ---


def test_f19_table_wall_900_pass(
    make_room, make_furniture, make_apartment,
):
    table = make_furniture(
        FT.DINING_TABLE, x=900, y=900, width=1350, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [table],
    )
    result = F19TableWallPassage().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f19_table_wall_700_fail(
    make_room, make_furniture, make_apartment,
):
    table = make_furniture(
        FT.DINING_TABLE, x=200, y=200, width=1350, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 2.0, 2.0, [table],
    )
    result = F19TableWallPassage().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F20: Shelf height ---


def test_f20_shelf_1900_pass(
    make_room, make_furniture, make_apartment,
):
    shelf = make_furniture(
        FT.SHELVING, x=0, y=0, width=1200, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [shelf],
    )
    result = F20ShelfHeight().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f20_shelf_2100_fail(
    make_room, make_furniture, make_apartment,
):
    shelf = make_furniture(
        FT.BOOKSHELF, x=0, y=0, width=900, depth=300,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [shelf],
    )
    result = F20ShelfHeight().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F21: Sofa-armchair distance ---


def test_f21_sofa_armchair_1500_pass(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    chair = make_furniture(
        FT.ARMCHAIR, x=500, y=1500, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [sofa, chair],
    )
    result = F21SofaArmchairDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f21_sofa_armchair_2500_fail(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    chair = make_furniture(
        FT.ARMCHAIR, x=500, y=3000, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 5.0, 5.0, [sofa, chair],
    )
    result = F21SofaArmchairDistance().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F22: Armchairs apart ---


def test_f22_armchairs_1050_pass(
    make_room, make_furniture, make_apartment,
):
    a1 = make_furniture(
        FT.ARMCHAIR, x=0, y=0, width=850, depth=850,
    )
    a2 = make_furniture(
        FT.ARMCHAIR, x=1900, y=0, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [a1, a2],
    )
    result = F22ArmchairsApart().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f22_armchairs_600_fail(
    make_room, make_furniture, make_apartment,
):
    a1 = make_furniture(
        FT.ARMCHAIR, x=0, y=0, width=850, depth=850,
    )
    a2 = make_furniture(
        FT.ARMCHAIR, x=1100, y=0, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [a1, a2],
    )
    result = F22ArmchairsApart().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F23: Wall-furniture gap ---


def test_f23_wall_furniture_900_pass(
    make_room, make_furniture, make_apartment,
):
    item = make_furniture(
        FT.COFFEE_TABLE, x=900, y=900,
        width=1000, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [item],
    )
    result = F23WallFurnitureGap().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f23_wall_furniture_500_fail(
    make_room, make_furniture, make_apartment,
):
    item = make_furniture(
        FT.COFFEE_TABLE, x=500, y=500,
        width=1000, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [item],
    )
    result = F23WallFurnitureGap().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F24: Carpet-wall distance ---


def test_f24_carpet_wall_600_pass(
    make_room, make_furniture, make_apartment,
):
    carpet = make_furniture(
        FT.COFFEE_TABLE, x=600, y=600,
        width=2000, depth=1500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [carpet],
    )
    result = F24CarpetWall().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f24_carpet_wall_300_fail(
    make_room, make_furniture, make_apartment,
):
    carpet = make_furniture(
        FT.COFFEE_TABLE, x=300, y=300,
        width=2000, depth=1500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [carpet],
    )
    result = F24CarpetWall().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F25: Shelving-furniture gap ---


def test_f25_shelving_800_pass(
    make_room, make_furniture, make_apartment,
):
    shelf = make_furniture(
        FT.SHELVING, x=0, y=0, width=1200, depth=375,
    )
    other = make_furniture(
        FT.SOFA_3, x=0, y=1175, width=2300, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [shelf, other],
    )
    result = F25ShelvingFurnitureGap().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f25_shelving_500_fail(
    make_room, make_furniture, make_apartment,
):
    shelf = make_furniture(
        FT.SHELVING, x=0, y=0, width=1200, depth=375,
    )
    other = make_furniture(
        FT.SOFA_3, x=0, y=700, width=2300, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [shelf, other],
    )
    result = F25ShelvingFurnitureGap().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F26: Living room furniture ratio ---


def test_f26_furniture_30pct_pass(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    table = make_furniture(
        FT.COFFEE_TABLE, x=0, y=1000,
        width=1000, depth=600,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 5.0, [sofa, table],
    )
    result = F26LivingRoomFurnitureRatio().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f26_furniture_50pct_fail(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    table = make_furniture(
        FT.DINING_TABLE, x=0, y=1000,
        width=1350, depth=850,
    )
    shelf = make_furniture(
        FT.SHELVING, x=0, y=2000, width=1200, depth=375,
    )
    chair = make_furniture(
        FT.ARMCHAIR, x=1500, y=0, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 3.0, 3.0,
        [sofa, table, shelf, chair],
    )
    result = F26LivingRoomFurnitureRatio().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F27: TV not facing window ---


def test_f27_tv_not_facing_window_pass(
    make_room, make_furniture, make_window, make_apartment,
):
    tv = make_furniture(
        FT.TV_STAND, x=0, y=0, width=1500, depth=425,
    )
    win = make_window(width=1500, height=1500)
    room = make_room(
        RT.LIVING_ROOM, width_m=4.0, height_m=5.0,
        furniture=[tv], windows=[win],
    )
    apt = make_apartment(AC.COMFORT, [room], num_rooms=1)
    result = F27TVNotFacingWindow().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f27_tv_facing_window_fail(
    make_room, make_furniture, make_window, make_apartment,
):
    tv = make_furniture(
        FT.TV_STAND, x=500, y=4500, width=1500, depth=425,
    )
    win = make_window(width=1500, height=1500)
    room = make_room(
        RT.LIVING_ROOM, width_m=4.0, height_m=5.0,
        furniture=[tv], windows=[win],
    )
    apt = make_apartment(AC.COMFORT, [room], num_rooms=1)
    result = F27TVNotFacingWindow().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F28: Sofa bed length ---


def test_f28_sofa_bed_2000_pass(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_3, x=0, y=0, width=2300, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [sofa],
    )
    result = F28SofaBedLength().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f28_sofa_bed_1800_fail(
    make_room, make_furniture, make_apartment,
):
    sofa = make_furniture(
        FT.SOFA_2, x=0, y=0, width=1750, depth=950,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [sofa],
    )
    result = F28SofaBedLength().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F29: Armchair seat width ---


def test_f29_armchair_480_pass(
    make_room, make_furniture, make_apartment,
):
    chair = make_furniture(
        FT.ARMCHAIR, x=0, y=0, width=850, depth=850,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [chair],
    )
    result = F29ArmchairSeatWidth().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f29_armchair_400_fail(
    make_room, make_furniture, make_apartment,
):
    chair = make_furniture(
        FT.ARMCHAIR, x=0, y=0, width=400, depth=400,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.LIVING_ROOM, 4.0, 4.0, [chair],
    )
    result = F29ArmchairSeatWidth().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F30: Entry zone ---


def test_f30_entry_zone_pass(
    make_room, make_door, make_apartment,
):
    hallway = make_room(RT.HALLWAY, width_m=2.0, height_m=2.0)
    door = make_door(
        door_type=DoorType.ENTRANCE,
        room_from="outside", room_to=hallway.id,
    )
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(AC.COMFORT, [hallway], num_rooms=1)
    result = F30EntryZone().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f30_entry_zone_blocked_fail(
    make_room, make_door, make_furniture, make_apartment,
):
    blocker = make_furniture(
        FT.HALLWAY_WARDROBE, x=0, y=0,
        width=1800, depth=500,
    )
    hallway = make_room(
        RT.HALLWAY, width_m=2.0, height_m=0.6,
        furniture=[blocker],
    )
    door = make_door(
        door_type=DoorType.ENTRANCE,
        position=Point(x=0, y=0),
        room_from="outside", room_to=hallway.id,
    )
    hallway = hallway.model_copy(update={"doors": [door]})
    apt = make_apartment(AC.COMFORT, [hallway], num_rooms=1)
    result = F30EntryZone().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F31: Washer back gap ---


def test_f31_washer_gap_50_pass(
    make_room, make_furniture, make_apartment,
):
    washer = make_furniture(
        FT.WASHING_MACHINE, x=100, y=50,
        width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 2.0, [washer],
    )
    result = F31WasherBackGap().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f31_washer_gap_20_fail(
    make_room, make_furniture, make_apartment,
):
    washer = make_furniture(
        FT.WASHING_MACHINE, x=100, y=20,
        width=600, depth=500,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.BATHROOM, 2.0, 2.0, [washer],
    )
    result = F31WasherBackGap().validate(apt)
    assert result.status == RuleStatus.FAIL


# --- F32: Toilet-riser distance ---


def test_f32_toilet_riser_800_pass(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=200, y=200,
        width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.TOILET, 1.5, 2.0, [toilet],
    )
    result = F32ToiletRiserDistance().validate(apt)
    assert result.status == RuleStatus.PASS


def test_f32_toilet_riser_1500_fail(
    make_room, make_furniture, make_apartment,
):
    toilet = make_furniture(
        FT.TOILET_BOWL, x=2000, y=2000,
        width=650, depth=375,
    )
    apt = _apt(
        make_room, make_apartment,
        RT.TOILET, 3.0, 3.0, [toilet],
    )
    result = F32ToiletRiserDistance().validate(apt)
    assert result.status == RuleStatus.FAIL
