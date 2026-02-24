"""CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from floorplan_generator.core.enums import ApartmentClass

app = typer.Typer(name="floorplan", help="Apartment floorplan generator")


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
        render_svg_to_file(result, str(svg_path), theme_obj, show_dimensions=dimensions)
        if png:
            png_path = output_dir / f"{json_file.stem}.png"
            render_png_to_file(result, str(png_path), theme_obj, show_dimensions=dimensions)
        if mask:
            mask_path = output_dir / f"{json_file.stem}_mask.png"
            render_mask_to_file(result, str(mask_path), theme_obj)
        rendered += 1

    typer.echo(f"Rendered {rendered} SVG files to {output_dir}")
