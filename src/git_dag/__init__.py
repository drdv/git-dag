"""Module interface."""

try:
    from ._version import __version__
except ModuleNotFoundError:
    __version__ = "unknown (package not installed)"

from .git_repository import GitRepository

__all__ = ["GitRepository"]
