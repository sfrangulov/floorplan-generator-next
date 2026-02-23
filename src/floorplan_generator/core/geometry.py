"""Geometric primitives for 2D floorplan operations."""

from __future__ import annotations

import math

from pydantic import BaseModel, model_validator


class Point(BaseModel, frozen=True):
    """2D point."""

    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Segment(BaseModel, frozen=True):
    """Line segment between two points."""

    start: Point
    end: Point

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point:
        return Point(
            x=(self.start.x + self.end.x) / 2,
            y=(self.start.y + self.end.y) / 2,
        )

    def intersects(self, other: Segment) -> bool:
        return segments_intersect(self, other)


class Rectangle(BaseModel, frozen=True):
    """Axis-aligned rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Point:
        return Point(x=self.x + self.width / 2, y=self.y + self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        sides = sorted([self.width, self.height])
        if sides[0] == 0:
            return float("inf")
        return sides[1] / sides[0]

    @property
    def corners(self) -> list[Point]:
        return [
            Point(x=self.x, y=self.y),
            Point(x=self.x + self.width, y=self.y),
            Point(x=self.x + self.width, y=self.y + self.height),
            Point(x=self.x, y=self.y + self.height),
        ]

    def contains(self, point: Point) -> bool:
        return (
            self.x <= point.x <= self.x + self.width
            and self.y <= point.y <= self.y + self.height
        )

    def overlaps(self, other: Rectangle) -> bool:
        """Strict overlap — touching edges do NOT count."""
        return rectangles_overlap(self, other)

    def distance_to(self, other: Rectangle) -> float:
        return min_distance_rect_to_rect(self, other)


class Polygon(BaseModel, frozen=True):
    """Arbitrary polygon defined by ordered vertices."""

    points: list[Point]

    @model_validator(mode="after")
    def _check_min_points(self) -> Polygon:
        if len(self.points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        return self

    @property
    def area(self) -> float:
        """Shoelace formula (absolute value)."""
        n = len(self.points)
        s = 0.0
        for i in range(n):
            j = (i + 1) % n
            s += self.points[i].x * self.points[j].y
            s -= self.points[j].x * self.points[i].y
        return abs(s) / 2.0

    @property
    def perimeter(self) -> float:
        n = len(self.points)
        return sum(
            self.points[i].distance_to(self.points[(i + 1) % n]) for i in range(n)
        )

    @property
    def bounding_box(self) -> Rectangle:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return Rectangle(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)

    @property
    def centroid(self) -> Point:
        """Centroid via the shoelace-based formula."""
        n = len(self.points)
        signed_area = 0.0
        cx = 0.0
        cy = 0.0
        for i in range(n):
            j = (i + 1) % n
            cross = (
                self.points[i].x * self.points[j].y
                - self.points[j].x * self.points[i].y
            )
            signed_area += cross
            cx += (self.points[i].x + self.points[j].x) * cross
            cy += (self.points[i].y + self.points[j].y) * cross
        signed_area /= 2.0
        if signed_area == 0:
            # Degenerate — return average
            avg_x = sum(p.x for p in self.points) / n
            avg_y = sum(p.y for p in self.points) / n
            return Point(x=avg_x, y=avg_y)
        cx /= 6.0 * signed_area
        cy /= 6.0 * signed_area
        return Point(x=cx, y=cy)

    def contains(self, point: Point) -> bool:
        return point_in_polygon(point, self)


# --- Module-level functions ---


def distance(a: Point, b: Point) -> float:
    """Euclidean distance between two points."""
    return a.distance_to(b)


def _cross(o: Point, a: Point, b: Point) -> float:
    """Cross product of vectors OA and OB."""
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """Check if point q lies on segment pr."""
    return (
        min(p.x, r.x) <= q.x <= max(p.x, r.x)
        and min(p.y, r.y) <= q.y <= max(p.y, r.y)
    )


def segments_intersect(s1: Segment, s2: Segment) -> bool:
    """Check if two segments intersect (proper or endpoint touch)."""
    p1, q1 = s1.start, s1.end
    p2, q2 = s2.start, s2.end

    d1 = _cross(p2, q2, p1)
    d2 = _cross(p2, q2, q1)
    d3 = _cross(p1, q1, p2)
    d4 = _cross(p1, q1, q2)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
        (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
    ):
        return True

    if d1 == 0 and _on_segment(p2, p1, q2):
        return True
    if d2 == 0 and _on_segment(p2, q1, q2):
        return True
    if d3 == 0 and _on_segment(p1, p2, q1):
        return True
    if d4 == 0 and _on_segment(p1, q2, q1):
        return True

    return False


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """Ray casting algorithm. Points on edge return True."""
    pts = polygon.points
    n = len(pts)
    # First check if on any edge
    for i in range(n):
        j = (i + 1) % n
        p1, p2 = pts[i], pts[j]
        # Check collinearity and within bounds
        cross = (point.y - p1.y) * (p2.x - p1.x) - (point.x - p1.x) * (p2.y - p1.y)
        if abs(cross) < 1e-10:
            if _on_segment(p1, point, p2):
                return True

    # Ray casting
    inside = False
    j = n - 1
    for i in range(n):
        yi, yj = pts[i].y, pts[j].y
        xi, xj = pts[i].x, pts[j].x
        if (yi > point.y) != (yj > point.y):
            x_intersect = (xj - xi) * (point.y - yi) / (yj - yi) + xi
            if point.x < x_intersect:
                inside = not inside
        j = i
    return inside


def rectangles_overlap(r1: Rectangle, r2: Rectangle) -> bool:
    """Strict overlap — touching edges do NOT count."""
    return not (
        r1.x + r1.width <= r2.x
        or r2.x + r2.width <= r1.x
        or r1.y + r1.height <= r2.y
        or r2.y + r2.height <= r1.y
    )


def min_distance_rect_to_rect(r1: Rectangle, r2: Rectangle) -> float:
    """Minimum distance between two axis-aligned rectangles."""
    # Horizontal gap
    dx = max(0.0, max(r2.x - (r1.x + r1.width), r1.x - (r2.x + r2.width)))
    # Vertical gap
    dy = max(0.0, max(r2.y - (r1.y + r1.height), r1.y - (r2.y + r2.height)))
    return math.sqrt(dx * dx + dy * dy)


def min_distance_point_to_segment(point: Point, seg: Segment) -> float:
    """Minimum distance from a point to a line segment."""
    ax, ay = seg.start.x, seg.start.y
    bx, by = seg.end.x, seg.end.y
    px, py = point.x, point.y

    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        return point.distance_to(seg.start)

    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    proj = Point(x=ax + t * dx, y=ay + t * dy)
    return point.distance_to(proj)


def min_distance_rect_to_segment(rect: Rectangle, seg: Segment) -> float:
    """Minimum distance from an axis-aligned rectangle to a line segment."""
    corners = rect.corners
    # Check all 4 corners to segment
    min_d = min(min_distance_point_to_segment(c, seg) for c in corners)
    # Check segment endpoints to rectangle edges
    rect_segs = [
        Segment(start=corners[i], end=corners[(i + 1) % 4])
        for i in range(4)
    ]
    for rs in rect_segs:
        min_d = min(min_d, min_distance_point_to_segment(seg.start, rs))
        min_d = min(min_d, min_distance_point_to_segment(seg.end, rs))
        # Check segment-segment intersection (distance = 0)
        if segments_intersect(rs, seg):
            return 0.0
    return min_d
