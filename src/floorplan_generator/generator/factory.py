"""Dataset generation factory."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.generator.types import GenerationResult

logger = logging.getLogger(__name__)


def generate_single(
    apartment_class: ApartmentClass,
    num_rooms: int,
    seed: int,
    max_restarts: int = 10,
) -> GenerationResult | None:
    """Generate a single apartment."""
    return generate_apartment(
        apartment_class, num_rooms, seed, max_restarts,
    )


def generate_dataset(
    apartment_class: ApartmentClass,
    num_rooms: int,
    count: int,
    seed: int,
    output: Path,
    max_restarts: int = 10,
) -> list[dict]:
    """Generate a dataset of apartments and save metadata.

    Returns metadata list.
    """
    output.mkdir(parents=True, exist_ok=True)
    metadata = []

    for i in range(count):
        result = generate_single(
            apartment_class, num_rooms,
            seed=seed + i,
            max_restarts=max_restarts,
        )

        if result is None:
            logger.warning("Failed to generate #%d", i)
            continue

        entry = {
            "index": i,
            "filename": f"{apartment_class.value}_{num_rooms}r_{i:04d}",
            "class": apartment_class.value,
            "rooms": num_rooms,
            "total_area_m2": round(result.apartment.total_area_m2, 1),
            "room_count": len(result.apartment.rooms),
            "restart_count": result.restart_count,
            "seed_used": result.seed_used,
            "recommended_violations": result.recommended_violations,
        }
        metadata.append(entry)

    # Save metadata
    meta_path = output / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return metadata
