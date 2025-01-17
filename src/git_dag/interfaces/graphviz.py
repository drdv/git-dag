"""Interface for graphviz (https://github.com/xflr6/graphviz)."""

from typing import Optional

from graphviz import Digraph  # type: ignore[import-untyped]

from .dag_base import DagBase


class DagGraphviz(DagBase):
    """Graphviz interface."""

    def edge(self, node1_name: str, node2_name: str) -> None:
        self.edges.add((node1_name, node2_name))

    def node(
        self,
        name: str,
        label: str,
        color: str,
        fillcolor: str,
        shape: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> None:
        self.nodes.append(
            {
                "name": name,
                "label": label,
                "color": color,
                "fillcolor": fillcolor,
                "shape": shape,
                "tooltip": tooltip,
            }
        )

    def build(
        self,
        format: str,  # pylint: disable=redefined-builtin
        node_attr: dict[str, str],
        edge_attr: dict[str, str],
        dag_attr: dict[str, str],
        filename: str,
    ) -> None:
        self._dag = Digraph(
            format=format,
            node_attr=node_attr,
            edge_attr=edge_attr,
            graph_attr=dag_attr,
            filename=filename,
        )

        for node in self.nodes:
            self._dag.node(**node)
        self._dag.edges(self.edges)

    def render(self) -> None:
        self._dag.render()

    def source(self) -> str:
        return str(self._dag.source())  # FIXME: str(.) is to make mypy happy
