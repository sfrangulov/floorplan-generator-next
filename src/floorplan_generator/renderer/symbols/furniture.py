"""SVG symbol definitions for furniture types.

Each function draws the furniture shape into an svgwrite group at (0,0)
with the given width and depth. Shapes are extracted from reference SVGs
in docs/svg/ and simplified for programmatic generation.

All drawing functions have signature:
    def draw_xxx(group, w, d, style) -> None
where w=width, d=depth (in SVG units), style=dict with stroke/fill.
"""

from __future__ import annotations

from collections.abc import Callable

import svgwrite.container
from svgwrite.shapes import Circle, Ellipse, Line, Rect
from svgwrite.text import Text

from floorplan_generator.core.enums import FurnitureType


def _style(s: dict) -> dict:
    """Convert style dict to svgwrite kwargs."""
    return {
        "stroke": s.get("stroke", "#000000"),
        "fill": s.get("fill", "none"),
        "stroke_width": s.get("stroke_width", 0.8),
        "stroke_linecap": "round",
        "stroke_linejoin": "round",
    }


def draw_bathtub(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bathtub: outer rect + inner rounded basin + shelf strip."""
    s = _style(style)
    # Shelf strip at top
    g.add(Rect(insert=(0, 0), size=(w, d * 0.04), **s))
    # Main body
    g.add(Rect(insert=(0, d * 0.04), size=(w, d * 0.96), **s))
    # Inner basin (inset rect with rounded corners)
    inset = w * 0.08
    g.add(Rect(
        insert=(inset, d * 0.15),
        size=(w - 2 * inset, d * 0.78),
        rx=w * 0.05, ry=d * 0.05,
        **s,
    ))
    # Drain circle
    g.add(Circle(center=(w * 0.5, d * 0.85), r=w * 0.025, **s))


def draw_toilet(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Toilet: tank rect + oval bowl + seat lid line."""
    s = _style(style)
    tank_h = d * 0.35
    # Tank
    g.add(Rect(insert=(0, 0), size=(w, tank_h), **s))
    # Bowl (ellipse)
    g.add(Ellipse(
        center=(w / 2, tank_h + (d - tank_h) / 2),
        r=(w * 0.42, (d - tank_h) * 0.48),
        **s,
    ))
    # Inner bowl
    g.add(Ellipse(
        center=(w / 2, tank_h + (d - tank_h) * 0.55),
        r=(w * 0.28, (d - tank_h) * 0.3),
        **s,
    ))
    # Seat lid line: horizontal line across the bowl area
    lid_y = tank_h + (d - tank_h) * 0.35
    g.add(Line(
        start=(w * 0.12, lid_y),
        end=(w * 0.88, lid_y),
        **s,
    ))


def draw_sink(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Sink: rect body + inner oval basin."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Basin oval
    g.add(Ellipse(center=(w / 2, d * 0.55), r=(w * 0.35, d * 0.3), **s))
    # Faucet circle
    g.add(Circle(center=(w / 2, d * 0.15), r=w * 0.05, **s))


def draw_washing_machine(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Washing machine: rect + control panel + large drum circle + inner circles."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Control panel strip at top
    panel_h = d * 0.1
    g.add(Rect(insert=(0, 0), size=(w, panel_h), **s))
    # Drum (centered below panel)
    r_drum = min(w, d) * 0.38
    cx, cy = w / 2, panel_h + (d - panel_h) / 2
    g.add(Circle(center=(cx, cy), r=r_drum, **s))
    g.add(Circle(center=(cx, cy), r=r_drum * 0.25, **s))


def draw_stove(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Stove/cooktop: rect body + 4 burner circles (2x2 grid)."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), rx=2, ry=2, **s))
    burner_r = min(w, d) * 0.12
    inner_r = burner_r * 0.57
    positions = [
        (w * 0.3, d * 0.3), (w * 0.7, d * 0.3),
        (w * 0.3, d * 0.7), (w * 0.7, d * 0.7),
    ]
    for bx, by in positions:
        g.add(Circle(center=(bx, by), r=burner_r, **s))
        g.add(Circle(center=(bx, by), r=inner_r, **s))


def draw_fridge(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Fridge: rect + compartment division line + handle."""
    s = _style(style)
    # Main body
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Horizontal division line at ~30% from top (freezer/fridge split)
    split_y = d * 0.3
    g.add(Line(start=(0, split_y), end=(w, split_y), **s))
    # Handle line on right side (small vertical line)
    handle_x = w * 0.88
    handle_top = d * 0.35
    handle_bot = d * 0.55
    g.add(Line(start=(handle_x, handle_top), end=(handle_x, handle_bot), **s))


def draw_bed(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bed: headboard rect + mattress rect + pillows + mattress edge line."""
    s = _style(style)
    head_h = d * 0.04
    # Headboard
    g.add(Rect(insert=(0, 0), size=(w, head_h), **s))
    # Mattress body
    g.add(Rect(insert=(0, head_h), size=(w, d - head_h), **s))
    # Pillow area (two pillows side by side)
    pillow_h = d * 0.15
    pillow_w = w * 0.45
    gap = w * 0.05
    for px in [gap, w - gap - pillow_w]:
        g.add(Rect(
            insert=(px, head_h + d * 0.02),
            size=(pillow_w, pillow_h),
            rx=pillow_h * 0.3, ry=pillow_h * 0.3,
            **s,
        ))
    # Mattress edge line: separates pillow area from mattress body
    edge_y = head_h + d * 0.02 + pillow_h + d * 0.02
    g.add(Line(start=(0, edge_y), end=(w, edge_y), **s))


def draw_sofa(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Sofa: backrest + seat + armrests + cushion division lines."""
    s = _style(style)
    back_d = d * 0.25
    arm_w = w * 0.08
    # Backrest
    g.add(Rect(insert=(0, 0), size=(w, back_d), **s))
    # Seat (rounded rect)
    g.add(Rect(
        insert=(arm_w, back_d), size=(w - 2 * arm_w, d - back_d),
        rx=d * 0.06, ry=d * 0.06, **s,
    ))
    # Left armrest
    g.add(Rect(
        insert=(0, back_d), size=(arm_w, d - back_d),
        rx=arm_w * 0.3, ry=arm_w * 0.3, **s,
    ))
    # Right armrest
    g.add(Rect(
        insert=(w - arm_w, back_d), size=(arm_w, d - back_d),
        rx=arm_w * 0.3, ry=arm_w * 0.3, **s,
    ))
    # Cushion division lines (2-3 vertical lines based on seat width)
    seat_w = w - 2 * arm_w
    n_cushions = 3 if seat_w > 150 else 2
    for i in range(1, n_cushions):
        cx = arm_w + seat_w * i / n_cushions
        g.add(Line(
            start=(cx, back_d + d * 0.05),
            end=(cx, d - d * 0.05),
            **s,
        ))


def draw_wardrobe(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Wardrobe: rect + vertical door division + handle circles."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Door edge line (near front)
    g.add(Line(start=(0, d * 0.95), end=(w, d * 0.95), **s))
    # Vertical center line for double doors
    g.add(Line(start=(w / 2, 0), end=(w / 2, d * 0.95), **s))
    # Door handle circles (small circles near center line)
    handle_y = d * 0.5
    handle_r = min(w, d) * 0.02
    g.add(Circle(center=(w / 2 - w * 0.05, handle_y), r=handle_r, **s))
    g.add(Circle(center=(w / 2 + w * 0.05, handle_y), r=handle_r, **s))


def draw_nightstand(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Nightstand: rect + single drawer line."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    g.add(Line(start=(w * 0.05, d * 0.5), end=(w, d * 0.5), **s))


def draw_table(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Dining/coffee table: rect with inset line + 4 leg circles at corners."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    inset = min(w, d) * 0.08
    g.add(Rect(insert=(inset, inset), size=(w - 2 * inset, d - 2 * inset), **s))
    # 4 small circles at corners for legs
    leg_r = min(w, d) * 0.03
    leg_inset = min(w, d) * 0.06
    for lx, ly in [
        (leg_inset, leg_inset),
        (w - leg_inset, leg_inset),
        (leg_inset, d - leg_inset),
        (w - leg_inset, d - leg_inset),
    ]:
        g.add(Circle(center=(lx, ly), r=leg_r, **s))


def draw_chair(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Chair: seat square + backrest line."""
    s = _style(style)
    g.add(Rect(insert=(0, d * 0.2), size=(w, d * 0.8), **s))
    # Backrest
    g.add(Rect(insert=(0, 0), size=(w, d * 0.2), **s))


def draw_desk(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Desk: rect + front edge line."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    g.add(Line(start=(0, d * 0.92), end=(w, d * 0.92), **s))


def draw_tv_stand(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """TV stand: wide rect + shelf divisions."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    g.add(Line(start=(0, d * 0.9), end=(w, d * 0.9), **s))
    g.add(Line(start=(w * 0.33, 0), end=(w * 0.33, d), **s))
    g.add(Line(start=(w * 0.66, 0), end=(w * 0.66, d), **s))


def draw_hood(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Range hood: 4 concentric circles."""
    s = _style(style)
    cx, cy = w / 2, d / 2
    r_max = min(w, d) * 0.45
    for frac in [1.0, 0.73, 0.47, 0.2]:
        g.add(Circle(center=(cx, cy), r=r_max * frac, **s))


def draw_rect_fallback(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
    label: str = "",
) -> None:
    """Fallback: simple rect with optional type label."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    if label:
        g.add(Text(
            label,
            insert=(w / 2, d / 2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=max(6, min(w, d) * 0.15),
            font_family="Arial, sans-serif",
            fill=s["stroke"],
        ))


draw_rect_fallback.is_fallback = True  # type: ignore[attr-defined]


# --- Registry mapping FurnitureType -> draw function ---

FURNITURE_DRAWERS: dict[FurnitureType, Callable] = {
    FurnitureType.BATHTUB: draw_bathtub,
    FurnitureType.TOILET_BOWL: draw_toilet,
    FurnitureType.SINK: draw_sink,
    FurnitureType.KITCHEN_SINK: draw_sink,
    FurnitureType.WASHING_MACHINE: draw_washing_machine,
    FurnitureType.STOVE: draw_stove,
    FurnitureType.HOB: draw_stove,
    FurnitureType.FRIDGE: draw_fridge,
    FurnitureType.FRIDGE_SIDE_BY_SIDE: draw_fridge,
    FurnitureType.BED_SINGLE: draw_bed,
    FurnitureType.BED_DOUBLE: draw_bed,
    FurnitureType.BED_KING: draw_bed,
    FurnitureType.CHILD_BED: draw_bed,
    FurnitureType.SOFA_2: draw_sofa,
    FurnitureType.SOFA_3: draw_sofa,
    FurnitureType.SOFA_4: draw_sofa,
    FurnitureType.SOFA_CORNER: draw_sofa,
    FurnitureType.ARMCHAIR: draw_sofa,
    FurnitureType.WARDROBE_SLIDING: draw_wardrobe,
    FurnitureType.WARDROBE_SWING: draw_wardrobe,
    FurnitureType.HALLWAY_WARDROBE: draw_wardrobe,
    FurnitureType.CHILD_WARDROBE: draw_wardrobe,
    FurnitureType.NIGHTSTAND: draw_nightstand,
    FurnitureType.DINING_TABLE: draw_table,
    FurnitureType.COFFEE_TABLE: draw_table,
    FurnitureType.DINING_CHAIR: draw_chair,
    FurnitureType.DESK: draw_desk,
    FurnitureType.CHILD_DESK: draw_desk,
    FurnitureType.TV_STAND: draw_tv_stand,
    FurnitureType.HOOD: draw_hood,
}


def get_drawer(ft: FurnitureType) -> Callable:
    """Get the draw function for a furniture type."""
    return FURNITURE_DRAWERS.get(ft, draw_rect_fallback)
