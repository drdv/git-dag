"""Git commands related functionality.

Note
-----
The are two kinds of comments: such that simply read data from the repository, and such
that modify the repository.

"""

import logging
import re
import shlex
import subprocess
import tarfile
from pathlib import Path
from typing import Literal, Optional

from git_dag.constants import CMD_TAGS_INFO, TAG_FORMAT_FIELDS
from git_dag.exceptions import EmptyGitRepository
from git_dag.pydantic_models import DictStrStr
from git_dag.utils import escape_decode

logging.basicConfig(level=logging.INFO)
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
        env: Optional[dict[str, str]] = None,
        encoding: str = "utf-8",
    ) -> str:
        """Run a git command."""
        return subprocess.run(
            shlex.split(f"{self.command_prefix} {command}"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env=env,
        ).stdout.decode(encoding, errors="replace")

    @staticmethod
    def run_general(
        command: str,
        env: Optional[dict[str, str]] = None,
        encoding: str = "utf-8",
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
            if error:
                raise ValueError(error)
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
    ) -> None:
        """Initialize instance."""
        self.author = author
        self.committer = committer
        self.env = self._get_env()

        super().__init__(path)

    def init(self) -> None:
        """Initialise a git repository."""
        self._run("init")

    def _get_env(self) -> dict[str, str]:
        """Return environment with author and committer to pass to commands."""
        env = {}
        match = re.search("(?P<name>.*) (?P<email><.*>)", self.author)
        if match:
            env["GIT_AUTHOR_NAME"] = match.group("name")
            env["GIT_AUTHOR_EMAIL"] = match.group("email")
        else:
            raise ValueError("Author not matched.")

        match = re.search("(?P<name>.*) (?P<email><.*>)", self.committer)
        if match:
            env["GIT_COMMITTER_NAME"] = match.group("name")
            env["GIT_COMMITTER_EMAIL"] = match.group("email")
        else:
            raise ValueError("Committer not matched.")

        return env

    def cm(
        self, messages: str | list[str], files: Optional[dict[str, str]] = None
    ) -> None:
        """Add commit(s).

        ``files`` specifies files to be added to the index before committing (its format
        is ``{'filename': 'file contents', ...}``, if not specified an empty commit is
        created). Names of files should not include the path to the repository (it is
        prepended).

        Note
        -----
        When ``messages`` is a list, multiple empty commits are created (``files``
        cannot be specified).

        """
        if isinstance(messages, str):
            if files is not None:
                for filename, contents in files.items():
                    with open(Path(self.path) / filename, "w", encoding="utf-8") as h:
                        h.write(contents)
                    self._run(f"add {filename}")

            self._run(f'commit --allow-empty -m "{messages}"', env=self.env)
        elif isinstance(messages, (list, tuple)):
            if files is not None:
                raise ValueError("Cannot add files with multiple commits.")
            for msg in messages:
                self._run(f'commit --allow-empty -m "{msg}"', env=self.env)
        else:
            raise ValueError("Unsupported message type.")

    def br(self, branch: str, create: bool = False, delete: bool = False) -> None:
        """Create/switch/delete branch."""
        if create and delete:
            raise ValueError("At most one of create and delete can be True.")

        if delete:
            self._run(f"branch -D {branch}")
        else:
            self._run(f"switch {'-c' if create else ''} {branch}")

    def mg(self, branch: str, message: str = "m", strategy: str = "theirs") -> None:
        """Merge."""
        self._run(f'merge -X {strategy} {branch} -m "{message}"', env=self.env)

    def stash(self, files: dict[str, str], title: Optional[str] = None) -> None:
        """Stash.

        ``files`` specifies files to be modified before we stash (its format is
        ``{'filename': 'file contents', ...}``. At least one file should be modified in
        order for ``git stash`` to be meaningful.

        """
        for filename, contents in files.items():
            with open(Path(self.path) / filename, "w", encoding="utf-8") as h:
                h.write(contents)

        if title is None:
            self._run("stash", env=self.env)
        else:
            self._run(f'stash push -m "{title}"', env=self.env)

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

    def config(self, option: str) -> None:
        """Set a gonfig option."""
        self._run(f"config {option}")

    @classmethod
    def clone_local_depth_1(cls, src_dir: str, target_dir: str) -> None:
        """Clone a local repository with ``--depth 1`` flag.

        Note
        -----
        This command doesn't mutate a repository but appears under
        :class:`GitCommandMutate` as it is meant to be used only in the unit tests.

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
            raise EmptyGitRepository("No objects, probably the repository is empty.")

        return objects

    def read_object_file(self, sha: str) -> list[str]:
        """Read the file associated with an object.

        Note
        -----
        It is quite slow if all objects are to be read like this (``-p`` stands for
        pretty-print).

        """
        return self._run(f"cat-file -p {sha}").strip().split("\n")

    def get_branches(self) -> dict[str, DictStrStr]:
        """Get local/remote branches."""
        refs: dict[str, DictStrStr] = {"local": {}, "remote": {}}

        try:
            cmd_output = self._run("show-ref").strip().split("\n")
        except subprocess.CalledProcessError as error:
            LOG.warning(error)
            return refs

        for ref in cmd_output:
            sha, name = ref.split()
            if "refs/heads" in ref:
                refs["local"]["/".join(name.split("/")[2:])] = sha

            if "refs/remotes" in ref:
                refs["remote"]["/".join(name.split("/")[2:])] = sha

        return refs

    def get_local_head(self) -> str:
        """Return local HEAD."""
        return self._run("rev-parse HEAD").strip()

    def is_detached_head(self) -> bool:
        """Check if the repository is in a detached HEAD state."""
        return not self._run("branch --show-current").strip()

    def local_branch_is_tracking(self, local_branch_sha: str) -> Optional[str]:
        """Detect if a local branch is tracking a remote one."""
        try:
            cmd = f"rev-parse --symbolic-full-name {local_branch_sha}@{{upstream}}"
            return self._run(cmd).strip()
        except subprocess.CalledProcessError:
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

    def get_blobs_and_trees_names(self) -> DictStrStr:
        """Return actual names of blobs and trees.

        Note
        -----
        Based on https://stackoverflow.com/a/25954360.

        Note
        -----
        It is normal for a tree object to sometimes have no name. This happens when a
        repository has no directories (note that a commit always has an associated tree
        object). Sometimes blobs don't have names (I am not sure why -- FIXME: to
        investigate).

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

    def get_tags_info_parsed(self) -> dict[str, dict[str, DictStrStr]]:
        """Return parsed info for all annotated and lightweight tags.

        Note
        -----
        The ``git for-each-ref ...`` command used in this function doesn't return
        deleted annotated tags. They are handled separately in
        :func:`GitInspector._get_objects_info_parsed` (note that their SHA is contained
        in the output of :func:`GitCommand.get_objects_sha_kind`).

        Note
        -----
        The ``--python`` flag (see `constants.CMD_TAGS_INFO`) forms groups delimited by
        '...' which makes them easy to split and parse. On the flip-side, we have to
        decode escapes of escapes while preserving unicode characters. Note that if the
        message contains explitic ``\n``-s, they would appear as ``\\\\n``.

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


class TestGitRepository:
    """Create test git repository."""

    @classmethod
    def create(
        cls,
        label: Literal["default", "empty"],
        repo_path: Path | str,  # assumed to exist
        tar_file_name: Optional[str] = None,
    ) -> None:
        """Git repository creation displatch."""
        match label:
            case "default":
                cls.repository_default(repo_path)
            case "empty":
                cls.repository_empty(repo_path)
            case _:
                raise ValueError(f"Unknown repository label: {label}")

        if tar_file_name is not None:
            cls.tar(repo_path, tar_file_name)

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
    def repository_empty(path: Path | str) -> None:
        """Empty repository."""
        git = GitCommandMutate(path)
        git.init()

    @staticmethod
    def repository_default(path: Path | str) -> None:
        """Default repository."""
        git = GitCommandMutate(path)
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
        git.config("gc.auto 0")


def create_test_repo_and_reference_dot_file() -> None:
    """Create a git repository and its associated DOT file (to use as reference).

    Note
    -----
    This is meant to be used only when the test resources should be changed. To execute:
    ``cd src/git_dag && python git_commands.py``.

    """
    # pylint: disable=import-outside-toplevel
    import shutil

    from git_dag.git_repository import GitRepository  # pylint: disable=cyclic-import

    path = Path("test/resources/default_repo")
    path.mkdir()
    TestGitRepository.create("default", path)

    repo = GitRepository(path, parse_trees=True)
    repo.show(
        show_unreachable_commits=True,
        show_local_branches=True,
        show_remote_branches=True,
        show_trees=True,
        show_blobs=True,
        show_tags=True,
        show_deleted_tags=True,
        show_stash=True,
        show_head=True,
        format="gv",
        filename=path / "../default_repo.gv",
    )

    TestGitRepository.tar(path, path / "../default_repo.tar.gz")

    with open(path / "../default_repo.repr", "w", encoding="utf-8") as h:
        h.write(repr(repo))

    shutil.rmtree(path)


if __name__ == "__main__":
    create_test_repo_and_reference_dot_file()
