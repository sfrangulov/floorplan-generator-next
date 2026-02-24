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


def draw_shower(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Shower: square tray + diagonal hatch lines + drain circle."""
    s = _style(style)
    # Outer tray
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Diagonal hatch lines (top-left to bottom-right direction)
    n_lines = 6
    for i in range(1, n_lines + 1):
        frac = i / (n_lines + 1)
        # Lines from left edge to bottom edge, then top edge to right edge
        if frac <= 0.5:
            g.add(Line(
                start=(0, d * frac * 2),
                end=(w * frac * 2, 0),
                **s,
            ))
        else:
            offset = (frac - 0.5) * 2
            g.add(Line(
                start=(w * offset, d),
                end=(w, d * offset),
                **s,
            ))
    # Drain circle (center)
    g.add(Circle(center=(w * 0.5, d * 0.5), r=min(w, d) * 0.06, **s))


def draw_double_sink(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Double sink: rect body + two oval basins side by side."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Left basin
    g.add(Ellipse(
        center=(w * 0.28, d * 0.55),
        r=(w * 0.2, d * 0.3),
        **s,
    ))
    # Right basin
    g.add(Ellipse(
        center=(w * 0.72, d * 0.55),
        r=(w * 0.2, d * 0.3),
        **s,
    ))
    # Faucet circles
    g.add(Circle(center=(w * 0.28, d * 0.15), r=w * 0.03, **s))
    g.add(Circle(center=(w * 0.72, d * 0.15), r=w * 0.03, **s))


def draw_bidet(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bidet: small oval bowl (like toilet without tank)."""
    s = _style(style)
    # Outer oval body
    g.add(Ellipse(
        center=(w / 2, d / 2),
        r=(w * 0.45, d * 0.45),
        **s,
    ))
    # Inner oval basin
    g.add(Ellipse(
        center=(w / 2, d * 0.55),
        r=(w * 0.28, d * 0.3),
        **s,
    ))
    # Faucet circle at top
    g.add(Circle(center=(w / 2, d * 0.15), r=w * 0.05, **s))


def draw_washer_dryer(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Washer+dryer combo: two machines side by side (washer left, dryer right)."""
    s = _style(style)
    # Outer rectangle
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Vertical dividing line at center
    g.add(Line(start=(w / 2, 0), end=(w / 2, d), **s))
    half = w / 2

    # --- Left half: washing machine ---
    panel_h = d * 0.1
    g.add(Rect(insert=(0, 0), size=(half, panel_h), **s))
    r_drum = min(half, d) * 0.38
    cx_l, cy_l = half / 2, panel_h + (d - panel_h) / 2
    g.add(Circle(center=(cx_l, cy_l), r=r_drum, **s))
    g.add(Circle(center=(cx_l, cy_l), r=r_drum * 0.25, **s))

    # --- Right half: dryer ---
    g.add(Rect(insert=(half, 0), size=(half, panel_h), **s))
    r_dryer = min(half, d) * 0.35
    cx_r, cy_r = half + half / 2, panel_h + (d - panel_h) / 2
    g.add(Circle(center=(cx_r, cy_r), r=r_dryer, **s))
    g.add(Circle(center=(cx_r, cy_r), r=r_dryer * 0.3, **s))
    # Vent dot in dryer control panel
    g.add(Circle(center=(half + half * 0.75, panel_h * 0.5), r=panel_h * 0.25, **s))


def draw_dryer(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Dryer: rect + control panel + front drum circle + vent circle."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Control panel strip at top
    panel_h = d * 0.1
    g.add(Rect(insert=(0, 0), size=(w, panel_h), **s))
    # Front drum circle (centered below panel)
    r_drum = min(w, d) * 0.35
    cx, cy = w / 2, panel_h + (d - panel_h) / 2
    g.add(Circle(center=(cx, cy), r=r_drum, **s))
    # Vent circle inside drum
    g.add(Circle(center=(cx, cy), r=r_drum * 0.3, **s))
    # Small vent dots in control panel
    g.add(Circle(center=(w * 0.75, panel_h * 0.5), r=panel_h * 0.25, **s))


def draw_oven(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Oven: rect body + inner rect (door) + circle (window)."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Inner door rect (inset)
    inset_x = w * 0.08
    inset_top = d * 0.12
    inset_bot = d * 0.08
    g.add(Rect(
        insert=(inset_x, inset_top),
        size=(w - 2 * inset_x, d - inset_top - inset_bot),
        **s,
    ))
    # Door window circle
    g.add(Circle(
        center=(w / 2, d * 0.55),
        r=min(w, d) * 0.18,
        **s,
    ))
    # Handle line at top of door
    g.add(Line(
        start=(w * 0.2, d * 0.06),
        end=(w * 0.8, d * 0.06),
        **s,
    ))


def draw_dishwasher(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Dishwasher: rect body + horizontal rack lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Control panel strip at top
    panel_h = d * 0.08
    g.add(Rect(insert=(0, 0), size=(w, panel_h), **s))
    # Horizontal rack lines (3 racks)
    for frac in [0.3, 0.55, 0.8]:
        y = d * frac
        g.add(Line(start=(w * 0.08, y), end=(w * 0.92, y), **s))
    # Handle line
    g.add(Line(
        start=(w * 0.3, d * 0.04),
        end=(w * 0.7, d * 0.04),
        **s,
    ))


def draw_microwave(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Microwave: rect body + rounded inner rect (door) + control panel."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Door area (left ~75%)
    door_w = w * 0.72
    inset = min(w, d) * 0.08
    g.add(Rect(
        insert=(inset, inset),
        size=(door_w - 2 * inset, d - 2 * inset),
        rx=min(w, d) * 0.03, ry=min(w, d) * 0.03,
        **s,
    ))
    # Control panel area (right ~25%) - vertical divider line
    g.add(Line(start=(door_w, 0), end=(door_w, d), **s))
    # Control panel buttons (small circles)
    panel_cx = door_w + (w - door_w) / 2
    for frac in [0.3, 0.5, 0.7]:
        g.add(Circle(
            center=(panel_cx, d * frac),
            r=min(w, d) * 0.03,
            **s,
        ))


def draw_bookshelf(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bookshelf: rect with 4-5 horizontal shelf lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # 5 horizontal shelf lines
    n_shelves = 5
    for i in range(1, n_shelves + 1):
        y = d * i / (n_shelves + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))


def draw_shelving(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Shelving: rect with horizontal + vertical divisions (grid)."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Horizontal divisions (3 shelves)
    n_rows = 3
    for i in range(1, n_rows + 1):
        y = d * i / (n_rows + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))
    # Vertical divisions (2 columns)
    n_cols = 2
    for i in range(1, n_cols + 1):
        x = w * i / (n_cols + 1)
        g.add(Line(start=(x, 0), end=(x, d), **s))


def draw_dresser(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Dresser: rect body + 3-4 horizontal drawer lines + small handle circles."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # 4 horizontal drawer divider lines
    n_drawers = 4
    for i in range(1, n_drawers + 1):
        y = d * i / (n_drawers + 1)
        g.add(Line(start=(0, y), end=(w, y), **s))
    # Small handle circles for each drawer (centered)
    for i in range(n_drawers + 1):
        cy = d * (i + 0.5) / (n_drawers + 1)
        g.add(Circle(center=(w / 2, cy), r=min(w, d) * 0.02, **s))


def draw_vanity(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Vanity: rect table + oval mirror circle above."""
    s = _style(style)
    # Table/counter (lower portion)
    table_h = d * 0.55
    g.add(Rect(insert=(0, d - table_h), size=(w, table_h), **s))
    # Mirror (ellipse in upper portion)
    mirror_cy = d * 0.25
    g.add(Ellipse(
        center=(w / 2, mirror_cy),
        r=(w * 0.35, d * 0.2),
        **s,
    ))
    # Small drawer line on table
    g.add(Line(
        start=(w * 0.1, d * 0.72),
        end=(w * 0.9, d * 0.72),
        **s,
    ))


def draw_shoe_rack(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Shoe rack: low rect with 2-3 angled shelf lines."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # 3 angled shelf lines (slightly tilted for shoe display)
    n_shelves = 3
    for i in range(1, n_shelves + 1):
        y = d * i / (n_shelves + 1)
        # Angled lines: left side slightly higher than right
        g.add(Line(
            start=(w * 0.05, y - d * 0.03),
            end=(w * 0.95, y + d * 0.03),
            **s,
        ))


def draw_bench(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Bench: rect with seat line + optional backrest."""
    s = _style(style)
    # Backrest (narrow strip at back)
    back_d = d * 0.2
    g.add(Rect(insert=(0, 0), size=(w, back_d), **s))
    # Seat
    g.add(Rect(insert=(0, back_d), size=(w, d - back_d), **s))
    # Seat line (edge between backrest and seat)
    g.add(Line(start=(0, back_d), end=(w, back_d), **s))
    # Leg indicators at corners
    leg_r = min(w, d) * 0.025
    for lx, ly in [
        (w * 0.08, d * 0.92),
        (w * 0.92, d * 0.92),
    ]:
        g.add(Circle(center=(lx, ly), r=leg_r, **s))


def draw_coat_rack(
    g: svgwrite.container.Group, w: float, d: float, style: dict,
) -> None:
    """Coat rack: rect with hook circles along top."""
    s = _style(style)
    g.add(Rect(insert=(0, 0), size=(w, d), **s))
    # Horizontal rail line near top
    rail_y = d * 0.25
    g.add(Line(start=(w * 0.05, rail_y), end=(w * 0.95, rail_y), **s))
    # Hook circles along the rail (5 hooks evenly spaced)
    n_hooks = 5
    hook_r = min(w, d) * 0.03
    for i in range(n_hooks):
        cx = w * (i + 1) / (n_hooks + 1)
        g.add(Circle(center=(cx, rail_y), r=hook_r, **s))
    # Shelf line at top
    g.add(Line(start=(0, d * 0.1), end=(w, d * 0.1), **s))


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
    FurnitureType.SHOWER: draw_shower,
    FurnitureType.TOILET_BOWL: draw_toilet,
    FurnitureType.SINK: draw_sink,
    FurnitureType.DOUBLE_SINK: draw_double_sink,
    FurnitureType.KITCHEN_SINK: draw_sink,
    FurnitureType.BIDET: draw_bidet,
    FurnitureType.WASHING_MACHINE: draw_washing_machine,
    FurnitureType.DRYER: draw_dryer,
    FurnitureType.WASHER_DRYER: draw_washer_dryer,
    FurnitureType.STOVE: draw_stove,
    FurnitureType.HOB: draw_stove,
    FurnitureType.OVEN: draw_oven,
    FurnitureType.FRIDGE: draw_fridge,
    FurnitureType.FRIDGE_SIDE_BY_SIDE: draw_fridge,
    FurnitureType.DISHWASHER: draw_dishwasher,
    FurnitureType.HOOD: draw_hood,
    FurnitureType.MICROWAVE: draw_microwave,
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
    FurnitureType.DRESSER: draw_dresser,
    FurnitureType.VANITY: draw_vanity,
    FurnitureType.DINING_TABLE: draw_table,
    FurnitureType.COFFEE_TABLE: draw_table,
    FurnitureType.DINING_CHAIR: draw_chair,
    FurnitureType.DESK: draw_desk,
    FurnitureType.CHILD_DESK: draw_desk,
    FurnitureType.TV_STAND: draw_tv_stand,
    FurnitureType.BOOKSHELF: draw_bookshelf,
    FurnitureType.SHELVING: draw_shelving,
    FurnitureType.SHOE_RACK: draw_shoe_rack,
    FurnitureType.BENCH: draw_bench,
    FurnitureType.COAT_RACK: draw_coat_rack,
}


def get_drawer(ft: FurnitureType) -> Callable:
    """Get the draw function for a furniture type."""
    return FURNITURE_DRAWERS.get(ft, draw_rect_fallback)
