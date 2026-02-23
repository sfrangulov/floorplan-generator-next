"""Wall rendering: outer perimeter (thick) + inner partitions (thin)."""

from __future__ import annotations

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.geometry import Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_EDGE_EPS = 1.0  # mm tolerance for shared edge detection


def _room_edges(room: Room) -> list[Segment]:
    """Get all edges of a room boundary as segments."""
    pts = room.boundary.points
    n = len(pts)
    return [
        Segment(start=pts[i], end=pts[(i + 1) % n])
        for i in range(n)
    ]


def _segments_overlap(a: Segment, b: Segment, eps: float = _EDGE_EPS) -> bool:
    """Check if two segments share a collinear overlap (shared wall)."""
    # Both must be axis-aligned for simple check
    a_horiz = abs(a.start.y - a.end.y) < eps
    b_horiz = abs(b.start.y - b.end.y) < eps
    a_vert = abs(a.start.x - a.end.x) < eps
    b_vert = abs(b.start.x - b.end.x) < eps

    if a_horiz and b_horiz and abs(a.start.y - b.start.y) < eps:
        a_min = min(a.start.x, a.end.x)
        a_max = max(a.start.x, a.end.x)
        b_min = min(b.start.x, b.end.x)
        b_max = max(b.start.x, b.end.x)
        return a_min < b_max - eps and b_min < a_max - eps

    if a_vert and b_vert and abs(a.start.x - b.start.x) < eps:
        a_min = min(a.start.y, a.end.y)
        a_max = max(a.start.y, a.end.y)
        b_min = min(b.start.y, b.end.y)
        b_max = max(b.start.y, b.end.y)
        return a_min < b_max - eps and b_min < a_max - eps

    return False


def _classify_edges(
    rooms: list[Room],
) -> tuple[list[Segment], list[Segment]]:
    """Classify room edges as outer or inner walls.

    An edge is inner if it overlaps with an edge of another room.
    Otherwise it's outer (perimeter).
    """
    all_edges: list[tuple[int, Segment]] = []
    for i, room in enumerate(rooms):
        for seg in _room_edges(room):
            all_edges.append((i, seg))

    outer: list[Segment] = []
    inner_set: set[int] = set()

    for idx_a, (room_a, seg_a) in enumerate(all_edges):
        is_shared = False
        for idx_b, (room_b, seg_b) in enumerate(all_edges):
            if room_a == room_b:
                continue
            if _segments_overlap(seg_a, seg_b):
                is_shared = True
                if idx_a not in inner_set:
                    inner_set.add(idx_a)
                break
        if not is_shared:
            outer.append(seg_a)

    inner = [all_edges[i][1] for i in inner_set]
    return outer, inner


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render outer walls (thick) and inner walls (thin)."""
    outer, inner = _classify_edges(rooms)

    for seg in outer:
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(
            start=start, end=end,
            stroke=theme.walls.outer_stroke,
            stroke_width=theme.walls.outer_width,
            stroke_linecap="round",
        ))

    for seg in inner:
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(
            start=start, end=end,
            stroke=theme.walls.inner_stroke,
            stroke_width=theme.walls.inner_width,
            stroke_linecap="round",
        ))
