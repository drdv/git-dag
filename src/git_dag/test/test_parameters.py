"""Test ``cli.py``."""

# pylint: disable=missing-function-docstring

from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml
from pytest import CaptureFixture

from git_dag.constants import CONFIG_FILE
from git_dag.parameters import (
    Params,
    ParamsBase,
    ParamsDagEdge,
    ParamsDagGlobal,
    ParamsDagNode,
    ParamsDagNodeColors,
    ParamsPublic,
    ParamsStandaloneCluster,
    context_ignore_config_file,
)

PARTIAL_CONFIG = """
public:
  format: png
  log_level: INFO
  init_refs:
    - a
    - b
  max_numb_commits: 500
  show_head: true
  show_blobs: false

dag_global:
  bgcolor: transparent
"""


def test_create_config(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    def verify_parameters(
        params_from_config_file: dict[str, Any],
        param_class_name: type,
        passed_params_values: dict[str, Any],
    ) -> None:
        section = param_class_name().section_in_config()

        for key, value in passed_params_values.items():
            assert params_from_config_file[section][key] == value

        with context_ignore_config_file():
            params_default_values = param_class_name().model_dump()
            for key, value in params_default_values.items():
                if key not in passed_params_values:
                    assert params_from_config_file[section][key] == value

    config_file = tmp_path / CONFIG_FILE.name

    public = {"show_tags": True, "file": "test.gv", "init_refs": ["r1", "r2"]}
    dag_global = {"rankdir": "LR"}
    dag_node = {"shape": "circle", "height": "0.1"}
    dag_edge = {"color": "red"}
    node_colors = {"commit": "black", "head": "red"}
    cluster = {"label": "cluster"}

    with patch("git_dag.parameters.CONFIG_FILE", config_file):
        params = Params(
            public=ParamsPublic.model_validate(public),
            dag_global=ParamsDagGlobal.model_validate(dag_global),
            dag_node=ParamsDagNode.model_validate(dag_node),
            dag_edge=ParamsDagEdge.model_validate(dag_edge),
            dag_node_colors=ParamsDagNodeColors.model_validate(node_colors),
            standalone_cluster=ParamsStandaloneCluster.model_validate(cluster),
        )
        params.create_config()
        assert f"Created config {config_file}." in capsys.readouterr().out

        params.create_config()
        assert f"Config file {config_file} already exists." in capsys.readouterr().out

    assert config_file.is_file()
    with open(config_file, "r", encoding="utf-8") as h:
        params_from_config_file = yaml.safe_load(h)

    verify_parameters(params_from_config_file, ParamsPublic, public)
    verify_parameters(params_from_config_file, ParamsDagGlobal, dag_global)
    verify_parameters(params_from_config_file, ParamsDagNode, dag_node)
    verify_parameters(params_from_config_file, ParamsDagEdge, dag_edge)
    verify_parameters(params_from_config_file, ParamsDagNodeColors, node_colors)
    verify_parameters(params_from_config_file, ParamsStandaloneCluster, cluster)


def test_default_values_from_config(tmp_path: Path) -> None:
    config_file = tmp_path / CONFIG_FILE.name

    with open(config_file, "w", encoding="utf-8") as h:
        h.write(PARTIAL_CONFIG)

    with patch("git_dag.parameters.CONFIG_FILE", config_file):
        public = ParamsPublic(show_blobs=True)
        dag_global = ParamsDagGlobal()
        dag_edge = ParamsDagEdge()

    assert public.format == "png"
    assert public.log_level == "INFO"
    assert public.init_refs == ["a", "b"]
    assert public.show_head
    assert public.show_blobs

    assert dag_global.bgcolor == "transparent"
    assert dag_global.rankdir == "TB"
    assert dag_global.dpi == "None"

    assert dag_edge.arrowsize == "0.5"


def test_default_values_from_config_manual(tmp_path: Path) -> None:
    config_file = tmp_path / CONFIG_FILE.name

    with open(config_file, "w", encoding="utf-8") as h:
        h.write(PARTIAL_CONFIG)

    Params.set_ignore_config_file(True)
    with patch("git_dag.parameters.CONFIG_FILE", config_file):
        public = ParamsPublic(show_blobs=True)

    assert public.format == "svg"
    assert public.log_level == "WARNING"
    assert public.init_refs is None
    assert not public.show_head
    assert public.show_blobs

    ParamsBase.set_ignore_config_file(False)
    with patch("git_dag.parameters.CONFIG_FILE", config_file):
        public = ParamsPublic(show_blobs=True)

    assert public.format == "png"
    assert public.log_level == "INFO"
    assert public.init_refs == ["a", "b"]
    assert public.show_head
    assert public.show_blobs
