"""Dimension constants from Russian building codes and ergonomic standards.

All lengths in millimeters (mm). All areas in square meters (m²).
Sources: СП 54.13330.2022, СНиП 31-01-2003, ГОСТ 13025, Нойферт.
"""

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
)

# --- Minimum areas (m²) ---

MIN_AREAS: dict[str, float] = {
    "living_room_1room": 14.0,
    "living_room_2plus": 16.0,
    "bedroom_1person": 8.0,
    "bedroom_2person": 10.0,
    "kitchen": 8.0,
    "kitchen_1room": 5.0,
    "kitchen_zone_dining": 6.0,
    "kitchen_niche": 5.0,
}

# Total apartment area ranges by class and room count (m²): (min, max)
APARTMENT_AREAS: dict[ApartmentClass, dict[int, tuple[float, float]]] = {
    ApartmentClass.ECONOMY: {
        1: (28.0, 38.0),
        2: (44.0, 53.0),
        3: (56.0, 65.0),
        4: (70.0, 80.0),
    },
    ApartmentClass.COMFORT: {
        1: (38.0, 50.0),
        2: (53.0, 75.0),
        3: (65.0, 90.0),
        4: (80.0, 110.0),
    },
    ApartmentClass.BUSINESS: {
        1: (45.0, 65.0),
        2: (70.0, 100.0),
        3: (90.0, 140.0),
        4: (110.0, 180.0),
    },
    ApartmentClass.PREMIUM: {
        1: (60.0, 120.0),
        2: (100.0, 200.0),
        3: (150.0, 300.0),
        4: (200.0, 400.0),
    },
}

# --- Minimum widths (mm) ---

MIN_WIDTHS: dict[str, float] = {
    "kitchen": 1700.0,
    "hallway": 1400.0,
    "corridor": 850.0,
    "corridor_long": 1000.0,  # corridor longer than 1500 mm
    "corridor_long_threshold": 1500.0,
    "bathroom": 1500.0,
    "combined_bathroom": 1700.0,
    "toilet": 800.0,
    "living_room": 3200.0,
    "living_room_min": 2400.0,
}

# --- Minimum heights (mm) ---

MIN_HEIGHTS: dict[str, float] = {
    "living_rooms_standard": 2500.0,
    "living_rooms_cold_climate": 2700.0,
    "corridors": 2100.0,
}

# Ceiling heights by class (mm)
CEILING_HEIGHTS: dict[ApartmentClass, tuple[float, float]] = {
    ApartmentClass.ECONOMY: (2500.0, 2600.0),
    ApartmentClass.COMFORT: (2600.0, 2800.0),
    ApartmentClass.BUSINESS: (3000.0, 3500.0),
    ApartmentClass.PREMIUM: (3000.0, 4000.0),
}

# --- Door sizes (mm): (width_min, width_max, height) ---

DOOR_SIZES: dict[DoorType, tuple[float, float, float]] = {
    DoorType.ENTRANCE: (860.0, 960.0, 2050.0),
    DoorType.INTERIOR: (800.0, 800.0, 2000.0),
    DoorType.INTERIOR_WIDE: (800.0, 900.0, 2000.0),
    DoorType.DOUBLE: (1300.0, 1500.0, 2000.0),
    DoorType.KITCHEN: (700.0, 800.0, 2000.0),
    DoorType.BATHROOM: (600.0, 600.0, 2000.0),
    DoorType.COMBINED_BATHROOM: (600.0, 700.0, 2000.0),
}

# --- Window ratios ---

WINDOW_RATIOS: dict[str, float] = {
    "min_ratio": 1.0 / 8.0,       # min window area / floor area
    "recommended_ratio": 1.0 / 6.0,
    "sill_height": 800.0,          # mm from floor
    "min_side_gap": 250.0,         # mm from window to side wall
    "max_room_depth": 6000.0,      # mm for one-sided illumination
}

# --- Adjacency matrix ---
# +: allowed, -: forbidden, (у): conditional
# Rows and columns indexed by RoomType values

