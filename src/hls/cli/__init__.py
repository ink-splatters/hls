import re
import sys
from urllib.parse import urljoin

import click
import m3u8

from .. import __version__


class MutuallyExclusiveOption(click.Option):
    """Click option that is mutually exclusive with another option."""

    def __init__(self, *args, not_required_if: list[str] | None = None, **kwargs) -> None:
        self.not_required_if = not_required_if or []
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx: click.Context, opts: dict, args: list) -> tuple:
        current = self.name in opts and opts[self.name] is not None
        for other in self.not_required_if:
            if other in opts and opts[other] is not None and current:
                raise click.UsageError(
                    f"--{self.name.replace('_', '-')} and --{other.replace('_', '-')} are mutually exclusive"
                )
        return super().handle_parse_result(ctx, opts, args)


class HeaderParamType(click.ParamType):
    """HTTP header in curl's ``Name: value`` form."""

    name = "header"

    def convert(
        self,
        value: str | tuple[str, str] | None,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[str, str]:
        if isinstance(value, tuple):
            return value
        if value is None or ":" not in value:
            self.fail("must be in 'Name: value' form", param, ctx)

        name, header_value = value.split(":", 1)
        name = name.strip()
        if not name:
            self.fail("header name cannot be empty", param, ctx)

        return name, header_value.strip()


def source_options(func):
    """Decorator adding playlist source and request header options."""
    func = click.option(
        "-H",
        "--headers",
        type=HeaderParamType(),
        multiple=True,
        help="HTTP request header in 'Name: value' form. May be repeated.",
    )(func)
    func = click.option(
        "-u",
        "--url",
        type=str,
        default=None,
        help="URL to fetch M3U8 from. Use '-' to read URL from stdin.",
        cls=MutuallyExclusiveOption,
        not_required_if=["file"],
    )(func)
    func = click.option(
        "-f",
        "--file",
        type=click.Path(exists=True, dir_okay=False, allow_dash=True),
        default=None,
        help="File path to read M3U8 from. Use '-' for stdin (default).",
        cls=MutuallyExclusiveOption,
        not_required_if=["url"],
    )(func)
    return func


def load_playlist(
    file: str | None,
    url: str | None,
    headers: tuple[tuple[str, str], ...] = (),
) -> tuple[m3u8.M3U8, str | None]:
    """Load M3U8 playlist from file or URL.

    Returns:
        Tuple of (playlist, base_url) where base_url is set when loading from URL
    """
    if url is not None:
        # URL mode
        if url == "-":
            # Read URL from stdin
            url = sys.stdin.read().strip()
        return m3u8.load(url, headers=dict(headers)), url
    else:
        # File mode (default: stdin)
        if file is None or file == "-":
            content = sys.stdin.read()
            return m3u8.loads(content), None
        else:
            return m3u8.load(file), None


def get_all_urls(playlist: m3u8.M3U8) -> list[str]:
    """Extract all URLs from playlist including init segment."""
    urls: list[str] = []

    # Add init segment if present (from #EXT-X-MAP)
    if playlist.segment_map:
        for init in playlist.segment_map:
            if init.uri:
                urls.append(init.uri)

    # Add all segment URLs
    urls.extend(seg.uri for seg in playlist.segments if seg.uri)

    return urls


def infer_base_url(playlist: m3u8.M3U8) -> str | None:
    """Infer a media-directory URL from the base URI resolved by m3u8."""
    if not playlist.base_uri:
        return None

    candidate = playlist.base_uri.rstrip("/")
    if re.search(r"\.[\w]+$", candidate):
        return candidate

    return None


def resolve_urls(urls: list[str], base_url: str) -> list[str]:
    """Resolve playlist URLs relative to a directory URL."""
    directory_url = f"{base_url.rstrip('/')}/"
    return [urljoin(directory_url, url) for url in urls]


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name="hls")
def hls() -> None:
    """HLS playlist utils"""


@hls.command()
@source_options
@click.option("--base-url", type=str, default=None, help="Base URL for resolving relative paths.")
def urls(
    file: str | None,
    url: str | None,
    headers: tuple[tuple[str, str], ...],
    base_url: str | None,
) -> None:
    """Extract segment URLs from M3U8 playlist.

    By default reads M3U8 content from stdin. Use -u to fetch from URL.

    Examples:
        cat playlist.m3u8 | hls urls
        hls urls -f playlist.m3u8
        hls urls -u https://example.com/playlist.m3u8
        echo "https://example.com/playlist.m3u8" | hls urls -u -
    """
    playlist, source_url = load_playlist(file, url, headers)

    if base_url is None and source_url is not None:
        base_url = infer_base_url(playlist)

    result = get_all_urls(playlist)

    if base_url:
        result = resolve_urls(result, base_url)

    print("\n".join(result))


@hls.command()
@source_options
def dump(
    file: str | None,
    url: str | None,
    headers: tuple[tuple[str, str], ...],
) -> None:
    """Dump M3U8 playlist contents.

    By default reads M3U8 content from stdin. Use -u to fetch from URL.

    Examples:
        cat playlist.m3u8 | hls dump
        hls dump -f playlist.m3u8
        hls dump -u https://example.com/playlist.m3u8
        echo "https://example.com/playlist.m3u8" | hls dump -u -
    """
    playlist, _ = load_playlist(file, url, headers)
    print(playlist.dumps())
