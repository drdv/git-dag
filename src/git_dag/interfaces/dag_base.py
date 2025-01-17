"""Based class to interface DAG backends."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class DagBase(ABC):
    """DAG base class."""

    def __init__(self) -> None:
        self._dag: Any = None  # FIXME: be specific with the type
        self.nodes: list[dict[str, Optional[str]]] = []
        self.edges: set[tuple[str, str]] = set()

    @abstractmethod
    def edge(self, node1_name: str, node2_name: str) -> None:
        """Add an edge."""

    @abstractmethod
    def node(
        self,
        name: str,
        label: str,
        color: str,
        fillcolor: str,
        shape: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> None:
        """Add a node."""

    @abstractmethod
    def build(
        self,
        format: str,  # pylint: disable=redefined-builtin
        node_attr: dict[str, str],
        edge_attr: dict[str, str],
        dag_attr: dict[str, str],
        filename: str,
    ) -> None:
        """Build the graph."""

    @abstractmethod
    def render(self) -> None:
        """Render the graph."""

    @abstractmethod
    def source(self) -> str:
        """Return graph source file."""
