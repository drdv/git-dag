"""Tests."""

# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest

from git_dag.exceptions import EmptyGitRepository
from git_dag.git_commands import GitCommandMutate
from git_dag.git_repository import GitRepository
from git_dag.pydantic_models import GitBlob, GitTag, GitTree


@pytest.fixture
def repository_empty(tmp_path: Path) -> Path:
    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()

    git = GitCommandMutate(repo_path)
    git.init()

    return repo_path


@pytest.fixture
def repository_default(tmp_path: Path) -> Path:
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    git = GitCommandMutate(repo_path)
    git.init()
    git.cm("A\n\nBody:\n * First line\n * Second line\n * Third line")
    git.br("topic", create=True)
    git.cm("D")
    git.br("feature", create=True)
    git.cm("F")
    git.cm("G", files={"file": "G"})
    git.br("topic")
    git.cm("E", files={"file": "E"})
    git.mg("feature")
    git.tag("0.1", "Summary\n\nBody:\n * First line\n * Second line\n * Third line")
    git.tag("0.2", "Summary\n\nBody:\n * First line\n * Second line\n * Third line")
    git.cm("H")
    git.br("main")
    git.cm(["B", "C"])
    git.br("feature", delete=True)
    git.br("topic")
    git.tag("0.3", "T1")
    git.tag("0.4")
    git.tag("0.5")
    git.tag("0.1", delete=True)
    git.tag("0.4", delete=True)
    git.br("bugfix", create=True)
    git.cm("I")
    git.tag("0.6", "Test:                    €.")
    git.cm("J")
    git.br("topic")
    git.br("bugfix", delete=True)
    git.stash({"file": "stash:first"})
    git.stash({"file": "stash:second"}, title="second")
    git.stash({"file": "stash:third"}, title="third")

    return repo_path


def test_repository_empty(repository_empty: Path) -> None:
    with pytest.raises(EmptyGitRepository):
        GitRepository(repository_empty)


def test_repository(repository_default: Path) -> None:
    repo = GitRepository(repository_default, parse_trees=True)
    print(repo)

    commits = repo.filter_objects().values()
    assert len([c for c in commits if c.is_reachable]) == 12
    assert len([c for c in commits if not c.is_reachable]) == 3

    tags = repo.tags.values()
    assert len([c for c in tags if not c.is_deleted]) == 3
    assert len([c for c in tags if c.is_deleted]) == 1

    assert len(repo.tags_lw) == 1
    repo.tags_lw["0.5"].name = "0.5"

    assert len(repo.filter_objects(GitTree).values()) == 6
    assert len(repo.filter_objects(GitBlob).values()) == 5

    stashes = repo.stashes
    assert len(stashes) == 3
    assert stashes[0].index == 0
    assert stashes[0].title == "On topic: third"
    assert stashes[0].commit.is_reachable
    assert not stashes[1].commit.is_reachable
    assert not stashes[2].commit.is_reachable

    assert {b.name for b in repo.branches} == {"main", "topic"}
    assert not repo.inspector.git.is_detached_head()
