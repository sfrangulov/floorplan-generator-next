"""Theme loading and validation for SVG renderer."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

_THEMES_DIR = Path(__file__).parent / "themes"


class CanvasTheme(BaseModel):
    width: int = 2000
    height: int = 2000
    background: str = "#FFFFFF"


class WallTheme(BaseModel):
    outer_stroke: str = "#000000"
    outer_width: float = 4.0
    inner_stroke: str = "#000000"
    inner_width: float = 1.5


class RoomTheme(BaseModel):
    default_fill: str = "none"
    default_stroke: str = "#000000"
    stroke_width: float = 0.5
    fills: dict[str, str] = {}


class DoorTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 1.0
    arc_stroke: str = "#000000"
    arc_width: float = 0.5
    gap_fill: str = "#FFFFFF"


class WindowTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 1.0
    fill: str = "#FFFFFF"
    cross_stroke: str = "#000000"


class FurnitureTheme(BaseModel):
    stroke: str = "#000000"
    stroke_width: float = 0.8
    fill: str = "none"


class RiserTheme(BaseModel):
    stroke: str = "#000000"
    fill: str = "#000000"
    radius: float = 3.0


class TextTheme(BaseModel):
    font_family: str = "Arial, sans-serif"
    font_size: int = 14
    fill: str = "#333333"
    area_font_size: int = 11


class Theme(BaseModel):
    """Complete SVG rendering theme."""

    name: str = "default"
    canvas: CanvasTheme = CanvasTheme()
    walls: WallTheme = WallTheme()
    rooms: RoomTheme = RoomTheme()
    doors: DoorTheme = DoorTheme()
    windows: WindowTheme = WindowTheme()
    furniture: FurnitureTheme = FurnitureTheme()
    riser: RiserTheme = RiserTheme()
    text: TextTheme = TextTheme()


def load_theme(name_or_path: str) -> Theme:
    """Load a theme by name (built-in) or file path.

    Built-in themes: 'blueprint', 'colored'.
    Custom themes: pass a path to a JSON file.
    """
    # Try built-in theme first
    builtin_path = _THEMES_DIR / f"{name_or_path}.json"
    if builtin_path.exists():
        data = json.loads(builtin_path.read_text())
        return Theme(**data)

    # Try as file path
    custom_path = Path(name_or_path)
    if custom_path.exists():
        data = json.loads(custom_path.read_text())
        return Theme(**data)

    msg = f"Theme not found: {name_or_path}"
    raise FileNotFoundError(msg)


def get_default_theme() -> Theme:
    """Return the default blueprint theme."""
    return load_theme("blueprint")
