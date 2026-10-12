# stream-parser

Python package and command-line utilities for working with HLS (M3U8) playlists and
MPEG-DASH Media Presentation Description (MPD) manifests.

## Installation

```bash
uv tool install 'stream-parser @ git+https://github.com/ink-splatters/stream-parser'
```

TODO: PyPI publication

## Roadmap

- [x] Load HLS playlists and DASH MPDs from files, stdin, and HTTP(S).
- [x] Serialize parsed manifests and enumerate initialization and media URLs.
- [x] `hls` and `dash` CLIs feature parity.
- [ ] Download media or delegate to a download manager, with track/representation
  selection and byte-range handling.
- [ ] Assemble downloaded media with FFmpeg, handling initialization segments
  and separate audio/video tracks.
- [ ] Explore streaming server with configurable segment duration and optional
  media processing, as a potential separate project, using `stream-parser`

## Usage

```bash
hls urls -f playlist.m3u8
dash urls -f manifest.mpd
dash dump -f manifest.mpd
cat manifest.mpd | dash urls
```

Use `-u` to fetch a manifest, and repeat `-H` to supply HTTP headers:

```bash
dash urls -u https://example.com/video/manifest.mpd \
  -H 'Referer: https://example.com/watch' \
  -H 'Authorization: Bearer token'

# contains url
pbpaste | hls urls -u -
```

## Development

```bash
uv sync --locked --all-extras
uv run poe fix
uv run poe test
```

Update all dependencies:

```bash
uv lock --upgrade
```

Update GitHub actions:

```bash
bunx actions-up
# or
# npx actions-up
```
