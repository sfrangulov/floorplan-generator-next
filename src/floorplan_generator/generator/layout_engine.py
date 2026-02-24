"""Orchestrator: Greedy → CSP → Validate → Apartment."""

from __future__ import annotations

import random
import uuid

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.core.models import Apartment
from floorplan_generator.generator.csp.solver import csp_solve
from floorplan_generator.generator.greedy.engine import greedy_layout
from floorplan_generator.generator.room_composer import (
    assign_sizes,
    determine_composition,
    get_canvas,
)
from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.rules.registry import create_default_registry
from floorplan_generator.rules.rule_engine import RuleResult, RuleStatus

MAX_MANDATORY_FAILURES = 0


def _validate_apartment(apartment: Apartment) -> tuple[int, list[RuleResult]]:
    """Validate apartment and return (mandatory_failure_count, all_violations)."""
    registry = create_default_registry()
    results = registry.validate_all(apartment)
    violations = [r for r in results if r.status in (RuleStatus.FAIL, RuleStatus.WARN)]
    mandatory_failures = sum(
        1 for r in results
        if r.status == RuleStatus.FAIL
        and registry.get(r.rule_id).is_mandatory
    )
    return mandatory_failures, violations


def generate_apartment(
    apartment_class: ApartmentClass,
    num_rooms: int,
    seed: int,
    max_restarts: int = 20,
    temperature: float = 0.5,
) -> GenerationResult | None:
    """Generate a complete apartment: rooms, doors, windows, furniture."""
    composition = determine_composition(apartment_class, num_rooms)
    best_result: GenerationResult | None = None
    best_failures = float("inf")

    for restart in range(max_restarts):
        current_seed = seed + restart * 1000
        rng = random.Random(current_seed)

        specs = assign_sizes(composition, rng, apartment_class, num_rooms)
        canvas = get_canvas(apartment_class, num_rooms, rng)

        # Greedy: place rooms
        greedy_result = greedy_layout(
            specs, canvas, current_seed,
            max_restarts=5,
            temperature=temperature,
        )
        if greedy_result is None or not greedy_result.success:
            continue

        # CSP: doors, windows, risers, furniture
        csp_rng = random.Random(current_seed + 500)
        csp_result = csp_solve(
            greedy_result.rooms,
            greedy_result.shared_walls,
            canvas,
            apartment_class,
            csp_rng,
        )
        if not csp_result.success:
            continue

        # Build apartment
        apartment = Apartment(
            id=uuid.uuid4().hex[:8],
            apartment_class=apartment_class,
            rooms=csp_result.rooms,
            num_rooms=num_rooms,
        )

        # Validate: check mandatory rule failures
        failures, violations = _validate_apartment(apartment)

        result = GenerationResult(
            apartment=apartment,
            risers=[],
            restart_count=restart,
            seed_used=current_seed,
            recommended_violations=csp_result.soft_violations,
            violations=violations,
        )

        if failures <= MAX_MANDATORY_FAILURES:
            return result  # Good enough

        # Track best result so far
        if failures < best_failures:
            best_failures = failures
            best_result = result

    return best_result
