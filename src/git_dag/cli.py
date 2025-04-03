#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Comman-line interface."""
import argparse
import logging
from typing import Any, Optional

import argcomplete

from git_dag.constants import CONFIG_FILE
from git_dag.git_repository import GitRepository
from git_dag.parameters import Params, ParamsPublic, context_ignore_config_file


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
    log_level: str

    html_embed_svg: bool
    show_unreachable_commits: bool
    show_tags: bool
    show_deleted_tags: bool
    show_local_branches: bool
    show_remote_branches: bool
    show_stash: bool
    show_trees: bool
    show_trees_standalone: bool
    show_blobs: bool
    show_blobs_standalone: bool
    show_head: bool
    show_prs_heads: bool
    range: Optional[str]
    commit_message_as_label: int
    xdg_open: bool


def get_cla_parser() -> argparse.ArgumentParser:
    """Define CLA parser.

    Note
    -----
    The default value of all flags (``action="store_true"``) is set to ``None`` because
    it is used when default values for parameters are being set (see ``parameters.py``).

    """
    parser = argparse.ArgumentParser(description="Visualize the git DAG.")

    parser.add_argument(
        "--config-create",
        action="store_true",
        default=None,
        help=f"Create config {CONFIG_FILE} and exit.",
    )

    parser.add_argument(
        "--config-ignore",
        action="store_true",
        default=None,
        help=f"Ignore the {CONFIG_FILE} config.",
    )

    parser.add_argument(
        "-p",
        "--path",
        help="Path to a git repository.",
    )

    parser.add_argument(
        "-f",
        "--file",
        help="Output graphviz file (e.g., `/path/to/file`).",
    )

    parser.add_argument(
        "-b",
        "--dag-backend",
        choices=["graphviz"],
        help="Backend DAG library.",
    )

    parser.add_argument(
        "--format",
        help=(
            "Graphviz output format (tooltips are available only with svg). "
            "If the format is set to `gv`, only the graphviz source file is generated."
        ),
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
        dest="range_expr",
        help="A range expression (e.g, main..feature).",
    )

    parser.add_argument(
        "-n",
        "--max-numb-commits",
        type=int,
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
        "-u",
        dest="show_unreachable_commits",
        action="store_true",
        default=None,
        help="Show unreachable commits.",
    )

    parser.add_argument(
        "-t",
        dest="show_tags",
        action="store_true",
        default=None,
        help="Show tags.",
    )

    parser.add_argument(
        "-D",
        dest="show_deleted_tags",
        action="store_true",
        default=None,
        help="Show deleted annotated tags.",
    )

    parser.add_argument(
        "-l",
        dest="show_local_branches",
        action="store_true",
        default=None,
        help="Show local branches.",
    )

    parser.add_argument(
        "-r",
        dest="show_remote_branches",
        action="store_true",
        default=None,
        help="Show remote branches.",
    )

    parser.add_argument(
        "-s",
        dest="show_stash",
        action="store_true",
        default=None,
        help="Show stash.",
    )

    parser.add_argument(
        "-H",
        dest="show_head",
        action="store_true",
        default=None,
        help="Show head (has effect only when -l or -r are set as well).",
    )

    parser.add_argument(
        "-a",
        dest="annotations",
        action="append",
        nargs="+",
        default=None,
        help=(
            "Annotations of refs (can be passed multiple times). The first argument "
            "after each -a should be a ref. Subsequent arguments (if any) are joined "
            "and placed in the tooltip of the corresponding node."
        ),
    )

    parser.add_argument(
        "--pr",
        dest="show_prs_heads",
        action="store_true",
        default=None,
        help=(
            "Show pull-requests heads "
            "(most of the time this requires passing -u as well)."
        ),
    )

    parser.add_argument(
        "-T",
        dest="show_trees",
        action="store_true",
        default=None,
        help="Show trees (WARNING: should be used only with small repositories).",
    )

    parser.add_argument(
        "--trees-standalone",
        dest="show_trees_standalone",
        action="store_true",
        default=None,
        help=(
            "Show trees that don't have parent commits reachable from "
            "a branch a tag or the reflog."
        ),
    )

    parser.add_argument(
        "-B",
        dest="show_blobs",
        action="store_true",
        default=None,
        help="Show blobs (discarded if -T is not set).",
    )

    parser.add_argument(
        "--blobs-standalone",
        dest="show_blobs_standalone",
        action="store_true",
        default=None,
        help=(
            "Show blobs that don't have parent commits reachable from "
            "a branch a tag or the reflog."
        ),
    )

    parser.add_argument(
        "-m",
        "--message",
        type=int,
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
        default=None,
        help="Open output file with xdg-open.",
    )

    parser.add_argument(
        "--html",
        dest="html_embed_svg",
        action="store_true",
        default=None,
        help=(
            "Create a standalone HTML file that embeds the generated SVG. "
            "Hass effect only when --format is svg."
        ),
    )

    parser.add_argument(
        "--log-level",
        choices=["NOTSET", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level.",
    )

    return parser


def get_user_defined_cla(
    raw_args: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Parse command-line arguments."""
    parser = get_cla_parser()

    argcomplete.autocomplete(parser)
    args = parser.parse_args(raw_args, namespace=CustomArgparseNamespace())
    return {key: value for key, value in vars(args).items() if value is not None}


def main(raw_args: Optional[list[str]] = None) -> None:
    """CLI entry poit."""
    user_defined_cla = get_user_defined_cla(raw_args)

    # config_ignore and config_create are not stored as parameters
    config_ignore = user_defined_cla.pop("config_ignore", False)
    config_create = user_defined_cla.pop("config_create", False)

    if config_ignore:
        with context_ignore_config_file():
            params = Params(public=ParamsPublic(**user_defined_cla))
    else:
        params = Params(public=ParamsPublic(**user_defined_cla))

    if config_create:
        params.create_config()
        return None

    logging.getLogger().setLevel(getattr(logging, params.public.log_level))
    GitRepository(
        params.public.path,
        parse_trees=params.public.show_trees,
    ).show(params)

    return None


if __name__ == "__main__":  # pragma: no cover
    main()
