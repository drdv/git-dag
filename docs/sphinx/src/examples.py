import shutil
import tempfile
from pathlib import Path

from git_dag import GitRepository
from git_dag.git_commands import GitCommandMutate

# TMP_DIR = tempfile.mkdtemp()
TMP_DIR = "/tmp/mitko"
shutil.rmtree(TMP_DIR, ignore_errors=True)

Path(TMP_DIR).mkdir()
SVG_DIR = Path(TMP_DIR) / "svg"
SVG_DIR.mkdir()

GIT = GitCommandMutate(TMP_DIR)

SHOW_ARGS = {
    "show_unreachable_commits": True,
    "show_local_branches": True,
    "show_remote_branches": True,
    "show_trees": True,
    "show_blobs_standalone": True,
    "show_blobs": True,
    "show_blobs_standalone": True,
    "show_tags": True,
    "show_deleted_tags": True,
    "show_stash": True,
    "show_head": True,
    "dag_attr": {"bgcolor": "transparent"},
}

print(f"Temporary directory created: {TMP_DIR}")


def step_create_empty():
    GIT.init()
    repo = GitRepository(TMP_DIR, parse_trees=True)
    repo.show(
        **SHOW_ARGS,
        filename=SVG_DIR / "00-empty.gv",
    )


def step_empty_repo_add_files_to_index():
    GIT.add({"README.md": "Test adding to index", "LICENSE": "Apache License"})
    repo = GitRepository(TMP_DIR, parse_trees=True)
    repo.show(
        **SHOW_ARGS,
        filename=SVG_DIR / "01-index-no-commits.gv",
    )


def step_first_commit():
    GIT.cm("Initial commit")
    repo = GitRepository(TMP_DIR, parse_trees=True)
    repo.show(
        **SHOW_ARGS,
        filename=SVG_DIR / "02-initial-commit.gv",
    )


def step_add_files_to_index_after_first_commit():
    GIT.add({"CHANGELOG": "Add CHANGELOG"})
    repo = GitRepository(TMP_DIR, parse_trees=True)
    repo.show(
        **SHOW_ARGS,
        filename=SVG_DIR / "03-index-after-first-commit.gv",
    )


if __name__ == "__main__":
    step_create_empty()
    step_empty_repo_add_files_to_index()
    step_first_commit()
    step_add_files_to_index_after_first_commit()
