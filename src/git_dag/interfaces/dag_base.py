"""Based class to interface DAG backends."""

from abc import ABC, abstractmethod
from typing import Any, Literal, Optional

from ..constants import DictStrStr


class DagBase(ABC):
    """DAG base class."""

    def __init__(self, standalone_cluster: bool = False) -> None:
        self._dag: Any = None
        self.nodes: list[dict[str, Optional[str]]] = []
        self.edges: list[tuple[str, str]] = []
        self.edges_custom: list[tuple[str, str, DictStrStr]] = []
        self.standalone_trees: list[dict[str, Optional[str]]] = []
        self.standalone_blobs: list[dict[str, Optional[str]]] = []
        self.standalone_cluster = standalone_cluster

    @abstractmethod
    def edge(self, node1_name: str, node2_name: str, **attrs: str) -> None:
        """Add an edge."""

    @abstractmethod
    def node(  # pylint: disable=too-many-positional-arguments
        self,
        name: str,
        label: str,
        color: str,
        tooltip: Optional[str] = None,
        URL: Optional[str] = None,
        standalone_kind: Optional[Literal["tree", "blob"]] = None,
        **attrs: str,
    ) -> None:
        """Add a node."""

    @abstractmethod
    def build(  # pylint: disable=too-many-positional-arguments
        self,
        format: str,  # pylint: disable=redefined-builtin
        node_attr: DictStrStr,
        edge_attr: DictStrStr,
        dag_attr: DictStrStr,
        filename: str,
        cluster_params: DictStrStr,
    ) -> None:
        """Build the graph."""

    @abstractmethod
    def render(self) -> None:
        """Render the graph."""

    @abstractmethod
    def source(self) -> str:
        """Return graph source file."""

    @abstractmethod
    def get(self) -> Any:
        """Return the backend graph object."""
