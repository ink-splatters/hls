"""Command-line interface for DASH manifests."""

import click

from stream_parser import __version__, dash
from stream_parser.common.cli import input_source, report_errors, source_options


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="dash")
def main() -> None:
    """DASH manifest utilities."""


@main.command(params=source_options())
@click.option("--base-url", help="Base directory URL for resolving relative paths.")
def urls(file: str | None, url: str | None, headers: dict[str, str], base_url: str | None) -> None:
    """Print initialization and media URLs, one per line.

    For live manifests, emits the segments available at the start of iteration.
    """
    with report_errors():
        manifest = dash.load(input_source(file, url), headers=headers)
        for segment_url in dash.iter_segment_urls(manifest, base_url):
            click.echo(segment_url)


@main.command(params=source_options())
def dump(file: str | None, url: str | None, headers: dict[str, str]) -> None:
    """Dump parsed MPD XML. Reads stdin by default."""
    with report_errors():
        manifest = dash.load(input_source(file, url), headers=headers)
        click.echo(dash.dumps(manifest))
