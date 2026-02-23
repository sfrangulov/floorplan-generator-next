"""Unit tests for geometric primitives (G01–G18)."""

import math

import pytest

from floorplan_generator.core.geometry import (
    Point,
    Polygon,
    Rectangle,
    Segment,
    distance,
    min_distance_rect_to_rect,
    point_in_polygon,
    rectangles_overlap,
    segments_intersect,
)


# G01
def test_point_distance():
    """Distance between two points."""
    a = Point(x=0, y=0)
    b = Point(x=3, y=4)
    assert a.distance_to(b) == pytest.approx(5.0)


# G02
def test_rectangle_area():
    """Area of a rectangle."""
    r = Rectangle(x=0, y=0, width=10, height=5)
    assert r.area == pytest.approx(50.0)


# G03
def test_rectangle_aspect_ratio():
    """Aspect ratio (max side / min side)."""
    r = Rectangle(x=0, y=0, width=4, height=8)
    assert r.aspect_ratio == pytest.approx(2.0)


# G04
def test_rectangle_contains_point():
    """Point inside rectangle."""
    r = Rectangle(x=0, y=0, width=10, height=10)
    assert r.contains(Point(x=5, y=5)) is True
    assert r.contains(Point(x=0, y=0)) is True  # corner
    assert r.contains(Point(x=11, y=5)) is False


# G05
def test_rectangle_overlap_true():
    """Two overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=5, y=5, width=10, height=10)
    assert r1.overlaps(r2) is True


# G06
def test_rectangle_overlap_false():
    """Two non-overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=20, y=20, width=10, height=10)
    assert r1.overlaps(r2) is False


# G07
def test_rectangle_overlap_edge():
    """Touching by edge — NOT overlapping (strict)."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=10, y=0, width=10, height=10)
    assert r1.overlaps(r2) is False


# G08
def test_polygon_area_square():
    """Area of a square as polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.area == pytest.approx(100.0)


# G09
def test_polygon_area_irregular():
    """Area of an irregular polygon (L-shape)."""
    # L-shape: 10x10 square minus 5x5 corner = 75
    poly = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=5),
        Point(x=5, y=5),
        Point(x=5, y=10),
        Point(x=0, y=10),
    ])
    assert poly.area == pytest.approx(75.0)


# G10
def test_polygon_contains_point_inside():
    """Point inside polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=5, y=5)) is True


# G11
def test_polygon_contains_point_outside():
    """Point outside polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=15, y=15)) is False


# G12
def test_polygon_contains_point_edge():
    """Point on edge of polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    assert square.contains(Point(x=5, y=0)) is True


# G13
def test_segment_intersection():
    """Two intersecting segments."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=10, y=10))
    s2 = Segment(start=Point(x=0, y=10), end=Point(x=10, y=0))
    assert s1.intersects(s2) is True


# G14
def test_segment_no_intersection():
    """Two non-intersecting segments."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=5, y=5))
    s2 = Segment(start=Point(x=6, y=6), end=Point(x=10, y=10))
    assert s1.intersects(s2) is False


# G15
def test_segment_parallel():
    """Parallel segments do not intersect."""
    s1 = Segment(start=Point(x=0, y=0), end=Point(x=10, y=0))
    s2 = Segment(start=Point(x=0, y=1), end=Point(x=10, y=1))
    assert s1.intersects(s2) is False


# G16
def test_min_distance_rects():
    """Minimum distance between two non-overlapping rectangles."""
    r1 = Rectangle(x=0, y=0, width=10, height=10)
    r2 = Rectangle(x=15, y=0, width=10, height=10)
    assert min_distance_rect_to_rect(r1, r2) == pytest.approx(5.0)


# G17
def test_polygon_bounding_box():
    """Bounding box of a polygon."""
    poly = Polygon(points=[
        Point(x=1, y=2),
        Point(x=5, y=1),
        Point(x=8, y=6),
        Point(x=3, y=9),
    ])
    bb = poly.bounding_box
    assert bb.x == pytest.approx(1.0)
    assert bb.y == pytest.approx(1.0)
    assert bb.width == pytest.approx(7.0)
    assert bb.height == pytest.approx(8.0)


# G18
def test_polygon_centroid():
    """Centroid of a square polygon."""
    square = Polygon(points=[
        Point(x=0, y=0),
        Point(x=10, y=0),
        Point(x=10, y=10),
        Point(x=0, y=10),
    ])
    c = square.centroid
    assert c.x == pytest.approx(5.0)
    assert c.y == pytest.approx(5.0)
