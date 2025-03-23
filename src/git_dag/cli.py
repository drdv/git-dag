#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Comman-line interface."""
import argparse
import logging
from typing import Optional

import argcomplete

from .constants import DagBackends
from .git_repository import GitRepository


class CustomArgparseNamespace(argparse.Namespace):
    """Type hints for argparse arguments.

    Note
    -----
    The argparse type parameter is a function that converts a string to something, and
    raises an error if it can't. It does not add typehints information.
    https://stackoverflow.com/q/56441342

    """

    path: str
    file: str
    format: str
    init_refs: Optional[list[str]]
    max_numb_commits: int
    dag_backend: str

    dpi: str
    rankdir: str
    bgcolor: str

    html_embed_svg: bool

    show_unreachable_commits: bool
    show_tags: bool
    show_deleted_tags: bool
    show_local_branches: bool
    show_remote_branches: bool
    show_stash: bool
    show_trees: bool
    show_blobs: bool
    show_head: bool
    show_prs_heads: bool
    range: Optional[list[str]]
    commit_message_as_label: int
    xdg_open: bool
    log_level: str


def get_cla_parser() -> argparse.ArgumentParser:
    """Define CLA parser."""

    def max_numb_commits_type(value_str: str) -> Optional[int]:
        """Handle the type returned by the -n flag."""
        value = int(value_str)
        if value < 1:
            return None
        return value

    parser = argparse.ArgumentParser(description="Visualize the git DAG.")

    parser.add_argument(
        "-p",
        "--path",
        default=".",
        help="Path to a git repository.",
    )

    parser.add_argument(
        "-f",
        "--file",
        default="git-dag.gv",
        help="Output graphviz file (e.g., `/path/to/file`).",
    )

    parser.add_argument(
        "-b",
        "--dag-backend",
        default="graphviz",
        choices=["graphviz"],
        help="Backend DAG library.",
    )

    parser.add_argument(
        "--format",
        default="svg",
        help=(
            "Graphviz output format (tooltips are available only with svg). "
            "If the format is set to `gv`, only the graphviz source file is generated."
        ),
    )

    parser.add_argument(
        "--dpi",
        help="DPI of output figure (used with `--format png`).",
    )

    parser.add_argument(
        "-i",
        "--init-refs",
        nargs="+",
        help=(
            "A list of branches, tags, git objects (commits, trees, blobs) that "
            "represents a limitation from where to display the DAG."
        ),
    )

    parser.add_argument(
        "-R",
        "--range",
        nargs="+",
        help="A list to commits in a range to display.",
    )

    parser.add_argument(
        "-n",
        "--max-numb-commits",
        type=max_numb_commits_type,
        default=1000,  # default protection
        help=(
            "Max number of commits to display. If set to 0 and the -i flag is not "
            "specified, no limitations are considered whatsoever. If set to n > 0, "
            "only n commits reachable from the initial references are displayed (in "
            "the absence of user-defined initial references, the output of "
            "`git rev-list --all --objects --no-object-names` is used (note that it "
            "might not include some unreachable commits."
        ),
    )

    parser.add_argument(
        "--rankdir",
        default="TB",
        choices=["LR", "RL", "TB", "BT"],
        help="rankdir argument of graphviz.",
    )

    parser.add_argument(
        "--bgcolor",
        default="transparent",
        help="bgcolor argument of graphviz (e.g., gray42).",
    )

    parser.add_argument(
        "-u",
        dest="show_unreachable_commits",
        action="store_true",
        help="Show unreachable commits.",
    )

    parser.add_argument(
        "-t",
        dest="show_tags",
        action="store_true",
        help="Show tags.",
    )

    parser.add_argument(
        "-D",
        dest="show_deleted_tags",
        action="store_true",
        help="Show deleted annotated tags.",
    )

    parser.add_argument(
        "-l",
        dest="show_local_branches",
        action="store_true",
        help="Show local branches.",
    )

    parser.add_argument(
        "-r",
        dest="show_remote_branches",
        action="store_true",
        help="Show remote branches.",
    )

    parser.add_argument(
        "-s",
        dest="show_stash",
        action="store_true",
        help="Show stash.",
    )

    parser.add_argument(
        "-H",
        dest="show_head",
        action="store_true",
        help="Show head (has effect only when -l or -r are set as well).",
    )

    parser.add_argument(
        "--prs-heads",
        dest="show_prs_heads",
        action="store_true",
        help=(
            "Show pull-requests heads "
            "(most of the time this requires passing -u as well)."
        ),
    )

    parser.add_argument(
        "-T",
        dest="show_trees",
        action="store_true",
        help="Show trees (WARNING: should be used only with small repositories).",
    )

    parser.add_argument(
        "--trees-standalone",
        dest="show_trees_standalone",
        action="store_true",
        help=(
            "Show trees that don't have parent commits reachable from "
            "a branch a tag or the reflog."
        ),
    )

    parser.add_argument(
        "-B",
        dest="show_blobs",
        action="store_true",
        help="Show blobs (discarded if -T is not set).",
    )

    parser.add_argument(
        "--blobs-standalone",
        dest="show_blobs_standalone",
        action="store_true",
        help=(
            "Show blobs that don't have parent commits reachable from "
            "a branch a tag or the reflog."
        ),
    )

    parser.add_argument(
        "-m",
        "--message",
        type=int,
        default=0,
        dest="commit_message_as_label",
        help=(
            "When greater than 0, this is the number of characters from the commit "
            "message to use as a commit label. The commit SHA is used otherwise."
        ),
    )

    parser.add_argument(
        "-o",
        "--xdg-open",
        action="store_true",
        help="Open output file with xdg-open.",
    )

    parser.add_argument(
        "--html",
        dest="html_embed_svg",
        action="store_true",
        help=(
            "Generate a standalone HTML file that embeds the generated SVG. "
            "Hass effect only when --format is svg."
        ),
    )

    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["NOTSET", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level.",
    )

    return parser


def get_cla(raw_args: Optional[list[str]] = None) -> CustomArgparseNamespace:
    """Parse command-line arguments."""
    parser = get_cla_parser()

    argcomplete.autocomplete(parser)
    return parser.parse_args(raw_args, namespace=CustomArgparseNamespace())


def main(raw_args: Optional[list[str]] = None) -> None:
    """CLI entry poit."""
    args = get_cla(raw_args)
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    GitRepository(
        args.path,
        parse_trees=args.show_trees,
        ls_remote=args.show_prs_heads,
    ).show(
        dag_backend=DagBackends[args.dag_backend.upper()],
        xdg_open=args.xdg_open,
        format=args.format,
        html_embed_svg=args.html_embed_svg,
        show_unreachable_commits=args.show_unreachable_commits,
        show_tags=args.show_tags,
        show_deleted_tags=args.show_deleted_tags,
        show_local_branches=args.show_local_branches,
        show_remote_branches=args.show_remote_branches,
        show_trees=args.show_trees,
        show_trees_standalone=args.show_trees_standalone,
        show_blobs=args.show_blobs,
        show_blobs_standalone=args.show_blobs_standalone,
        show_stash=args.show_stash,
        show_head=args.show_head,
        show_prs_heads=args.show_prs_heads,
        range=args.range,
        commit_message_as_label=args.commit_message_as_label,
        init_refs=args.init_refs,
        filename=args.file,
        dag_attr={
            "rankdir": args.rankdir,
            "dpi": args.dpi,
            "bgcolor": args.bgcolor,
        },
        max_numb_commits=args.max_numb_commits,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
