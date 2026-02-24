"""CLI entry point."""

from __future__ import annotations

import random
from pathlib import Path

import typer

from floorplan_generator.core.enums import ApartmentClass

app = typer.Typer(name="floorplan", help="Apartment floorplan generator")

_ALL_CLASSES = list(ApartmentClass)
_ALL_ROOMS = [1, 2, 3, 4]
_ALL_THEMES = [
    "blueprint", "colored", "contrast", "dark", "monochrome",
    "nordic", "pastel", "rose", "sage", "technical", "warm", "watercolor",
]


@app.callback()
def main() -> None:
    """Generate synthetic apartment floorplan datasets in SVG format."""


@app.command()
def generate(
    apartment_class: ApartmentClass = typer.Option(
        ApartmentClass.ECONOMY, "--class", "-c", help="Apartment class",
    ),
    rooms: int = typer.Option(1, "--rooms", "-r", help="Number of living rooms"),
    count: int = typer.Option(10, "--count", "-n", help="Number of apartments"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output dir"),
    theme: str = typer.Option("blueprint", "--theme", "-t", help="Theme name or path"),
    max_restarts: int = typer.Option(10, "--max-restarts", help="Max restarts"),
    png: bool = typer.Option(False, "--png", help="Also export PNG renders"),
    mask: bool = typer.Option(False, "--mask", help="Also export segmentation masks"),
    dimensions: bool = typer.Option(False, "--dimensions", "-d", help="Add dimension annotations"),
    labels: bool = typer.Option(True, "--labels/--no-labels", help="Show room names and areas"),
) -> None:
    """Generate apartment floorplans and save as SVG."""
    from floorplan_generator.generator.factory import generate_dataset
    from floorplan_generator.renderer.theme import load_theme

    theme_obj = load_theme(theme)
    metadata = generate_dataset(
        apartment_class, rooms, count, seed, output,
        max_restarts=max_restarts,
        theme=theme_obj,
        png=png,
        mask=mask,
        dimensions=dimensions,
        labels=labels,
    )
    typer.echo(f"Generated {len(metadata)} apartments in {output}")


@app.command()
def render(
    input_dir: Path = typer.Option(
        ..., "--input", "-i", help="Input dir with JSON files",
    ),
    output_dir: Path = typer.Option(
        ..., "--output", "-o", help="Output dir for SVGs",
    ),
    theme: str = typer.Option(
        "blueprint", "--theme", "-t", help="Theme name or path",
    ),
    png: bool = typer.Option(False, "--png", help="Also export PNG renders"),
    mask: bool = typer.Option(False, "--mask", help="Also export segmentation masks"),
    dimensions: bool = typer.Option(False, "--dimensions", "-d", help="Add dimension annotations"),
    labels: bool = typer.Option(True, "--labels/--no-labels", help="Show room names and areas"),
) -> None:
    """Re-render apartment JSON files to SVG with a different theme."""
    from floorplan_generator.generator.types import GenerationResult
    from floorplan_generator.renderer.segmentation import render_mask_to_file
    from floorplan_generator.renderer.svg_renderer import (
        render_png_to_file,
        render_svg_to_file,
    )
    from floorplan_generator.renderer.theme import load_theme

    theme_obj = load_theme(theme)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "metadata.json"]

    rendered = 0
    for json_file in json_files:
        result = GenerationResult.model_validate_json(json_file.read_text())
        svg_path = output_dir / f"{json_file.stem}.svg"
        render_svg_to_file(result, str(svg_path), theme_obj, show_dimensions=dimensions, show_labels=labels)
        if png:
            png_path = output_dir / f"{json_file.stem}.png"
            render_png_to_file(result, str(png_path), theme_obj, show_dimensions=dimensions, show_labels=labels)
        if mask:
            mask_path = output_dir / f"{json_file.stem}_mask.png"
            render_mask_to_file(result, str(mask_path), theme_obj)
        rendered += 1

    typer.echo(f"Rendered {rendered} SVG files to {output_dir}")


@app.command()
def random_generate(
    count: int = typer.Option(10, "--count", "-n", help="Total number of apartments"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for parameter sampling"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output dir"),
    max_restarts: int = typer.Option(10, "--max-restarts", help="Max restarts per apartment"),
    png: bool = typer.Option(False, "--png", help="Also export PNG renders"),
    mask: bool = typer.Option(False, "--mask", help="Also export segmentation masks"),
) -> None:
    """Generate apartments with random class, rooms, theme, and labels.

    Distributes parameters proportionally across the generated count so every
    apartment class, room count (1-4), and theme gets roughly equal coverage.
    Labels (room names + area) are toggled randomly (~50/50).
    """
    from floorplan_generator.generator.factory import generate_single
    from floorplan_generator.renderer.segmentation import render_mask_to_file
    from floorplan_generator.renderer.svg_renderer import (
        render_png_to_file,
        render_svg_to_file,
    )
    from floorplan_generator.renderer.theme import load_theme

    output.mkdir(parents=True, exist_ok=True)

    # Build a proportionally distributed schedule
    combos = [
        (cls, rooms)
        for cls in _ALL_CLASSES
        for rooms in _ALL_ROOMS
    ]  # 16 combos
    schedule: list[tuple[ApartmentClass, int, str, bool]] = []
    for i in range(count):
        cls, rooms = combos[i % len(combos)]
        theme_name = _ALL_THEMES[i % len(_ALL_THEMES)]
        show_labels = i % 2 == 0  # alternating → ~50/50
        schedule.append((cls, rooms, theme_name, show_labels))

    # Shuffle with the user seed so it's reproducible but not purely cyclic
    rng = random.Random(seed)
    rng.shuffle(schedule)

    metadata = []
    for i, (apt_class, num_rooms, theme_name, show_labels) in enumerate(schedule):
        item_seed = seed + i
        result = generate_single(
            apt_class, num_rooms, seed=item_seed, max_restarts=max_restarts,
        )
        if result is None:
            typer.echo(f"  skip #{i} ({apt_class.value}/{num_rooms}r) — generation failed")
            continue

        theme_obj = load_theme(theme_name)
        filename = f"rand_{apt_class.value}_{num_rooms}r_{theme_name}_{i:04d}"

        svg_path = output / f"{filename}.svg"
        render_svg_to_file(result, str(svg_path), theme_obj, show_labels=show_labels)

        if png:
            png_path = output / f"{filename}.png"
            render_png_to_file(result, str(png_path), theme_obj, show_labels=show_labels)

        if mask:
            mask_path = output / f"{filename}_mask.png"
            render_mask_to_file(result, str(mask_path), theme_obj)

        json_path = output / f"{filename}.json"
        json_path.write_text(result.model_dump_json(indent=2))

        entry = {
            "index": i,
            "filename": filename,
            "class": apt_class.value,
            "rooms": num_rooms,
            "theme": theme_name,
            "labels": show_labels,
            "total_area_m2": round(result.apartment.total_area_m2, 1),
            "room_count": len(result.apartment.rooms),
            "restart_count": result.restart_count,
            "seed_used": result.seed_used,
        }
        metadata.append(entry)
        labels_tag = "labels" if show_labels else "no-labels"
        typer.echo(
            f"  [{i+1}/{count}] {apt_class.value}/{num_rooms}r "
            f"theme={theme_name} {labels_tag} area={entry['total_area_m2']}m²",
        )

    import json as _json
    meta_path = output / "metadata.json"
    meta_path.write_text(_json.dumps(metadata, indent=2, ensure_ascii=False))

    typer.echo(f"Generated {len(metadata)} random apartments in {output}")
