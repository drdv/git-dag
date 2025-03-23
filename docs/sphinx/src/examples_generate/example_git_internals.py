"""Example from https://git-scm.com/book/en/v2/Git-Internals-Git-Objects"""

import inspect
import shutil
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional

from git_dag import GitRepository
from git_dag.cli import get_user_defined_cla
from git_dag.constants import DictStrStr
from git_dag.git_commands import GitCommandMutate
from git_dag.parameters import Params, ParamsPublic

EXAMPLE_NAME = "git_internals"

# ------------------------------------------------
# TMP_DIR = tempfile.mkdtemp()
# ------------------------------------------------
TMP_DIR = f"/tmp/git-dag-examples/{EXAMPLE_NAME}"
shutil.rmtree(TMP_DIR, ignore_errors=True)
Path(TMP_DIR).mkdir(parents=True)
# ------------------------------------------------

OUT_DIR = Path(TMP_DIR) / "out"
OUT_DIR.mkdir()

GIT = GitCommandMutate(TMP_DIR)

SHOW_DEFAULT_ARGS = [
    "-T",
    "-B",
    "-l",
    "-r",
    "-u",
    "-s",
    "-t",
    "-D",
    "-H",
    "-n",
    "0",
    "--trees-standalone",
    "--blobs-standalone",
]


def visualize(name: str, show_args: list[str]) -> None:
    params = Params(
        public=ParamsPublic(
            **get_user_defined_cla(show_args),
            file=OUT_DIR / f"{name}.gv",
        )
    )
    GitRepository(TMP_DIR, parse_trees=True).show(params)

    with open(OUT_DIR / f"{name}_html.rst", "w") as h:
        h.write(
            dedent(
                f"""
                .. raw:: html

                    <object class="svg-object"
                            data="_static/examples/{EXAMPLE_NAME}/{name}.gv.svg"
                            type="image/svg+xml">
                    </object>
                """
            )
        )

    with open(OUT_DIR / f"{name}_args.rst", "w") as h:
        h.write(
            dedent(
                f"""
                .. code-block:: bash
                    :caption: Visualize DAG

                    git dag {' '.join(show_args)}
                """
            )
        )


def generate_output(
    name: Optional[str] = None,
    show_args: Optional[list[str]] = None,
    commands: Optional[str] = None,
) -> None:
    global STEP_NUMBER
    if name is not None:
        name = f"{STEP_NUMBER:02}_{name}"
        STEP_NUMBER += 1
    else:
        STEP_NUMBER += 1
        return None

    visualize(name, SHOW_DEFAULT_ARGS if show_args is None else show_args)

    if commands is not None:
        with open(OUT_DIR / f"{name}_cmd.rst", "w") as h:
            h.write(commands)


def step_create_empty() -> None:
    GIT.init()

    generate_output()


def step_create_blob() -> None:
    GIT.run_general(
        f"echo 'test content' | {GIT.command_prefix} hash-object -w --stdin"
    )

    generate_output(
        inspect.stack()[0][3],
        show_args=["-B", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a blob from the content of a string

                echo 'test content' | git hash-object -w --stdin

            .. code-block:: console
                :caption: Output

                d670460b4b4aece5915caf5c68d12f560a9fe3e4
            """
        ),
    )


def step_create_blob_from_file() -> None:
    GIT.add({"test.txt": "version 1\n"})
    GIT.run_general(f"{GIT.command_prefix} hash-object -w test.txt")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-B", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a blob from the content of a file

                echo 'version 1' > test.txt
                git hash-object -w test.txt

            .. code-block:: console
                :caption: Output

                83baae61804e65cc73a7201a7252750c76066a30
            """
        ),
    )


def step_create_blob_from_modified_file() -> None:
    GIT.add({"test.txt": "version 2\n"})
    GIT.run_general(f"{GIT.command_prefix} hash-object -w test.txt")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-B", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a blob from the content of a modified file

                echo 'version 2' > test.txt
                git hash-object -w test.txt

            .. code-block:: console
                :caption: Output

                1f7a7a472abf3dd9643fd615f6da379c4acb3e3a
            """
        ),
    )


def step_create_tree_from_cached_blob() -> None:
    GIT.run_general(
        f"{GIT.command_prefix} update-index --add --cacheinfo 100644 "
        "83baae61804e65cc73a7201a7252750c76066a30 test.txt"
    )
    GIT.run_general(f"{GIT.command_prefix} write-tree")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "--trees-standalone", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a tree from a cached blob

                git update-index --add --cacheinfo 100644 83baae61804e65cc73a7201a7252750c76066a30 test.txt
                git write-tree

            .. code-block:: console
                :caption: Output

                d8329fc1cc938780ffdd9f94e0d364e0ea74f579
            """
        ),
    )


def step_create_tree_from_cached_blob_and_file() -> None:
    GIT.add({"new.txt": "new file\n"})
    GIT.run_general(
        f"{GIT.command_prefix} update-index --cacheinfo 100644 "
        "1f7a7a472abf3dd9643fd615f6da379c4acb3e3a test.txt"
    )
    GIT.run_general(f"{GIT.command_prefix} update-index --add new.txt")
    GIT.run_general(f"{GIT.command_prefix} write-tree")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "--trees-standalone", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a tree from a cached blob and a file

                echo 'new file' > new.txt
                git update-index --add --cacheinfo 100644 1f7a7a472abf3dd9643fd615f6da379c4acb3e3a test.txt
                git update-index --add new.txt
                git write-tree

            .. code-block:: console
                :caption: Output

                0155eb4229851634a0f03eb265b69f5a2d56f341
            """
        ),
    )


def step_create_tree_with_tree() -> None:
    GIT.run_general(f"{GIT.command_prefix} read-tree --prefix=bak d8329fc1")
    GIT.run_general(f"{GIT.command_prefix} write-tree")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "--trees-standalone", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Create a tree containing another tree

                git read-tree --prefix=bak d8329fc1
                git write-tree

            .. code-block:: console
                :caption: Output

                3c4e9cd789d88d8d89c1073707c3585e41b0e614
            """
        ),
    )


