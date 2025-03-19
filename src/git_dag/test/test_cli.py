"""Test ``cli.py``."""

# pylint: disable=missing-function-docstring,redefined-outer-name

from pathlib import Path
from typing import Any

import pytest

from git_dag.cli import get_cla, main

ALL_ARGS = {
    "-p": ("path", "."),
    "-f": ("file", "git-dag.gv"),
    "-b": ("dag_backend", "graphviz"),
    "--format": ("format", "svg"),
    "--dpi": ("dpi", None),
    "--init-refs": ("init_refs", None),
    "-R": ("range", None),
    "-n": ("max_numb_commits", 1000),
    "--rankdir": ("rankdir", "TB"),
    "--bgcolor": ("bgcolor", "transparent"),
    "-u": ("show_unreachable_commits", False),
    "-t": ("show_tags", False),
    "-D": ("show_deleted_tags", False),
    "-l": ("show_local_branches", False),
    "-r": ("show_remote_branches", False),
    "-s": ("show_stash", False),
    "-H": ("show_head", False),
    "-T": ("show_trees", False),
    "-B": ("show_blobs", False),
    "-m": ("commit_message_as_label", 0),
    "-o": ("xdg_open", False),
    "--log-level": ("log_level", "WARNING"),
}


def test_cli_main(git_repository_default: Path) -> None:
    repo_path = git_repository_default

    _p = ("-p", str(repo_path))
    _i = ("-i", "main")
    _m = ("-m", "1")
    _b = ("-b", "graphviz")
    _n = ("-n", "1000")
    _f = ("-f", f'{repo_path / "out.gv"}')
    _format = ("--format", "svg")
    _rankdir = ("--rankdir", "LR")
    _bgcolor = ("--bgcolor", "transparent")
    _log_level = ("--log-level", "INFO")

    main(
        [
            "-l",
            "-r",
            "-s",
            "-t",
            "-T",
            "-B",
            "-D",
            "-H",
            "-u",
            *_f,
            *_p,
            *_i,
            *_m,
            *_b,
            *_n,
            *_f,
            *_format,
            *_rankdir,
            *_bgcolor,
            *_log_level,
        ]
    )

    assert (repo_path / "out.gv").exists()
    assert (repo_path / "out.gv.svg").exists()


@pytest.mark.parametrize(
    "arg,value",
    [
        ("--init-refs", "main topic"),
        ("-R", "main topic"),
        ("-p", "/some/path"),
        ("-f", "/some/path/git-dag.gv"),
        ("--format", "png"),
        ("--dpi", "150"),
        ("-n", 10),
        ("--rankdir", "LR"),
        ("--bgcolor", "red"),
        ("-u", True),
        ("-t", True),
        ("-D", True),
        ("-s", True),
        ("-H", True),
        ("-T", True),
        ("-B", True),
        ("-m", 1),
        ("-o", True),
        ("-l", True),
        ("-r", True),
        ("--log-level", "INFO"),
    ],
)
def test_cli_args(arg: str, value: Any) -> None:
    parsed_args = get_cla(
        [arg] if isinstance(value, bool) and value else [arg, str(value)]
    )

    field = ALL_ARGS[arg][0]
    result = getattr(parsed_args, field)

    if arg in ["--init-refs", "-R"]:
        value = [value]

    assert result == value

    for arg_default, (field, value_default) in ALL_ARGS.items():
        if arg_default != arg:
            assert getattr(parsed_args, field) == value_default
