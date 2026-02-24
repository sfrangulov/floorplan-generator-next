"""Wall outline computation using Shapely polygon operations."""

from __future__ import annotations

from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box
from shapely.ops import unary_union

from floorplan_generator.core.geometry import Segment
from floorplan_generator.core.models import Room
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper

_EDGE_EPS = 1.0  # mm tolerance


def _room_to_shapely(room: Room) -> ShapelyPolygon:
    """Convert room boundary to Shapely polygon."""
    coords = [(pt.x, pt.y) for pt in room.boundary.points]
    return ShapelyPolygon(coords)


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
        overlap_start = max(a_min, b_min)
        overlap_end = min(a_max, b_max)
        if overlap_end - overlap_start > eps:
            return True

    if a_vert and b_vert and abs(a.start.x - b.start.x) < eps:
        a_min = min(a.start.y, a.end.y)
        a_max = max(a.start.y, a.end.y)
        b_min = min(b.start.y, b.end.y)
        b_max = max(b.start.y, b.end.y)
        overlap_start = max(a_min, b_min)
        overlap_end = min(a_max, b_max)
        if overlap_end - overlap_start > eps:
            return True

    return False


def _find_shared_edges(rooms: list[Room]) -> list[Segment]:
    """Find all shared edges between rooms (for inner walls)."""
    all_edges: list[tuple[int, Segment]] = []
    for i, room in enumerate(rooms):
        for seg in _room_edges(room):
            all_edges.append((i, seg))

    shared: list[Segment] = []
    seen: set[int] = set()

    for idx_a, (room_a, seg_a) in enumerate(all_edges):
        if idx_a in seen:
            continue
        for idx_b, (room_b, seg_b) in enumerate(all_edges):
            if room_a == room_b:
                continue
            if _segments_overlap(seg_a, seg_b):
                if idx_a not in seen:
                    shared.append(seg_a)
                    seen.add(idx_a)
                break

    return shared


def _segment_to_box(seg: Segment, thickness: float) -> ShapelyPolygon:
    """Create a thin rectangle (Shapely box) centered on a segment."""
    half_t = thickness / 2.0
    is_horiz = abs(seg.start.y - seg.end.y) < _EDGE_EPS

    if is_horiz:
        x_min = min(seg.start.x, seg.end.x)
        x_max = max(seg.start.x, seg.end.x)
        y_center = seg.start.y
        return box(x_min, y_center - half_t, x_max, y_center + half_t)
    else:
        y_min = min(seg.start.y, seg.end.y)
        y_max = max(seg.start.y, seg.end.y)
        x_center = seg.start.x
        return box(x_center - half_t, y_min, x_center + half_t, y_max)


def _window_opening_box(window, wall_thickness: float) -> ShapelyPolygon:
    """Create a rectangular cutout for a window opening."""
    pos = window.position
    w = window.width
    half_t = wall_thickness / 2.0 + 10.0

    if window.wall_side in ("north", "south"):
        return box(pos.x, pos.y - half_t, pos.x + w, pos.y + half_t)
    else:
        return box(pos.x - half_t, pos.y, pos.x + half_t, pos.y + w)


def _door_opening_box(door, wall_thickness: float) -> ShapelyPolygon:
    """Create a rectangular cutout for a door opening."""
    pos = door.position
    w = door.width
    half_t = wall_thickness / 2.0 + 10.0

    if door.wall_orientation == "horizontal":
        return box(pos.x, pos.y - half_t, pos.x + w, pos.y + half_t)
    else:
        return box(pos.x - half_t, pos.y, pos.x + half_t, pos.y + w)


def compute_outer_wall_polygon(
    rooms: list[Room],
    thickness: float = 225.0,
    *,
    cut_windows: bool = False,
    cut_doors: bool = False,
) -> ShapelyPolygon:
    """Compute exterior wall polygon as a ring.

    1. Union all room boundaries -> inner contour
    2. Buffer outward by thickness -> outer contour
    3. Difference -> wall ring
    4. Optionally cut window/door openings
    """
    if not rooms:
        return ShapelyPolygon()

    room_polys = [_room_to_shapely(r) for r in rooms]
    inner = unary_union(room_polys)
    outer = inner.buffer(thickness, join_style="mitre", mitre_limit=5.0)
    wall_ring = outer.difference(inner)

    if cut_windows:
        for room in rooms:
            for window in room.windows:
                opening = _window_opening_box(window, thickness)
                wall_ring = wall_ring.difference(opening)

    if cut_doors:
        from floorplan_generator.core.enums import DoorType
        seen_ids: set[str] = set()
        for room in rooms:
            for door in room.doors:
                if door.id in seen_ids:
                    continue
                seen_ids.add(door.id)
                if door.door_type == DoorType.ENTRANCE:
                    opening = _door_opening_box(door, thickness)
                    wall_ring = wall_ring.difference(opening)

    return wall_ring


def compute_inner_wall_polygons(
    rooms: list[Room],
    thickness: float = 75.0,
    *,
    cut_doors: bool = True,
) -> ShapelyPolygon:
    """Compute interior wall polygons from shared edges.

    1. Find shared edges between rooms
    2. Create thin rectangle for each shared edge
    3. Union all rectangles
    4. Optionally cut door openings
    """
    if len(rooms) < 2:
        return ShapelyPolygon()

    shared_edges = _find_shared_edges(rooms)
    if not shared_edges:
        return ShapelyPolygon()

    wall_boxes = [_segment_to_box(seg, thickness) for seg in shared_edges]
    wall_union = unary_union(wall_boxes)

    if cut_doors:
        seen_ids: set[str] = set()
        for room in rooms:
            for door in room.doors:
                if door.id in seen_ids:
                    continue
                seen_ids.add(door.id)
                opening = _door_opening_box(door, thickness)
                wall_union = wall_union.difference(opening)

    return wall_union


def shapely_to_svg_path(
    poly: ShapelyPolygon,
    mapper: CoordinateMapper,
) -> str:
    """Convert a Shapely polygon (possibly with holes) to SVG path d attribute."""
    if poly.is_empty:
        return ""

    parts = []

    def _ring_to_commands(coords: list[tuple[float, float]]) -> str:
        cmds = []
        for i, (mx, my) in enumerate(coords):
            sx, sy = mapper.to_svg_raw(mx, my)
            if i == 0:
                cmds.append(f"M {sx},{sy}")
            else:
                cmds.append(f"L {sx},{sy}")
        cmds.append("Z")
        return " ".join(cmds)

    if poly.geom_type == "Polygon":
        ext_coords = list(poly.exterior.coords)
        parts.append(_ring_to_commands(ext_coords))
        for interior in poly.interiors:
            int_coords = list(interior.coords)
            parts.append(_ring_to_commands(int_coords))
    elif poly.geom_type == "MultiPolygon":
        for sub_poly in poly.geoms:
            ext_coords = list(sub_poly.exterior.coords)
            parts.append(_ring_to_commands(ext_coords))
            for interior in sub_poly.interiors:
                int_coords = list(interior.coords)
                parts.append(_ring_to_commands(int_coords))

    return " ".join(parts)
