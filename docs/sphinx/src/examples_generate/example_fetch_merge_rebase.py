"""Example of fetch with merge or rebase."""

# pylint: disable=missing-function-docstring,line-too-long,wrong-import-position,wrong-import-order

import inspect
import sys
from pathlib import Path
from typing import Any

from git_dag.constants import COMMIT_DATE
from git_dag.git_commands import GitCommandMutate

sys.path.append(str(Path(__file__).parent))
from common_utils import StepResultsGenerator

EXAMPLE_NAME = "_".join(Path(__file__).stem.split("_")[1:])

ELENA_CREDENTIALS = "Elena Coder <elena.coder@mail.com>"
MARINA_CREDENTIALS = "Marina Coder <marina.coder@mail.com>"

SERVER_DIR = "server"
ELENA_DIR = "elena"
MARINA_DIR = "marina"
SHOW_ARGS = ["-m", "1", "-l", "-r", "-H", "-u"]


def bare_repo_and_two_clones() -> dict[str, Any]:
    repo_server_path = SRG.example_dir / SERVER_DIR
    repo_elena_path = SRG.example_dir / ELENA_DIR
    repo_marina_path = SRG.example_dir / MARINA_DIR

    repo_server_path.mkdir(parents=True)
    repo_elena_path.mkdir(parents=True)
    repo_marina_path.mkdir(parents=True)

    GitCommandMutate(repo_server_path).init(bare=True)

    git_elena = GitCommandMutate(
        repo_elena_path,
        author=ELENA_CREDENTIALS,
        committer=ELENA_CREDENTIALS,
        date=COMMIT_DATE,
        evolving_date=True,
    )
    git_elena.clone_from_local(repo_server_path, repo_elena_path)

    git_elena.init_remote_head()
    git_elena.cm(["A", "B", "C"])
    git_elena.push()

    git_marina = GitCommandMutate(
        repo_marina_path,
        author=MARINA_CREDENTIALS,
        committer=MARINA_CREDENTIALS,
        date=git_elena.date,
        evolving_date=True,
    )
    git_marina.clone_from_local(repo_server_path, repo_marina_path)
    git_marina.pull()
    git_marina.cm(["D", "E"])
    git_marina.push()

    git_elena.cm(["F", "G"])
    git_elena.fetch()

    return {
        "example_path": SRG.example_dir,
        "repo_server_path": repo_server_path,
        "repo_elena_path": repo_elena_path,
        "repo_marina_path": repo_marina_path,
        "git_elena": git_elena,
        "git_marina": git_marina,
    }


def start_new_repo(step_number: int = 1) -> StepResultsGenerator:
    return StepResultsGenerator(example_name=EXAMPLE_NAME, step_number=step_number)


def example_initial_state() -> None:
    args = bare_repo_and_two_clones()

    SRG.results(
        inspect.stack()[0][3] + "-marina",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_marina_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-server",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_server_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-elena",
        show_args=SHOW_ARGS + ["-R", "..@{u}"],
        repo_dir=args["repo_elena_path"],
    )


def example_merge() -> None:
    args = bare_repo_and_two_clones()

    args["git_elena"].mg("origin/main")
    args["git_elena"].push()
    args["git_marina"].pull()

    SRG.results(
        inspect.stack()[0][3] + "-marina",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_marina_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-server",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_server_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-elena",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_elena_path"],
    )


def example_rebase() -> None:
    args = bare_repo_and_two_clones()

    args["git_elena"].rebase("origin/main")
    args["git_elena"].push()
    args["git_marina"].pull()

    SRG.results(
        inspect.stack()[0][3] + "-marina",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_marina_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-server",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_server_path"],
    )

    SRG.results(
        inspect.stack()[0][3] + "-elena",
        show_args=SHOW_ARGS,
        repo_dir=args["repo_elena_path"],
    )


SRG = start_new_repo()
example_initial_state()

SRG = start_new_repo(SRG.step_number)
example_merge()

SRG = start_new_repo(SRG.step_number)
example_rebase()
