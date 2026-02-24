"""Room composition and size assignment."""

from __future__ import annotations

import random

from floorplan_generator.core.dimensions import (  # noqa: F401
    APARTMENT_AREAS,
    FURNITURE_SIZES,
)
from floorplan_generator.core.enums import ApartmentClass, FurnitureType, RoomType
from floorplan_generator.core.geometry import Rectangle
from floorplan_generator.generator.types import RoomSpec

# Base compositions by room count
_BASE_COMPOSITIONS: dict[int, list[RoomType]] = {
    1: [
        RoomType.HALLWAY,
        RoomType.CORRIDOR,
        RoomType.LIVING_ROOM,
        RoomType.KITCHEN,
        RoomType.COMBINED_BATHROOM,
    ],
    2: [
        RoomType.HALLWAY,
        RoomType.CORRIDOR,
        RoomType.LIVING_ROOM,
        RoomType.BEDROOM,
        RoomType.KITCHEN,
        RoomType.BATHROOM,
        RoomType.TOILET,
    ],
    3: [
        RoomType.HALLWAY,
        RoomType.CORRIDOR,
        RoomType.LIVING_ROOM,
        RoomType.BEDROOM,
        RoomType.BEDROOM,
        RoomType.KITCHEN,
        RoomType.BATHROOM,
        RoomType.TOILET,
    ],
    4: [
        RoomType.HALLWAY,
        RoomType.CORRIDOR,
        RoomType.LIVING_ROOM,
        RoomType.BEDROOM,
        RoomType.BEDROOM,
        RoomType.BEDROOM,
        RoomType.KITCHEN,
        RoomType.BATHROOM,
        RoomType.TOILET,
    ],
}

_CLASS_EXTRAS: dict[ApartmentClass, list[RoomType]] = {
    ApartmentClass.ECONOMY: [],
    ApartmentClass.COMFORT: [RoomType.STORAGE],
    ApartmentClass.BUSINESS: [RoomType.STORAGE, RoomType.WARDROBE],
    ApartmentClass.PREMIUM: [RoomType.STORAGE, RoomType.WARDROBE, RoomType.LAUNDRY],
}

# Room size ranges (mm): (min_w, max_w, min_h, max_h)
_SIZE_RANGES: dict[RoomType, tuple[float, float, float, float]] = {
    RoomType.HALLWAY: (1400, 3000, 1200, 2500),
    RoomType.CORRIDOR: (850, 1500, 2000, 6000),
    RoomType.LIVING_ROOM: (3200, 5500, 3800, 5500),
    RoomType.BEDROOM: (2400, 4000, 3000, 5000),
    RoomType.CHILDREN: (2400, 3500, 3000, 4000),
    RoomType.CABINET: (2400, 3000, 2400, 3500),
    RoomType.KITCHEN: (2500, 4500, 2800, 4500),
    RoomType.KITCHEN_DINING: (3000, 5000, 3500, 5500),
    RoomType.BATHROOM: (1500, 2500, 1500, 3000),
    RoomType.TOILET: (800, 1200, 1200, 2000),
    RoomType.COMBINED_BATHROOM: (1700, 3000, 1700, 3500),
    RoomType.STORAGE: (800, 2000, 800, 2500),
    RoomType.WARDROBE: (1000, 2500, 1000, 2500),
    RoomType.LAUNDRY: (1200, 2000, 1200, 2000),
}

# Required furniture per room type
REQUIRED_FURNITURE: dict[RoomType, list[FurnitureType]] = {
    RoomType.HALLWAY: [FurnitureType.HALLWAY_WARDROBE, FurnitureType.SHOE_RACK],
    RoomType.KITCHEN: [
        FurnitureType.STOVE,
        FurnitureType.KITCHEN_SINK,
        FurnitureType.FRIDGE,
        FurnitureType.HOOD,
    ],
    RoomType.LIVING_ROOM: [
        FurnitureType.SOFA_3,
        FurnitureType.TV_STAND,
        FurnitureType.COFFEE_TABLE,
    ],
    RoomType.BEDROOM: [FurnitureType.BED_DOUBLE, FurnitureType.WARDROBE_SLIDING],
    RoomType.CHILDREN: [
        FurnitureType.CHILD_BED,
        FurnitureType.CHILD_DESK,
        FurnitureType.CHILD_WARDROBE,
    ],
    RoomType.BATHROOM: [FurnitureType.BATHTUB, FurnitureType.SINK],
    RoomType.TOILET: [FurnitureType.TOILET_BOWL],
    RoomType.COMBINED_BATHROOM: [
        FurnitureType.BATHTUB,
        FurnitureType.SINK,
        FurnitureType.TOILET_BOWL,
    ],
}

