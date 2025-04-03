"""Git commands related functionality.

Note
-----
The are two kinds of commands: such that simply read data from the repository, and such
that modify the repository (the latter is used only in unit tests).

"""

import logging
import re
import shlex
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any, Literal, Optional

from git_dag.constants import CMD_TAGS_INFO, SHA_PATTERN, TAG_FORMAT_FIELDS, DictStrStr
from git_dag.exceptions import CalledProcessCustomError
from git_dag.parameters import Params, ParamsPublic, context_ignore_config_file
from git_dag.utils import escape_decode

logging.basicConfig(level=logging.WARNING)
LOG = logging.getLogger(__name__)


class GitCommandBase:
    """Base class for git commands."""

    def __init__(self, path: str | Path = ".") -> None:
        """Initialize instance."""
        self.path = path
        self.command_prefix = f"git -C {path}"

    def _run(
        self,
        command: str,
        env: Optional[DictStrStr] = None,
        encoding: str = "utf-8",
    ) -> str:
        """Run a git command."""
        try:
            return subprocess.run(
                shlex.split(f"{self.command_prefix} {command}"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                env=env,
            ).stdout.decode(encoding, errors="replace")
        except subprocess.CalledProcessError as e:
            raise CalledProcessCustomError(e) from e

    @staticmethod
    def run_general(
        command: str,
        env: Optional[DictStrStr] = None,
        encoding: str = "utf-8",
        expected_stderr: Optional[str] = None,
    ) -> str:
        """Run a general command."""
        with subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        ) as process:
            output, error = process.communicate()
            # some git commands output messages to stderr even when there is no error
            if error:
                if expected_stderr is None:
                    raise RuntimeError(error)
                if not expected_stderr in error.decode("utf-8"):
                    raise RuntimeError(error)
            return output.decode(encoding, errors="replace").strip()


