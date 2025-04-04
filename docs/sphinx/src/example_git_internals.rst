Git Internals - Git Objects
----------------------------

Here we follow the famous `Git Internals - Git Objects
<https://git-scm.com/book/en/v2/Git-Internals-Git-Objects>`_ tutorial. The example below
is meant to be complementary to it and in no way a substitute. It is assumed that, as a
preliminary step, an empty git repository is created (``git init``).

Git blob
~~~~~~~~~

A blob is an objects that stores data. This data could e.g., be the content of a file
or, in general, a sequence of raw bytes with no specific structure or interpretation. A
blob is identified using the `SHA-1 <https://en.wikipedia.org/wiki/SHA-1>`_ hash of its
data.

.. include:: .static/examples/git_internals/01_step_create_blob_cmd.rst

The ``git hash-object`` command above outputs the SHA-1 hash of the ``'test content'``
string and registers a blob in the git object store. Let us visualize it:

.. include:: .static/examples/git_internals/01_step_create_blob_args.rst
.. include:: .static/examples/git_internals/01_step_create_blob_html.rst

The above figure depicts one blob whose full hash is displayed in the tooltip (the
meaning of "Standalone Blobs & Trees" would become clear shortly).

Following the tutorial, we create another blob, this time from a file (``test.txt``)

.. include:: .static/examples/git_internals/02_step_create_blob_from_file_cmd.rst
.. include:: .static/examples/git_internals/02_step_create_blob_from_file_args.rst
.. include:: .static/examples/git_internals/02_step_create_blob_from_file_html.rst

Next, update the content of the ``test.txt`` file, and register it in the git object
store:

.. include:: .static/examples/git_internals/03_step_create_blob_from_modified_file_cmd.rst
.. include:: .static/examples/git_internals/03_step_create_blob_from_modified_file_args.rst
.. include:: .static/examples/git_internals/03_step_create_blob_from_modified_file_html.rst

Note that, the ``83baae6`` and ``1f7a7a4`` blobs do not contain information related to
the name of the file (``test.txt``) whose data they store.

Git tree
~~~~~~~~~

A git tree object allows to group blobs and other trees together (much like a directory
groups files and other directories). A tree object is normally created by taking the
state of the staging area:

.. include:: .static/examples/git_internals/04_step_create_tree_from_cached_blob_cmd.rst

Trees as well are identified using the SHA-1 hash of the data they contain.

.. include:: .static/examples/git_internals/04_step_create_tree_from_cached_blob_args.rst
.. include:: .static/examples/git_internals/04_step_create_tree_from_cached_blob_html.rst

The tooltip of the ``83baae6`` blob is now the actual name of the file whose data it
stores (the name has been retrieved from the containing tree object).

In a similar way we can create another tree that contains the second version of
``test.txt`` and a new file as well.

.. include:: .static/examples/git_internals/05_step_create_tree_from_cached_blob_and_file_cmd.rst
.. include:: .static/examples/git_internals/05_step_create_tree_from_cached_blob_and_file_args.rst
.. include:: .static/examples/git_internals/05_step_create_tree_from_cached_blob_and_file_html.rst

Next we create a tree that contains another tree:

.. include:: .static/examples/git_internals/06_step_create_tree_with_tree_cmd.rst
.. include:: .static/examples/git_internals/06_step_create_tree_with_tree_args.rst
.. include:: .static/examples/git_internals/06_step_create_tree_with_tree_html.rst

Similar to a blob, a tree does not include information about its own name. However, if
contained in another tree, its name can be retrieved (see the tooltip of ``d8329fc``
and compare it with the tooltips of ``3c4e9cd`` and ``0155eb4``).

Git commit
~~~~~~~~~~~

A commit object contains information about who, when and why created a given tree and
what are the parent commit(s) from where it descended. Each commit has exactly one
associated tree (which of course may contain sub-trees).

.. include:: .static/examples/git_internals/07_step_add_commits_cmd.rst
.. include:: .static/examples/git_internals/07_step_add_commits_args.rst
.. include:: .static/examples/git_internals/07_step_add_commits_html.rst

As with blobs and trees, commits are identified using the SHA-1 hash of the data they
contain (see their tooltips). Our three commits are currently **unreachable** from any
branch or tag (this is due to the nature of the plumbing command ``git commit-tree``
that was used to create them). Furthermore, they don't even appear in the ``reflog`` --
because of this, their associated trees and blobs are included in the "Standalone Blobs
& Trees" cluster [1]_.

Git tag
~~~~~~~~

A tag is a label (with additional metadata) assigned to a particular point in the git
history. This is the fourth (and last) git object -- the other ones being blobs, trees
and commits.

.. include:: .static/examples/git_internals/08_step_add_tag_cmd.rst
.. include:: .static/examples/git_internals/08_step_add_tag_args.rst
.. include:: .static/examples/git_internals/08_step_add_tag_html.rst

The colour of the first commit has changed as it is now reachable through our
(annotated) tag. Because of this, its child tree and blob are not considered as
standalone anymore.

Branch
~~~~~~~

A branch is a label of the most recent commit of a given line of development. It is not
a git object in the same way as blobs, trees, commits and (annotated) tags are.

.. include:: .static/examples/git_internals/09_step_add_branch_cmd.rst
.. include:: .static/examples/git_internals/09_step_add_branch_args.rst
.. include:: .static/examples/git_internals/09_step_add_branch_html.rst

Note that the tooltip of the main branch is ``-> None`` -- this implies that it doesn't
track any remote branch.

Let us reset the main branch to point to the second commit. The first commit would now
become unreachable from a branch or a tag, however it is reachable from the reflog (the
reflog records the reset operation) and thus its child tree and blob are not considered
as standalone.

.. include:: .static/examples/git_internals/10_step_reset_main_cmd.rst
.. include:: .static/examples/git_internals/10_step_reset_main_args.rst
.. include:: .static/examples/git_internals/10_step_reset_main_html.rst

If we checkout the second commit, the HEAD becomes detached (now HEAD points directly to
the second commit and its box in the visualized DAG has a border).

.. include:: .static/examples/git_internals/11_step_detached_head_cmd.rst
.. include:: .static/examples/git_internals/11_step_detached_head_args.rst
.. include:: .static/examples/git_internals/11_step_detached_head_html.rst

Lightweight tag
~~~~~~~~~~~~~~~~

Adding a lightweight tag to point to the currently unreachable third commit makes it
reachable again (lightweight tags are colour-coded differently from annotated tags and
their tooltip is different as well).

.. include:: .static/examples/git_internals/12_step_add_lightweight_tag_cmd.rst
.. include:: .static/examples/git_internals/12_step_add_lightweight_tag_args.rst
.. include:: .static/examples/git_internals/12_step_add_lightweight_tag_html.rst

In the end, we have only one standalone blob left. Visualizing trees and blobs is
reasonable for educational purpose for small repositories only. Skipping them results in
(here, the ``-u`` flag is superfluous as there are no unreachable commits):

.. include:: .static/examples/git_internals/final_dag_no_trees_and_blobs_args.rst
.. include:: .static/examples/git_internals/final_dag_no_trees_and_blobs_html.rst

.. [1] The notion of standalone trees and blobs is not standard. We use it to label
       trees and blobs that don't have parent commits that are reachable from a branch a
       tag or the reflog.
