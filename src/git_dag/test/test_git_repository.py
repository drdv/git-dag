"""Test git_repository.py."""

# pylint: disable=missing-function-docstring

import logging
from pathlib import Path

import pytest

from git_dag.constants import GIT_EMPTY_TREE_OBJECT_SHA
from git_dag.exceptions import CalledProcessCustomError
from git_dag.git_commands import GitCommandMutate
from git_dag.git_objects import GitBlob, GitTree
from git_dag.git_repository import GitRepository
from git_dag.parameters import Params, ParamsPublic, context_ignore_config_file

TEST_DIR = Path(__file__).parent


def test_missing_path(tmp_path: Path) -> None:
    repo_path = tmp_path / "missing"
    with pytest.raises(
        RuntimeError,
        match=f"Path {repo_path} doesn't exist.",
    ):
        GitRepository(repo_path)


def test_not_a_git_repository(tmp_path: Path) -> None:
    repo_path = tmp_path
    with pytest.raises(
        CalledProcessCustomError,
        match="not a git repository",
    ):
        GitRepository(repo_path)


def test_repository_empty(
    git_repository_empty: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    repo_path = git_repository_empty
    with caplog.at_level(logging.WARNING):
        repo = GitRepository(repo_path)

    assert not repo.head.is_defined

    assert "No objects" in caplog.text
    assert "No Head" in caplog.text
    assert "No refs" in caplog.text

    with context_ignore_config_file():
        params = Params(
            public=ParamsPublic(
                show_trees_standalone=True,
                show_blobs_standalone=True,
                format="gv",
                file=repo_path / "empty_repo_cluster.gv",
            )
        )

    repo.show(params)
    with open(TEST_DIR / "resources/empty_repo_cluster.gv", "r", encoding="utf-8") as h:
        reference_gv = h.read()

    with open(repo_path / "empty_repo_cluster.gv", "r", encoding="utf-8") as h:
        result_gv = h.read()

    assert result_gv == reference_gv


def test_repository_empty_with_index(
    git_repository_empty_with_index: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        GitRepository(git_repository_empty_with_index)

    assert "No objects" not in caplog.text
    assert "No Head" in caplog.text
    assert "No refs" in caplog.text


def test_repository_clone_depth_1(git_repository_default: Path) -> None:
    src_repo = str(git_repository_default)
    target_repo = src_repo + "_cloned"
    GitCommandMutate.clone_local_depth_1(src_repo, target_repo)

    repo = GitRepository(target_repo, parse_trees=True)

    commits = repo.commits.values()
    assert len([c for c in commits if c.is_reachable]) == 1
    assert len([c for c in commits if not c.is_reachable]) == 0

    tags = repo.tags.values()
    assert len([c for c in tags if not c.is_deleted]) == 1

    assert len(repo.tags_lw) == 1

    assert len(repo.filter_objects(GitTree).values()) == 1
    assert len(repo.filter_objects(GitBlob).values()) == 1

    assert {b.name for b in repo.branches} == {"origin/topic", "topic"}
    assert not repo.head.is_detached


def test_repository_default(git_repository_default: Path) -> None:
    repo = GitRepository(git_repository_default, parse_trees=True)

    for obj in repo.objects.values():
        assert obj.is_ready

    commits = repo.commits.values()
    assert len([c for c in commits if c.is_reachable]) == 12
    # in reality there should be 5 unreachable commits but all three stashes share the
    # same index commit because the commit date is fixed in GitCommandMutate
    assert len([c for c in commits if not c.is_reachable]) == 3

    tags = repo.tags.values()
    assert len([c for c in tags if not c.is_deleted]) == 6
    assert len([c for c in tags if c.is_deleted]) == 1

    assert len(repo.tags_lw) == 1
    repo.tags_lw["0.5"].name = "0.5"

    standalone_trees, standalone_blobs = 1, 2
    assert len(repo.filter_objects(GitTree)) == 6 + standalone_trees
    assert len(repo.filter_objects(GitBlob)) == 5 + standalone_blobs

    stashes = repo.stashes
    assert len(stashes) == 3
    assert stashes[0].index == 0
    assert stashes[0].title == "On topic: third"
    assert stashes[0].commit.is_reachable
    assert not stashes[1].commit.is_reachable
    assert not stashes[2].commit.is_reachable

    assert {b.name for b in repo.branches} == {"main", "topic"}
    assert not repo.head.is_detached


def test_repository_default_with_notes(git_repository_default_with_notes: Path) -> None:
    """
    Maybe this test should be split. It tests three things:
    1. that git notes label is added
    2. setting max_numb_commits to 0
    3. setting commit_message_as_label to 1
    """
    repo_path = git_repository_default_with_notes
    repo = GitRepository(repo_path, parse_trees=True)

    for obj in repo.objects.values():
        assert obj.is_ready

    # two notes were added
    notes_commits = notes_trees = notes_blobs = 2
    standalone_trees, standalone_blobs = 1, 2

    commits = repo.commits.values()
    assert len([c for c in commits if c.is_reachable]) == 12 + notes_commits
    assert len([c for c in commits if not c.is_reachable]) == 3
    assert len(repo.filter_objects(GitTree)) == 6 + standalone_trees + notes_trees
    assert len(repo.filter_objects(GitBlob)) == 5 + standalone_blobs + notes_blobs

    file = repo_path / "default_repo_with_notes.gv"
    params = Params(
        public=ParamsPublic(
            max_numb_commits=0,
            commit_message_as_label=1,
            format="gv",
            file=file,
        )
    )

    repo.show(params)
    with open(file, "r", encoding="utf-8") as h:
        result_gv = h.read()

    assert (
        '"GIT-NOTES-LABEL" [label="git notes" fillcolor=white shape=egg '
        'tooltip="refs/notes/commits"]'
    ) in result_gv
    for name in list("ABCDEFGHINmO"):
        assert f"label={name}" in result_gv


def test_unknown_dag_backend(git_repository_default: Path) -> None:
    repo_path = git_repository_default
    repo = GitRepository(repo_path, parse_trees=False)

    params = Params(
        public=ParamsPublic(
            dag_backend="unknown-backend",
            format="gv",
            file=repo_path / "tmp.gv",
        )
    )

    with pytest.raises(KeyError):
        repo.show(params)


def test_repository_default_dag(git_repository_default: Path) -> None:
    # pylint: disable=duplicate-code

    repo_path = git_repository_default
    repo = GitRepository(repo_path, parse_trees=True)
    with context_ignore_config_file():
        params = Params(
            public=ParamsPublic(
                show_unreachable_commits=True,
                show_local_branches=True,
                show_remote_branches=True,
                show_trees=True,
                show_trees_standalone=True,
                show_blobs=True,
                show_blobs_standalone=True,
                show_tags=True,
                show_deleted_tags=True,
                show_stash=True,
                show_head=True,
                max_numb_commits=0,
                annotations=[
                    ["4499ee63", "just a tooltip"],
                    ["0.3", "additional info"],
                    ["0.5"],  # this will not be displayed
                    ["HEAD"],
                    ["main^", "a clarification"],
                ],
                format="gv",
                file=repo_path / "default_repo.gv",
            )
        )

    repo.show(params)

    with open(TEST_DIR / "resources/default_repo.gv", "r", encoding="utf-8") as h:
        reference_gv = h.read()

    with open(repo_path / "default_repo.gv", "r", encoding="utf-8") as h:
        result_gv = h.read()

    assert result_gv == reference_gv

    with open(TEST_DIR / "resources/default_repo.repr", "r", encoding="utf-8") as h:
        reference_repr = h.read()

    result_repr = repr(repo).replace(str(repo_path), "test/resources/default_repo")
    assert result_repr == reference_repr


def test_repository_default_dag_svg(git_repository_default: Path) -> None:
    repo_path = git_repository_default
    repo = GitRepository(repo_path, parse_trees=True)
    repo.show(
        Params(
            public=ParamsPublic(
                file=repo_path / "default_repo.gv",
            )
        )
    )
    assert (repo_path / "default_repo.gv.svg").is_file()


def test_gittree_children() -> None:
    tree = GitTree(sha=GIT_EMPTY_TREE_OBJECT_SHA, raw_data=[], no_children=True)
    with pytest.raises(
        TypeError,
        match="Attempting to set children when there should be none.",
    ):
        tree.children = [GitBlob(sha="2086abdf88ac520682ae9cbacc913bfa3f1eb541")]
