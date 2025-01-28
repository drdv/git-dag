"""Pydantic models of git objects."""

from __future__ import annotations

import abc
from enum import Enum
from typing import ClassVar, Optional, cast

from pydantic import BaseModel, Field, computed_field

DictStrStr = dict[str, str]
GitCommitRawDataType = dict[str, str | list[str]]
"""
Type of the data associated with a git commit object.

value ``str`` is for the tree associated with a commit
value ``list[str]`` is for the parents (there can be 0, 1 or many).
"""

#: Type of raw data associated with a git tree object
GitTreeRawDataType = list[DictStrStr]

#: Type of raw data associated with a git tag object
GitTagRawDataType = DictStrStr


class GitObjectKind(str, Enum):
    """Git object kind/type."""

    blob = "blob"
    tree = "tree"
    commit = "commit"
    tag = "tag"


class GitObject(BaseModel, abc.ABC):
    """A base class for git objects."""

    @property
    @abc.abstractmethod
    def kind(self) -> GitObjectKind:
        """The object type."""

    @property
    @computed_field(repr=True)
    def is_ready(self) -> bool:
        """Indicates whether the object is ready to use.

        Note
        -----
        See note in :func:`~GitInspector.get_raw_objects`.

        """
        return self._is_ready

    @is_ready.setter
    def is_ready(self, ready: bool) -> None:
        self._is_ready = ready

    sha: str

    _is_ready: bool = False


class GitBlob(GitObject):
    """Git blob object."""

    kind: ClassVar[GitObjectKind] = GitObjectKind.blob
    _is_ready: bool = True


class GitTag(GitObject):
    """Git (annotated) tag object."""

    kind: ClassVar[GitObjectKind] = GitObjectKind.tag
    name: str

    raw_data: GitTagRawDataType = Field(repr=False)

    # I keep track of deleted (annotated) tags that haven't been garbage collected
    deleted: bool = False

    _anchor: GitObject

    @property
    def anchor(self) -> GitObject:
        """Return the associated anchor.

        Note
        -----
        An annotated tag can point to another tag: https://stackoverflow.com/a/19812276

        """
        return self._anchor

    @anchor.setter
    def anchor(self, anchor: GitObject) -> None:
        self._anchor = anchor

    @property
    def misc_info(self) -> str:
        """Return misc info (e.g., tag message)."""
        return self.raw_data["misc"]


class GitCommit(GitObject):
    """Git commit object."""

    kind: ClassVar[GitObjectKind] = GitObjectKind.commit
    reachable: bool

    raw_data: GitCommitRawDataType = Field(repr=False)
    _tree: GitTree
    _parents: list[GitCommit]
    _message: str

    @property
    def tree(self) -> GitTree:
        """Return the associated tree (there can be exactly one)."""
        return self._tree

    @tree.setter
    def tree(self, tree: GitTree) -> None:
        self._tree = tree

    @property
    def parents(self) -> list[GitCommit]:
        """Return the parents."""
        return self._parents

    @parents.setter
    def parents(self, parents: list[GitCommit]) -> None:
        self._parents = parents

    @property
    def message(self) -> str:
        """Return the commit message."""
        return self._message

    @message.setter
    def message(self, message: str) -> None:
        self._message = message

    @property
    def misc_info(self) -> str:
        """Return misc info (e.g., commit message)."""
        return cast(str, self.raw_data["misc"])


class GitTree(GitObject):
    """Git tree object."""

    kind: ClassVar[GitObjectKind] = GitObjectKind.tree

    raw_data: GitTreeRawDataType = Field(repr=False)
    _children: list[GitTree | GitBlob]

    # Set to True when it is known apriory that there would be no children
    # e.g., for the empty git tree object
    no_children: bool = False

    @property
    def children(self) -> list[GitTree | GitBlob]:
        """Return the children."""
        if self.no_children:
            return []
        return self._children

    @children.setter
    def children(self, children: list[GitTree | GitBlob]) -> None:
        if self.no_children and children:
            raise TypeError("Setting children when there should be none.")
        self._children = children


class GitTagLightweight(BaseModel):
    """Git lightweight tag (this is not a ``GitObject``)."""

    name: str
    anchor: GitObject


class GitBranch(BaseModel):
    """A branch."""

    name: str
    commit: GitCommit
    is_local: bool = False
    tracking: Optional[str] = None


class GitStash(BaseModel):
    """A stash."""

    index: int
    title: str
    commit: GitCommit
