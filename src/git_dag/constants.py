"""Constants."""

from enum import Enum

#: Tag misc info format (same as the one in :func:`RegexParser.parse_tag`).
TAG_MISC_FORMAT = """tagger %(tagger)

%(subject)

%(body)
"""


class DagBackends(Enum):
    """Backend libraries for DAG visualisation."""

    GRAPHVIZ = 1  #: https://github.com/xflr6/graphviz


#: Empty git tree object.
GIT_EMPTY_TREE_OBJECT_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

#: Node colors (https://graphviz.org/doc/info/colors.html).
DAG_NODE_COLORS = {
    "commit": "gold3",
    "commit-unreachable": "darkorange",
    "tree": "deepskyblue4",
    "the-empty-tree": "darkturquoise",
    "blob": "gray",
    "tag": "pink",
    "tag-deleted": "rosybrown4",
    "tag-lw": "lightcoral",
    "head": "cornflowerblue",
    "local-branches": "forestgreen",
    "remote-branches": "firebrick",
    "stash": "skyblue",
}

DAG_ATTR = {
    "rankdir": "TB",
    "dpi": "96.0",
    "bgcolor": "gray42",
}

DAG_NODE_ATTR = {
    "shape": "box",
    "style": "filled",
    "margin": "0.01,0.01",
    "width": "0.02",
    "height": "0.02",
}

DAG_EDGE_ATTR = {
    "arrowsize": "0.5",
    "color": "gray10",
}

#: Nuber of SHA characters to display in labels.
SHA_LIMIT = 8