def step_add_commits() -> DictStrStr:
    env = {
        "GIT_AUTHOR_NAME": "First Last",
        "GIT_AUTHOR_EMAIL": "first.last.mail.com",
        "GIT_COMMITTER_NAME": "Nom Prenom",
        "GIT_COMMITTER_EMAIL": "nom.prenom@mail.com",
    }

    commit1 = GIT.run_general(
        f"echo 'First commit' | {GIT.command_prefix} commit-tree d8329f",
        env=env,
    )

    commit2 = GIT.run_general(
        f"echo 'Second commit' | {GIT.command_prefix} commit-tree 0155eb -p {commit1}",
        env=env,
    )

    commit3 = GIT.run_general(
        f"echo 'Third commit' | {GIT.command_prefix} commit-tree 3c4e9c -p {commit2}",
        env=env,
    )

    generate_output(
        inspect.stack()[0][3],
        show_args=[
            "-T",
            "-B",
            "-u",
            "-n",
            "0",
            "--trees-standalone",
            "--blobs-standalone",
        ],
        commands=dedent(
            f"""
            .. code-block:: bash
                :caption: Create three commits

                GIT_AUTHOR_NAME="First Last"
                GIT_AUTHOR_EMAIL="first.last.mail.com"
                GIT_COMMITTER_NAME="Nom Prenom"
                GIT_COMMITTER_EMAIL="nom.prenom@mail.com"

                SHA_FIRST_COMMIT=$(echo 'First commit' | git commit-tree d8329f)
                SHA_SECOND_COMMIT=$(echo 'Second commit' | git commit-tree 0155eb -p $SHA_FIRST_COMMIT)
                SHA_THIRD_COMMIT=$(echo 'Third commit' | git commit-tree 3c4e9c -p $SHA_SECOND_COMMIT)

                echo $SHA_FIRST_COMMIT
                echo $SHA_SECOND_COMMIT
                echo $SHA_THIRD_COMMIT

            .. code-block:: console
                :caption: Output

                {commit1}
                {commit2}
                {commit3}
            """
        ),
    )

    return {"commit1": commit1, "commit2": commit2, "commit3": commit3}


def step_add_tag(commits: DictStrStr) -> None:
    GIT.run_general(
        f'{GIT.command_prefix} tag first-commit -m "First commit" {commits["commit1"]}'
    )

    generate_output(
        inspect.stack()[0][3],
        show_args=[
            "-T",
            "-B",
            "-t",
            "-u",
            "-n",
            "0",
            "--trees-standalone",
            "--blobs-standalone",
        ],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Add a tag to the first commit

                git tag first-commit -m "First commit" $SHA_FIRST_COMMIT
            """
        ),
    )


def step_add_branch(commits: DictStrStr) -> None:
    GIT.run_general(f"{GIT.command_prefix} branch main {commits['commit3']}")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "-H", "-l", "-t", "-u", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Add a branch

                git branch main $SHA_THIRD_COMMIT
            """
        ),
    )


def step_reset_main(commits: DictStrStr) -> None:
    GIT.run_general(f"{GIT.command_prefix} reset {commits['commit2']}")

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "-H", "-l", "-t", "-u", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Reset main

                git reset $SHA_SECOND_COMMIT
            """
        ),
    )


def step_detached_head(commits: DictStrStr) -> None:
    GIT.run_general(
        f"{GIT.command_prefix} checkout {commits['commit2']}",
        expected_stderr="You are in 'detached HEAD' state",
    )

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "-H", "-l", "-t", "-u", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Checkout a commit

                git checkout $SHA_SECOND_COMMIT
            """
        ),
    )


def step_add_lightweight_tag(commits: DictStrStr) -> None:
    GIT.run_general(f'{GIT.command_prefix} tag third-commit {commits["commit3"]}')

    generate_output(
        inspect.stack()[0][3],
        show_args=["-T", "-B", "-H", "-l", "-t", "-u", "--blobs-standalone"],
        commands=dedent(
            """
            .. code-block:: bash
                :caption: Add a lightweight tag to the third commit

                git tag third-commit $SHA_THIRD_COMMIT
            """
        ),
    )


if __name__ == "__main__":
    STEP_NUMBER = 0

    step_create_empty()
    step_create_blob()
    step_create_blob_from_file()
    step_create_blob_from_modified_file()
    step_create_tree_from_cached_blob()
    step_create_tree_from_cached_blob_and_file()
    step_create_tree_with_tree()
    commits = step_add_commits()
    step_add_tag(commits)
    step_add_branch(commits)
    step_reset_main(commits)
    step_detached_head(commits)
    step_add_lightweight_tag(commits)
    visualize(
        "final_dag_no_trees_and_blobs",
        show_args=["-H", "-l", "-t", "-u"],
    )

    print(f"Temporary directory created: {TMP_DIR}")
