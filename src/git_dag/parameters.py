"""Parameters.

Note
-----
``ParamsDagGlobal``, ``ParamsDagNode`` and ``ParamsDagEdge`` are directly passed to the
backend (FIXME: currently all parameters assume graphviz) and allow extra arguments --
``model_config = ConfigDict(extra="allow")``.

"""

import logging
from abc import abstractmethod
from contextlib import ContextDecorator
from pathlib import Path
from types import TracebackType
from typing import Any, ClassVar, Literal, Optional, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from git_dag.constants import CONFIG_FILE

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger(__name__)


class CustomYamlDumper(yaml.SafeDumper):
    """Insert empty line between top-level sections.

    https://github.com/yaml/pyyaml/issues/127#issuecomment-525800484
    """

    def write_line_break(self, data: Any = None) -> None:
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()


class ParamsBase(BaseModel):
    """Base class for parameters."""

    model_config = ConfigDict(extra="forbid")

    ignore_config_file: ClassVar[bool] = False

    @staticmethod
    def set_ignore_config_file(value: bool) -> None:
        """Set whether to ignore the config file or not.

        Note
        -----
        This is a class method that can be used from any child class to ignore the
        config file for all child classes (note that below we set the
        ``ignore_config_file`` class variable directly on the base class).

        Warning
        --------
        Instances of child classes of :class:`ParamsBase` created before using this
        method are not impacted by changes in :attr:`ignore_config_file`. The
        recommended way to ignore the config wile is using the context manager
        :class:`context_ignore_config_file`.

        """
        ParamsBase.ignore_config_file = value

    @staticmethod
    @abstractmethod
    def section_in_config() -> str:
        """Return associated section in the config file.

        Warning
        --------
        The section name has to coincide with the field names in :class:`Params`.

        """

    @model_validator(mode="after")
    def set_defaults_values(self) -> Self:
        """Set parameter default values.

        Note
        -----
        Parameters in decreasing order of priority:
          + user-specified parameters
          + parameters from the config file (if it exists)
          + built-in default parameters

        Warning
        --------
        Calling this method from each child class would result in parsing the same
        config file again and again. This is acceptable as the time to parse is
        negligible and this simplifies the code. FIXME: maybe rework things later ...

        """
        if not self.ignore_config_file and CONFIG_FILE.is_file():
            with open(CONFIG_FILE, "r", encoding="utf-8") as h:
                params_from_config_file = yaml.safe_load(h)

            if self.section_in_config() in params_from_config_file:
                section_params = params_from_config_file[self.section_in_config()]
                fields_defined_by_user = self.model_dump(exclude_unset=True)
                for key, value in section_params.items():
                    if key not in fields_defined_by_user:
                        setattr(self, key, value)

        return self


class LinksTemplates(BaseModel):
    """Parameters of of git providers for links to commits, tags, branches."""

    base: str
    commit: str
    branch: str
    tag: str


class ParamsLinks(ParamsBase):
    """Parameters of of git providers for links to commits, tags, branches."""

    # https://docs.pydantic.dev/latest/concepts/serialization/
    # https://docs.pydantic.dev/latest/concepts/fields/#mutable-default-values
    templates: dict[str, SerializeAsAny[LinksTemplates]] = {
        "github": LinksTemplates(
            base="https://github.com",
            commit="{base}/{user}/{project}/commit/{commit}",
            branch="{base}/{user}/{project}/tree/{branch}",
            tag="{base}/{user}/{project}/releases/tag/{tag}",
        ),
        "bitbucket": LinksTemplates(
            base="https://bitbucket.org",
            commit="{base}/{user}/{project}/commits/{commit}",
            branch="{base}/{user}/{project}/src/{branch}",
            tag="{base}/{user}/{project}/src/{tag}",
        ),
    }

    @staticmethod
    def section_in_config() -> str:
        return "links"


class ParamsStandaloneCluster(ParamsBase):
    """Standalone cluster parameters."""

    color: str = "lightgrey"
    label: str = r"Standalone\nTrees & Blobs"
    fontname: str = "Courier"

    @staticmethod
    def section_in_config() -> str:
        return "standalone_cluster"


class ParamsDagGlobal(ParamsBase):
    """Global DAG parameters."""

    model_config = ConfigDict(extra="allow")

    rankdir: Literal["LR", "RL", "TB", "BT"] = "TB"
    dpi: str = "None"
    bgcolor: str = "white"  # bgcolor "transparent" is inconsistent accross browsers

    @staticmethod
    def section_in_config() -> str:
        return "dag_global"


class ParamsDagNode(ParamsBase):
    """DAG node parameters."""

    model_config = ConfigDict(extra="allow")

    shape: str = "box"
    style: str = "filled"
    margin: str = "0.01,0.01"
    width: str = "0.02"
    height: str = "0.02"
    fontname: str = "Courier"

    @staticmethod
    def section_in_config() -> str:
        return "dag_node"


class ParamsDagEdge(ParamsBase):
    """DAG edge parameters."""

    model_config = ConfigDict(extra="allow")

    arrowsize: str = "0.5"
    color: str = "gray10"

    @staticmethod
    def section_in_config() -> str:
        return "dag_edge"


