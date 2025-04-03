"""Git repository parsing functionality."""

from __future__ import annotations

import logging
import multiprocessing
import re
from functools import wraps
from operator import itemgetter
from pathlib import Path
from time import time
from typing import Annotated, Any, Callable, Optional, Type, cast

from pydantic import BeforeValidator, TypeAdapter

from git_dag.exceptions import CalledProcessCustomError

from .constants import GIT_EMPTY_TREE_OBJECT_SHA, SHA_PATTERN, DictStrStr
from .dag import DagVisualizer
from .git_commands import GitCommand
from .git_objects import (
    GitBlob,
    GitBranch,
    GitCommit,
    GitCommitRawDataType,
    GitHead,
    GitObject,
    GitObjectKind,
    GitStash,
    GitTag,
    GitTagLightweight,
    GitTagRawDataType,
    GitTree,
    GitTreeRawDataType,
)
from .parameters import Params
from .utils import creator_timestamp_format

IG = itemgetter("sha", "kind")
logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger(__name__)

# https://stackoverflow.com/q/9765453
# For example it is created when using git rebase -i --root
GIT_EMPTY_TREE_OBJECT = GitTree(
    sha=GIT_EMPTY_TREE_OBJECT_SHA,
    raw_data=[],
    no_children=True,
)


def time_it[R, **P](f: Callable[P, R]) -> Callable[P, R]:
    """Return decorator for timing.

    Note
    -----
    The generic ``P`` is a ``ParamSpec``.

    """

    @wraps(f)
    def wrap(*args: P.args, **kwargs: P.kwargs) -> R:
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        LOG.info(f"{f.__qualname__:<30} took: {te-ts:0.5f} sec")
        return result

    return wrap


class RegexParser:
    """Regex parser for files associated with git objects.

    Note
    -----
    All this is quite ad hoc.

    """

    @staticmethod
    def parse_object_descriptor(string: str) -> DictStrStr:
        """Parse an object descriptor with format ``SHA OBJECT_TYPE``."""
        pattern = f"^{SHA_PATTERN} (?P<kind>.+)"
        match = re.search(pattern, string)
        if match:
            return {"sha": match.group("sha"), "kind": match.group("kind")}
        raise RuntimeError(f'Object string "{string}" not matched.')  # pragma: no cover

    @staticmethod
    def parse_tree_info(data: Optional[list[str]] = None) -> GitTreeRawDataType:
        """Parse a tree object file (read with ``cat-file -p``)."""
        # for the empty tree object, data = [""]
        if data is None or (len(data) == 1 and not data[0]):
            return []

        # in the presence of submodules, trees may refer to commits as well
        pattern = f"(?P<kind>tree|blob|commit) {SHA_PATTERN}\t"
        output = []
        for string in data:
            match = re.search(pattern, string)
            if match:
                kind = match.group("kind")
                if kind != "commit":  # skip references to commits
                    output.append({"sha": match.group("sha"), "kind": kind})
            else:
                raise RuntimeError(
                    f'Tree string "{string}" not matched.'
                )  # pragma: no cover

        return output

    @staticmethod
    def _collect_commit_info(
        commit_object_data: list[DictStrStr],
        misc_info: list[str],
    ) -> GitCommitRawDataType:
        """Collect commit related info."""

        def strip_creator_label(string: str) -> str:
            """Remove the author/committer label.

            E.g., remove the  "author" from "author First Last <first.last.mail.com>".
            """
            return " ".join(string.split()[1:])

        def extract_message(misc_info: list[str]) -> str:
            return "\n".join(
                [
                    string.strip()
                    for string in misc_info[2:]  # skip author and committer
                    if string and not string.startswith("Co-authored-by")
                ]
            )

        parents = []
        tree = ""
        for d in commit_object_data:
            sha, kind = IG(d)
            if kind == "tree":
                if tree:
                    raise ValueError(
                        "Exactly one tree expected per commit."
                    )  # pragma: no cover
                tree = sha
            elif kind == "parent":
                parents.append(sha)
            else:
                raise RuntimeError("It is not expected to be here!")  # pragma: no cover

        author, author_email, author_date = creator_timestamp_format(
            strip_creator_label(misc_info[0])
        )
        committer, committer_email, committer_date = creator_timestamp_format(
            strip_creator_label(misc_info[1])
        )
        return {
            "tree": tree,
            "parents": parents,
            "message": extract_message(misc_info),
            "author": author,
            "author_email": author_email,
            "author_date": author_date,
            "committer": committer,
            "committer_email": committer_email,
            "committer_date": committer_date,
        }

    @staticmethod
    def parse_commit_info(data: list[str]) -> GitCommitRawDataType:
        """Parse a commit object file (read with ``git cat-file -p``)."""
        pattern = f"^(?P<kind>tree|parent) {SHA_PATTERN}"
        output, misc_info = [], []
        # The tree and the parents always come first in the object file of a commit.
        # Next is the author, and this is the start of what I call "misc info".
        # collect_misc_info is used to avoid matching a commit message like "tree SHA".
        collect_misc_info = False
        for string in data:
            match = re.search(pattern, string)
            if not collect_misc_info and match:
                output.append({"sha": match.group("sha"), "kind": match.group("kind")})
            else:
                collect_misc_info = True
                misc_info.append(string)

        return RegexParser._collect_commit_info(output, misc_info)

    @staticmethod
    def parse_tag_info(data: list[str]) -> GitTagRawDataType:
        """Parse a tag object file (read using ``git cat-file -p``)."""
        labels = ["sha", "type", "refname", "tagger"]
        patterns = [
            f"^object {SHA_PATTERN}",
            "^type (?P<type>.+)",
            "^tag (?P<refname>.+)",
            "^tagger (?P<tagger>.+)",
        ]

        output = {}
        for pattern, string, label in zip(patterns, data, labels):
            match = re.search(pattern, string)
            if match:
                output[label] = match.group(label)
            else:
                raise RuntimeError(
                    f'Tag string "{string}" not matched.'
                )  # pragma: no cover

        tagger, tagger_email, tag_date = creator_timestamp_format(output["tagger"])
        output["taggername"] = tagger
        output["taggeremail"] = tagger_email
        output["taggerdate"] = tag_date
        output["message"] = "\n".join(data[5:])
        output["anchor"] = output.pop("sha")
        output["tag"] = output["refname"]  # abusing things a bit
        return output

    @staticmethod
    def parse_stash_info(data: Optional[list[str]]) -> list[DictStrStr]:
        """Parse stash info as returned by :func:`GitCommand.get_stash_info`."""
        if not data:
            return []

        pattern = f"{SHA_PATTERN} stash@{{(?P<index>[0-9]+)}} (?P<title>.*)"
        keys = ["index", "sha", "title"]

        out = []
        for string in data:
            match = re.search(pattern, string)
            if match:
                out.append({key: match.group(key) for key in keys})
            else:
                raise RuntimeError(
                    'Stash string "{string}" not matched.'
                )  # pragma: no cover

        return out


