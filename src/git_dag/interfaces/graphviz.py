"""Interface for graphviz (https://github.com/xflr6/graphviz)."""

from typing import Any, Optional

from graphviz import Digraph  # type: ignore[import-untyped]

from .dag_base import DagBase


class DagGraphviz(DagBase):
    """Graphviz interface."""

    def edge(self, node1_name: str, node2_name: str) -> None:
        self.edges.add((node1_name, node2_name))

    def node(  # pylint: disable=too-many-positional-arguments
        self,
        name: str,
        label: str,
        color: Optional[str] = None,
        fillcolor: Optional[str] = None,
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

    def build(  # pylint: disable=too-many-positional-arguments
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

        # node order influences DAG
        for node in sorted(self.nodes, key=lambda x: (x["label"], x["tooltip"])):
            self._dag.node(**node)
        self._dag.edges(sorted(self.edges))

    def render(self) -> None:
        self._dag.render()

    def source(self) -> str:
        return str(self._dag.source)  # use str(.) is to make mypy happy

    def get(self) -> Any:
        return self._dag
