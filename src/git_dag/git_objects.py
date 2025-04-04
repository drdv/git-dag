"""Pydantic models of git objects."""

from __future__ import annotations

import abc
from enum import Enum
from typing import ClassVar, Optional, cast

from pydantic import BaseModel, ConfigDict, Field, computed_field

from .constants import DictStrStr

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

    model_config = ConfigDict(extra="forbid")

    @property
    @abc.abstractmethod
    def kind(self) -> GitObjectKind:
        """The object type."""

    @computed_field(repr=True)
    def is_ready(self) -> bool:
        """Indicates whether the object is ready to use.

        Note
        -----
        See note in :func:`~git_dag.git_repository.GitInspector.get_raw_objects`.

        """
        return self._is_ready

    # https://docs.pydantic.dev/2.0/usage/computed_fields/
    @is_ready.setter  # type: ignore[no-redef]
    def is_ready(self, ready: bool) -> None:
        self._is_ready = ready

    sha: str

    _is_ready: bool = False


class GitBlob(GitObject):
    """Git blob object."""

    model_config = ConfigDict(extra="forbid")

    kind: ClassVar[GitObjectKind] = GitObjectKind.blob
    _is_ready: bool = True


class GitTag(GitObject):
    """Git (annotated) tag object."""

    model_config = ConfigDict(extra="forbid")

    kind: ClassVar[GitObjectKind] = GitObjectKind.tag
    name: str

    raw_data: GitTagRawDataType = Field(repr=False)

    # I keep track of deleted (annotated) tags that haven't been garbage-collected
    is_deleted: bool = False

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
    def tagger(self) -> str:
        """Return tagger."""
        return self.raw_data["taggername"]

    @property
    def tagger_email(self) -> str:
        """Return tagger email."""
        return self.raw_data["taggeremail"]

    @property
    def tagger_date(self) -> str:
        """Return tagger date."""
        return self.raw_data["taggerdate"]

    @property
    def message(self) -> str:
        """Return the message."""
        return self.raw_data["message"]


class GitCommit(GitObject):
    """Git commit object."""

    model_config = ConfigDict(extra="forbid")

    kind: ClassVar[GitObjectKind] = GitObjectKind.commit
    is_reachable: bool

    raw_data: GitCommitRawDataType = Field(repr=False)
    _tree: GitTree
    _parents: list[GitCommit]

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
    def author(self) -> str:
        """Return the author."""
        return cast(str, self.raw_data["author"])

    @property
    def author_email(self) -> str:
        """Return the author email."""
        return cast(str, self.raw_data["author_email"])

    @property
    def author_date(self) -> str:
        """Return the author date."""
        return cast(str, self.raw_data["author_date"])

    @property
    def committer(self) -> str:
        """Return the committer."""
        return cast(str, self.raw_data["committer"])

    @property
    def committer_email(self) -> str:
        """Return the committer email."""
        return cast(str, self.raw_data["committer_email"])

    @property
    def committer_date(self) -> str:
        """Return the committer date."""
        return cast(str, self.raw_data["committer_date"])

    @property
    def message(self) -> str:
        """Return the commit message."""
        return cast(str, self.raw_data["message"])


class GitTree(GitObject):
    """Git tree object."""

    model_config = ConfigDict(extra="forbid")

    kind: ClassVar[GitObjectKind] = GitObjectKind.tree

    #: Raw data.
    raw_data: GitTreeRawDataType = Field(repr=False)

    #: Child trees and blobs.
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
            raise TypeError("Attempting to set children when there should be none.")
        self._children = children


class GitTagLightweight(BaseModel):
    """Git lightweight tag (this is not a ``GitObject``)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    anchor: GitObject


class GitBranch(BaseModel):
    """A branch."""

    model_config = ConfigDict(extra="forbid")

    name: str
    commit: GitCommit
    is_local: bool = False
    tracking: Optional[str] = None


class GitStash(BaseModel):
    """A stash."""

    model_config = ConfigDict(extra="forbid")

    index: int
    title: str
    commit: GitCommit


class GitHead(BaseModel):
    """A head (local or remote)."""

    model_config = ConfigDict(extra="forbid")

    commit: Optional[GitCommit] = None
    branch: Optional[GitBranch] = None

    @property
    def is_defined(self) -> bool:
        """Is the HEAD defined."""
        return self.commit is not None

    @property
    def is_detached(self) -> bool:
        """Is the HEAD detached."""
        return self.branch is None

    def __repr__(self) -> str:
        if not self.is_defined:
            return "None"

        if self.is_detached:
            return "DETACHED"

        # type narrowing to make mypy happy
        assert (self.commit is not None) and (self.branch is not None)

        return f"{self.commit.sha} ({self.branch.name})"