class GitInspector:
    """Git inspector."""

    @time_it
    def __init__(self, repository_path: str | Path = ".", parse_trees: bool = False):
        """Initialize instance (read most required info from the repository).

        Parameters
        -----------
        repository_path
            Path to the git repository.
        parse_trees
            Whether to parse the tree objects (doing this can be very slow and is best
            omitted for anything other than small repos). FIXME: currenlty all tree
            objects are parsed even if we intend to display only a small part of them.

        """
        self.parse_trees = parse_trees
        self.repository_path = repository_path
        self.git = GitCommand(repository_path)

        self.objects_sha_kind = self.git.get_objects_sha_kind()
        self.commits_sha = self._get_commits_sha()
        self.commits_info = self._get_commits_info()
        self.tags_info_parsed = self.git.get_tags_info_parsed()
        self.trees_info = self._get_trees_info() if self.parse_trees else {}
        self.blobs_and_trees_names: DictStrStr = self.git.get_blobs_and_trees_names(
            self.trees_info
        )
        self.stashes_info_parsed = RegexParser.parse_stash_info(
            self.git.get_stash_info()
        )
        self.notes_dag_root = self.git.get_notes_dag_root()

    def _get_commits_sha(self) -> dict[str, set[str]]:
        """Return SHA of all reachable/unreachable commits.

        Note
        -----
        Git handles stashes through the reflog and it keeps only the last stash in
        ``.git/refs/stash`` (see output of ``git reflog stash``). Hence, we consider
        commits associated with earlier stashes to be unreachable (as they are not
        referred by any reference).

        """
        reachable_commits = set(self.git.rev_list("--all").strip().split("\n"))
        all_commits = set(
            obj.split()[0] for obj in self.objects_sha_kind if "commit" in obj
        )
        return {
            "all": all_commits,
            "reachable": reachable_commits,
            "unreachable": all_commits - reachable_commits,
        }

    def _get_commits_info(self) -> dict[str, list[str]]:
        """Get content of object files for all commits.

        Note
        -----
        It is much faster to read the info for all commits using ``git rev-list --all
        --reflog --header`` instead of using ``git cat-file -p SHA`` per commit. The
        ``--reflog`` flag includes unreachable commits as well.

        Warning
        --------
        In some cases, ``git rev-list --all --reflog`` doesn't return all unreachable
        commits (when this happens, the corresponding object files are read using ``git
        cat-file -p``).

        """
        commits_info = {}
        for info in self.git.rev_list("--all --reflog --header").split("\x00"):
            if info:
                commit_sha, *rest = info.split("\n")
                commits_info[commit_sha] = rest

        numb_commits_not_found = len(self.commits_sha["all"]) - len(commits_info)
        if numb_commits_not_found > 0:
            LOG.info(
                f"{numb_commits_not_found} commits not found in "
                "git rev-list --all --reflog"
            )
        elif numb_commits_not_found < 0:
            raise RuntimeError("We shouldn't be here.")  # pragma: no cover

        return commits_info

    @time_it
    def _get_trees_info(self) -> dict[str, list[str]]:
        """Get content of object files for all trees.

        Warning
        --------
        This is slow! I simply don't know how to speed-up this operation. I ended-up
        using multiprocessing but there must be a better way. In ``GitPython`` they
        interact with ``git cat-file --batch`` with streams (to explore). It seems
        strange to be able to read all object files for commits at once (using ``git
        rev-list``) and to not be able to do it for trees (I must be missing something).
        FIXME: to find a better way to do this.

        """
        all_sha = [obj.split()[0] for obj in self.objects_sha_kind if "tree" in obj]
        with multiprocessing.Pool() as pool:
            object_file_content = pool.map(
                self.git.ls_tree,
                all_sha,
            )
        return dict(zip(all_sha, object_file_content))

    def _get_objects_info_parsed(self, sha: str, kind: str) -> GitObject:
        match kind:
            case GitObjectKind.blob:
                return GitBlob(sha=sha)
            case GitObjectKind.commit:
                if sha in self.commits_info:
                    commit_info = self.commits_info[sha]
                else:
                    commit_info = self.git.read_object_file(sha)  # slower
                    LOG.info(f"[commit] manually executing git cat-file -p {sha}")

                return GitCommit(
                    sha=sha,
                    is_reachable=sha in self.commits_sha["reachable"],
                    raw_data=RegexParser.parse_commit_info(commit_info),
                )
            case GitObjectKind.tag:
                try:
                    tag = self.tags_info_parsed["annotated"][sha]
                    is_deleted = False
                except KeyError:
                    # slower (used only for deleted annotated tags)
                    tag = RegexParser.parse_tag_info(self.git.read_object_file(sha))
                    is_deleted = True

                return GitTag(
                    sha=sha,
                    name=tag["refname"],
                    raw_data=tag,
                    is_deleted=is_deleted,
                )
            case GitObjectKind.tree:
                return GitTree(
                    sha=sha,
                    raw_data=RegexParser.parse_tree_info(self.trees_info.get(sha)),
                )
            case _:  # pragma: no cover
                raise RuntimeError("Leaking objects!")

    @time_it
    def get_raw_objects(self) -> dict[str, GitObject]:
        """Return all raw objects in a git repository.

        Note
        -----
        The objects are "raw", in the sense that they are not fully initialized. For
        example, consider a :class:`~git_dag.git_objects.GitTree` object. Even
        though all necessary data is available in
        :attr:`~git_dag.git_objects.GitTree.raw_data`, the ``GitTree._children``
        field is still not initialized (and the
        :class:`~git_dag.git_objects.GitTree` instances are not fully functional).
        The remaining post-processing is performed in
        :func:`~git_dag.git_repository.GitRepository.post_process_inspector_data` (as
        all instances need to be formed first). The
        :attr:`~git_dag.git_objects.GitObject.is_ready` property indicates whether
        an instance has been fully initialized.

        """

        def git_entity_before_validator(object_descriptor: str) -> GitObject:
            """Transform/validate data.

            Note
            -----
            ``self`` is used from the closure.

            """
            return self._get_objects_info_parsed(
                *IG(RegexParser.parse_object_descriptor(object_descriptor))
            )

        GitObjectAnnotated = Annotated[
            GitObject,
            BeforeValidator(git_entity_before_validator),
        ]

        return {
            obj.sha: obj
            for obj in TypeAdapter(list[GitObjectAnnotated]).validate_python(
                self.objects_sha_kind
            )
        }


