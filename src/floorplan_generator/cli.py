"""CLI entry point."""

import typer

app = typer.Typer(name="floorplan", help="Apartment floorplan generator")


@app.callback()
def main() -> None:
    """Generate synthetic apartment floorplan datasets in SVG format."""
