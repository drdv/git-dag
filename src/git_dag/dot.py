"""Graphviz visualization.

Note
-----
Naturally the edge connecting two commits should point to the parent. Following the same
argument, the edge from a commit and its associated tree should point to the commit but,
I find this counter-intuitive because then, following the same logic, the edges from
blobs should point to the containing tree. So while commits point to parent commits, for
trees and blobs the logic is inverted (and this leads to nicer layouts with graphviz,
where trees and files end-up towards the bottom).

"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from graphviz import Digraph  # type: ignore[import-untyped]

from .constants import (
    GIT_EMPTY_TREE_OBJECT_SHA,
    GRAPHVIZ_EDGE_ATTR,
    GRAPHVIZ_GRAPH_ATTR,
    GRAPHVIZ_NODE_ATTR,
    GRAPHVIZ_NODE_COLORS,
    SHA_LIMIT,
)
from .pydantic_models import GitBlob, GitCommit, GitTree

if TYPE_CHECKING:
    from .git_repository import GitRepository

LOG = logging.getLogger(__name__)


@dataclass
class DagVisualizer:
    """Git DAG visualizer."""

    repository: GitRepository
    objects_sha_to_include: Optional[set[str]] = None

    graph_attr: Optional[dict[str, str]] = None
    format: str = "svg"
    filename: str = "git-dag.gv"

    show_local_branches: bool = True
    show_remote_branches: bool = False
    show_trees: bool = False
    show_blobs: bool = False
    show_tags: bool = True
    show_stash: bool = False

    def __post_init__(self) -> None:
        self.tooltip_names = self.repository.inspector.names_of_blobs_and_trees
        self.edges: set[tuple[str, str]] = set()
        self.included_nodes_id: set[str] = set()

        self.graph = Digraph(
            format=self.format,
            node_attr=GRAPHVIZ_NODE_ATTR,
            edge_attr=GRAPHVIZ_EDGE_ATTR,
            graph_attr={
                **GRAPHVIZ_GRAPH_ATTR,
                **({} if self.graph_attr is None else self.graph_attr),
            },
            filename=self.filename,
        )
        self._build_graph()

    def show(self, xdg_open: bool = False) -> Optional[Digraph]:
        """Show the graph.

        Note
        -----
        When the ``format`` is set to ``gv``, only the source file is generated and the
        user can generate the graph manually with any layout engine and parameters.
        For example: ``dot -Gnslimit=2 -Tsvg git-dag.gv -o git-dag.gv.svg``, see
        https://forum.graphviz.org/t/creating-a-dot-graph-with-thousands-of-nodes/1092/2

        Generating a graph with more than 1000 nodes could be time-consuming. It is
        recommended to get an initial view using ``git dag -lrto`` and then limit to
        specific references and number of nodes using the ``-i`` and ``-n`` flags.

        """
        if self.format == "gv":
            with open(self.filename, "w", encoding="utf-8") as h:
                h.write(self.graph.source)
        else:
            self.graph.render()
            if xdg_open:
                subprocess.run(
                    f"xdg-open {self.filename}.{self.format}",
                    shell=True,
                    check=True,
                )
            else:
                return self.graph

        return None

    def _is_object_to_include(self, sha: str) -> bool:
        """Return ``True`` if the object with given ``sha`` is to be displayed."""
        if self.objects_sha_to_include is None:
            return True
        return sha in self.objects_sha_to_include

    def _add_head(self) -> None:
        head = self.repository.head
        detached = self.repository.inspector.git.is_detached_head()
        if self._is_object_to_include(head.sha):
            self.graph.node(
                "HEAD",
                label="HEAD *" if detached else "HEAD",
                color=GRAPHVIZ_NODE_COLORS["head"],
                fillcolor=GRAPHVIZ_NODE_COLORS["head"],
            )
            self.edges.add(("HEAD", head.sha))

    def _add_local_branches(self) -> None:
        local_branches = [b for b in self.repository.branches if b.is_local]
        for branch in local_branches:
            if self._is_object_to_include(branch.commit.sha):
                node_id = f"local-branch-{branch.name}"
                self.graph.node(
                    node_id,
                    label=branch.name,
                    color=GRAPHVIZ_NODE_COLORS["local-branches"],
                    fillcolor=GRAPHVIZ_NODE_COLORS["local-branches"],
                    tooltip=f"-> {branch.tracking}",
                )
                self.edges.add((node_id, branch.commit.sha))

    def _add_remote_branches(self) -> None:
        remote_branches = [b for b in self.repository.branches if not b.is_local]
        for branch in remote_branches:
            if self._is_object_to_include(branch.commit.sha):
                node_id = f"remote-branch-{branch.name}"
                self.graph.node(
                    node_id,
                    label=branch.name,
                    color=GRAPHVIZ_NODE_COLORS["remote-branches"],
                    fillcolor=GRAPHVIZ_NODE_COLORS["remote-branches"],
                )
                self.edges.add((node_id, branch.commit.sha))

    def _add_annotated_tags(self) -> None:
        for sha, item in self.repository.tags["annotated"].items():
            if self._is_object_to_include(item.anchor.sha):
                self.graph.node(
                    sha,
                    label=item.name,
                    color=GRAPHVIZ_NODE_COLORS["tag"],
                    fillcolor=GRAPHVIZ_NODE_COLORS["tag"],
                )
                if item.anchor.sha in self.included_nodes_id:
                    self.edges.add((sha, item.anchor.sha))

    def _add_lightweight_tags(self) -> None:
        for name, item in self.repository.tags["lightweight"].items():
            if self._is_object_to_include(item.anchor.sha):
                node_id = f"lwt-{name}-{item.anchor.sha}"
                self.graph.node(
                    node_id,
                    label=name,
                    color=GRAPHVIZ_NODE_COLORS["tag-lw"],
                    fillcolor=GRAPHVIZ_NODE_COLORS["tag-lw"],
                )
                if item.anchor.sha in self.included_nodes_id:
                    self.edges.add((node_id, item.anchor.sha))

    def _add_tree(self, sha: str, item: GitTree) -> None:
        self.included_nodes_id.add(sha)
        if sha == GIT_EMPTY_TREE_OBJECT_SHA:
            color_label = "the-empty-tree"
            tooltip = f"THE EMPTY TREE\n{GIT_EMPTY_TREE_OBJECT_SHA}"
        else:
            color_label = "tree"
            tooltip = self.tooltip_names.get(sha, sha)

        self.graph.node(
            sha,
            label=sha[:SHA_LIMIT],
            color=GRAPHVIZ_NODE_COLORS[color_label],
            fillcolor=GRAPHVIZ_NODE_COLORS[color_label],
            shape="folder",
            tooltip=tooltip,
        )

        if self.show_blobs:
            for child in item.children:
                self.edges.add((sha, child.sha))

    def _add_blob(self, sha: str) -> None:
        self.included_nodes_id.add(sha)
        self.graph.node(
            sha,
            label=sha[:SHA_LIMIT],
            color=GRAPHVIZ_NODE_COLORS["blob"],
            fillcolor=GRAPHVIZ_NODE_COLORS["blob"],
            shape="note",
            tooltip=self.tooltip_names.get(sha, sha),
        )

    def _add_commit(self, sha: str, item: GitCommit) -> None:
        if self._is_object_to_include(sha):
            self.included_nodes_id.add(sha)
            color = "commit" if item.reachable else "commit-unreachable"
            self.graph.node(
                sha,
                label=sha[:SHA_LIMIT],
                color=GRAPHVIZ_NODE_COLORS[color],
                fillcolor=GRAPHVIZ_NODE_COLORS[color],
                tooltip=item.misc_info,
            )

            if self.show_trees:
                self.edges.add((sha, item.tree.sha))

            for parent in item.parents:
                if self._is_object_to_include(parent.sha):
                    self.edges.add((sha, parent.sha))

    def _add_stashes(self) -> None:
        for stash in self.repository.stashes:
            if self._is_object_to_include(stash.commit.sha):
                stash_id = f"stash-{stash.index}"
                self.graph.node(
                    stash_id,
                    label=f"stash:{stash.index}",
                    color=GRAPHVIZ_NODE_COLORS["stash"],
                    fillcolor=GRAPHVIZ_NODE_COLORS["stash"],
                    tooltip=stash.title,
                )
                self.edges.add((stash_id, stash.commit.sha))

    def _build_graph(self) -> None:
        # tags are not handled in this loop
        for sha, item in self.repository.objects.items():
            if self.show_trees:
                if self._is_object_to_include(sha):
                    if isinstance(item, GitTree):
                        self._add_tree(sha, item)

                    if self.show_blobs and isinstance(item, GitBlob):
                        self._add_blob(sha)

            if isinstance(item, GitCommit):
                self._add_commit(sha, item)

        if self.show_local_branches:
            self._add_local_branches()

        if self.show_remote_branches:
            self._add_remote_branches()

        if self.show_tags:
            self._add_annotated_tags()
            self._add_lightweight_tags()

        if self.show_stash:
            self._add_stashes()

        self._add_head()
        self.graph.edges(self.edges)
