"""Domain enumerations for the floorplan generator."""

from enum import StrEnum


class RoomType(StrEnum):
    """Type of room in an apartment."""

    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    CHILDREN = "children"
    CABINET = "cabinet"
    KITCHEN = "kitchen"
    KITCHEN_DINING = "kitchen_dining"
    KITCHEN_NICHE = "kitchen_niche"
    HALLWAY = "hallway"
    CORRIDOR = "corridor"
    HALL = "hall"
    BATHROOM = "bathroom"
    TOILET = "toilet"
    COMBINED_BATHROOM = "combined_bathroom"
    STORAGE = "storage"
    WARDROBE = "wardrobe"
    LAUNDRY = "laundry"
    BALCONY = "balcony"

    @property
    def is_wet_zone(self) -> bool:
        return self in _WET_ZONES

    @property
    def requires_window(self) -> bool:
        return self in _WINDOW_REQUIRED

    @property
    def is_living(self) -> bool:
        """True for rooms counted as 'living area' (жилая площадь)."""
        return self in _LIVING_ROOMS


_WET_ZONES = frozenset({
    RoomType.KITCHEN,
    RoomType.KITCHEN_DINING,
    RoomType.KITCHEN_NICHE,
    RoomType.BATHROOM,
    RoomType.TOILET,
    RoomType.COMBINED_BATHROOM,
    RoomType.LAUNDRY,
})

_WINDOW_REQUIRED = frozenset({
    RoomType.LIVING_ROOM,
    RoomType.BEDROOM,
    RoomType.CHILDREN,
    RoomType.CABINET,
    RoomType.KITCHEN,
    RoomType.KITCHEN_DINING,
})

_LIVING_ROOMS = frozenset({
    RoomType.LIVING_ROOM,
    RoomType.BEDROOM,
    RoomType.CHILDREN,
    RoomType.CABINET,
})


class ApartmentClass(StrEnum):
    """Housing class."""

    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"
    PREMIUM = "premium"


class DoorType(StrEnum):
    """Type of door."""

    ENTRANCE = "entrance"
    INTERIOR = "interior"
    INTERIOR_WIDE = "interior_wide"
    DOUBLE = "double"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    COMBINED_BATHROOM = "combined_bathroom"


class SwingDirection(StrEnum):
    """Door swing direction."""

    INWARD = "inward"
    OUTWARD = "outward"


class FurnitureType(StrEnum):
    """Type of furniture or equipment."""

    # Plumbing
    BATHTUB = "bathtub"
    SHOWER = "shower"
    SINK = "sink"
    DOUBLE_SINK = "double_sink"
    TOILET_BOWL = "toilet_bowl"
    BIDET = "bidet"
    WASHING_MACHINE = "washing_machine"
    DRYER = "dryer"
    # Kitchen
    STOVE = "stove"
    HOB = "hob"
    OVEN = "oven"
    FRIDGE = "fridge"
    FRIDGE_SIDE_BY_SIDE = "fridge_side_by_side"
    DISHWASHER = "dishwasher"
    KITCHEN_SINK = "kitchen_sink"
    HOOD = "hood"
    MICROWAVE = "microwave"
    # Living room
    SOFA_2 = "sofa_2"
    SOFA_3 = "sofa_3"
    SOFA_4 = "sofa_4"
    SOFA_CORNER = "sofa_corner"
    ARMCHAIR = "armchair"
    COFFEE_TABLE = "coffee_table"
    TV_STAND = "tv_stand"
    SHELVING = "shelving"
    # Bedroom
    BED_SINGLE = "bed_single"
    BED_DOUBLE = "bed_double"
    BED_KING = "bed_king"
    NIGHTSTAND = "nightstand"
    DRESSER = "dresser"
    WARDROBE_SLIDING = "wardrobe_sliding"
    WARDROBE_SWING = "wardrobe_swing"
    VANITY = "vanity"
    # Children
    CHILD_BED = "child_bed"
    CHILD_DESK = "child_desk"
    CHILD_WARDROBE = "child_wardrobe"
    # Hallway
    HALLWAY_WARDROBE = "hallway_wardrobe"
    SHOE_RACK = "shoe_rack"
    BENCH = "bench"
    COAT_RACK = "coat_rack"
    # General
    DINING_TABLE = "dining_table"
    DINING_CHAIR = "dining_chair"
    DESK = "desk"
    BOOKSHELF = "bookshelf"


class FunctionalZone(StrEnum):
    """Functional zone of the apartment."""

    ENTRY = "entry"
    DAY = "day"
    NIGHT = "night"


class LayoutType(StrEnum):
    """Furniture layout type in living room."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    CIRCULAR = "circular"


class KitchenLayoutType(StrEnum):
    """Kitchen layout type."""

    LINEAR = "linear"
    L_SHAPED = "l_shaped"
    U_SHAPED = "u_shaped"
    PARALLEL = "parallel"
    ISLAND = "island"
    PENINSULA = "peninsula"

    @property
    def min_area_m2(self) -> float:
        return _KITCHEN_MIN_AREAS[self]


_KITCHEN_MIN_AREAS = {
    KitchenLayoutType.LINEAR: 5.0,
    KitchenLayoutType.L_SHAPED: 7.0,
    KitchenLayoutType.U_SHAPED: 10.0,
    KitchenLayoutType.PARALLEL: 9.0,
    KitchenLayoutType.ISLAND: 15.0,
    KitchenLayoutType.PENINSULA: 12.0,
}
