"""Common utils for example generation."""

import shutil
from pathlib import Path
from textwrap import dedent
from typing import Optional

from git_dag import GitRepository
from git_dag.cli import get_user_defined_cla
from git_dag.parameters import (
    Params,
    ParamsDagGlobal,
    ParamsPublic,
    context_ignore_config_file,
)


class StepResultsGenerator:
    """Generate results for a given step."""

    def __init__(self, example_name: str, step_number: int = 1) -> None:
        self.example_name = example_name

        self.repo_dir = f"/tmp/git-dag-examples/{self.example_name}"
        shutil.rmtree(self.repo_dir, ignore_errors=True)
        Path(self.repo_dir).mkdir(parents=True)

        self.out_dir = Path(f"{self.repo_dir}-out")
        self.out_dir.mkdir(exist_ok=True)

        self.step_number = step_number
        self.rankdir = "TB"

    def results(
        self,
        name: str,
        show_args: list[str],
        commands: Optional[str] = None,
        rankdir: Optional[str] = None,
        increment_step_number: bool = True,
    ) -> None:
        """Store all results."""
        if rankdir is not None:
            self.rankdir = rankdir

        if increment_step_number:
            name = f"{self.step_number:02}_{name}"
            self.step_number += 1

        self._store_svg(name, show_args)
        if commands is not None:
            self._store_commands(name, commands)

    def _store_svg(self, name: str, show_args: list[str]) -> None:
        """Store SVG."""
        with context_ignore_config_file():
            params = Params(
                public=ParamsPublic(
                    **get_user_defined_cla(show_args),
                    file=self.out_dir / f"{name}.gv",
                ),
                dag_global=ParamsDagGlobal(rankdir=self.rankdir),  # type: ignore[arg-type]
            )

        GitRepository(self.repo_dir, parse_trees=True).show(params)

        self._store_args(name, show_args)
        with open(self.out_dir / f"{name}_html.rst", "w", encoding="utf-8") as h:
            h.write(
                dedent(
                    f"""
                    .. raw:: html

                        <object class="svg-object"
                                data="_static/examples/{self.example_name}/{name}.gv.svg"
                                type="image/svg+xml">
                        </object>
                    """
                )
            )

    def _store_args(self, name: str, show_args: list[str]) -> None:
        """Store args."""
        with open(self.out_dir / f"{name}_args.rst", "w", encoding="utf-8") as h:
            h.write(
                dedent(
                    f"""
                    .. code-block:: bash
                        :caption: Visualize DAG

                        git dag {' '.join(show_args)}
                    """
                )
            )

    def _store_commands(self, name: str, commands: Optional[str]) -> None:
        """Store commands."""
        if commands is not None:
            with open(self.out_dir / f"{name}_cmd.rst", "w", encoding="utf-8") as h:
                h.write(commands)
