import typing as t
import pathlib

# Source can be a Path (file), str (URL), or text stream (stdin).
type Source = pathlib.Path | str | t.TextIO