class GitCommandMutate(GitCommandBase):
    """Git commands that create/modify a repository.

    Warning
    --------
    The functionality in this class is rudimentary and is used only to create a
    repository for the tests.

    """

    def __init__(
        self,
        path: str | Path = ".",  # assumed to exist
        author: str = "First Last <first.last@mail.com>",
        committer: str = "Nom Prenom <nom.prenom@mail.com>",
        date: Optional[str] = None,
    ) -> None:
        """Initialize instance."""
        self.author = author
        self.committer = committer
        self.date = date
        self.env = self.get_env()

        super().__init__(path)

    def init(self, branch: str = "main") -> None:
        """Initialise a git repository."""
        self._run(f"init -b {branch}")

    def get_env(self) -> DictStrStr:
        """Return environment with author and committer to pass to commands."""
        env = {}
        match = re.search("(?P<name>.*) (?P<email><.*>)", self.author)
        if match:
            env["GIT_AUTHOR_NAME"] = match.group("name")
            env["GIT_AUTHOR_EMAIL"] = match.group("email")
        else:
            raise ValueError("Author not matched.")  # pragma: no cover

        match = re.search("(?P<name>.*) (?P<email><.*>)", self.committer)
        if match:
            env["GIT_COMMITTER_NAME"] = match.group("name")
            env["GIT_COMMITTER_EMAIL"] = match.group("email")
        else:
            raise ValueError("Committer not matched.")  # pragma: no cover

        if self.date is not None:
            env["GIT_AUTHOR_DATE"] = self.date
            env["GIT_COMMITTER_DATE"] = self.date

        return env

    def add(self, files: DictStrStr) -> None:
        """Add files to the index.

        ``files`` specifies files to be added to the index (its format is ``{'filename':
        'file contents', ...}``). Names of files should not include the path to the
        repository (it is prepended).

        """
        for filename, contents in files.items():
            with open(Path(self.path) / filename, "w", encoding="utf-8") as h:
                h.write(contents)
            self._run(f"add {filename}")

    def cm(self, messages: str | list[str], files: Optional[DictStrStr] = None) -> None:
        """Add commit(s).

        If ``files`` is not specified an empty commit is created.

        Note
        -----
        When ``messages`` is a list, multiple empty commits are created (``files``
        cannot be specified).

        """
        if isinstance(messages, str):
            if files is not None:
                self.add(files)

            self._run(f'commit --allow-empty -m "{messages}"', env=self.env)
        elif isinstance(messages, (list, tuple)):
            if files is not None:
                raise ValueError("Cannot add files with multiple commits.")
            for msg in messages:
                self._run(f'commit --allow-empty -m "{msg}"', env=self.env)
        else:
            raise ValueError("Unsupported message type.")

    def br(
        self,
        branch: str,
        create: bool = False,
        orphan: bool = False,
        delete: bool = False,
    ) -> None:
        """Create/switch/delete branch."""
        if create and delete:
            raise ValueError("At most one of create and delete can be True.")

        if delete:
            self._run(f"branch -D {branch}")
        else:
            create_switch = ""
            if create:
                create_switch = "--orphan" if orphan else "-c"

            self._run(f"switch {create_switch} {branch}")

    def mg(
        self,
        branch: str,
        message: str = "m",
        strategy: str = "theirs",
        unrelated: bool = False,
    ) -> None:
        """Merge."""
        if unrelated:
            flags = "--allow-unrelated-histories"
        else:
            flags = f"-X {strategy}"
        self._run(f'merge {flags} {branch} -m "{message}"', env=self.env)

    def mg_multiple(self, branches: list[str], message: str = "m") -> None:
        """Merge multiple (possibly orphan) branches without conflicts."""
        try:
            self._run(
                f'merge --allow-unrelated-histories {' '.join(branches)} -m "{message}"',
                env=self.env,
            )
        except CalledProcessCustomError as e:
            if (
                "Automatic merge failed; fix conflicts and then commit the result"
                in e.output.decode("utf-8")
            ):
                self.cm(message)
            else:
                raise

    def stash(
        self,
        files: DictStrStr,
        title: Optional[str] = None,
        sleep: bool = True,
    ) -> None:
        """Stash.

        Note
        -----
        ``files`` specifies files to be modified before we stash (its format is
        ``{'filename': 'file contents', ...}``. At least one file should be modified in
        order for ``git stash`` to be meaningful.

        Warning
        --------
        At the end of this method we sleep for 1 second otherwise stashes created very
        fast one after another might share the "index commit" (or might not, depending
        on delay). See https://github.com/drdv/git-dag/issues/84.

        """
        for filename, contents in files.items():
            with open(Path(self.path) / filename, "w", encoding="utf-8") as h:
                h.write(contents)

        if title is None:
            self._run("stash", env=self.env)
        else:
            self._run(f'stash push -m "{title}"', env=self.env)

        if sleep:
            time.sleep(1)  # see Warning in docstring

    def tag(
        self,
        name: str,
        message: Optional[str] = None,
        ref: Optional[str] = None,
        delete: bool = False,
    ) -> None:
        """Create/delete annotated or lightweight tag.

        Note
        -----
        When a message is specified, an annotated tag is created.

        """
        if message is not None and delete:
            raise ValueError("When delete is True, message should be None.")

        if delete:
            self._run(f"tag -d {name}")
        else:
            ref_str = ref if ref is not None else ""
            message_str = f'-m "{message}"' if message is not None else ""
            self._run(f"tag {name} {ref_str} {message_str}", env=self.env)

    def note(self, msg: str, ref: Optional[str] = None) -> None:
        """Add a git note to a given ref (e.g., hash, branch name)."""
        self._run(
            f'notes add -m "{msg}" {ref if ref is not None else ""}',
            env=self.env,
        )

    def config(self, option: str) -> None:
        """Set a gonfig option."""
        self._run(f"config {option}")

    @classmethod
    def clone_local_depth_1(cls, src_dir: str, target_dir: str) -> None:
        """Clone a local repository with ``--depth 1`` flag.

        Note
        -----
        This command doesn't mutate a repository but appears under
        :class:`GitCommandMutate` as it is meant to be used only in the unit tests and
        docs examples.

        """
        # note that git clone sends to stderr (so I suppress it using -q)
        cls.run_general(f"git clone -q --depth 1 file://{src_dir} {target_dir}")


