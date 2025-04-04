"""Example of revisions and ranges.

Note
-----
See https://git-scm.com/docs/gitrevisions.

"""

# pylint: disable=missing-function-docstring,line-too-long,wrong-import-position,wrong-import-order

import inspect
import sys
from pathlib import Path

from git_dag.git_commands import GitCommandMutate

sys.path.append(str(Path(__file__).parent))
from common_utils import StepResultsGenerator

EXAMPLE_NAME = "_".join(Path(__file__).stem.split("_")[1:])


def repo_jon_loeliger(git: GitCommandMutate) -> None:
    """Example from https://git-scm.com/docs/gitrevisions."""
    git.init()

    for name in ["G", "H", "I", "J", "E"]:
        git.br(name, create=True, orphan=True)
        git.cm(name)

    git.br("G")
    git.br("D", create=True)
    git.mg("H", unrelated=True, message="D")

    git.br("I")
    git.br("F", create=True)
    git.mg("J", unrelated=True, message="F")

    git.br("D")
    git.br("B", create=True)

    git.mg_multiple(["E", "F"], "B")

    git.br("F")
    git.br("C", create=True)
    git.cm("C")

    git.br("B")
    git.br("A", create=True)
    git.mg("C", message="A")


def start_new_repo(step_number: int = 1) -> StepResultsGenerator:
    return StepResultsGenerator(example_name=EXAMPLE_NAME, step_number=step_number)


def example_revisions() -> None:
    git = GitCommandMutate(SRG.repo_dir, date="01/01/25 09:00 +0100")
    repo_jon_loeliger(git)

    SRG.results(inspect.stack()[0][3], show_args=["-m 1"], rankdir="BT")
    SRG.results(inspect.stack()[0][3], show_args=["-m 1", "-l"], rankdir="BT")
    SRG.results(
        inspect.stack()[0][3],
        show_args=[
            "-m 1",
            "-a A^0",
            "-a A^",
            "-a A^1",
            "-a A~1",
            "-a A^2",
            "-a A^^",
            "-a A^1^1",
            "-a A~2",
            "-a B^2",
            "-a A^^2",
            "-a B^3",
            "-a A^^3",
            "-a A^^^",
            "-a A^1^1^1",
            "-a A~3",
            "-a D^2",
            "-a B^^2",
            "-a A^^^2",
            "-a A~2^2",
            "-a F^",
            "-a B^3^",
            "-a A^^3^",
            "-a F^2",
            "-a B^3^2",
            "-a A^^3^2",
        ],
        rankdir="BT",
    )
    SRG.results(
        inspect.stack()[0][3],
        show_args=[
            "-m 1",
            "-a C^{commit}",
            "-a HEAD",
            "-a :/H",
            "-a HEAD^{/F}",
            "-a @",
        ],
        rankdir="BT",
    )


def example_ranges() -> None:
    git = GitCommandMutate(SRG.repo_dir, date="01/01/25 09:00 +0100")
    repo_jon_loeliger(git)

    SRG.results(inspect.stack()[0][3], show_args=["-m 1", "-R D F"], rankdir="BT")
    SRG.results(inspect.stack()[0][3], show_args=["-m 1", "-R B..C"], rankdir="BT")
    SRG.results(inspect.stack()[0][3], show_args=["-m 1", "-R B...C"], rankdir="BT")
    SRG.results(inspect.stack()[0][3], show_args=["-m 1", "-R C^@"], rankdir="BT")


SRG = start_new_repo()
example_revisions()

SRG = start_new_repo(SRG.step_number)
example_ranges()
