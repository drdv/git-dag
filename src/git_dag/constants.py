"""Constants."""

import os
from enum import Enum
from pathlib import Path
from typing import Final

DictStrStr = dict[str, str]


class DagBackends(Enum):
    """Backend libraries for DAG visualisation."""

    GRAPHVIZ = 1  #: https://github.com/xflr6/graphviz


#: Regex patterx for SHA-1 hash.
SHA_PATTERN: Final[str] = "(?P<sha>[0-9a-f]{40})"

#: See https://stackoverflow.com/a/21868228
TAG_FORMAT_FIELDS: Final[list[str]] = [
    "refname",  # short name of lightweight tag (LWT)
    "sha",  # SHA of tag object (for annotated tags) or pointed object for LWT
    "object",  # SHA of pointed object
    "type",  # type of pointed object
    "tag",  # name of annotated tag
    "taggername",
    "taggeremail",
    "taggerdate",
    "contents",
]

#: Plumbing command to get tag info.
CMD_TAGS_INFO: Final[str] = (
    "for-each-ref --python --format '"
    "%(refname:short) %(objectname) %(object) %(type) %(tag) "
    "%(taggername) %(taggeremail) %(taggerdate) %(contents)"
    "' refs/tags"
)

#: Empty git tree object.
GIT_EMPTY_TREE_OBJECT_SHA: Final[str] = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

#: HTML template to embed SVG
HTML_EMBED_SVG: Final[
    str
] = """
<!DOCTYPE html>
<!-- serve using python -m http.server -d /path/to/src -->
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>Embed SVG</title>
    <style>
      .svg-object {{
          height: 97vh;
          width: 100%;
          border: 1px solid black;
      }}
    </style>
    <script>
    {svg_pan_zoom_js}
    </script>
    <script>
    {custom_js}
    </script>
  </head>
  <body>
    <object class="svg-object" data="{svg_filename}" type="image/svg+xml"></object>
  </body>
</html>
"""

#: Configuration file.
CONFIG_FILE: Final[Path] = Path(
    os.getenv("GIT_DAG_CONFIG_FILE", os.path.expandvars("$HOME/.git-dag.yml"))
)