ADJACENCY_MATRIX: dict[RoomType, dict[RoomType, str]] = {
    RoomType.HALLWAY: {
        RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "+", RoomType.TOILET: "+",
        RoomType.COMBINED_BATHROOM: "+", RoomType.STORAGE: "+",
    },
    RoomType.CORRIDOR: {
        RoomType.HALLWAY: "+", RoomType.LIVING_ROOM: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "+", RoomType.TOILET: "+",
        RoomType.COMBINED_BATHROOM: "+", RoomType.STORAGE: "+",
    },
    RoomType.LIVING_ROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.BEDROOM: "+",
        RoomType.KITCHEN: "+", RoomType.BATHROOM: "(у)", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "(у)", RoomType.STORAGE: "+",
    },
    RoomType.BEDROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.KITCHEN: "-", RoomType.BATHROOM: "(у)", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "(у)", RoomType.STORAGE: "+",
    },
    RoomType.KITCHEN: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "-", RoomType.BATHROOM: "-", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "+",
    },
    RoomType.BATHROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "(у)",
        RoomType.BEDROOM: "(у)", RoomType.KITCHEN: "-", RoomType.TOILET: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "-",
    },
    RoomType.TOILET: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "-",
        RoomType.BEDROOM: "-", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.COMBINED_BATHROOM: "-", RoomType.STORAGE: "-",
    },
    RoomType.COMBINED_BATHROOM: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "(у)",
        RoomType.BEDROOM: "(у)", RoomType.KITCHEN: "-", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.STORAGE: "-",
    },
    RoomType.STORAGE: {
        RoomType.HALLWAY: "+", RoomType.CORRIDOR: "+", RoomType.LIVING_ROOM: "+",
        RoomType.BEDROOM: "+", RoomType.KITCHEN: "+", RoomType.BATHROOM: "-",
        RoomType.TOILET: "-", RoomType.COMBINED_BATHROOM: "-",
    },
}

# --- Furniture sizes (mm): (width, depth, height) ---

FURNITURE_SIZES: dict[FurnitureType, tuple[float, float, float]] = {
    # Plumbing
    FurnitureType.BATHTUB: (1700.0, 750.0, 600.0),
    FurnitureType.SHOWER: (900.0, 900.0, 2100.0),
    FurnitureType.SINK: (600.0, 500.0, 850.0),
    FurnitureType.DOUBLE_SINK: (1350.0, 500.0, 850.0),
    FurnitureType.TOILET_BOWL: (650.0, 375.0, 420.0),
    FurnitureType.BIDET: (580.0, 375.0, 400.0),
    FurnitureType.WASHING_MACHINE: (600.0, 500.0, 850.0),
    FurnitureType.DRYER: (600.0, 550.0, 850.0),
    # Kitchen
    FurnitureType.STOVE: (600.0, 600.0, 850.0),
    FurnitureType.HOB: (590.0, 520.0, 50.0),
    FurnitureType.OVEN: (580.0, 575.0, 595.0),
    FurnitureType.FRIDGE: (600.0, 600.0, 1800.0),
    FurnitureType.FRIDGE_SIDE_BY_SIDE: (900.0, 725.0, 1800.0),
    FurnitureType.DISHWASHER: (600.0, 575.0, 820.0),
    FurnitureType.KITCHEN_SINK: (600.0, 550.0, 200.0),
    FurnitureType.HOOD: (600.0, 400.0, 100.0),
    FurnitureType.MICROWAVE: (525.0, 350.0, 320.0),
    # Living room
    FurnitureType.SOFA_2: (1750.0, 950.0, 770.0),
    FurnitureType.SOFA_3: (2300.0, 950.0, 770.0),
    FurnitureType.SOFA_4: (2500.0, 950.0, 770.0),
    FurnitureType.SOFA_CORNER: (2750.0, 1750.0, 800.0),
    FurnitureType.ARMCHAIR: (850.0, 850.0, 770.0),
    FurnitureType.COFFEE_TABLE: (1000.0, 600.0, 400.0),
    FurnitureType.TV_STAND: (1500.0, 425.0, 500.0),
    FurnitureType.SHELVING: (1200.0, 375.0, 1900.0),
    # Bedroom
    FurnitureType.BED_SINGLE: (900.0, 2000.0, 500.0),
    FurnitureType.BED_DOUBLE: (1600.0, 2000.0, 500.0),
    FurnitureType.BED_KING: (1800.0, 2100.0, 500.0),
    FurnitureType.NIGHTSTAND: (500.0, 425.0, 600.0),
    FurnitureType.DRESSER: (1000.0, 450.0, 1000.0),
    FurnitureType.WARDROBE_SLIDING: (2000.0, 625.0, 2300.0),
    FurnitureType.WARDROBE_SWING: (1600.0, 575.0, 2100.0),
    FurnitureType.VANITY: (1000.0, 450.0, 750.0),
    # Children
    FurnitureType.CHILD_BED: (1700.0, 800.0, 400.0),
    FurnitureType.CHILD_DESK: (1100.0, 600.0, 640.0),
    FurnitureType.CHILD_WARDROBE: (1000.0, 500.0, 1650.0),
    # Hallway
    FurnitureType.HALLWAY_WARDROBE: (1800.0, 500.0, 2250.0),
    FurnitureType.SHOE_RACK: (800.0, 325.0, 750.0),
    FurnitureType.BENCH: (900.0, 375.0, 475.0),
    FurnitureType.COAT_RACK: (900.0, 275.0, 1600.0),
    # General
    FurnitureType.DINING_TABLE: (1350.0, 850.0, 760.0),
    FurnitureType.DINING_CHAIR: (450.0, 450.0, 440.0),
    FurnitureType.DESK: (1200.0, 600.0, 750.0),
    FurnitureType.BOOKSHELF: (900.0, 300.0, 2000.0),
}

