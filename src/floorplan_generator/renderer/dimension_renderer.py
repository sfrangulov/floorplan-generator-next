"""Dimension annotation renderer — architectural dimension lines with labels."""

from __future__ import annotations

import svgwrite

from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

# Tolerance for detecting rooms touching the apartment edge (1 mm)
_EDGE_TOL = 1.0


def render_dimensions(
    dwg: svgwrite.Drawing,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Add dimension annotation chains along top and left edges."""
    if not rooms:
        return

    dim = theme.dimensions
    group = dwg.g(id="dimensions")

    apt_bbox = _apartment_bbox(rooms)

    # Top edge: horizontal dimension chain
    top_splits = _find_edge_splits_top(rooms, apt_bbox)
    if len(top_splits) >= 2:
        y_mm = apt_bbox["min_y"]
        svg_y = mapper.to_svg_raw(0, y_mm)[1]
        level1_y = svg_y - dim.offset
        level2_y = level1_y - dim.level_gap

        # Level 1: individual segments
        for i in range(len(top_splits) - 1):
            x1_mm, x2_mm = top_splits[i], top_splits[i + 1]
            _draw_horizontal_dim(
                dwg, group, mapper, dim,
                x1_mm, x2_mm, level1_y, svg_y,
            )

        # Level 2: overall width
        _draw_horizontal_dim(
            dwg, group, mapper, dim,
            top_splits[0], top_splits[-1], level2_y, svg_y,
        )

    # Left edge: vertical dimension chain
    left_splits = _find_edge_splits_left(rooms, apt_bbox)
    if len(left_splits) >= 2:
        x_mm = apt_bbox["min_x"]
        svg_x = mapper.to_svg_raw(x_mm, 0)[0]
        level1_x = svg_x - dim.offset
        level2_x = level1_x - dim.level_gap

        # Level 1: individual segments
        for i in range(len(left_splits) - 1):
            y1_mm, y2_mm = left_splits[i], left_splits[i + 1]
            _draw_vertical_dim(
                dwg, group, mapper, dim,
                y1_mm, y2_mm, level1_x, svg_x,
            )

        # Level 2: overall height
        _draw_vertical_dim(
            dwg, group, mapper, dim,
            left_splits[0], left_splits[-1], level2_x, svg_x,
        )

    dwg.add(group)


def _apartment_bbox(rooms: list[Room]) -> dict[str, float]:
    """Compute apartment bounding box as union of all room bboxes."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for room in rooms:
        bb = room.boundary.bounding_box
        min_x = min(min_x, bb.x)
        min_y = min(min_y, bb.y)
        max_x = max(max_x, bb.x + bb.width)
        max_y = max(max_y, bb.y + bb.height)
    return {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}


def _find_edge_splits_top(
    rooms: list[Room], apt_bbox: dict[str, float],
) -> list[float]:
    """Find x-coordinate splits along the top edge of the apartment."""
    top_y = apt_bbox["min_y"]
    splits: set[float] = set()
    for room in rooms:
        bb = room.boundary.bounding_box
        if abs(bb.y - top_y) <= _EDGE_TOL:
            splits.add(bb.x)
            splits.add(bb.x + bb.width)
    # Clamp to apartment bbox range
    splits = {x for x in splits if apt_bbox["min_x"] - _EDGE_TOL <= x <= apt_bbox["max_x"] + _EDGE_TOL}
    return sorted(splits)


def _find_edge_splits_left(
    rooms: list[Room], apt_bbox: dict[str, float],
) -> list[float]:
    """Find y-coordinate splits along the left edge of the apartment."""
    left_x = apt_bbox["min_x"]
    splits: set[float] = set()
    for room in rooms:
        bb = room.boundary.bounding_box
        if abs(bb.x - left_x) <= _EDGE_TOL:
            splits.add(bb.y)
            splits.add(bb.y + bb.height)
    # Clamp to apartment bbox range
    splits = {y for y in splits if apt_bbox["min_y"] - _EDGE_TOL <= y <= apt_bbox["max_y"] + _EDGE_TOL}
    return sorted(splits)


def _draw_horizontal_dim(
    dwg: svgwrite.Drawing,
    group: svgwrite.container.Group,
    mapper: CoordinateMapper,
    dim,
    x1_mm: float,
    x2_mm: float,
    dim_y: float,
    wall_y: float,
) -> None:
    """Draw a horizontal dimension line between two x positions (mm)."""
    sx1 = mapper.to_svg_raw(x1_mm, 0)[0]
    sx2 = mapper.to_svg_raw(x2_mm, 0)[0]
    length_mm = abs(x2_mm - x1_mm)
    label = f"{length_mm / 1000:.{dim.precision}f}"

    style = {"stroke": dim.stroke, "stroke_width": dim.stroke_width}

    # Extension lines (from wall down to dimension line level)
    group.add(dwg.line(start=(sx1, wall_y), end=(sx1, dim_y - dim.tick_size), **style))
    group.add(dwg.line(start=(sx2, wall_y), end=(sx2, dim_y - dim.tick_size), **style))

    # Main dimension line
    group.add(dwg.line(start=(sx1, dim_y), end=(sx2, dim_y), **style))

    # Tick marks (perpendicular)
    group.add(dwg.line(
        start=(sx1, dim_y - dim.tick_size), end=(sx1, dim_y + dim.tick_size), **style,
    ))
    group.add(dwg.line(
        start=(sx2, dim_y - dim.tick_size), end=(sx2, dim_y + dim.tick_size), **style,
    ))

    # Label
    mid_x = (sx1 + sx2) / 2
    group.add(dwg.text(
        label,
        insert=(mid_x, dim_y - dim.tick_size - 2),
        text_anchor="middle",
        font_family=dim.font_family,
        font_size=dim.font_size,
        fill=dim.fill,
    ))


def _draw_vertical_dim(
    dwg: svgwrite.Drawing,
    group: svgwrite.container.Group,
    mapper: CoordinateMapper,
    dim,
    y1_mm: float,
    y2_mm: float,
    dim_x: float,
    wall_x: float,
) -> None:
    """Draw a vertical dimension line between two y positions (mm)."""
    sy1 = mapper.to_svg_raw(0, y1_mm)[1]
    sy2 = mapper.to_svg_raw(0, y2_mm)[1]
    length_mm = abs(y2_mm - y1_mm)
    label = f"{length_mm / 1000:.{dim.precision}f}"

    style = {"stroke": dim.stroke, "stroke_width": dim.stroke_width}

    # Extension lines (from wall to dimension line level)
    group.add(dwg.line(start=(wall_x, sy1), end=(dim_x - dim.tick_size, sy1), **style))
    group.add(dwg.line(start=(wall_x, sy2), end=(dim_x - dim.tick_size, sy2), **style))

    # Main dimension line
    group.add(dwg.line(start=(dim_x, sy1), end=(dim_x, sy2), **style))

    # Tick marks (perpendicular)
    group.add(dwg.line(
        start=(dim_x - dim.tick_size, sy1), end=(dim_x + dim.tick_size, sy1), **style,
    ))
    group.add(dwg.line(
        start=(dim_x - dim.tick_size, sy2), end=(dim_x + dim.tick_size, sy2), **style,
    ))

    # Label (rotated 90 degrees)
    mid_y = (sy1 + sy2) / 2
    group.add(dwg.text(
        label,
        insert=(dim_x - dim.tick_size - 2, mid_y),
        text_anchor="middle",
        font_family=dim.font_family,
        font_size=dim.font_size,
        fill=dim.fill,
        transform=f"rotate(-90, {dim_x - dim.tick_size - 2}, {mid_y})",
    ))
