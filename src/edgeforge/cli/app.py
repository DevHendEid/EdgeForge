from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from edgeforge import __version__
from edgeforge.data.adapters.crypto import BinanceDepthAdapter, OkxBooksAdapter
from edgeforge.data.adapters.jsonl_payload import read_jsonl
from edgeforge.data.adapters.lobster import LobsterMessageAdapter
from edgeforge.data.registry import DATASETS
from edgeforge.replay.engine import replay_l2, replay_l3
from edgeforge.storage.jsonl import read_events, write_events

app = typer.Typer(help="EdgeForge quantitative research platform")
console = Console()


@app.command()
def doctor() -> None:
    """Check the local research environment."""
    table = Table(title="EdgeForge doctor")
    table.add_column("Component"); table.add_column("Value")
    table.add_row("EdgeForge", __version__)
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Platform", platform.platform())
    for mod in ("polars", "pyarrow", "duckdb"):
        try:
            m = __import__(mod)
            table.add_row(mod, str(getattr(m, "__version__", "installed")))
        except ImportError:
            table.add_row(mod, "not installed")
    console.print(table)


@app.command("datasets")
def datasets() -> None:
    """List approved datasets and their intended role."""
    table = Table(title="Dataset registry")
    for column in ("Key", "Name", "Grade", "Purpose", "Access"):
        table.add_column(column)
    for item in DATASETS:
        table.add_row(item.key, item.name, item.grade, item.purpose, item.access)
    console.print(table)


@app.command("ingest-lobster")
def ingest_lobster(
    message_csv: Path,
    instrument: str,
    trading_date: str,
    output: Path = Path("data/canonical/lobster/events.jsonl"),
) -> None:
    """Normalize a LOBSTER message CSV into canonical EdgeForge JSONL."""
    n = write_events(output, LobsterMessageAdapter(message_csv, instrument, trading_date))
    console.print(f"wrote {n} events -> {output}")


@app.command("ingest-binance-depth")
def ingest_binance_depth(
    input_jsonl: Path,
    instrument: str,
    output: Path = Path("data/canonical/binance/events.jsonl"),
) -> None:
    """Normalize Binance depth JSONL payloads."""
    n = write_events(output, BinanceDepthAdapter(read_jsonl(input_jsonl), instrument))
    console.print(f"wrote {n} events -> {output}")


@app.command("ingest-okx-books")
def ingest_okx_books(
    input_jsonl: Path,
    instrument: str,
    output: Path = Path("data/canonical/okx/events.jsonl"),
) -> None:
    """Normalize OKX books JSONL payloads."""
    n = write_events(output, OkxBooksAdapter(read_jsonl(input_jsonl), instrument))
    console.print(f"wrote {n} events -> {output}")


@app.command("replay")
def replay(path: Path, level: int = typer.Option(3, min=2, max=3), strict: bool = True) -> None:
    """Replay canonical JSONL through the L2 or L3 book and print a report."""
    events = read_events(path)
    report = replay_l3(events, strict=strict) if level == 3 else replay_l2(events, strict=strict)
    console.print_json(json.dumps({
        "events": report.events,
        "errors": report.errors,
        "state_hash": report.state_hash,
        "sequence_gaps": report.sequence_gaps,
    }))


if __name__ == "__main__":
    app()
