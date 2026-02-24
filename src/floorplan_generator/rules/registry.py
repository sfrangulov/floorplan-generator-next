"""Rule registry — central collection of all validators."""

from __future__ import annotations

from floorplan_generator.core.models import Apartment
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
    P35SingleDoorUtilityRooms,
    P36WindowsOnExternalWalls,
    P37KitchenNotPassthrough,
    P38EntranceDoorExists,
    P39WardrobeConnection,
)
from floorplan_generator.rules.rule_engine import (
    RuleResult,
    RuleValidator,
)


class RuleRegistry:
    """Central registry of all rule validators."""

    def __init__(self) -> None:
        self._rules: dict[str, RuleValidator] = {}

    def register(self, rule: RuleValidator) -> None:
        self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> RuleValidator:
        return self._rules[rule_id]

    def all_rules(self) -> list[RuleValidator]:
        return list(self._rules.values())

    def mandatory_rules(self) -> list[RuleValidator]:
        return [
            r for r in self._rules.values() if r.is_mandatory
        ]

    def recommended_rules(self) -> list[RuleValidator]:
        return [
            r for r in self._rules.values()
            if not r.is_mandatory
        ]

    def validate_all(
        self, apartment: Apartment,
    ) -> list[RuleResult]:
        return [
            rule.validate(apartment)
            for rule in self._rules.values()
        ]


_ALL_RULE_CLASSES: list[type[RuleValidator]] = [
    # Planning rules P01-P34
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
    P35SingleDoorUtilityRooms,
    P36WindowsOnExternalWalls,
    P37KitchenNotPassthrough,
    P38EntranceDoorExists,
    P39WardrobeConnection,
    # Furniture rules F01-F32
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
]


def create_default_registry() -> RuleRegistry:
    """Create registry with all P01-P34 and F01-F32 rules."""
    registry = RuleRegistry()
    for rule_cls in _ALL_RULE_CLASSES:
        registry.register(rule_cls())
    return registry
