"""Integration tests for SVG renderer (RI01-RI07)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from xml.etree import ElementTree

from floorplan_generator.core.enums import ApartmentClass
from floorplan_generator.generator.factory import generate_dataset
from floorplan_generator.generator.layout_engine import generate_apartment
from floorplan_generator.generator.types import GenerationResult
from floorplan_generator.renderer.svg_renderer import render_svg, render_svg_to_file
from floorplan_generator.renderer.theme import load_theme


# RI01
def test_generate_economy_svg():
    """Generate economy 1-room, render SVG, check valid XML."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    svg = render_svg(result)
    assert len(svg) > 100
    # Valid XML
    root = ElementTree.fromstring(svg)
    assert root.tag.endswith("svg")


# RI02
def test_generate_with_themes():
    """Same apartment renders differently with blueprint vs colored."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    bp = render_svg(result, load_theme("blueprint"))
    col = render_svg(result, load_theme("colored"))
    assert bp != col
    # Colored should have room fill colors
    assert "#E3F2FD" in col or "#FFF3E0" in col or "#E0F7FA" in col


# RI03
def test_svg_file_output():
    """render_svg_to_file produces a valid SVG file."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.svg"
        render_svg_to_file(result, str(path))
        assert path.exists()
        content = path.read_text()
        assert "<svg" in content
        assert len(content) > 500


# RI04
def test_svg_file_size_reasonable():
    """SVG file size < 500KB for typical apartment."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42)
    assert result is not None
    svg = render_svg(result)
    assert len(svg) < 500_000


# RI05
def test_comfort_2room_all_layers():
    """Comfort 2-room SVG has all expected layer groups."""
    result = generate_apartment(ApartmentClass.COMFORT, 2, seed=42)
    assert result is not None
    svg = render_svg(result)
    for layer_id in ["rooms", "mebel", "floor", "doors", "windows"]:
        assert f'id="{layer_id}"' in svg


# RI06
def test_dataset_generation_svgs():
    """generate_dataset produces SVG files + JSON + metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir)
        metadata = generate_dataset(
            ApartmentClass.ECONOMY, 1, 3, 42, output,
        )
        assert len(metadata) > 0
        assert (output / "metadata.json").exists()
        svg_files = list(output.glob("*.svg"))
        json_files = [
            f for f in output.glob("*.json")
            if f.name != "metadata.json"
        ]
        assert len(svg_files) == len(metadata)
        assert len(json_files) == len(metadata)


# RI07
def test_render_from_json():
    """Serialize apartment to JSON, reload, re-render matches."""
    result = generate_apartment(ApartmentClass.ECONOMY, 1, seed=42)
    assert result is not None
    json_str = result.model_dump_json()
    reloaded = GenerationResult.model_validate_json(json_str)
    svg1 = render_svg(result)
    svg2 = render_svg(reloaded)
    assert svg1 == svg2