class GitCommand(GitCommandBase):
    """Git commands that query the repository to process (without modifications)."""

    def get_objects_sha_kind(self) -> list[str]:
        """Return the SHA and type of all git objects (in one string).

        Note
        -----
        Unreachable commits (and deleted annotated tags) are included as well.

        Note
        -----
        The ``--unordered`` flag is used because ordering by SHA is not necessary.

        """
        CMD = (
            "cat-file --batch-all-objects --unordered "
            '--batch-check="%(objectname) %(objecttype)"'
        )
        objects = self._run(CMD).strip().split("\n")

        if len(objects) == 1 and not objects[0]:
            LOG.warning("No objects")
            return []

        return objects

    def read_object_file(self, sha: str) -> list[str]:
        """Read the file associated with an object.

        Note
        -----
        It is quite slow if all objects are to be read like this (``-p`` stands for
        pretty-print).

        """
        return self._run(f"cat-file -p {sha}").strip().split("\n")

    def get_remotes(self) -> list[str]:
        """Return list of remotes."""
        cmd_output = self._run("remote").strip().split("\n")
        if len(cmd_output) == 1 and "" in cmd_output:
            return []
        return cmd_output

    def get_fsck_unreachable_commits(self) -> list[str]:
        """Return unreachable commits not in the reflog."""
        cmd_output = (
            self.run_general(
                f"{self.command_prefix} fsck --unreachable --no-reflog 2>/dev/null | "
                "grep commit | cut -d' ' -f3"
            )
            .strip()
            .split("\n")
        )

        return [] if len(cmd_output) == 1 and "" in cmd_output else cmd_output

    def get_remote_heads_sym_ref(self, remotes: list[str]) -> DictStrStr:
        """Return symbolic references of remote heads."""
        symb_refs = {}
        for remote in remotes:
            cmd = f"symbolic-ref refs/remotes/{remote}/HEAD"
            try:
                cmd_output = self._run(cmd).strip().split("\n")
                # drop refs/remotes
                symb_refs[f"{remote}/HEAD"] = "/".join(cmd_output[0].split("/")[2:])
            except CalledProcessCustomError:
                LOG.warning(f"HEAD not defined for {remote}.")
        return symb_refs

    def get_prs_heads(self) -> DictStrStr:
        """Return heads of pull-requests."""
        try:
            cmd_output = self._run("ls-remote").strip().split("\n")
        except CalledProcessCustomError as e:
            LOG.warning(e)
            return {}

        out = {}
        for line in cmd_output:
            match = re.search(f"{SHA_PATTERN}\trefs/pull/(?P<pr_id>\\d+)/head", line)
            if match:
                out[match.group("pr_id")] = match.group("sha")

        return out

    def get_branches(self, remotes: list[str]) -> dict[str, DictStrStr]:
        """Get local/remote branches (while excluding remote HEADs)."""
        refs: dict[str, DictStrStr] = {"local": {}, "remote": {}}

        try:
            cmd_output = self._run("show-ref").strip().split("\n")
        except CalledProcessCustomError:
            LOG.warning("No refs")
            return refs

        for ref in cmd_output:
            sha, name = ref.split()
            if "refs/heads" in ref:
                refs["local"]["/".join(name.split("/")[2:])] = sha

            if "refs/remotes" in ref:
                # skip remote HEADs (handled in  GitCommand.get_remote_heads_sym_ref)
                if name not in [f"refs/remotes/{remote}/HEAD" for remote in remotes]:
                    refs["remote"]["/".join(name.split("/")[2:])] = sha

        return refs

    def get_local_head_commit_sha(self) -> str:
        """Return SHA of the commit pointed to by local HEAD."""
        return self._run("rev-parse HEAD").strip()

    def rev_parse_descriptors(
        self, descriptors: Optional[list[str]]
    ) -> Optional[list[str]]:
        """Return a set of SHA corresponding to a list of descriptors.

        Note
        -----
        A descriptor can be e.g., HEAD, main, a truncated SHA, etc.

        """
        if descriptors is None:
            return None

        args = " ".join([f"'{descriptor}'" for descriptor in descriptors])
        try:
            return self._run(f"rev-parse {args}").strip().split("\n")
        except CalledProcessCustomError as e:
            LOG.warning(e)

        return None

    def rev_list_range(self, range_expr: Optional[str]) -> Optional[list[str]]:
        """Return set of commit SHA in the range defined by ``range_expr``.

        Note
        -----
        For example ``range_expr`` could be ``main..feature``.

        """
        if range_expr is None:
            return None

        try:
            out = self._run(f"rev-list {range_expr}").strip().split("\n")
            return None if len(out) == 1 and not out[0] else out
        except CalledProcessCustomError as e:
            LOG.warning(e)

        return None

    def get_local_head_branch(self) -> Optional[str]:
        """Return name of branch pointed to by HEAD."""
        branch_name = self._run("branch --show-current").strip()
        return branch_name if branch_name else None

    def local_branch_is_tracking(self, local_branch_sha: str) -> Optional[str]:
        """Detect if a local branch is tracking a remote one."""
        try:
            cmd = f"rev-parse --symbolic-full-name {local_branch_sha}@{{upstream}}"
            return self._run(cmd).strip()
        except CalledProcessCustomError:
            return None

    def get_stash_info(self) -> Optional[list[str]]:
        """Return stash IDs and their associated SHAs."""
        if not self._run("stash list").strip():
            return None

        cmd = "reflog stash --no-abbrev --format='%H %gD %gs'"
        return self._run(cmd).strip().split("\n")

    def rev_list(self, args: str) -> str:
        """Return output of ``git-rev-list``.

        Note
        -----
        The ``--all`` flag doesn't imply all commits but all commits reachable from
        any reference.

        """
        return self._run(f"rev-list {args}")

    def ls_tree(self, sha: str) -> list[str]:
        """Return children of a tree object.

        Note
        -----
        The default output of ``git ls-tree SHA`` is the same as
        ``git cat-file -p SHA``. Maybe I should use the ``--object-only`` flag.

        """
        return self._run(f"ls-tree {sha}").strip().split("\n")

    def get_blobs_and_trees_names(self, trees_info: dict[str, list[str]]) -> DictStrStr:
        """Return actual names of blobs and trees.

        Note
        -----
        Based on https://stackoverflow.com/a/25954360.

        Note
        -----
        A tree object might have no name -- this happens when a repository has no
        directories (note that a commit always has an associated tree object) or when a
        tree object is created manually (without a commit). Sometimes a blob has no
        name, e.g., when it are created manually (``git hash-object -w``) or it is not
        referenced by a tree object.

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

        # may add names of standalone trees/objects
        for tree_info in trees_info.values():
            for tree_or_blob in tree_info:
                if tree_or_blob:  # protect against the empty tree object
                    sha, name = tree_or_blob.split(" ")[-1].split("\t")
                    sha_name[sha] = name

        return sha_name

    def get_tags_info_parsed(self) -> dict[str, dict[str, DictStrStr]]:
        """Return parsed info for all annotated and lightweight tags.

        Note
        -----
        The ``git for-each-ref ...`` command (see
        :obj:`~git_dag.constants.CMD_TAGS_INFO`) used in this function doesn't return
        deleted annotated tags. They are handled separately in
        :func:`GitInspector._get_objects_info_parsed` (note that their SHA is included
        in the output of :func:`GitCommand.get_objects_sha_kind`).

        Note
        -----
        The ``--python`` flag (see :obj:`~git_dag.constants.CMD_TAGS_INFO`) forms
        groups delimited by ``'...'`` which makes them easy to split and parse. On the
        flip-side, we have to decode escapes of escapes while preserving unicode
        characters. Note that if the message contains ``\\n``-s (i.e., one backlash),
        they would appear as ``\\\\\\\\n`` (four backlashes).

        """
        tags: dict[str, dict[str, DictStrStr]] = {"annotated": {}, "lightweight": {}}
        for raw_tag in [
            dict(zip(TAG_FORMAT_FIELDS, re.findall(r"'((?:[^'\\]|\\.)*)'", t)))
            # splitlines() cannot be used here because it splits on CRLF characters
            for t in self._run(CMD_TAGS_INFO).strip().split("\n")
            if t  # when there are no tags "".split("\n") results in [""]
        ]:
            if raw_tag["object"]:
                raw_tag["anchor"] = raw_tag.pop("object")
                raw_tag["message"] = escape_decode(raw_tag["contents"])
                tags["annotated"][raw_tag.pop("sha")] = raw_tag  # indexed by SHA
            else:
                raw_tag["anchor"] = raw_tag.pop("sha")
                tags["lightweight"][raw_tag.pop("refname")] = raw_tag  # indexed by name

        return tags

    def get_notes_dag_root(self) -> Optional[DictStrStr]:
        """Return the root node of the DAG for git notes."""
        notes_ref = self._run("notes get-ref").strip().split("\n")[0]
        try:
            notes_dag_root = self._run(f"rev-list {notes_ref}").strip().split("\n")[0]
        except CalledProcessCustomError:
            return None  # there are no git notes
        return {"ref": notes_ref, "root": notes_dag_root}


class TestGitRepository:
    """Create test git repository."""

    @classmethod
    def create(
        cls,
        label: Literal["default", "default-with-notes", "empty"],
        repo_path: Path | str,  # assumed to exist
        tar_file_name: Optional[Path | str] = None,
        **kwargs: dict[str, Any],
    ) -> GitCommandMutate:
        """Git repository creation displatch."""
        match label:
            case "default":
                git = cls.repository_default(repo_path)
            case "default-with-notes":
                git = cls.repository_default_with_notes(repo_path)
            case "empty":
                git = cls.repository_empty(repo_path, **kwargs)
            case _:
                raise ValueError(f"Unknown repository label: {label}")

        if tar_file_name is not None:
            cls.tar(repo_path, tar_file_name)

        return git

    @staticmethod
    def tar(src_path: Path | str, tar_file_name: Path | str) -> None:
        """Tar a git repository."""
        with tarfile.open(tar_file_name, "w:gz") as h:
            h.add(src_path, arcname=".")

    @staticmethod
    def untar(tar_file_name: Path | str, extract_path: Path | str) -> None:
        """Untar a git repository."""
        with tarfile.open(tar_file_name, "r:gz") as tar:
            tar.extractall(path=extract_path, filter="fully_trusted")

    @staticmethod
    def repository_empty(
        path: Path | str,
        files: Optional[DictStrStr] = None,
    ) -> GitCommandMutate:
        """Empty repository (possibly with files added to the index)."""
        git = GitCommandMutate(path)
        git.init()

        if files is not None:
            git.add(files)

        return git

    @staticmethod
    def repository_default(path: Path | str) -> GitCommandMutate:
        """Default repository."""
        git = GitCommandMutate(path, date="01/01/25 09:00 +0100")
        git.init()
        git.cm("A\n\nBody:\n * First line\n * Second line\n * Third line")
        git.br("topic", create=True)
        git.cm("D")
        git.br("feature", create=True)
        git.cm("F")
        git.cm("G", files={"file": "G"})
        git.br("topic")
        git.cm("E", files={"file": "E"})
        git.mg("feature")
        git.tag("0.1", "Summary\n\nBody:\n * First line\n * Second line\n * Third line")
        git.tag("0.2", "Summary\n\nBody:\n * First line\n * Second line\n * Third line")
        git.cm("H")
        git.br("main")
        git.cm(["B", "C"])
        git.tag("0.7", "tag 0.7")
        git.tag("0.7r", "ref to tag 0.7", ref="0.7")
        git.tag("0.7rr", "ref to ref to tag 0.7", ref="0.7r")
        git.br("feature", delete=True)
        git.br("topic")
        git.tag("0.3", "T1")
        git.tag("0.4")
        git.tag("0.5")
        git.tag("0.1", delete=True)
        git.tag("0.4", delete=True)
        git.br("bugfix", create=True)
        git.cm("I")
        git.tag(
            # pylint: disable=invalid-character-sub
            "0.6",
            "Test:                    €.",
        )
        git.cm("J")
        git.br("topic")
        git.br("bugfix", delete=True)
        git.stash({"file": "stash:first"})
        git.stash({"file": "stash:second"}, title="second")
        git.stash({"file": "stash:third"}, title="third")

        # add two standalone blobs and a standalone tree
        prefix = git.command_prefix
        git.run_general(f"echo 'test content 1' | {prefix} hash-object -w --stdin")
        git.run_general(f"echo 'test content 2' | {prefix} hash-object -w --stdin")

        sha = "74689c87fb53b6d666de95efea667d99ba2fa52a"
        git.run_general(f"{prefix} update-index --add --cacheinfo 100644 {sha} tmp.txt")
        git.run_general(f"{prefix} write-tree")

        git.config("gc.auto 0")

        return git

    @classmethod
    def repository_default_with_notes(cls, path: Path | str) -> GitCommandMutate:
        """Default repository with git notes."""
        git = cls.repository_default(path)

        git.note("Add a note")
        git.note("Add a another note", "main")

        return git


def create_test_repo_and_reference_dot_file(
    path: Path | str = "test/resources/default_repo",
) -> None:
    """Create a git repository and its associated DOT file (to use as reference).

    Note
    -----
    This is meant to be used only when the test resources should be changed. To execute:
    ``cd src/git_dag && python git_commands.py``.

    """
    # pylint: disable=import-outside-toplevel
    import shutil

    from git_dag.git_repository import GitRepository  # pylint: disable=cyclic-import

    path = Path(path)
    path.mkdir()
    TestGitRepository.create("default", path)

    repo = GitRepository(path, parse_trees=True)
    with context_ignore_config_file():
        params = Params(
            public=ParamsPublic(
                show_unreachable_commits=True,
                show_local_branches=True,
                show_remote_branches=True,
                show_trees=True,
                show_trees_standalone=True,
                show_blobs=True,
                show_blobs_standalone=True,
                show_tags=True,
                show_deleted_tags=True,
                show_stash=True,
                show_head=True,
                max_numb_commits=0,
                annotations=[
                    ["4499ee63", "just a tooltip"],
                    ["0.3", "additional info"],
                    ["0.5"],  # this will not be displayed
                    ["HEAD"],
                    ["main^", "a clarification"],
                ],
                format="gv",
                file=path / "../default_repo.gv",
            )
        )
    repo.show(params)

    # TestGitRepository.tar(path, path / "../default_repo.tar.gz")

    with open(path / "../default_repo.repr", "w", encoding="utf-8") as h:
        h.write(repr(repo))

    shutil.rmtree(path)


if __name__ == "__main__":  # pragma: no cover
    create_test_repo_and_reference_dot_file()
