"""Constants."""

from enum import Enum
from typing import Final

DictStrStr = dict[str, str]

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


class DagBackends(Enum):
    """Backend libraries for DAG visualisation."""

    GRAPHVIZ = 1  #: https://github.com/xflr6/graphviz


#: Empty git tree object.
GIT_EMPTY_TREE_OBJECT_SHA: Final[str] = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

#: Node colors (https://graphviz.org/doc/info/colors.html).
DAG_NODE_COLORS: Final[DictStrStr] = {
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
    "notes": "white",
}

#: Parameters of the cluster for standalone trees and blobs
STANDALONE_CLUSTER_PARAMS: DictStrStr = {
    "color": "lightgrey",
    "label": "Standalone\nTrees & Blobs",
}


DAG_ATTR: Final[DictStrStr] = {
    "rankdir": "TB",
    "dpi": "None",
    "bgcolor": "transparent",
}

DAG_NODE_ATTR: Final[DictStrStr] = {
    "shape": "box",
    "style": "filled",
    "margin": "0.01,0.01",
    "width": "0.02",
    "height": "0.02",
}

DAG_EDGE_ATTR: Final[DictStrStr] = {
    "arrowsize": "0.5",
    "color": "gray10",
}

#: Nuber of SHA characters to display in labels.
SHA_LIMIT: Final[int] = 8
