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
from typing import TYPE_CHECKING, Optional

from graphviz import Digraph  # type: ignore[import-untyped]

from .constants import GIT_EMPTY_TREE_OBJECT_SHA
from .pydantic_models import GitBlob, GitCommit, GitTree

if TYPE_CHECKING:
    from .git_repository import GitRepository

LOG = logging.getLogger(__name__)

#: Node colors.
NODE_COLORS = {
    "commit": "gold3",
    "commit-unreachable": "darkorange",
    "tree": "deepskyblue4",
    "the-empty-tree": "darkturquoise",
    "blob": "gray",
    "tag": "pink",
    "tag-lw": "lightcoral",
    "head": "cornflowerblue",
    "local-branches": "forestgreen",
    "remote-branches": "firebrick",
    "stash": "skyblue",
}

#: Nuber of SHA characters to display in labels.
SHA_LIMIT = 8


class DagVisualizer:
    """Git DAG visualizer."""

    def __init__(
        # pylint: disable=too-many-positional-arguments
        self,
        repository: GitRepository,
        objects_sha_to_include: Optional[set[str]] = None,
        format: str = "svg",  # pylint: disable=redefined-builtin
        show_tags: bool = True,
        show_local_branches: bool = True,
        show_remote_branches: bool = False,
        show_trees: bool = False,
        show_blobs: bool = False,
        show_stash: bool = False,
        filename: str = "git-dag.gv",
        graph_attr: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize instance."""
        self.repository = repository
        self.filename = filename
        self.format = format
        self.show_tags = show_tags
        self.show_local_branches = show_local_branches
        self.show_remote_branches = show_remote_branches
        self.show_trees = show_trees
        self.show_blobs = show_blobs and show_trees and repository.inspector.parse_trees
        self.show_stash = show_stash

        self.objects_sha_to_include = objects_sha_to_include
        self.tooltip_names = self.repository.inspector.names_of_blobs_and_trees
        self.edges: set[tuple[str, str]] = set()
        self.included_nodes_id: set[str] = set()

        defult_graph_attr = {
            "rankdir": "TB",
            "dpi": None,
            "bgcolor": "gray42",
        }
        if graph_attr is None:
            graph_attr = {}

        self.graph = Digraph(
            format=self.format,
            node_attr={
                "shape": "box",
                "style": "filled",
                "margin": "0.01,0.01",
                "width": "0.02",
                "height": "0.02",
            },
            edge_attr={
                "arrowsize": "0.5",
                "color": "gray10",
            },
            graph_attr={**defult_graph_attr, **graph_attr},
            filename=self.filename,
        )
        self.build()

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
                color=NODE_COLORS["head"],
                fillcolor=NODE_COLORS["head"],
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
                    color=NODE_COLORS["local-branches"],
                    fillcolor=NODE_COLORS["local-branches"],
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
                    color=NODE_COLORS["remote-branches"],
                    fillcolor=NODE_COLORS["remote-branches"],
                )
                self.edges.add((node_id, branch.commit.sha))

    def _add_annotated_tags(self) -> None:
        for sha, item in self.repository.tags["annotated"].items():
            if self._is_object_to_include(item.anchor.sha):
                self.graph.node(
                    sha,
                    label=item.name,
                    color=NODE_COLORS["tag"],
                    fillcolor=NODE_COLORS["tag"],
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
                    color=NODE_COLORS["tag-lw"],
                    fillcolor=NODE_COLORS["tag-lw"],
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
            color=NODE_COLORS[color_label],
            fillcolor=NODE_COLORS[color_label],
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
            color=NODE_COLORS["blob"],
            fillcolor=NODE_COLORS["blob"],
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
                color=NODE_COLORS[color],
                fillcolor=NODE_COLORS[color],
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
                    color=NODE_COLORS["stash"],
                    fillcolor=NODE_COLORS["stash"],
                    tooltip=stash.title,
                )
                self.edges.add((stash_id, stash.commit.sha))

    def build(self) -> None:
        """Build the graph."""
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
