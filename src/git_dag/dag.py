"""DAG visualization.

Note
-----
The edge between two git objects points towards the parent object. I consider a commit
to be the child of its associated tree (because it is formed from it) and this tree is a
child of its blobs (and trees). A commit is the parent of a tag (that points to it).

"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol

from .constants import (
    DAG_ATTR,
    DAG_EDGE_ATTR,
    DAG_NODE_ATTR,
    DAG_NODE_COLORS,
    GIT_EMPTY_TREE_OBJECT_SHA,
    SHA_LIMIT,
    DagBackends,
)
from .git_objects import DictStrStr, GitBlob, GitCommit, GitTag, GitTree
from .interfaces.graphviz import DagGraphviz
from .utils import transform_ascii_control_chars

if TYPE_CHECKING:  # pragma: no cover
    from .git_repository import GitRepository


class MixinProtocol(Protocol):
    """Mixin protocol."""

    show_unreachable_commits: bool
    show_local_branches: bool
    show_remote_branches: bool
    show_trees: bool
    show_trees_standalone: bool
    show_blobs: bool
    show_blobs_standalone: bool
    show_tags: bool
    show_deleted_tags: bool
    show_stash: bool
    show_head: bool
    range: Optional[list[str]]
    commit_message_as_label: int
    included_nodes_id: set[str]
    tooltip_names: DictStrStr
    repository: GitRepository
    dag: Any

    def _is_object_to_include(self, sha: str) -> bool: ...  # pragma: no cover
    def _is_tag_to_include(self, item: GitTag) -> bool: ...  # pragma: no cover
    def _add_notes_label_node(self, sha: str, ref: str) -> None: ...  # pragma: no cover


class CommitHandlerMixin:
    """Handle commits."""

    def _add_notes_label_node(self: MixinProtocol, sha: str, ref: str) -> None:
        """Add a node that labels the root of the git notes DAG."""
        self.dag.node(
            name="GIT-NOTES-LABEL",
            label="git notes",
            fillcolor=DAG_NODE_COLORS["notes"],
            tooltip=ref,
            shape="egg",
        )
        self.dag.edge("GIT-NOTES-LABEL", sha)

    def _add_commit(self: MixinProtocol, sha: str, item: GitCommit) -> None:
        def form_tooltip(item: GitCommit) -> str:
            return repr(
                f"author: {item.author} {item.author_email}\n"
                f"{item.author_date}\n"
                f"committer: {item.committer} {item.committer_email}\n"
                f"{item.committer_date}\n\n"
                f"{transform_ascii_control_chars(item.message)}"
            )[1:-1]

        unreachable_switch = item.is_reachable or self.show_unreachable_commits
        if self._is_object_to_include(sha) and unreachable_switch:
            self.included_nodes_id.add(sha)
            color_label = "commit" if item.is_reachable else "commit-unreachable"
            in_range = self.range is None or sha not in self.range

            if self.commit_message_as_label > 0:
                label = item.message[: self.commit_message_as_label]
            else:
                label = sha[:SHA_LIMIT]

            self.dag.node(
                name=sha,
                label=label,
                color=DAG_NODE_COLORS[color_label] if in_range else None,
                fillcolor=DAG_NODE_COLORS[color_label],
                tooltip=form_tooltip(item),
            )

            if self.repository.notes_dag_root is not None:
                if sha == self.repository.notes_dag_root["root"]:
                    self._add_notes_label_node(
                        sha,
                        self.repository.notes_dag_root["ref"],
                    )

            if self.show_trees:
                self.dag.edge(sha, item.tree.sha)

            for parent in item.parents:
                if self._is_object_to_include(parent.sha):
                    self.dag.edge(sha, parent.sha)


class TreeBlobHandlerMixin:
    """Handle trees and blobs."""

    def _add_tree(
        self: MixinProtocol,
        sha: str,
        item: GitTree,
        standalone: bool = False,
    ) -> None:
        self.included_nodes_id.add(sha)
        if sha == GIT_EMPTY_TREE_OBJECT_SHA:
            color_label = "the-empty-tree"
            tooltip = f"THE EMPTY TREE\n{GIT_EMPTY_TREE_OBJECT_SHA}"
        else:
            color_label = "tree"
            tooltip = self.tooltip_names.get(sha, sha)

        self.dag.node(
            name=sha,
            label=sha[:SHA_LIMIT],
            color=DAG_NODE_COLORS[color_label],
            fillcolor=DAG_NODE_COLORS[color_label],
            shape="folder",
            tooltip=tooltip,
            standalone_kind="tree" if standalone else None,
        )

        if self.show_blobs:
            for child in item.children:
                self.dag.edge(sha, child.sha)

    def _add_blob(self: MixinProtocol, sha: str, standalone: bool = False) -> None:
        self.included_nodes_id.add(sha)
        self.dag.node(
            name=sha,
            label=sha[:SHA_LIMIT],
            color=DAG_NODE_COLORS["blob"],
            fillcolor=DAG_NODE_COLORS["blob"],
            shape="note",
            tooltip=self.tooltip_names.get(sha, sha),
            standalone_kind="blob" if standalone else None,
        )


class TagHandlerMixin:
    """Handle tags."""

    def _is_tag_to_include(self: MixinProtocol, item: GitTag) -> bool:
        """Check if an annotated tag should be displayed.

        Note
        -----
        Lightweight tags cannot point to other tags or be pointed by annotated tags.

        """
        while isinstance(item.anchor, GitTag):
            item = item.anchor
        return item.anchor.sha in self.included_nodes_id

    def _add_annotated_tags(self: MixinProtocol) -> None:
        def form_tooltip(item: GitTag) -> str:
            return repr(
                f"{item.tagger} {item.tagger_email}\n"
                f"{item.tagger_date}\n\n"
                f"{transform_ascii_control_chars(item.message)}"
            )[1:-1]

        for sha, item in self.repository.tags.items():
            color_label = "tag-deleted" if item.is_deleted else "tag"
            if self._is_tag_to_include(item):
                if self.show_deleted_tags or not item.is_deleted:
                    self.dag.node(
                        name=sha,
                        label=item.name,
                        color=DAG_NODE_COLORS[color_label],
                        fillcolor=DAG_NODE_COLORS[color_label],
                        tooltip=form_tooltip(item),
                    )
                    self.dag.edge(sha, item.anchor.sha)

    def _add_lightweight_tags(self: MixinProtocol) -> None:
        for name, item in self.repository.tags_lw.items():
            if self._is_object_to_include(item.anchor.sha):
                node_id = f"lwt-{name}-{item.anchor.sha}"
                self.dag.node(
                    name=node_id,
                    label=name,
                    color=DAG_NODE_COLORS["tag-lw"],
                    fillcolor=DAG_NODE_COLORS["tag-lw"],
                    tooltip=item.anchor.sha,
                )
                if item.anchor.sha in self.included_nodes_id:
                    self.dag.edge(node_id, item.anchor.sha)


class StashHandlerMixin:
    """Handle stash."""

    def _add_stashes(self: MixinProtocol) -> None:
        for stash in self.repository.stashes:
            if self._is_object_to_include(stash.commit.sha):
                stash_id = f"stash-{stash.index}"
                self.dag.node(
                    name=stash_id,
                    label=f"stash:{stash.index}",
                    color=DAG_NODE_COLORS["stash"],
                    fillcolor=DAG_NODE_COLORS["stash"],
                    tooltip=stash.title,
                )
                if self.show_unreachable_commits or stash.commit.is_reachable:
                    self.dag.edge(stash_id, stash.commit.sha)


class BranchHandlerMixin:
    """Handle branches."""

    def _add_local_branches(self: MixinProtocol) -> None:
        local_branches = [b for b in self.repository.branches if b.is_local]
        for branch in local_branches:
            if self._is_object_to_include(branch.commit.sha):
                node_id = f"local-branch-{branch.name}"
                self.dag.node(
                    name=node_id,
                    label=branch.name,
                    color=DAG_NODE_COLORS["local-branches"],
                    fillcolor=DAG_NODE_COLORS["local-branches"],
                    tooltip=f"-> {branch.tracking}",
                )
                self.dag.edge(node_id, branch.commit.sha)

    def _add_remote_branches(self: MixinProtocol) -> None:
        remote_branches = [b for b in self.repository.branches if not b.is_local]
        for branch in remote_branches:
            if self._is_object_to_include(branch.commit.sha):
                node_id = f"remote-branch-{branch.name}"
                self.dag.node(
                    name=node_id,
                    label=branch.name,
                    color=DAG_NODE_COLORS["remote-branches"],
                    fillcolor=DAG_NODE_COLORS["remote-branches"],
                )
                self.dag.edge(node_id, branch.commit.sha)


class HeadHandlerMixin:
    """Handle HEAD."""

    def _add_local_head(self: MixinProtocol) -> None:
        head = self.repository.head
        if head.is_defined:
            assert head.commit is not None  # to make mypy happy
            if self._is_object_to_include(head.commit.sha):
                if head.is_detached:
                    self.dag.edge("HEAD", head.commit.sha)
                    tooltip = head.commit.sha
                else:
                    assert head.branch is not None  # to make mypy happy
                    self.dag.edge("HEAD", f"local-branch-{head.branch.name}")
                    tooltip = head.branch.name

                self.dag.node(
                    name="HEAD",
                    label="HEAD",
                    color=None if head.is_detached else DAG_NODE_COLORS["head"],
                    fillcolor=DAG_NODE_COLORS["head"],
                    tooltip=tooltip,
                )

    def _add_remote_heads(self: MixinProtocol) -> None:
        for head, ref in self.repository.remote_heads.items():
            self.dag.node(
                name=head,
                label=head,
                color=DAG_NODE_COLORS["head"],
                fillcolor=DAG_NODE_COLORS["head"],
                tooltip=ref,
            )
            self.dag.edge(head, f"remote-branch-{ref}")


@dataclass
class DagVisualizer(
    CommitHandlerMixin,
    TreeBlobHandlerMixin,
    TagHandlerMixin,
    StashHandlerMixin,
    BranchHandlerMixin,
    HeadHandlerMixin,
):
    """Git DAG visualizer."""

    repository: GitRepository
    dag_backend: DagBackends
    objects_sha_to_include: Optional[set[str]] = None

    dag_attr: Optional[DictStrStr] = None
    format: str = "svg"
    filename: str = "git-dag.gv"

    show_unreachable_commits: bool = False
    show_local_branches: bool = False
    show_remote_branches: bool = False
    show_trees: bool = False
    show_trees_standalone: bool = False
    show_blobs: bool = False
    show_blobs_standalone: bool = False
    show_tags: bool = False
    show_deleted_tags: bool = False
    show_stash: bool = False
    show_head: bool = False
    range: Optional[list[str]] = None

    commit_message_as_label: int = 0

    def __post_init__(self) -> None:
        self.tooltip_names = self.repository.inspector.blobs_and_trees_names
        self.included_nodes_id: set[str] = set()
        self.dag_attr_normalized = {
            **DAG_ATTR,
            **(
                {}
                if self.dag_attr is None
                else {key: str(value) for key, value in self.dag_attr.items()}
            ),
        }

        match self.dag_backend:
            case DagBackends.GRAPHVIZ:
                self.dag = DagGraphviz(
                    self.show_blobs_standalone or self.show_trees_standalone
                )
            case _:
                raise ValueError(f"Unrecognised backend: {self.dag_backend}")

        self._build_dag()

    def show(self, xdg_open: bool = False) -> Any:
        """Show the dag.

        Note
        -----
        When the ``format`` is set to ``gv``, only the source file is generated and the
        user can generate the DAG manually with any layout engine and parameters. For
        example: ``dot -Gnslimit=2 -Tsvg git-dag.gv -o git-dag.gv.svg``, see `this
        <https://forum.graphviz.org/t/creating-a-dot-graph-with-thousands-of-nodes/1092/2>`_
        thread.

        Generating a DAG with more than 1000 nodes could be time-consuming. It is
        recommended to get an initial view using ``git dag -lrto`` and then limit to
        specific references and number of nodes using the ``-i`` and ``-n`` flags.

        """
        if self.format == "gv":
            with open(self.filename, "w", encoding="utf-8") as h:
                h.write(self.dag.source())
        else:
            self.dag.render()
            if xdg_open:  # pragma: no cover
                subprocess.run(
                    f"xdg-open {self.filename}.{self.format}",
                    shell=True,
                    check=True,
                )

        return self.dag.get()

    def _is_object_to_include(self, sha: str) -> bool:
        """Return ``True`` if the object with given ``sha`` is to be displayed."""
        if self.objects_sha_to_include is None:
            return True
        return sha in self.objects_sha_to_include

    def _build_dag(self) -> None:
        # tags are not handled in this loop
        for sha, item in self.repository.objects.items():
            to_include = self._is_object_to_include(sha)
            not_reachable = sha not in self.repository.all_reachable_objects_sha
            match item:
                case GitTree():
                    if not_reachable and self.show_trees_standalone:
                        self._add_tree(sha, item, standalone=True)
                    elif to_include and self.show_trees:
                        self._add_tree(sha, item)
                case GitBlob():
                    if not_reachable and self.show_blobs_standalone:
                        self._add_blob(sha, standalone=True)
                    elif to_include and self.show_blobs:
                        self._add_blob(sha)
                case GitCommit():
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

        if self.show_head:
            self._add_local_head()
            self._add_remote_heads()

        self.dag.build(
            format=self.format,
            node_attr=DAG_NODE_ATTR,
            edge_attr=DAG_EDGE_ATTR,
            dag_attr=self.dag_attr_normalized,
            filename=self.filename,
        )
