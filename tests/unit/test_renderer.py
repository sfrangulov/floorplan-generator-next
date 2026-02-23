"""Unit tests for SVG renderer (R01-R20)."""

from __future__ import annotations

from xml.etree import ElementTree

from floorplan_generator.core.enums import (
    ApartmentClass,
    DoorType,
    FurnitureType,
    RoomType,
    SwingDirection,
)
from floorplan_generator.core.geometry import Point, Polygon
from floorplan_generator.core.models import (
    Apartment,
    Door,
    FurnitureItem,
    Room,
    Window,
)
from floorplan_generator.generator.types import GenerationResult, Stoyak
from floorplan_generator.renderer.coordinate_mapper import CoordinateMapper
from floorplan_generator.renderer.svg_renderer import render_svg
from floorplan_generator.renderer.theme import load_theme


def _make_room(
    room_type: RoomType,
    x: float, y: float, w: float, h: float,
    *,
    room_id: str = "",
    doors: list[Door] | None = None,
    windows: list[Window] | None = None,
    furniture: list[FurnitureItem] | None = None,
) -> Room:
    """Helper: create a rectangular room at (x,y) with size (w,h) in mm."""
    return Room(
        id=room_id or f"r_{room_type.value}",
        room_type=room_type,
        boundary=Polygon(points=[
            Point(x=x, y=y),
            Point(x=x + w, y=y),
            Point(x=x + w, y=y + h),
            Point(x=x, y=y + h),
        ]),
        doors=doors or [],
        windows=windows or [],
        furniture=furniture or [],
    )


def _make_result(
    rooms: list[Room],
    stoyaks: list[Stoyak] | None = None,
) -> GenerationResult:
    """Helper: wrap rooms into a GenerationResult."""
    apt = Apartment(
        id="test_apt",
        apartment_class=ApartmentClass.ECONOMY,
        rooms=rooms,
        num_rooms=1,
    )
    return GenerationResult(
        apartment=apt,
        stoyaks=stoyaks or [],
        restart_count=0,
        seed_used=42,
        recommended_violations=0,
    )


def _parse_svg(svg_str: str) -> ElementTree.Element:
    """Parse SVG string to XML element tree."""
    return ElementTree.fromstring(svg_str)


# R01
def test_coordinate_mapper_basic():
    """mm point maps to correct SVG coords."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    # Origin should map near padding area
    x, y = mapper.to_svg(Point(x=0, y=0))
    assert 50 < x < 500
    assert 50 < y < 200
    # Far corner
    x2, y2 = mapper.to_svg(Point(x=4000, y=5000))
    assert x2 > 1500
    assert y2 > 1800


# R02
def test_coordinate_mapper_centering():
    """Floorplan centered in canvas."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    center_mm = Point(x=2000, y=2000)
    cx, cy = mapper.to_svg(center_mm)
    # Should be near canvas center (1000, 1000)
    assert 900 < cx < 1100
    assert 900 < cy < 1100


# R03
def test_coordinate_mapper_scale():
    """Scale preserves aspect ratio."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 8000, 4000)
    mapper = CoordinateMapper([room], 2000, 2000, padding=100)
    # Width is double height in mm; in SVG should maintain ratio
    w_svg = mapper.scale_length(8000)
    h_svg = mapper.scale_length(4000)
    assert abs(w_svg / h_svg - 2.0) < 0.01


# R04
def test_theme_load_blueprint():
    """Load blueprint.json correctly."""
    theme = load_theme("blueprint")
    assert theme.name == "blueprint"
    assert theme.canvas.background == "#FFFFFF"
    assert theme.walls.outer_width == 4.0
    assert theme.rooms.default_fill == "none"


# R05
def test_theme_load_colored():
    """Load colored.json correctly."""
    theme = load_theme("colored")
    assert theme.name == "colored"
    assert theme.rooms.fills.get("living_room") == "#E3F2FD"
    assert theme.rooms.fills.get("kitchen") == "#FFF3E0"
    assert theme.rooms.fills.get("bathroom") == "#E0F7FA"


# R06
def test_theme_custom_json(tmp_path):
    """Load custom theme from file path."""
    custom = tmp_path / "custom.json"
    custom.write_text('{"name": "custom", "canvas": {"background": "#FF0000"}}')
    theme = load_theme(str(custom))
    assert theme.name == "custom"
    assert theme.canvas.background == "#FF0000"


# R07
def test_room_polygon_render():
    """Room boundary renders as SVG polygon."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    polygons = root.findall(".//svg:g[@id='rooms']/svg:polygon", ns)
    assert len(polygons) >= 1


# R08
def test_room_label_render():
    """Room label at centroid with name + area."""
    room = _make_room(RoomType.KITCHEN, 0, 0, 3000, 3000)
    result = _make_result([room])
    svg = render_svg(result)
    assert "Кухня" in svg
    assert "9.0 м²" in svg


