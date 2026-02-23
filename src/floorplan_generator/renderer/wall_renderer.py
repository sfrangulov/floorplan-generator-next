"""Wall rendering: filled rectangles with real thickness and door/window openings."""

from __future__ import annotations

from dataclasses import dataclass

import svgwrite.container
import svgwrite.drawing

from floorplan_generator.core.geometry import Point, Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.theme import Theme

_EDGE_EPS = 1.0  # mm tolerance for shared edge detection


@dataclass
class _Opening:
    """An opening (door or window) on a wall segment."""

    offset_start: float  # distance along wall from wall start
    offset_end: float  # distance along wall from wall start


def _room_edges(room: Room) -> list[Segment]:
    """Get all edges of a room boundary as segments."""
    pts = room.boundary.points
    n = len(pts)
    return [Segment(start=pts[i], end=pts[(i + 1) % n]) for i in range(n)]


def _segments_overlap(a: Segment, b: Segment, eps: float = _EDGE_EPS) -> bool:
    """Check if two segments share a collinear overlap (shared wall)."""
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


def _is_horizontal(seg: Segment) -> bool:
    return abs(seg.start.y - seg.end.y) < _EDGE_EPS


def _is_vertical(seg: Segment) -> bool:
    return abs(seg.start.x - seg.end.x) < _EDGE_EPS


def _classify_edges(
    rooms: list[Room],
) -> tuple[list[Segment], list[Segment]]:
    """Classify room edges as outer or inner walls."""
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


def _collect_openings(seg: Segment, rooms: list[Room]) -> list[_Opening]:
    """Find all door/window openings on a given wall segment."""
    openings: list[_Opening] = []
    horiz = _is_horizontal(seg)
    vert = _is_vertical(seg)

    if not horiz and not vert:
        return openings

    if horiz:
        seg_min = min(seg.start.x, seg.end.x)
        seg_max = max(seg.start.x, seg.end.x)
        seg_coord = seg.start.y
    else:
        seg_min = min(seg.start.y, seg.end.y)
        seg_max = max(seg.start.y, seg.end.y)
        seg_coord = seg.start.x

    for room in rooms:
        for door in room.doors:
            dp = door.position
            dw = door.width
            if horiz:
                if abs(dp.y - seg_coord) < _EDGE_EPS * 2:
                    d_start = dp.x
                    d_end = dp.x + dw
                    if d_start >= seg_min - _EDGE_EPS and d_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, d_start - seg_min),
                            offset_end=min(seg_max - seg_min, d_end - seg_min),
                        ))
            elif vert:
                if abs(dp.x - seg_coord) < _EDGE_EPS * 2:
                    d_start = dp.y
                    d_end = dp.y + dw
                    if d_start >= seg_min - _EDGE_EPS and d_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, d_start - seg_min),
                            offset_end=min(seg_max - seg_min, d_end - seg_min),
                        ))

        for window in room.windows:
            wp = window.position
            ww = window.width
            if horiz and window.wall_side in ("north", "south"):
                if abs(wp.y - seg_coord) < _EDGE_EPS * 2:
                    w_start = wp.x
                    w_end = wp.x + ww
                    if w_start >= seg_min - _EDGE_EPS and w_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, w_start - seg_min),
                            offset_end=min(seg_max - seg_min, w_end - seg_min),
                        ))
            elif vert and window.wall_side in ("east", "west"):
                if abs(wp.x - seg_coord) < _EDGE_EPS * 2:
                    w_start = wp.y
                    w_end = wp.y + ww
                    if w_start >= seg_min - _EDGE_EPS and w_end <= seg_max + _EDGE_EPS:
                        openings.append(_Opening(
                            offset_start=max(0.0, w_start - seg_min),
                            offset_end=min(seg_max - seg_min, w_end - seg_min),
                        ))

    openings.sort(key=lambda o: o.offset_start)
    return openings


def _split_around_openings(
    total_length: float,
    openings: list[_Opening],
) -> list[tuple[float, float]]:
    """Split a wall into sub-segments avoiding openings."""
    if not openings:
        return [(0.0, total_length)]

    pieces: list[tuple[float, float]] = []
    cursor = 0.0
    for op in openings:
        if op.offset_start > cursor + _EDGE_EPS:
            pieces.append((cursor, op.offset_start))
        cursor = max(cursor, op.offset_end)
    if cursor < total_length - _EDGE_EPS:
        pieces.append((cursor, total_length))
    return pieces


def _render_wall_segment(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    seg: Segment,
    thickness_px: float,
    fill: str,
    rooms: list[Room],
    mapper: CoordinateMapper,
) -> None:
    """Render one wall segment as filled rects, with openings cut out."""
    horiz = _is_horizontal(seg)
    vert = _is_vertical(seg)

    if not horiz and not vert:
        start = mapper.to_svg(seg.start)
        end = mapper.to_svg(seg.end)
        group.add(dwg.line(start=start, end=end, stroke=fill, stroke_width=thickness_px))
        return

    openings = _collect_openings(seg, rooms)

    if horiz:
        seg_min_x = min(seg.start.x, seg.end.x)
        seg_max_x = max(seg.start.x, seg.end.x)
        total_len = seg_max_x - seg_min_x
        pieces = _split_around_openings(total_len, openings)

        for piece_start, piece_end in pieces:
            p1 = mapper.to_svg(Point(x=seg_min_x + piece_start, y=seg.start.y))
            p2 = mapper.to_svg(Point(x=seg_min_x + piece_end, y=seg.start.y))
            rect_w = p2[0] - p1[0]
            if rect_w < 1.0:
                continue
            group.add(dwg.rect(
                insert=(p1[0], p1[1] - thickness_px / 2),
                size=(rect_w, thickness_px),
                fill=fill,
                stroke="none",
            ))
    else:  # vertical
        seg_min_y = min(seg.start.y, seg.end.y)
        seg_max_y = max(seg.start.y, seg.end.y)
        total_len = seg_max_y - seg_min_y
        pieces = _split_around_openings(total_len, openings)

        for piece_start, piece_end in pieces:
            p1 = mapper.to_svg(Point(x=seg.start.x, y=seg_min_y + piece_start))
            p2 = mapper.to_svg(Point(x=seg.start.x, y=seg_min_y + piece_end))
            rect_h = p2[1] - p1[1]
            if rect_h < 1.0:
                continue
            group.add(dwg.rect(
                insert=(p1[0] - thickness_px / 2, p1[1]),
                size=(thickness_px, rect_h),
                fill=fill,
                stroke="none",
            ))


def render_walls(
    dwg: svgwrite.drawing.Drawing,
    group: svgwrite.container.Group,
    rooms: list[Room],
    mapper: CoordinateMapper,
    theme: Theme,
) -> None:
    """Render walls as filled rects with real thickness and openings."""
    outer, inner = _classify_edges(rooms)

    outer_t = mapper.scale_thickness(theme.walls.outer_thickness)
    inner_t = mapper.scale_thickness(theme.walls.inner_thickness)

    for seg in outer:
        _render_wall_segment(
            dwg, group, seg, outer_t,
            theme.walls.outer_fill, rooms, mapper,
        )

    for seg in inner:
        _render_wall_segment(
            dwg, group, seg, inner_t,
            theme.walls.inner_fill, rooms, mapper,
        )