class GitRepository:
    """Git repository.

    Note
    -----
    All git objects are processed (optionally tree objects can be skipped). This seems
    fine even for large repositories, e.g., it takes less than 20 sec. to process the
    repository of git itself which has 75K commits (without reading the tree object
    files).

    """

    def __init__(
        self,
        repository_path: str | Path = ".",
        parse_trees: bool = False,
    ) -> None:
        """Initialize instance.

        Parameters
        -----------
        repository_path
            Path to the git repository.
        parse_trees
            Whether to parse the tree objects (doing this can be very slow).

        """
        if not Path(repository_path).exists():
            raise RuntimeError(f"Path {repository_path} doesn't exist.")

        self.inspector = GitInspector(repository_path, parse_trees)
        self.post_process_inspector_data()

    @time_it
    def post_process_inspector_data(self) -> None:
        """Post-process inspector data (see :func:`GitInspector.get_raw_objects`)."""
        self.objects: dict[str, GitObject] = self._form_objects()
        self.all_reachable_objects_sha: set[str] = self.get_all_reachable_objects()
        self.commits = self.filter_objects(GitCommit)
        self.tags: dict[str, GitTag] = self._form_annotated_tags()
        self.tags_lw: dict[str, GitTagLightweight] = self._form_lightweight_tags()
        self.remotes: list[str] = self.inspector.git.get_remotes()
        self.branches: list[GitBranch] = self._form_branches()
        self.head: GitHead = self._form_local_head()
        self.remote_heads: DictStrStr = self._form_remote_heads()
        self.stashes: list[GitStash] = self._form_stashes()
        self.notes_dag_root: Optional[DictStrStr] = self.inspector.notes_dag_root

    @time_it
    def _form_branches(self) -> list[GitBranch]:
        """Post-process branches."""
        branches_raw = self.inspector.git.get_branches(self.remotes)
        branches: list[GitBranch] = []

        for branch_name, sha in branches_raw["local"].items():
            branches.append(
                GitBranch(
                    name=branch_name,
                    commit=self.commits[sha],
                    is_local=True,
                    tracking=self.inspector.git.local_branch_is_tracking(branch_name),
                )
            )

        for branch_name, sha in branches_raw["remote"].items():
            branches.append(
                GitBranch(
                    name=branch_name,
                    commit=self.commits[sha],
                )
            )

        return branches

    @time_it
    def _form_local_head(self) -> GitHead:
        """Post-process HEAD."""
        try:
            head_commit_sha = self.inspector.git.get_local_head_commit_sha()
        except CalledProcessCustomError:
            LOG.warning("No Head")
            return GitHead()

        head_branch_name = self.inspector.git.get_local_head_branch()
        if head_branch_name is None:
            return GitHead(commit=self.commits[head_commit_sha])

        head_branch = [b for b in self.branches if b.name == head_branch_name]
        if len(head_branch) != 1:
            raise RuntimeError("Head branch not found!")

        return GitHead(commit=self.commits[head_commit_sha], branch=head_branch[0])

    @time_it
    def _form_remote_heads(self) -> DictStrStr:
        """Form remote HEADs."""
        return self.inspector.git.get_remote_heads_sym_ref(self.remotes)

    @time_it
    def _form_annotated_tags(self) -> dict[str, GitTag]:
        """Post-process annotated tags."""
        tags = {}
        for sha, obj in self.objects.items():
            match obj:
                case GitTag():
                    tags[sha] = obj

        return tags

    @time_it
    def _form_lightweight_tags(self) -> dict[str, GitTagLightweight]:
        """Post-process lightweight tags."""
        lw_tags = {}
        for name, tag in self.inspector.tags_info_parsed["lightweight"].items():
            lw_tags[name] = GitTagLightweight(
                name=name,
                anchor=self.objects[tag["anchor"]],
            )

        return lw_tags

    @time_it
    def _form_objects(self) -> dict[str, GitObject]:
        """Post-process objects."""
        git_objects = self.inspector.get_raw_objects()

        # Commits can heve an empty tree object but it isn't returned by:
        # git cat-file --batch-all-objects --batch-check="%(objectname) %(objecttype)"
        # FIXME: maybe it is possible to pass a flag to git cat-file to include it?
        # Meanwhile I detect it manually.
        git_empty_tree_object_exists = False
        for obj in git_objects.values():
            match obj:
                case GitCommit():
                    tree_key = cast(str, obj.raw_data["tree"])
                    parent_keys = cast(list[str], obj.raw_data["parents"])

                    if tree_key == GIT_EMPTY_TREE_OBJECT.sha:
                        obj.tree = GIT_EMPTY_TREE_OBJECT
                        git_empty_tree_object_exists = True
                    else:
                        # I prefer for the key-lookup to fail if tree_key is missing
                        obj.tree = cast(GitTree, git_objects[tree_key])

                    try:
                        obj.parents = cast(
                            list[GitCommit], [git_objects[sha] for sha in parent_keys]
                        )
                    except KeyError:
                        # the only way to be here is if the repo is cloned with --depth
                        obj.parents = []
                case GitTree():
                    obj.children = [
                        cast(GitTree | GitBlob, git_objects[child["sha"]])
                        for child in obj.raw_data
                    ]
                case GitTag():
                    obj.anchor = git_objects[obj.raw_data["anchor"]]
                case GitBlob():
                    pass  # no need of post-processing

        # add the empty tree if it was detected
        if git_empty_tree_object_exists:
            git_objects[GIT_EMPTY_TREE_OBJECT.sha] = GIT_EMPTY_TREE_OBJECT

        for obj in git_objects.values():
            obj.is_ready = True  # type: ignore[method-assign]

        return git_objects

    @time_it
    def _form_stashes(self) -> list[GitStash]:
        """Post-process stashes."""
        return [
            GitStash(
                index=int(stash["index"]),
                title=stash["title"],
                commit=self.commits[stash["sha"]],
            )
            for stash in self.inspector.stashes_info_parsed
        ]

    @time_it
    def get_all_reachable_objects(self) -> set[str]:
        """Return all reachable objects (from all refs and reflog)."""
        cmd = "--all --reflog --objects --no-object-names"
        out = self.inspector.git.rev_list(cmd).strip().split("\n")
        return set() if len(out) == 1 and "" in out else set(out)

    @time_it
    def get_objects_reachable_from(
        self,
        init_refs: Optional[list[str]],
        max_numb_commits: Optional[int] = None,
    ) -> set[str]:
        """Return SHA of all objects that are reachable from ``init_refs``."""
        cla = " ".join(init_refs) if init_refs else "--all --reflog"
        cmd = f"{cla} --objects --no-object-names"
        if max_numb_commits is not None:
            cmd += f" -n {max_numb_commits}"

        cmd_output = self.inspector.git.rev_list(cmd).strip().split("\n")
        return set() if len(cmd_output) == 1 and "" in cmd_output else set(cmd_output)

    def filter_objects[T: GitObject](self, object_type: Type[T]) -> dict[str, T]:
        """Filter objects."""
        return {
            sha: obj
            for sha, obj in self.objects.items()
            if isinstance(obj, object_type)
        }

    @time_it
    def show(self, params: Optional[Params] = None) -> Any:
        """Show dag."""

        if params is None:
            params = Params()

        max_numb_commits = (
            None
            if params.public.max_numb_commits < 1
            else params.public.max_numb_commits
        )

        if not params.public.init_refs and max_numb_commits is None:
            objects_sha_to_include = None
        else:
            objects_sha_to_include = self.get_objects_reachable_from(
                params.public.init_refs,
                max_numb_commits,
            )

        return DagVisualizer(
            repository=self,
            params=params,
            objects_sha_to_include=objects_sha_to_include,
            in_range_commits=(
                self.inspector.git.rev_list_range(params.public.range_expr)
            ),
        ).show(params.public.xdg_open)

    def __repr__(self) -> str:
        local_branches = [b for b in self.branches if b.is_local]
        remote_branches = [b for b in self.branches if not b.is_local]

        out = (
            f"[GitRepository: {self.inspector.repository_path}]\n"
            f"  parsed trees         : {self.inspector.parse_trees}\n"
            f"  objects              : {len(self.inspector.objects_sha_kind)}\n"
            f"  commits (reachable)  : {len(self.inspector.commits_sha['reachable'])}\n"
            f"  commits (unreachable): {len(self.inspector.commits_sha['unreachable'])}\n"
            f"  tags (annotated)     : {len(self.tags)}\n"
            f"  tags (lightweight)   : {len(self.tags_lw)}\n"
            f"  branches (remote)    : {len(remote_branches)}\n"
            f"  branches (local)     : {len(local_branches)}"
        )
        for branch in local_branches:
            out += f"\n    {branch.name}"

        out += f"\n  HEAD: {self.head}"
        if self.stashes:
            out += f"\n  stashes: {len(self.stashes)}"
            for stash in self.stashes:
                out += f"\n     stash@{{{stash.index}}}: {stash.title[:40]}"

        return out