# Optional furniture added by class
OPTIONAL_FURNITURE: dict[RoomType, list[FurnitureType]] = {
    RoomType.HALLWAY: [FurnitureType.BENCH, FurnitureType.COAT_RACK],
    RoomType.KITCHEN: [FurnitureType.DISHWASHER, FurnitureType.MICROWAVE],
    RoomType.LIVING_ROOM: [
        FurnitureType.ARMCHAIR,
        FurnitureType.ARMCHAIR,
        FurnitureType.SHELVING,
    ],
    RoomType.BEDROOM: [
        FurnitureType.NIGHTSTAND,
        FurnitureType.NIGHTSTAND,
        FurnitureType.DRESSER,
    ],
    RoomType.CHILDREN: [FurnitureType.BOOKSHELF],
    RoomType.BATHROOM: [FurnitureType.WASHING_MACHINE],
    RoomType.COMBINED_BATHROOM: [FurnitureType.WASHING_MACHINE],
}


def determine_composition(
    apartment_class: ApartmentClass,
    num_rooms: int,
    rng: random.Random | None = None,
) -> list[RoomType]:
    """Determine room composition for given class and room count.

    For 2+ room apartments, randomly chooses between separate
    bathroom + toilet and a combined bathroom (50/50).
    """
    base = list(_BASE_COMPOSITIONS[num_rooms])
    extras = _CLASS_EXTRAS.get(apartment_class, [])
    composition = base + extras

    # Optionally merge bathroom + toilet into combined bathroom
    if (
        num_rooms >= 2
        and rng is not None
        and RoomType.BATHROOM in composition
        and RoomType.TOILET in composition
        and rng.random() < 0.5
    ):
        composition.remove(RoomType.BATHROOM)
        composition.remove(RoomType.TOILET)
        composition.append(RoomType.COMBINED_BATHROOM)

    return composition


def assign_sizes(
    composition: list[RoomType],
    rng: random.Random,
    apartment_class: ApartmentClass,
    num_rooms: int,
) -> list[RoomSpec]:
    """Assign random sizes to rooms within allowed ranges, scaled to target area."""
    target_min, target_max = APARTMENT_AREAS[apartment_class][num_rooms]
    target_mm2 = rng.uniform(target_min, target_max) * 1_000_000

    specs = []
    for rt in composition:
        min_w, max_w, min_h, max_h = _SIZE_RANGES.get(
            rt, (1000, 2000, 1000, 2000),
        )
        w = rng.uniform(min_w, max_w)
        h = rng.uniform(min_h, max_h)
        specs.append(RoomSpec(
            room_type=rt,
            width=round(w / 50) * 50,
            height=round(h / 50) * 50,
        ))

    # Scale to match target area
    total = sum(s.width * s.height for s in specs)
    if total > 0:
        scale = (target_mm2 / total) ** 0.5
        scaled = []
        for s in specs:
            min_w, max_w, min_h, max_h = _SIZE_RANGES.get(
                s.room_type, (1000, 2000, 1000, 2000),
            )
            new_w = max(min_w, min(max_w, round(s.width * scale / 50) * 50))
            new_h = max(min_h, min(max_h, round(s.height * scale / 50) * 50))
            scaled.append(RoomSpec(
                room_type=s.room_type, width=new_w, height=new_h,
            ))
        return scaled
    return specs


def get_canvas(
    apartment_class: ApartmentClass,
    num_rooms: int,
    rng: random.Random,
) -> Rectangle:
    """Generate canvas rectangle for the apartment."""
    target_min, target_max = APARTMENT_AREAS[apartment_class][num_rooms]
    target_mm2 = rng.uniform(target_min, target_max) * 1_000_000
    aspect = rng.uniform(1.0, 1.8)
    width = (target_mm2 * aspect) ** 0.5
    height = target_mm2 / width
    # Add 20% padding
    return Rectangle(x=0, y=0, width=width * 1.2, height=height * 1.2)


def get_furniture_list(
    room_type: RoomType,
    apartment_class: ApartmentClass,
    area_m2: float,
    rng: random.Random,
) -> list[FurnitureType]:
    """Determine furniture list for a room."""
    required = list(REQUIRED_FURNITURE.get(room_type, []))
    optional = OPTIONAL_FURNITURE.get(room_type, [])

    if apartment_class in (ApartmentClass.BUSINESS, ApartmentClass.PREMIUM):
        for item in optional:
            if rng.random() < 0.7:
                required.append(item)
    elif apartment_class == ApartmentClass.COMFORT:
        for item in optional:
            if rng.random() < 0.4:
                required.append(item)

    # Size-based upgrades
    if room_type == RoomType.BEDROOM and area_m2 >= 14:
        if FurnitureType.BED_DOUBLE in required:
            idx = required.index(FurnitureType.BED_DOUBLE)
            required[idx] = FurnitureType.BED_KING

    return required
