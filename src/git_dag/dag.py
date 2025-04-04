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
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Protocol

from .constants import (
    GIT_EMPTY_TREE_OBJECT_SHA,
    HTML_EMBED_SVG,
    DagBackends,
    DictStrStr,
)
from .git_objects import GitBlob, GitCommit, GitTag, GitTree
from .interfaces.graphviz import DagGraphviz
from .parameters import Params
from .utils import transform_ascii_control_chars

if TYPE_CHECKING:  # pragma: no cover
    from .git_repository import GitRepository


class MixinProtocol(Protocol):
    """Mixin protocol."""

    repository: GitRepository
    params: Params
    objects_sha_to_include: Optional[set[str]]
    dag: Any
    included_nodes_id: set[str]
    tooltip_names: DictStrStr
    in_range_commits: Optional[list[str]]

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
            fillcolor=self.params.dag_node_colors.notes,
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

        unreachable_switch = (
            item.is_reachable or self.params.public.show_unreachable_commits
        )

        if self._is_object_to_include(sha) and unreachable_switch:
            self.included_nodes_id.add(sha)
            color_label = "commit" if item.is_reachable else "commit_unreachable"
            is_in_range = (
                self.in_range_commits is not None and sha in self.in_range_commits
            )

            if self.params.public.commit_message_as_label > 0:
                label = item.message[: self.params.public.commit_message_as_label]
            else:
                label = sha[: self.params.misc.sha_truncate]

            color = getattr(self.params.dag_node_colors, color_label)
            self.dag.node(
                name=sha,
                label=label,
                color=(
                    self.params.dag_node_colors.commit_in_range
                    if is_in_range
                    else color
                ),
                fillcolor=color,
                tooltip=form_tooltip(item),
            )

            if self.repository.notes_dag_root is not None:
                if sha == self.repository.notes_dag_root["root"]:
                    self._add_notes_label_node(
                        sha,
                        self.repository.notes_dag_root["ref"],
                    )

            if self.params.public.show_trees:
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
            color_label = "the_empty_tree"
            tooltip = f"THE EMPTY TREE\n{GIT_EMPTY_TREE_OBJECT_SHA}"
        else:
            color_label = "tree"
            tooltip = self.tooltip_names.get(sha, sha)

        color = getattr(self.params.dag_node_colors, color_label)
        self.dag.node(
            name=sha,
            label=sha[: self.params.misc.sha_truncate],
            color=color,
            fillcolor=color,
            shape="folder",
            tooltip=tooltip,
            standalone_kind="tree" if standalone else None,
        )

        for child in item.children:
            match child:
                case GitTree():
                    self.dag.edge(sha, child.sha)
                case GitBlob():
                    if self.params.public.show_blobs:
                        self.dag.edge(sha, child.sha)

    def _add_blob(self: MixinProtocol, sha: str, standalone: bool = False) -> None:
        self.included_nodes_id.add(sha)
        self.dag.node(
            name=sha,
            label=sha[: self.params.misc.sha_truncate],
            color=self.params.dag_node_colors.blob,
            fillcolor=self.params.dag_node_colors.blob,
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
            if self._is_tag_to_include(item):
                if self.params.public.show_deleted_tags or not item.is_deleted:
                    self.included_nodes_id.add(sha)
                    color_label = "tag_deleted" if item.is_deleted else "tag"
                    color = getattr(self.params.dag_node_colors, color_label)
                    self.dag.node(
                        name=sha,
                        label=item.name,
                        color=color,
                        fillcolor=color,
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
                    color=self.params.dag_node_colors.tag_lw,
                    fillcolor=self.params.dag_node_colors.tag_lw,
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
                    color=self.params.dag_node_colors.stash,
                    fillcolor=self.params.dag_node_colors.stash,
                    tooltip=stash.title,
                )
                if (
                    self.params.public.show_unreachable_commits
                    or stash.commit.is_reachable
                ):
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
                    color=self.params.dag_node_colors.local_branches,
                    fillcolor=self.params.dag_node_colors.local_branches,
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
                    color=self.params.dag_node_colors.remote_branches,
                    fillcolor=self.params.dag_node_colors.remote_branches,
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

                color = self.params.dag_node_colors.head
                self.dag.node(
                    name="HEAD",
                    label="HEAD",
                    color=None if head.is_detached else color,
                    fillcolor=color,
                    tooltip=tooltip,
                )

    def _add_remote_heads(self: MixinProtocol) -> None:
        for head, ref in self.repository.remote_heads.items():
            self.dag.node(
                name=head,
                label=head,
                color=self.params.dag_node_colors.head,
                fillcolor=self.params.dag_node_colors.head,
                tooltip=ref,
            )
            self.dag.edge(head, f"remote-branch-{ref}")

    def _add_prs_heads(self: MixinProtocol) -> None:
        """Add pull-request heads."""
        if self.params.public.show_prs_heads:
            prs_heads = self.repository.inspector.git.get_prs_heads()
            if prs_heads is not None:
                for pr_id, sha in prs_heads.items():
                    if sha in self.included_nodes_id:
                        node_name = f"PR_{pr_id}_HEAD"
                        self.dag.node(
                            name=node_name,
                            label=pr_id,
                            color=self.params.dag_node_colors.head,
                            fillcolor=self.params.dag_node_colors.head,
                            shape="circle",
                        )
                        self.dag.edge(node_name, sha)

    def _add_annotations(self: MixinProtocol) -> None:
        if self.params.public.annotations is not None:
            for annotation in self.params.public.annotations:
                descriptor = annotation[0].strip()
                shas = self.repository.inspector.git.rev_parse_descriptors([descriptor])

                if shas is None:
                    continue

                sha = shas[0]
                if descriptor in sha or isinstance(
                    self.repository.objects[sha], GitTag
                ):
                    tooltip = (
                        None  # the annotation will not be displayed at all
                        if len(annotation) == 1
                        else " ".join(annotation[1:])
                    )
                    label = self.params.misc.annotations_symbol
                    shape = self.params.misc.annotations_shape
                else:
                    tooltip = (
                        descriptor if len(annotation) == 1 else " ".join(annotation[1:])
                    )
                    label = descriptor
                    shape = None

                if sha in self.included_nodes_id and tooltip is not None:
                    # colon in node name not supported by graphviz
                    name = f"annotation-{descriptor.replace(":", "=")}"
                    self.dag.node(
                        name=name,
                        label=label[: self.params.misc.annotations_truncate],
                        color=self.params.dag_node_colors.annotations,
                        fillcolor=self.params.dag_node_colors.annotations,
                        tooltip=tooltip,
                        shape=shape,
                    )
                    self.dag.edge(name, sha, style="dashed")


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
    params: Params
    objects_sha_to_include: Optional[set[str]] = None
    in_range_commits: Optional[list[str]] = None

    def __post_init__(self) -> None:
        self.tooltip_names = self.repository.inspector.blobs_and_trees_names
        self.included_nodes_id: set[str] = set()

        match DagBackends[self.params.public.dag_backend.upper()]:
            case DagBackends.GRAPHVIZ:
                self.dag = DagGraphviz(
                    self.params.public.show_blobs_standalone
                    or self.params.public.show_trees_standalone
                )
            case _:
                raise ValueError(
                    f"Unrecognised backend: {self.params.public.dag_backend}"
                )

        self._build_dag()

    @staticmethod
    def _embed_svg_in_html(filename: str) -> None:
        with open(
            "docs/sphinx/src/.static/js/svg-pan-zoom.min.js",
            "r",
            encoding="utf-8",
        ) as h:
            svg_pan_zoom_js = h.read()

        with open(
            "docs/sphinx/src/.static/js/custom.js",
            "r",
            encoding="utf-8",
        ) as h:
            custom_js = h.read()

        with open(filename + ".html", "w", encoding="utf-8") as h:
            h.write(
                HTML_EMBED_SVG.format(
                    svg_pan_zoom_js=svg_pan_zoom_js,
                    custom_js=custom_js,
                    svg_filename=Path(filename).name,
                )
            )

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
        if self.params.public.format == "gv":
            with open(self.params.public.file, "w", encoding="utf-8") as h:
                h.write(self.dag.source())
        else:
            self.dag.render()

            filename_format = f"{self.params.public.file}.{self.params.public.format}"
            if xdg_open:  # pragma: no cover
                subprocess.run(
                    f"xdg-open {filename_format}",
                    shell=True,
                    check=True,
                )

            if self.params.public.format == "svg" and self.params.public.html_embed_svg:
                self._embed_svg_in_html(filename_format)

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
                    if not_reachable and self.params.public.show_trees_standalone:
                        self._add_tree(sha, item, standalone=True)
                    elif to_include and self.params.public.show_trees:
                        self._add_tree(sha, item)
                case GitBlob():
                    if not_reachable and self.params.public.show_blobs_standalone:
                        self._add_blob(sha, standalone=True)
                    elif to_include and self.params.public.show_blobs:
                        self._add_blob(sha)
                case GitCommit():
                    self._add_commit(sha, item)

        # no point in displaying HEAD if branches are not displayed
        if self.params.public.show_local_branches:
            self._add_local_branches()
            if self.params.public.show_head:
                self._add_local_head()

        if self.params.public.show_remote_branches:
            self._add_remote_branches()
            if self.params.public.show_head:
                self._add_remote_heads()

        if self.params.public.show_tags:
            self._add_annotated_tags()
            self._add_lightweight_tags()

        if self.params.public.show_stash:
            self._add_stashes()

        self._add_prs_heads()
        self._add_annotations()

        self.dag.build(
            format=self.params.public.format,
            node_attr=self.params.dag_node.model_dump(),
            edge_attr=self.params.dag_edge.model_dump(),
            dag_attr=self.params.dag_global.model_dump(),
            filename=self.params.public.file,
            cluster_params=self.params.standalone_cluster.model_dump(),
        )
