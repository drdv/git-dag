"""Git repository parsing functionality."""

from __future__ import annotations

import logging
import multiprocessing
import re
import shlex
import subprocess
import sys
from functools import wraps
from operator import itemgetter
from time import time
from typing import Annotated, Any, Callable, Optional, ParamSpec, TypeVar, cast

import graphviz  # type: ignore[import-untyped]
from pydantic import BeforeValidator, TypeAdapter

from .constants import GIT_EMPTY_TREE_OBJECT_SHA
from .dot import DagVisualizer
from .pydantic_models import (
    DictStrStr,
    GenericTag,
    GitBlob,
    GitBranch,
    GitCommit,
    GitCommitRawDataType,
    GitObject,
    GitObjectKind,
    GitStash,
    GitTag,
    GitTagLightweight,
    GitTagRawDataType,
    GitTree,
    GitTreeRawDataType,
)

IG = itemgetter("sha", "kind")
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

# https://stackoverflow.com/q/9765453
# I always see that an empty git tree object is created when I use git rebase -i --root,
# even if I end-up squashing with a commit different from the initial one.
GIT_EMPTY_TREE_OBJECT = GitTree(
    sha=GIT_EMPTY_TREE_OBJECT_SHA,
    raw_data=[],
    no_children=True,
)


def time_it(f: Callable[P, R]) -> Callable[P, R]:
    """Return decorator for timing."""

    @wraps(f)
    def wrap(*args: P.args, **kwargs: P.kwargs) -> R:
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        LOG.info(f"{f.__qualname__:<30} took: {te-ts:0.5f} sec")
        return result

    return wrap


