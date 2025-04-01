"""Test ``git_commands.py``."""

# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest

from git_dag.git_commands import (
    GitCommandMutate,
    TestGitRepository,
    create_test_repo_and_reference_dot_file,
)


def test_cm(git_repository_empty: Path) -> None:
    git = GitCommandMutate(git_repository_empty)

    with pytest.raises(ValueError, match="Unsupported message type."):
        git.cm(set(["a", "b"]))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Cannot add files with multiple commits."):
        git.cm(["a", "b"], {"filename": "file content"})


def test_br(git_repository_empty: Path) -> None:
    git = GitCommandMutate(git_repository_empty)

    with pytest.raises(
        ValueError,
        match="At most one of create and delete can be True.",
    ):
        git.br("branch-name", create=True, delete=True)


def test_tag(git_repository_empty: Path) -> None:
    git = GitCommandMutate(git_repository_empty)

    with pytest.raises(
        ValueError,
        match="When delete is True, message should be None.",
    ):
        git.tag("tag-name", "some message", delete=True)


def test_create(tmp_path: Path) -> None:
    repo_path = tmp_path
    tar_file_name = repo_path / "tmp.tar.gz"

    with pytest.raises(
        ValueError,
        match="Unknown repository label: missing-repo-name",
    ):
        TestGitRepository.create(
            "missing-repo-name",  # type: ignore[arg-type]
            repo_path,
            tar_file_name=tar_file_name,
        )

    assert not tar_file_name.exists()

    TestGitRepository.create(
        "default",
        repo_path,
        tar_file_name=tar_file_name,
    )

    assert tar_file_name.exists()


def test_create_test_repo_and_reference_dot_file(tmp_path: Path) -> None:
    path = tmp_path
    create_test_repo_and_reference_dot_file(path / "default_repo")

    assert not (path / "default_repo").exists()
    assert (path / "default_repo.gv").exists()
    assert (path / "default_repo.repr").exists()


def test_run_general(tmp_path: Path) -> None:
    git = GitCommandMutate(tmp_path)

    git.run_general("crazy-command-run", expected_stderr="crazy-command-run")

    with pytest.raises(RuntimeError):
        git.run_general("crazy-command-run")

    with pytest.raises(RuntimeError):
        git.run_general("crazy-command-run", expected_stderr="not matchd")
