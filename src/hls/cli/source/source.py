import io
import pathlib

# Source can be a Path (file), str (URL), or TextIOWrapper (stdin)
# We use TextIOWrapper to type hint stdin/stdout/stderr file objects
type Source = pathlib.Path | str | io.TextIOWrapper