class GitCommand:
    """Execute useful commands for quering a git repository."""

    def __init__(self, path: str = ".") -> None:
        """Initialize instance."""
        self.path = path
        self.command_prefix = f"git -C {path}"

    def get_all_objects_sha_kind(self) -> list[str]:
        """Return the SHA and type of all git objects (in one string)."""
        return self.run(
            'cat-file --batch-all-objects --batch-check="%(objectname) %(objecttype)"'
        ).splitlines()

    def read_object_file(self, sha: str) -> list[str]:
        """Read the file associated with an object.

        Note
        -----
        This is quite slow (note that ``-p`` stands for pretty-print).

        """
        return self.run(f"cat-file -p {sha}").splitlines()

    def get_branches(self, local: bool = True) -> DictStrStr:
        """Get local/remote branches."""
        pattern = "refs/heads" if local else "refs/remotes"
        refs = {}
        for ref in self.run("show-ref").splitlines():
            if pattern in ref:
                sha, name = ref.split()
                refs["/".join(name.split("/")[2:])] = sha

        return refs

    def get_local_head(self) -> str:
        """Return local HEAD."""
        return self.run("rev-parse HEAD").strip()

    def is_detached_head(self) -> bool:
        """Detect if in detached HEAD."""
        return not self.run("branch --show-current").strip()

    def local_branch_is_tracking(self, local_branch_sha: str) -> Optional[str]:
        """Detect if a local branch is tracking a remote one."""
        try:
            cmd = f"rev-parse --symbolic-full-name {local_branch_sha}@{{upstream}}"
            return self.run(cmd).strip()
        except subprocess.CalledProcessError:
            return None

    def get_stash_info(self) -> Optional[list[str]]:
        """Return stash IDs and their associated SHAs."""
        if not self.run("stash list").strip():
            return None

        cmd = "reflog stash --no-abbrev --format='%H %gD %gs'"
        return self.run(cmd).strip().split("\n")

    def rev_list(self, args: str) -> str:
        """Return output of ``git-rev-list``.

        Note
        -----
        The ``--all`` flag doesn't imply all commits but all commits reachable from
        any reference.

        """
        return self.run(f"rev-list {args}")

    def ls_tree(self, sha: str) -> list[str]:
        """Return children of a tree object.

        Note
        -----
        The default output of ``git ls-tree SHA`` is the same as
        ``git cat-file -p SHA``. Maybe I should use the ``--object-only`` flag.

        """
        return self.run(f"ls-tree {sha}").strip().split("\n")

    def get_names_of_blobs_and_trees(self) -> DictStrStr:
        """Return actual names of blobs and trees.

        Based on https://stackoverflow.com/a/25954360

        Note
        -----
        I am not sure why, but some blobs don't have a name (it is clear why sometimes
        a tree wouldn't have a name - we always have a tree associated with a commit
        and sometimes there are no directories).

        """
        cmd_out = (
            self.run_general(
                f"{self.command_prefix} rev-list --objects --reflog --all | "
                f"{self.command_prefix} cat-file "
                "--batch-check='%(objectname) %(objecttype) %(rest)' | "
                r"grep '^[^ ]* blob\|tree' | "
                "cut -d' ' -f1,3"
            )
            .strip()
            .split("\n")
        )

        sha_name = {}
        for blob_or_tree in cmd_out:
            components = blob_or_tree.split()
            if len(components) == 2:
                sha_name[components[0]] = components[1]

        return sha_name

    def get_all_tags(self) -> dict[str, dict[str, DictStrStr]]:
        """Get all annotated and lightweight tags."""
        data = self.run(
            "for-each-ref --format "
            "'%(refname:short) %(objectname) %(object) %(type) %(tag)' refs/tags"
        ).splitlines()

        keys = [
            "refname",  # short name of lightweight tag (LWT)
            "sha",  # SHA of tag object (for annotated tags) or pointed object for LWT
            "object",  # SHA of pointed object
            "type",  # type of pointed object
            "tag",  # name of annotated tag
        ]

        all_tags: dict[str, dict[str, DictStrStr]] = {
            "annotated": {},
            "lightweight": {},
        }
        for raw_tag in [dict(zip(keys, t.split())) for t in data]:
            if "object" in raw_tag:
                # indexed by SHA
                all_tags["annotated"][raw_tag.pop("sha")] = raw_tag
            else:
                # sha is the SHA of the pointed object (rename for consistency)
                raw_tag["object"] = raw_tag.pop("sha")

                # indexed by name
                all_tags["lightweight"][raw_tag.pop("refname")] = raw_tag

        return all_tags

    def run(self, command: str) -> str:
        """Run a git command."""
        return subprocess.run(
            shlex.split(f"{self.command_prefix} {command}"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.decode("latin-1")

    def run_general(self, command: str) -> str:
        """Run a general command."""
        with subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            output, error = process.communicate()
            if error:
                raise ValueError(error)
            return output.decode("latin-1").strip()


class RegexParser:
    """Regex parser for files associated with git objects.

    Note
    -----
    All this is quite ad hoc.

    """

    SHA_PATTERN = "(?P<sha>[0-9a-f]{40})"

    @staticmethod
    def parse_object(string: str) -> DictStrStr:
        """Parse an object descriptor with format ``SHA OBJECT_TYPE``."""
        pattern = f"{RegexParser.SHA_PATTERN} (?P<kind>.+)"
        match = re.search(pattern, string)
        if match:
            return {"sha": match.group("sha"), "kind": match.group("kind")}
        raise RuntimeError(f"object string {string} not matched")

    @staticmethod
    def parse_tree(data: Optional[list[str]] = None) -> GitTreeRawDataType:
        """Parse a tree object file (read with ``cat-file -p``)."""
        # for the empty tree object, data = [""]
        if data is None or (len(data) == 1 and not data[0]):
            return []

        pattern = f"(?P<kind>tree|blob) {RegexParser.SHA_PATTERN}\t"
        output = []
        for string in data:
            match = re.search(pattern, string)
            if match:
                output.append({"sha": match.group("sha"), "kind": match.group("kind")})
            else:
                raise RuntimeError(f"tree string {string} not matched")

        return output

    @staticmethod
    def _collect_commit_info(
        commit_object_data: list[DictStrStr],
        commit_misc_info: Optional[list[str]] = None,
    ) -> GitCommitRawDataType:
        """Collect commit related info."""
        parents = []
        misc_info: list[str] = [] if commit_misc_info is None else commit_misc_info
        tree, tree_counter = None, 0
        for d in commit_object_data:
            sha, kind = IG(d)
            if kind == "tree":
                tree = sha
                tree_counter += 1
            elif kind == "parent":
                parents.append(sha)
            else:
                raise ValueError("Handle something else?")

        if tree_counter != 1:
            raise ValueError(
                f"Exactly one tree expected per commit (found {tree_counter})."
            )

        return {"tree": tree, "parents": parents, "misc": "\n".join(misc_info)}

    @staticmethod
    def parse_commit(data: list[str]) -> GitCommitRawDataType:
        """Parse a commit object file (read with ``git cat-file -p``)."""
        pattern = f"(?P<kind>tree|parent) {RegexParser.SHA_PATTERN}"
        output, misc_info = [], []
        objects_metadata = False
        for string in data:
            match = re.search(pattern, string)
            if not objects_metadata and match:
                output.append({"sha": match.group("sha"), "kind": match.group("kind")})
            else:
                objects_metadata = True
                misc_info.append(string)

        return RegexParser._collect_commit_info(output, misc_info)

    @staticmethod
    def parse_tag(data: list[str]) -> GitTagRawDataType:
        """Parse a tag object tile (read with ``git cat-file -p``)."""
        pattern = f"(?P<kind>tree|parent) {RegexParser.SHA_PATTERN}"

        labels = ["sha", "type", "refname"]
        patterns = [
            f"object {RegexParser.SHA_PATTERN}",
            "type (?P<type>.+)",
            "tag (?P<refname>.+)",
        ]

        output = {}
        for pattern, string, label in zip(patterns, data, labels):
            match = re.search(pattern, string)
            if match:
                output[label] = match.group(label)
            else:
                raise RuntimeError(f"tag string {string} not matched")

        output["misc"] = "\n".join(data[3:])
        output["object"] = output.pop("sha")
        output["tag"] = output["refname"]  # abusing things a bit
        return output

    @staticmethod
    def parse_stash_info(data: Optional[list[str]]) -> list[DictStrStr]:
        """Parse stash info as returned by :func:`GitCommand.get_stash_info`."""
        if not data:
            return []

        pattern = f"{RegexParser.SHA_PATTERN} stash@{{(?P<index>[0-9]+)}} (?P<title>.*)"
        keys = ["index", "sha", "title"]

        out = []
        for string in data:
            match = re.search(pattern, string)
            if match:
                out.append({key: match.group(key) for key in keys})
            else:
                raise ValueError("Stash string {string} not matched.")

        return out


class GitInspector:
    """Git inspector."""

    @time_it
    def __init__(self, repository_path: str = ".", parse_trees: bool = False):
        """Initialize instance (here we read most info we need from the repository).

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

        self.all_objects_sha_kind = self.git.get_all_objects_sha_kind()
        self.commits_sha = self._pre_process_commits_sha()
        self.commits_headers = self._pre_process_commits_headers()
        self.tags = self.git.get_all_tags()
        self.names_of_blobs_and_trees = self.git.get_names_of_blobs_and_trees()
        self.trees_children = self._pre_process_trees() if self.parse_trees else {}
        self.stashes = RegexParser.parse_stash_info(self.git.get_stash_info())

    def _pre_process_commits_sha(self) -> dict[str, set[str]]:
        """
        Here my logic to distinguish between reachable and unreachable commits is not
        entirely correct. It fails with stashes. Note that git handles stashes through
        the reflog and it keeps only the last stash in ``.git/refs/stash``. When I
        stash multiple times ``git fsck`` doesn't flag older stashes as unreachable
        while my logic does. FIXME: something can be improved here.
        """
        all_commits = set(
            obj.split()[0] for obj in self.all_objects_sha_kind if "commit" in obj
        )
        reachable = set(self.git.rev_list("--all").splitlines())
        unreachable = all_commits - reachable
        return {"all": all_commits, "reachable": reachable, "unreachable": unreachable}

    def _pre_process_commits_headers(self) -> dict[str, list[str]]:
        headers = {}
        # the --reflog flag includes unreachable commits as well
        for commit_string in self.git.rev_list("--all --reflog --header").split("\x00"):
            if commit_string:
                commit_sha, *commit_header = commit_string.split("\n")
                headers[commit_sha] = commit_header

        numb_not_found = len(self.commits_sha["all"]) - len(headers)
        if abs(numb_not_found) > 0:  # no need but just in case use abs
            # https://stackoverflow.com/a/12166263
            # normally, we should be able to find them using ``git fsck``
            LOG.warning(f"{numb_not_found} commits not found by --all --reflog")

        return headers

    def _pre_process_trees(self) -> dict[str, list[str]]:
        """Read object files of trees.

        Note
        -----
        FIXME: This is slow! I simply don't know how to speed-up this operation. I
        ended-up using multiprocessing but there must be a better way. In ``GitPython``
        they interact with ``git cat-file --batch`` with streams (to explore). It seems
        strange to be able to read all object files for commits at once (using
        ``git rev-list``) and to not be able to do it for trees (I must be missing
        something).

        """
        all_sha = [obj.split()[0] for obj in self.all_objects_sha_kind if "tree" in obj]
        with multiprocessing.Pool() as pool:
            object_file_content = pool.map(
                self.git.ls_tree,
                all_sha,
            )
        return dict(zip(all_sha, object_file_content))

    def _get_object_info(self, sha: str, kind: str) -> GitObject:
        match kind:
            case GitObjectKind.blob:
                return GitBlob(sha=sha)
            case GitObjectKind.commit:
                if sha in self.commits_headers:
                    commit_object_file_data = self.commits_headers[sha]
                else:
                    commit_object_file_data = self.git.read_object_file(sha)  # slow
                    LOG.warning(f"[commit] manually doing git cat-file -p {sha}")

                return GitCommit(
                    sha=sha,
                    reachable=sha in self.commits_sha["reachable"],
                    raw_data=RegexParser.parse_commit(commit_object_file_data),
                )
            case GitObjectKind.tag:
                # tag = RegexParser.parse_tag(self.git.read_object_file(sha))  # slower
                tag = self.tags["annotated"][sha]
                return GitTag(
                    sha=sha,
                    name=tag["refname"],
                    raw_data={"sha": tag["object"], "misc": ""},
                )
            case GitObjectKind.tree:
                return GitTree(
                    sha=sha,
                    raw_data=RegexParser.parse_tree(self.trees_children.get(sha)),
                )
            case _:
                raise RuntimeError("Leaking objects!")

    @time_it
    def get_raw_objects(self) -> dict[str, GitObject]:
        """Return all raw objects in a git repository.

        Note
        -----
        The objects are "raw", meaning that they are not fully initialized. For example,
        even though all necessary data is available in :func:`GitTree.raw_data`,
        :arg:`GitTree._children` is still not initialized (and the :class:`GitTree`
        instances are not fully functional). The remaining post-processing is performed
        in the ``GitRepository.post_process_inspector_data`` methods (as all instances
        need to be formed first). The :func:`GitTree.is_ready` property indicates
        whether an instance has been fully initialized.

        """

        def git_entity_before_validator(obj_descriptor: str) -> GitObject:
            """Transform/validate data.

            Note
            -----
            ``self`` is used from the closure.

            """
            return self._get_object_info(*IG(RegexParser.parse_object(obj_descriptor)))

        GitObjectAnnotated = Annotated[
            GitObject,
            BeforeValidator(git_entity_before_validator),
        ]

        return {
            obj.sha: obj
            for obj in TypeAdapter(list[GitObjectAnnotated]).validate_python(
                self.all_objects_sha_kind
            )
        }


def filter_objects(
    git_objects: dict[str, GitObject],
    object_type: Any = GitCommit | GitTag,
) -> dict[str, GitObject]:
    """Filter objects - a convenience function."""
    return {
        sha: obj for sha, obj in git_objects.items() if isinstance(obj, object_type)
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
        repository_path: str = ".",
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
        self.inspector = GitInspector(repository_path, parse_trees)
        self.post_process_inspector_data()

    @time_it
    def post_process_inspector_data(self) -> None:
        """Post-process inspector data (see :func:`GitInspector.get_raw_objects`)."""
        self.objects: dict[str, GitObject] = self._form_objects()
        self.head: GitCommit = self._form_head()
        self.tags: GenericTag = self._form_tags()
        self.branches: list[GitBranch] = self._form_branches()
        self.stashes: list[GitStash] = self._form_stashes()

    @time_it
    def _form_head(self) -> GitCommit:
        """Post-process HEAD.

        Note
        -----
        Set HEAD to point to a commit. In reality, HEAD would point to a commit SHA only
        in detached HEAD, otherwise it points to a branch reference. I don't make this
        distinction here.

        """
        try:
            head = self.inspector.git.get_local_head()
        except subprocess.CalledProcessError as e:
            LOG.error("Head is not defined (probably the repository is empty)")
            LOG.error(f"  COMMAND: {' '.join(e.cmd)}")
            LOG.error(f"   OUTPUT: {e.output}")
            # LOG.error(f"EXIT CODE: {e.returncode}")
            sys.exit(1)
        return cast(GitCommit, self.objects[head])

    @time_it
    def _form_branches(self) -> list[GitBranch]:
        """Post-process branches."""
        branches: list[GitBranch] = []

        for branch_name, sha in self.inspector.git.get_branches().items():
            branches.append(
                GitBranch(
                    name=branch_name,
                    commit=cast(GitCommit, self.objects[sha]),
                    is_local=True,
                    tracking=self.inspector.git.local_branch_is_tracking(branch_name),
                )
            )

        for branch_name, sha in self.inspector.git.get_branches(local=False).items():
            branches.append(
                GitBranch(
                    name=branch_name,
                    commit=cast(GitCommit, self.objects[sha]),
                )
            )

        return branches

    @time_it
    def _form_tags(self) -> GenericTag:
        """Post-process tags."""
        tags_raw = self.inspector.tags

        ats = {sha: cast(GitTag, self.objects[sha]) for sha in tags_raw["annotated"]}
        lwts = {}
        for name, tag in tags_raw["lightweight"].items():
            lwts[name] = GitTagLightweight(
                name=name,
                anchor=self.objects[tag["object"]],
            )

        return {"annotated": ats, "lightweight": lwts}

    @time_it
    def _form_objects(self) -> dict[str, GitObject]:
        """Post-process objects."""
        git_objects = self.inspector.get_raw_objects()

        # Commits can heve an empty tree object but it isn't returned by:
        # git cat-file --batch-all-objects --batch-check="%(objectname) %(objecttype)"
        # FIXME: maybe I have to pass a flag to git cat-file to include it.
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

                    obj.parents = cast(
                        list[GitCommit], [git_objects[sha] for sha in parent_keys]
                    )
                case GitTree():
                    obj.children = [
                        cast(GitTree | GitBlob, git_objects[child["sha"]])
                        for child in obj.raw_data
                    ]
                case GitTag():
                    obj.anchor = git_objects[obj.raw_data["sha"]]
                case GitBlob():
                    pass  # no need of post-processing

        # setting is_ready here is a bit sloppy (but let's have feith)
        for obj in git_objects.values():
            obj.is_ready = True

        # add the empty tree if it was detected
        if git_empty_tree_object_exists:
            git_objects[GIT_EMPTY_TREE_OBJECT.sha] = GIT_EMPTY_TREE_OBJECT
        return git_objects

    @time_it
    def _form_stashes(self) -> list[GitStash]:
        """Post-process stashes."""
        return [
            GitStash(
                index=int(stash["index"]),
                title=stash["title"],
                commit=cast(GitCommit, self.objects[stash["sha"]]),
            )
            for stash in self.inspector.stashes
        ]

    @time_it
    def get_objects_reachable_from(
        self,
        starting_objects: Optional[list[str]],
        max_numb_commits: Optional[int] = None,
    ) -> set[str]:
        """Return SHA of all objects that are reachable from ``starting_objects``."""
        cla = " ".join(starting_objects) if starting_objects else "--all --reflog"
        cmd = f"{cla} --objects --no-object-names"
        if max_numb_commits is not None:
            cmd += f" -n {max_numb_commits}"
        return set(self.inspector.git.rev_list(cmd).strip().split("\n"))

    @time_it
    def show(
        self,
        xdg_open: bool = False,
        starting_objects: Optional[list[str]] = None,
        max_numb_commits: Optional[int] = 1000,
        **kwargs: Any,
    ) -> Optional[graphviz.Digraph]:
        """Show dag.

        Parameters
        -----------
        xdg_open
            Whether to open the graph using ``xdg-open``.
        starting_objects
            A list of SHA of object (commits, tags, trees, blobs) that represents a
            limitation from where to display the DAG (there are no limitations when the
            list is empty).
        max_numb_commits
            Max number of commit objects to display.

        """
        if not starting_objects and max_numb_commits is None:
            objects_sha_to_include = None
        else:
            objects_sha_to_include = self.get_objects_reachable_from(
                starting_objects,
                max_numb_commits,
            )

        return DagVisualizer(
            self,
            objects_sha_to_include=objects_sha_to_include,
            **kwargs,
        ).show(xdg_open)

    def __repr__(self) -> str:
        local_branches = [b for b in self.branches if b.is_local]
        remote_branches = [b for b in self.branches if not b.is_local]

        out = (
            f"[GitRepository: {self.inspector.repository_path}]\n"
            f"  parsed trees         : {self.inspector.parse_trees}\n"
            f"  objects              : {len(self.inspector.all_objects_sha_kind)}\n"
            f"  commits (reachable)  : {len(self.inspector.commits_sha['reachable'])}\n"
            f"  commits (unreachable): {len(self.inspector.commits_sha['unreachable'])}\n"
            f"  tags (annotated)     : {len(self.tags['annotated'])}\n"
            f"  tags (lightweight)   : {len(self.tags['lightweight'])}\n"
            f"  branches (remote)    : {len(remote_branches)}\n"
            f"  branches (local)     : {len(local_branches)}"
        )
        for branch in local_branches:
            out += f"\n    {branch.name}"

        out += f"\n  HEAD: {self.head.sha[:8]}"
        for branch in [b for b in self.branches if b.commit == self.head]:
            out += f"\n    {branch.name}"

        if self.stashes:
            out += f"\n  stashes: {len(self.stashes)}"
            for stash in self.stashes:
                out += f"\n     stash@{{{stash.index}}}: {stash.title[:40]}"

        return out
