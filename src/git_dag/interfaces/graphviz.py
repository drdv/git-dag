"""Interface for graphviz (https://github.com/xflr6/graphviz)."""

from pathlib import Path
from typing import Any, Literal, Optional

from graphviz import Digraph  # type: ignore[import-untyped]

from ..constants import DictStrStr
from .dag_base import DagBase


def handle_none(x: Optional[str] = None) -> str:
    """Handle None values when sorting."""
    return "" if x is None else x


class DagGraphviz(DagBase):
    """Graphviz interface."""

    def edge(
        self,
        node1_name: str,
        node2_name: str,
        **attrs: str,
    ) -> None:
        if attrs:
            self.edges_custom.append((node1_name, node2_name, attrs))
        else:
            self.edges.append((node1_name, node2_name))

    def node(  # pylint: disable=too-many-positional-arguments
        self,
        name: str,
        label: str,
        color: Optional[str] = None,
        tooltip: Optional[str] = None,
        URL: Optional[str] = None,
        standalone_kind: Optional[Literal["tree", "blob"]] = None,
        **attrs: str,
    ) -> None:
        combined_attrs = {
            "name": name,
            "label": label,
            "color": color,
            "tooltip": tooltip,
            "URL": URL,
            **attrs,
        }
        if URL is not None:
            combined_attrs["target"] = "_blank"

        if standalone_kind is None:
            self.nodes.append(combined_attrs)
        elif standalone_kind == "tree":
            self.standalone_trees.append(combined_attrs)
        elif standalone_kind == "blob":
            self.standalone_blobs.append(combined_attrs)

    def build(  # pylint: disable=too-many-positional-arguments
        self,
        format: str,  # pylint: disable=redefined-builtin
        node_attr: DictStrStr,
        edge_attr: DictStrStr,
        dag_attr: DictStrStr,
        filename: str | Path,
        cluster_params: DictStrStr,
    ) -> None:
        def form_clulster_of_standalone_trees_and_blobs() -> None:
            # standalone blobs and trees are placed in a cluster
            if (
                self.standalone_cluster
                or self.standalone_trees
                or self.standalone_blobs
            ):
                with self._dag.subgraph(
                    name="cluster_standalone",
                    edge_attr={"style": "invis"},
                ) as c:
                    c.attr(**cluster_params)
                    sorted_standalone_trees = sorted(
                        self.standalone_trees,
                        key=lambda x: (x["label"], handle_none(x["tooltip"])),
                    )
                    sorted_standalone_blobs = sorted(
                        self.standalone_blobs,
                        key=lambda x: (x["label"], handle_none(x["tooltip"])),
                    )

                    tree_names = [t["name"] for t in sorted_standalone_trees]
                    blob_names = [b["name"] for b in sorted_standalone_blobs]

                    for node in sorted_standalone_trees:
                        c.node(**node)
                    c.edges(zip(tree_names, tree_names[1:]))

                    for node in sorted_standalone_blobs:
                        c.node(**node)
                    c.edges(zip(blob_names, blob_names[1:]))

                    if not tree_names and not blob_names:
                        c.node("node", style="invis")  # to display an empty cluster

        self._dag = Digraph(
            format=format,
            node_attr=node_attr,
            edge_attr=edge_attr,
            graph_attr=dag_attr,
            filename=filename,
        )

        # node order influences DAG
        for node in sorted(
            self.nodes, key=lambda x: (x["label"], handle_none(x["tooltip"]))
        ):
            self._dag.node(**node)
        self._dag.edges(sorted(self.edges))
        for node1, node2, attrs in self.edges_custom:
            self._dag.edge(node1, node2, **attrs)

        form_clulster_of_standalone_trees_and_blobs()

    def render(self) -> None:
        self._dag.render()

    def source(self) -> str:
        return str(self._dag.source)  # use str(.) is to make mypy happy

    def get(self) -> Any:
        return self._dag
