"""Command-line interface for HLS playlists."""

import click

from stream_parser import __version__, hls
from stream_parser.common.cli import input_source, report_errors, source_options


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="hls")
def main() -> None:
    """HLS playlist utilities."""


@main.command(params=source_options())
@click.option("--base-url", help="Base directory URL for resolving relative paths.")
def urls(file: str | None, url: str | None, headers: dict[str, str], base_url: str | None) -> None:
    """Print initialization and media URLs, one per line."""
    with report_errors():
        playlist = hls.load(input_source(file, url), headers=headers)
        for segment_url in hls.iter_segment_urls(playlist, base_url):
            click.echo(segment_url)


@main.command(params=source_options())
def dump(file: str | None, url: str | None, headers: dict[str, str]) -> None:
    """Dump parsed M3U8 text. Reads stdin by default."""
    with report_errors():
        playlist = hls.load(input_source(file, url), headers=headers)
        click.echo(hls.dumps(playlist))