# R09
def test_wall_outer_thick():
    """Outer walls drawn with thick stroke."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 4000)
    result = _make_result([room])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    # Should contain stroke-width matching outer_width
    assert f'stroke-width="{int(theme.walls.outer_width)}"' in svg or \
           f'stroke-width="{theme.walls.outer_width}"' in svg


# R10
def test_wall_inner_thin():
    """Inner walls drawn with thin stroke when rooms share edge."""
    r1 = _make_room(RoomType.HALLWAY, 0, 0, 2000, 3000, room_id="r1")
    r2 = _make_room(RoomType.LIVING_ROOM, 2000, 0, 4000, 3000, room_id="r2")
    result = _make_result([r1, r2])
    theme = load_theme("blueprint")
    svg = render_svg(result, theme)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    lines = root.findall(".//svg:g[@id='floor']/svg:line", ns)
    # Should have both outer and inner wall lines
    assert len(lines) >= 4


# R11
def test_door_gap():
    """Door creates visual element in SVG."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    room = _make_room(
        RoomType.HALLWAY, 0, 0, 2000, 3000,
        room_id="r1", doors=[door],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    door_group = root.findall(".//svg:g[@id='doors']", ns)
    assert len(door_group) == 1
    # Should have children (rect + path)
    assert len(list(door_group[0])) >= 1


# R12
def test_door_swing_arc():
    """Swing arc is quarter circle path."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    room = _make_room(
        RoomType.HALLWAY, 0, 0, 2000, 3000,
        room_id="r1", doors=[door],
    )
    result = _make_result([room])
    svg = render_svg(result)
    # Arc path should contain SVG arc command 'A'
    assert " A " in svg


# R13
def test_window_rect():
    """Window rect on external wall."""
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    win_group = root.findall(".//svg:g[@id='windows']", ns)
    assert len(win_group) == 1
    assert len(list(win_group[0])) >= 1


# R14
def test_window_panes():
    """Window has pane division lines."""
    window = Window(
        id="w1", position=Point(x=1000, y=0),
        width=1500.0, height=1500.0, wall_side="north",
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        windows=[window],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    win_group = root.findall(".//svg:g[@id='windows']", ns)[0]
    lines = win_group.findall("svg:line", ns)
    assert len(lines) >= 3  # 3 pane division lines


# R15
def test_furniture_rendered():
    """Furniture item creates elements in mebel group."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.BATHTUB,
        position=Point(x=100, y=100), width=1700, depth=750,
    )
    room = _make_room(
        RoomType.BATHROOM, 0, 0, 2000, 2000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    mebel = root.findall(".//svg:g[@id='mebel']", ns)
    assert len(mebel) == 1
    assert len(list(mebel[0])) >= 1


# R16
def test_furniture_placement_position():
    """Furniture placed at correct SVG position via transform."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.STOVE,
        position=Point(x=500, y=500), width=600, depth=600,
    )
    room = _make_room(
        RoomType.KITCHEN, 0, 0, 3000, 3000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    assert "translate(" in svg


# R17
def test_furniture_rotation():
    """Rotated furniture has correct transform."""
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.BED_DOUBLE,
        position=Point(x=500, y=500), width=1600, depth=2000,
        rotation=90.0,
    )
    room = _make_room(
        RoomType.BEDROOM, 0, 0, 4000, 4000,
        furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    assert "rotate(90" in svg


# R18
def test_stoyak_circle():
    """Stoyak renders as filled circle."""
    room = _make_room(RoomType.BATHROOM, 0, 0, 2000, 2000)
    stoyak = Stoyak(id="s1", position=Point(x=100, y=100))
    result = _make_result([room], stoyaks=[stoyak])
    svg = render_svg(result)
    root = _parse_svg(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    stoyak_group = root.findall(".//svg:g[@id='stoyaks']", ns)
    assert len(stoyak_group) == 1
    circles = stoyak_group[0].findall("svg:circle", ns)
    assert len(circles) == 1


# R19
def test_full_render_produces_valid_svg():
    """Full render returns valid SVG string with correct root element."""
    room = _make_room(RoomType.LIVING_ROOM, 0, 0, 4000, 5000)
    result = _make_result([room])
    svg = render_svg(result)
    assert svg.startswith("<?xml") or "<svg" in svg[:200]
    root = _parse_svg(svg)
    assert root.tag.endswith("svg")


# R20
def test_full_render_layers_order():
    """Elements appear in correct z-order: rooms, mebel, floor, doors, windows."""
    door = Door(
        id="d1", position=Point(x=1000, y=0), width=800.0,
        door_type=DoorType.INTERIOR, swing=SwingDirection.INWARD,
        room_from="r1", room_to="r2",
    )
    window = Window(
        id="w1", position=Point(x=500, y=0),
        width=1200.0, height=1500.0, wall_side="north",
    )
    item = FurnitureItem(
        id="f1", furniture_type=FurnitureType.SOFA_3,
        position=Point(x=500, y=500), width=2300, depth=950,
    )
    room = _make_room(
        RoomType.LIVING_ROOM, 0, 0, 4000, 5000,
        room_id="r1",
        doors=[door], windows=[window], furniture=[item],
    )
    result = _make_result([room])
    svg = render_svg(result)
    # Check layer order by finding group IDs in SVG string
    rooms_pos = svg.find('id="rooms"')
    mebel_pos = svg.find('id="mebel"')
    floor_pos = svg.find('id="floor"')
    doors_pos = svg.find('id="doors"')
    windows_pos = svg.find('id="windows"')
    assert rooms_pos < mebel_pos < floor_pos < doors_pos < windows_pos
