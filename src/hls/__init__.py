from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("apfs-hcp-patcher")
except PackageNotFoundError:
    __version__ = "dev"

__all__ = [
    "__version__",
]
