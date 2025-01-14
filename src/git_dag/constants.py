"""Constants."""

#: Empty git tree object.
GIT_EMPTY_TREE_OBJECT_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

#: Graphviz node colors.
GRAPHVIZ_NODE_COLORS = {
    "commit": "gold3",
    "commit-unreachable": "darkorange",
    "tree": "deepskyblue4",
    "the-empty-tree": "darkturquoise",
    "blob": "gray",
    "tag": "pink",
    "tag-lw": "lightcoral",
    "head": "cornflowerblue",
    "local-branches": "forestgreen",
    "remote-branches": "firebrick",
    "stash": "skyblue",
}

#: Nuber of SHA characters to display in labels.
SHA_LIMIT = 8
