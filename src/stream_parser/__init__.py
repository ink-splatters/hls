from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("stream-parser")
except PackageNotFoundError:
    __version__ = "dev"

__all__ = [
    "__version__",
]