# --- Clearance zones (mm, distance in front of furniture) ---

CLEARANCES: dict[str, float] = {
    # Bathroom
    "toilet_center_from_wall": 350.0,
    "toilet_front": 600.0,
    "toilet_front_optimal": 750.0,
    "sink_front": 700.0,
    "sink_front_optimal": 800.0,
    "bathtub_exit": 550.0,
    "bathtub_exit_optimal": 750.0,
    "outlet_from_water": 600.0,
    # Kitchen
    "stove_side_wall": 200.0,
    "stove_window": 450.0,
    "hood_gas_stove": 750.0,
    "hood_electric_stove": 650.0,
    "fridge_stove": 300.0,
    "kitchen_rows_parallel": 1200.0,
    "kitchen_passage": 900.0,
    # Bedroom
    "bed_passage_double": 700.0,
    "bed_passage_double_optimal": 900.0,
    "wardrobe_swing_front": 800.0,
    "wardrobe_sliding_front": 700.0,
    "drawers_front": 800.0,
    # Safety
    "oven_front": 800.0,
    "passage_min": 700.0,
    "passage_two_people": 1100.0,
    # Dining
    "table_wall_passage": 900.0,
    "table_wall_no_passage": 600.0,
    "shelf_max_height": 1900.0,
    # Living room
    "sofa_armchair_max": 2000.0,
    "armchairs_apart": 1050.0,
    "wall_furniture_not_perimeter": 900.0,
    "carpet_wall": 600.0,
    "shelving_other_furniture": 800.0,
    "living_room_max_furniture_ratio": 0.35,
    # Hallway
    "entry_zone_width": 600.0,
    "entry_zone_depth": 800.0,
    # Appliances
    "washer_back_gap": 50.0,
    "toilet_riser_max": 1000.0,
}

# --- Kitchen triangle (mm) ---

KITCHEN_TRIANGLE: dict[str, float] = {
    "perimeter_min": 3500.0,
    "perimeter_max": 8000.0,
    "perimeter_optimal_min": 4000.0,
    "perimeter_optimal_max": 6000.0,
    "sink_stove_min": 800.0,
    "sink_stove_max": 2000.0,
    "fridge_stove_min": 350.0,
    "sink_fridge_max": 2500.0,
}

# --- Wall thicknesses (mm) ---

WALL_THICKNESS: dict[str, float] = {
    "external": 225.0,
    "internal_partition": 100.0,
    "load_bearing": 290.0,
}

# --- Room placement priority (lower = placed earlier) ---

ROOM_PLACEMENT_PRIORITY: dict[RoomType, int] = {
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
    # Optional rooms — lowest priority
    RoomType.STORAGE: 10,
    RoomType.WARDROBE: 10,
    RoomType.BALCONY: 10,
}
