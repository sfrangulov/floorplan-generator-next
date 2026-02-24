"""SVG pattern fills for walls and rooms (hatching, brick, tile, etc.)."""

from __future__ import annotations

from collections.abc import Callable

import svgwrite.drawing
import svgwrite.pattern


def _build_hatch(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """45-degree diagonal line hatch."""
    p = dwg.pattern(
        id=pattern_id, size=(8, 8),
        patternUnits="userSpaceOnUse",
        patternTransform="rotate(45)",
    )
    p.add(dwg.line(start=(0, 0), end=(0, 8), stroke=color, stroke_width=1.5))
    return p


def _build_crosshatch(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """45-degree + 135-degree crosshatch."""
    p = dwg.pattern(
        id=pattern_id, size=(8, 8),
        patternUnits="userSpaceOnUse",
    )
    p.add(dwg.line(start=(0, 0), end=(8, 8), stroke=color, stroke_width=1))
    p.add(dwg.line(start=(8, 0), end=(0, 8), stroke=color, stroke_width=1))
    return p


def _build_brick(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """Staggered brick pattern."""
    p = dwg.pattern(
        id=pattern_id, size=(16, 12),
        patternUnits="userSpaceOnUse",
    )
    # Row 1 – full-width brick
    p.add(dwg.rect(insert=(0, 0), size=(16, 6),
                    fill="none", stroke=color, stroke_width=1))
    # Row 2 – half-offset brick
    p.add(dwg.rect(insert=(-8, 6), size=(16, 6),
                    fill="none", stroke=color, stroke_width=1))
    p.add(dwg.rect(insert=(8, 6), size=(16, 6),
                    fill="none", stroke=color, stroke_width=1))
    return p


def _build_tile(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """Square grid tile (bathrooms)."""
    p = dwg.pattern(
        id=pattern_id, size=(12, 12),
        patternUnits="userSpaceOnUse",
    )
    p.add(dwg.rect(insert=(0, 0), size=(12, 12),
                    fill="none", stroke=color, stroke_width=0.8))
    return p


def _build_wood(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """Parallel horizontal lines (wood grain)."""
    p = dwg.pattern(
        id=pattern_id, size=(20, 6),
        patternUnits="userSpaceOnUse",
    )
    p.add(dwg.line(start=(0, 3), end=(20, 3), stroke=color, stroke_width=0.8))
    p.add(dwg.line(start=(0, 6), end=(20, 6), stroke=color, stroke_width=0.4))
    return p


def _build_dots(
    dwg: svgwrite.drawing.Drawing, pattern_id: str, color: str,
) -> svgwrite.pattern.Pattern:
    """Dot stipple pattern."""
    p = dwg.pattern(
        id=pattern_id, size=(8, 8),
        patternUnits="userSpaceOnUse",
    )
    p.add(dwg.circle(center=(4, 4), r=1.2, fill=color))
    return p


PATTERN_CATALOG: dict[str, Callable[
    [svgwrite.drawing.Drawing, str, str], svgwrite.pattern.Pattern
]] = {
    "hatch": _build_hatch,
    "crosshatch": _build_crosshatch,
    "brick": _build_brick,
    "tile": _build_tile,
    "wood": _build_wood,
    "dots": _build_dots,
}


def is_pattern_ref(fill: str) -> bool:
    """Check whether *fill* is a ``pattern:<name>:<color>`` reference."""
    return fill.startswith("pattern:")


def parse_pattern_ref(fill: str) -> tuple[str, str]:
    """Split ``"pattern:hatch:#000"`` into ``("hatch", "#000")``."""
    parts = fill.split(":", 2)
    if len(parts) != 3:  # noqa: PLR2004
        msg = f"Invalid pattern reference: {fill!r}"
        raise ValueError(msg)
    return parts[1], parts[2]


def resolve_fill(
    dwg: svgwrite.drawing.Drawing,
    fill_value: str,
    context_id: str,
    registered_patterns: set[str] | None = None,
) -> str:
    """Return an SVG fill string — plain color or ``url(#pat-...)``."""
    if not is_pattern_ref(fill_value):
        return fill_value

    name, color = parse_pattern_ref(fill_value)
    if name not in PATTERN_CATALOG:
        return color  # fallback to plain color

    # Build a deterministic pattern element id
    color_slug = color.lstrip("#")
    pattern_id = f"pat-{context_id}-{name}-{color_slug}"

    if registered_patterns is None:
        registered_patterns = set()

    if pattern_id not in registered_patterns:
        builder = PATTERN_CATALOG[name]
        pat = builder(dwg, pattern_id, color)
        dwg.defs.add(pat)
        registered_patterns.add(pattern_id)

    return f"url(#{pattern_id})"