class ParamsDagNodeColors(ParamsBase):
    """Colors for DAG nodes."""

    commit: str = "gold3"
    commit_unreachable: str = "darkorange"
    commit_in_range: str = "red"
    tree: str = "deepskyblue4"
    the_empty_tree: str = "darkturquoise"
    blob: str = "gray"
    tag: str = "pink"
    tag_deleted: str = "rosybrown4"
    tag_lw: str = "lightcoral"
    head: str = "cornflowerblue"
    local_branches: str = "forestgreen"
    remote_branches: str = "firebrick"
    stash: str = "skyblue"
    notes: str = "white"
    annotations: str = "aquamarine3"

    @staticmethod
    def section_in_config() -> str:
        return "dag_node_colors"


class ParamsMisc(ParamsBase):
    """Misc parameters."""

    annotations_symbol: str = "&#9758;"
    annotations_shape: str = "cds"
    annotations_truncate: int = 20
    sha_truncate: int = 7

    @staticmethod
    def section_in_config() -> str:
        return "misc"


class ParamsPublic(ParamsBase):
    """Parameters exposed as command-line arguments."""

    path: str = "."
    file: str | Path = "git-dag.gv"
    format: str = "svg"
    dag_backend: str = "graphviz"
    log_level: str = "WARNING"

    range_expr: Optional[str] = None
    init_refs: Optional[list[str]] = None
    annotations: Optional[list[list[str]]] = None

    max_numb_commits: int = 1000
    commit_message_as_label: int = 0

    html_embed_svg: bool = False
    show_unreachable_commits: bool = False
    show_tags: bool = False
    show_deleted_tags: bool = False
    show_local_branches: bool = False
    show_remote_branches: bool = False
    show_stash: bool = False
    show_trees: bool = False
    show_trees_standalone: bool = False
    show_blobs: bool = False
    show_blobs_standalone: bool = False
    show_head: bool = False
    show_prs_heads: bool = False
    xdg_open: bool = False

    @staticmethod
    def section_in_config() -> str:
        return "public"


class context_ignore_config_file(ContextDecorator):
    """Context manager within which the config file is ignored.

    Example
    --------
    .. code-block:: python

        print(ParamsPublic.ignore_config_file)  # False
        with context_ignore_config_file():
            print(ParamsPublic.ignore_config_file)  # True

        print(ParamsPublic.ignore_config_file)  # False

    """

    def __enter__(self) -> Self:
        ParamsBase.ignore_config_file = True
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        ParamsBase.ignore_config_file = False


class Params(BaseModel):
    """A container class for all parameters.

    Note
    -----
    It is important to evaluate the default values at runtime (in order to consider
    potential changes in :attr:`~ParamsBase.ignore_config_file`) -- thus
    ``default_factory`` is used.

    Warning
    --------
    Pylint complains about no-member if the fields are defined using e.g.,
    ``public: ParamsPublic = Field(default_factory=ParamsPublic)`` -- with which mypy is
    happy. On the other hand, mypy complains about call-arg (Missing named argument) if
    we use ``public: Annotated[ParamsPublic, Field(default_factory=ParamsPublic)]`` with
    which pylint is happy (see first comment of https://stackoverflow.com/a/77844893).

    + mypy 1.15.0
    + pylint 3.3.6 (astroid 3.3.9)
    + python 3.13.1

    The former syntax is used below (i.e., mypy is prioritized) and pylint errors are
    suppressed by specifying ``generated-members`` in ``pyproject.toml``.

    """

    model_config = ConfigDict(extra="forbid")

    public: ParamsPublic = Field(default_factory=ParamsPublic)
    dag_global: ParamsDagGlobal = Field(default_factory=ParamsDagGlobal)
    dag_node: ParamsDagNode = Field(default_factory=ParamsDagNode)
    dag_edge: ParamsDagEdge = Field(default_factory=ParamsDagEdge)
    dag_node_colors: ParamsDagNodeColors = Field(default_factory=ParamsDagNodeColors)
    standalone_cluster: ParamsStandaloneCluster = Field(
        default_factory=ParamsStandaloneCluster
    )
    links: ParamsLinks = Field(default_factory=ParamsLinks)
    misc: ParamsMisc = Field(default_factory=ParamsMisc)

    @staticmethod
    def set_ignore_config_file(value: bool) -> None:
        """Set whether to ignore the config file or not.

        Warning
        --------
        This method is defined for convenience. See
        :func:`~ParamsBase.set_ignore_config_file`.

        """
        ParamsBase.ignore_config_file = value

    def create_config(self) -> None:
        """Create a config file from the parameters in the current instance."""
        if not CONFIG_FILE.is_file():
            with open(CONFIG_FILE, "w", encoding="utf-8") as h:
                yaml.dump(
                    self.model_dump(),
                    h,
                    Dumper=CustomYamlDumper,
                    sort_keys=False,
                )
            print(f"Created config {CONFIG_FILE}.")
        else:
            print(f"Config file {CONFIG_FILE} already exists.")
