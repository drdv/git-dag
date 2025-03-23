"""Pytest fixtures."""

# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest

from git_dag.git_commands import TestGitRepository


@pytest.fixture
def git_repository_empty(tmp_path: Path) -> Path:
    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()

    TestGitRepository.create("empty", repo_path)
    return repo_path


@pytest.fixture
def git_repository_empty_with_index(tmp_path: Path) -> Path:
    repo_path = tmp_path / "empty_repo_with_index"
    repo_path.mkdir()

    TestGitRepository.create("empty", repo_path, files={"tmp_file": "1"})
    return repo_path


@pytest.fixture
def git_repository_default(tmp_path: Path) -> Path:
    repo_path = tmp_path / "default_repo"
    repo_path.mkdir()

    TestGitRepository.create("default", repo_path)
    return repo_path


@pytest.fixture
def git_repository_default_with_notes(tmp_path: Path) -> Path:
    repo_path = tmp_path / "default_repo_with_notes"
    repo_path.mkdir()

    TestGitRepository.create("default-with-notes", repo_path)
    return repo_path
