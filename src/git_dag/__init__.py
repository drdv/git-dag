"""Module interface."""

try:
    from ._version import __version__
except ModuleNotFoundError:
    __version__ = "unknown (package not installed)"

from .git_repository import GitRepository
from .parameters import (
    Params,
    ParamsDagEdge,
    ParamsDagGlobal,
    ParamsDagNode,
    ParamsDagNodeColors,
    ParamsMisc,
    ParamsPublic,
    ParamsStandaloneCluster,
)

__all__ = [
    "GitRepository",
    "Params",
    "ParamsDagEdge",
    "ParamsDagGlobal",
    "ParamsDagNode",
    "ParamsDagNodeColors",
    "ParamsMisc",
    "ParamsPublic",
    "ParamsStandaloneCluster",
]
