"""Integration tests for SVG output structure (SVG01-SVG03)."""

from __future__ import annotations

from xml.etree import ElementTree

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.renderer.svg_renderer import render_svg


# SVG01
def test_generated_svg_has_reference_structure():
    """Full pipeline: generate + render produces SVG with reference structure."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=50)
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
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42, max_restarts=50)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    floor = None
    for el in root.iter():
        if el.get("id") == "floor":
            floor = el
            break
    assert floor is not None
    # Should have path elements (wall polygons + door arcs)
    paths = [el for el in floor.iter() if el.tag.endswith("path")]
    assert len(paths) >= 1, f"Floor should have wall/door paths, got {len(paths)}"


# SVG03
def test_furniture_group_contains_furniture():
    """The furniture group contains furniture elements."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=50)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    furniture_g = None
    for el in root.iter():
        if el.get("id") == "mebel":
            furniture_g = el
            break
    assert furniture_g is not None
    children = list(furniture_g)
    assert len(children) >= 1, "furniture group should have furniture"


# SVG04
def test_walls_are_paths_not_lines():
    """Generated SVG has wall paths (not lines) in floor group."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=50)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    floor = root.find(".//svg:g[@id='floor']", ns)
    paths = floor.findall("svg:path", ns)
    assert len(paths) >= 1, f"Expected wall paths, got {len(paths)}"


# SVG05
def test_mebel_group_exists():
    """Furniture group is named 'mebel'."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=50)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    mebel = root.findall(".//svg:g[@id='mebel']", ns)
    assert len(mebel) == 1


# SVG06
def test_text_font_size_is_large():
    """Room labels use font-size >= 20."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42, max_restarts=50)
    assert result is not None
    svg_str = render_svg(result)
    root = ElementTree.fromstring(svg_str)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    texts = root.findall(".//svg:text", ns)
    assert len(texts) >= 2
    for text_el in texts:
        fs = text_el.get("font-size", "0")
        assert int(fs) >= 20, f"Font size {fs} too small"
