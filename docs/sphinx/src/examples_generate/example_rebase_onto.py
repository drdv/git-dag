"""Example of using ``git rebase --onto``."""

# pylint: disable=missing-function-docstring,line-too-long,wrong-import-position,wrong-import-order

import inspect
import sys
from pathlib import Path
from textwrap import dedent
from typing import Optional

from git_dag.constants import COMMIT_DATE
from git_dag.git_commands import GitCommandMutate

sys.path.append(str(Path(__file__).parent))
from common_utils import StepResultsGenerator

EXAMPLE_NAME = "_".join(Path(__file__).stem.split("_")[1:])

SHOW_ARGS = ["-l", "-H", "-u"]

ELENA_CREDENTIALS = {"name": "Elena Coder", "mail": "elena.coder@mail.com"}
MARINA_CREDENTIALS = {"name": "Marina Coder", "mail": "marina.coder@mail.com"}


def repo_example1(show_args: Optional[list[str]] = None) -> None:
    # pylint: disable=possibly-used-before-assignment

    GIT.cm(list("AB"))
    GIT.br("feature", create=True)
    GIT.cm(list("CDE"))
    GIT.br("main")
    GIT.cm(list("FG"))
    GIT.br("feature")

    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
    )


def example1_rebase(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} rebase main feature",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase main feature
            """
        ),
    )


def example1_rebase_onto1(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} rebase --onto main~1 b5c0976 feature",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase --onto main~1 b5c0976 feature
            """
        ),
    )


def example1_rebase_onto2(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} rebase --onto main~1 f8ed6cd feature",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase --onto main~1 f8ed6cd feature
            """
        ),
    )


def example1_rebase_onto3(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} rebase --onto main~1 f8ed6cd feature~0",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase --onto main~1 f8ed6cd feature~0
            """
        ),
    )


def example1_move_feature_after_rebase_onto3(
    show_args: Optional[list[str]] = None,
) -> None:
    GIT.run_general(f"{GIT.command_prefix} branch -f feature HEAD", env=GIT.env)
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git branch -f feature HEAD
                # alternative: git update-ref -m "reflog MSG" refs/heads/feature HEAD
            """
        ),
    )


def example1_switch_feature(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} switch feature",
        env=GIT.env,
        expected_stderr="Switched to branch 'feature'",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git switch feature
            """
        ),
    )


def repo_example2(show_args: Optional[list[str]] = None) -> None:
    GIT.cm(["C1", "C2"])
    GIT.br("server", create=True)
    GIT.cm(["C3"], author_info=ELENA_CREDENTIALS)
    GIT.br("client", create=True)
    GIT.cm(["C8", "C9"], author_info=MARINA_CREDENTIALS)
    GIT.br("server")
    GIT.cm(["C4", "C10"], author_info=ELENA_CREDENTIALS)
    GIT.br("main")
    GIT.cm(["C5", "C6"])
    GIT.br("server")

    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
    )


def example2_rebase_server(show_args: Optional[list[str]] = None) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} rebase main",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase main  # note that we are on the server branch
            """
        ),
    )


def example2_rebase_client(show_args: Optional[list[str]] = None) -> None:
    GIT.br("client")
    GIT.run_general(
        f"{GIT.command_prefix} rebase --onto server 103ff1e client",
        env=GIT.env,
        expected_stderr="Successfully rebased and updated",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=SHOW_ARGS if show_args is None else show_args,
        commands=dedent(
            """
            .. code-block:: bash

                git rebase --onto server 103ff1e client
            """
        ),
    )


def start_new_repo(
    step_number: int = 1,
) -> tuple[StepResultsGenerator, GitCommandMutate]:
    srg = StepResultsGenerator(example_name=EXAMPLE_NAME, step_number=step_number)
    git = GitCommandMutate(srg.example_dir, date=COMMIT_DATE, evolving_date=True)
    git.init()

    return srg, git


if __name__ == "__main__":
    # ----------------------------------------------------------------------------------
    # Example 1
    # ----------------------------------------------------------------------------------
    SRG, GIT = start_new_repo()
    repo_example1(SHOW_ARGS + ["-R", "main..feature"])
    example1_rebase()

    SRG, GIT = start_new_repo(SRG.step_number)
    repo_example1(SHOW_ARGS + ["-R", "b5c0976..feature"])
    example1_rebase_onto1()

    SRG, GIT = start_new_repo(SRG.step_number)
    repo_example1(SHOW_ARGS + ["-R", "f8ed6cd..feature"])
    example1_rebase_onto2()

    SRG, GIT = start_new_repo(SRG.step_number)
    repo_example1(SHOW_ARGS + ["-R", "f8ed6cd..feature~0"])
    example1_rebase_onto3()
    example1_move_feature_after_rebase_onto3()
    example1_switch_feature()

    # ----------------------------------------------------------------------------------
    # Example 2
    # ----------------------------------------------------------------------------------

    SRG, GIT = start_new_repo(SRG.step_number)
    repo_example2()
    example2_rebase_server(SHOW_ARGS)
    example2_rebase_client(SHOW_ARGS)
