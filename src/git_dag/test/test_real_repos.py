"""Tests."""

# pylint: disable=missing-function-docstring,redefined-outer-name

from pathlib import Path

import pytest

from git_dag.git_repository import GitRepository

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize("repo_name", ["casadi", "git", "magit", "pydantic"])
def test_real_repository(repo_name: Path) -> None:
    BASE_DIR = TEST_DIR / ".." / ".." / ".."
    REPOS_DIR = BASE_DIR / "integration_tests" / "repos"
    OUT_DIR = BASE_DIR / "integration_tests" / "out"
    REFS_DIR = BASE_DIR / "integration_tests" / "references" / "references"

    repo_path = REPOS_DIR / repo_name
    if not repo_path.exists():
        pytest.skip(f"{repo_name} doesn't exist!")

    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    gv_file = OUT_DIR / f"{repo_name}.gv"
    GitRepository(repo_path, parse_trees=False).show(
        show_unreachable_commits=True,
        show_local_branches=True,
        show_remote_branches=True,
        show_trees=False,
        show_blobs=False,
        show_tags=True,
        show_deleted_tags=True,
        show_stash=True,
        show_head=True,
        format="gv",
        filename=gv_file,
    )

    with open(REFS_DIR / f"{repo_name}.gv", "r", encoding="utf-8") as h:
        reference_gv = h.read()

    with open(gv_file, "r", encoding="utf-8") as h:
        result_gv = h.read()

    assert result_gv == reference_gv
