"""Test ``cli.py``."""

# pylint: disable=missing-function-docstring

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from git_dag.cli import get_user_defined_cla, main
from git_dag.constants import CONFIG_FILE
from git_dag.parameters import ParamsPublic


def test_cli_main(git_repository_default: Path) -> None:
    repo_path = git_repository_default

    out_filename = "out.gv"
    _p = ("-p", str(repo_path))
    _i = ("-i", "main")
    _m = ("-m", "1")
    _f = ("-f", f"{repo_path / out_filename}")
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
            "--html",
            "--config-ignore",
            *_f,
            *_p,
            *_i,
            *_m,
            *_f,
            *_log_level,
        ]
    )

    assert (repo_path / out_filename).exists()
    assert (repo_path / f"{out_filename}.svg").exists()
    assert (repo_path / f"{out_filename}.svg.html").exists()


def test_cli_main_config_create(tmp_path: Path) -> None:
    config_file = tmp_path / CONFIG_FILE.name

    with patch("git_dag.parameters.CONFIG_FILE", config_file):
        main(["--config-create"])

    assert config_file.exists()


@pytest.mark.parametrize(
    "arg,field,value",
    [
        ("--init-refs", "init_refs", ["main", "topic"]),
        ("-R", "range_expr", "main..topic"),
        ("-p", "path", "/some/path"),
        ("-f", "file", "/some/path/git-dag.gv"),
        ("--format", "format", "png"),
        ("-n", "max_numb_commits", 10),
        ("-m", "commit_message_as_label", 1),
        ("--log-level", "log_level", "INFO"),
        # flags have value None
        ("-u", "show_unreachable_commits", None),
        ("-t", "show_tags", None),
        ("-D", "show_deleted_tags", None),
        ("-s", "show_stash", None),
        ("-H", "show_head", None),
        ("--pr", "show_prs_heads", None),
        ("-T", "show_trees", None),
        ("--trees-standalone", "show_trees_standalone", None),
        ("-B", "show_blobs", None),
        ("--blobs-standalone", "show_blobs_standalone", None),
        ("-o", "xdg_open", None),
        ("-l", "show_local_branches", None),
        ("-r", "show_remote_branches", None),
        ("--html", "html_embed_svg", None),
    ],
)
def test_cli_args(arg: str, field: str, value: Any) -> None:
    if value is None:
        arg_and_value = [arg]  # arg is a flag
    elif isinstance(value, list):
        arg_and_value = [arg] + value  # if value is a list it is a list of string
    else:
        arg_and_value = [arg, str(value)]

    # we need to pass [] to get_cla because of the way pytest sets sys.argv
    default_params = ParamsPublic(**get_user_defined_cla([])).model_dump()
    params_dict = ParamsPublic(**get_user_defined_cla(arg_and_value)).model_dump()

    assert params_dict[field] == (True if value is None else value)
    for default_field, default_value in default_params.items():
        if default_field != field:
            assert params_dict[default_field] == default_value
