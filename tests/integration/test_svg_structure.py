"""Integration tests for SVG output structure (SVG01-SVG03)."""

from __future__ import annotations

from xml.etree import ElementTree

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.renderer.svg_renderer import render_svg


# SVG01
def test_generated_svg_has_reference_structure():
    """Full pipeline: generate + render produces SVG with reference structure."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    assert "background" in ids
    assert "mebel" in ids
    assert "floor" in ids
    # At least one room group with type prefix
    room_groups = [i for i in ids if len(i) <= 3 and i[0] in "hrsc" and i[1:].isdigit()]
    assert len(room_groups) >= 3, f"Expected room groups, got {ids}"


# SVG02
def test_floor_group_contains_walls_and_doors():
    """The floor group contains wall lines and door elements."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    floor = None
    for el in root.iter():
        if el.get("id") == "floor":
            floor = el
            break
    assert floor is not None
    # Should have line elements (walls) and path elements (door arcs)
    lines = [el for el in floor.iter() if el.tag.endswith("line")]
    paths = [el for el in floor.iter() if el.tag.endswith("path")]
    assert len(lines) >= 4, f"Floor should have wall lines, got {len(lines)}"
    assert len(paths) >= 1, f"Floor should have door arc paths, got {len(paths)}"


# SVG03
def test_mebel_group_contains_furniture():
    """The mebel group contains furniture elements."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=20)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    mebel = None
    for el in root.iter():
        if el.get("id") == "mebel":
            mebel = el
            break
    assert mebel is not None
    children = list(mebel)
    assert len(children) >= 1, "mebel group should have furniture"
