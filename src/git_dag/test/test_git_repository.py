"""Tests."""

# pylint: disable=missing-function-docstring

from pathlib import Path

import pytest

from git_dag.git_commands import GitCommandMutate
from git_dag.git_repository import GitRepository
from git_dag.pydantic_models import GitBlob, GitTag, GitTree


@pytest.fixture
def sample_repository(tmp_path: Path) -> Path:
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
    # git.stash({"file": "stash:0"})
    # git.stash({"file": "stash:1"})
    # git.stash({"file": "stash:2"})

    return repo_path


def test_git_repository(sample_repository: Path) -> None:
    gr = GitRepository(sample_repository, parse_trees=True)
    print(gr)

    assert {b.name for b in gr.branches} == {"main", "topic"}

    commits = gr.filter_objects().values()
    assert len([c for c in commits if c.is_reachable]) == 10
    assert len([c for c in commits if not c.is_reachable]) == 1

    tags = gr.filter_objects(GitTag).values()
    assert len([c for c in tags if not c.is_deleted]) == 3
    assert len([c for c in tags if c.is_deleted]) == 1

    trees = gr.filter_objects(GitTree).values()
    assert len(trees) == 3

    blobs = gr.filter_objects(GitBlob).values()
    assert len(blobs) == 2
