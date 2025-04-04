Rebase ``--onto``
------------------

Here we consider the ``--onto`` flag of ``git-rebase`` -- it gives fine-grained control
over the rebase process by allowing to move a range of commits onto a new base commit.
There are two examples: the first one simply illustrates the syntax, while the second
one describes a scenario where using the ``--onto`` flag is particularly well-suited.

The basic format of the command is:

.. code-block:: bash

   git rebase --onto <new-base> <range-start> <range-end>

The range of commits to rebase onto the ``<new-base>`` is formed using
``<range-start>..<range-end>`` (the former is excluded from the range, while the latter
is included).

Example 1
~~~~~~~~~~

We consider four cases. In all of them, the "Before" tab depicts the same repository
with two branches (``main`` and ``feature``) -- the only difference being the
highlighted range of commits, which is precisely the range used in the rebase command
(included at the top on the "After" tab).

In the first case we consider a vanilla rebase command ``git rebase main feature``,
which is equivalent to ``git rebase --onto main main feature``, i.e., the changes of the
commits in the range ``main..feature`` are applied starting from the tip of ``main``. As
can be seen in the "After" tab, commits ``C``, ``D`` and ``E`` have been recreated
(compare their tooltips), that is:

+ ``C``: ``4878cee`` → ``9d41ef9``
+ ``D``: ``63e7edb`` → ``5deeea5``
+ ``E``: ``09fb3c2`` → ``5ede5cd``.

Of course, the original three commits are still available in the repository however they
are unreachable from any branch (or tag) and, normally, would be garbage-collected
eventually (note that they are displayed with a different color [1]_).

.. tab:: Before (1)

   .. include:: .static/examples/rebase_onto/01_repo_example1_args.rst
   .. include:: .static/examples/rebase_onto/01_repo_example1_html.rst

.. tab:: After (1)

   .. include:: .static/examples/rebase_onto/02_example1_rebase_cmd.rst
   .. include:: .static/examples/rebase_onto/02_example1_rebase_args.rst
   .. include:: .static/examples/rebase_onto/02_example1_rebase_html.rst

.. -----------------------------------------------------------------------

The range in the second case, is the same as in the first case even though it is defined
using ``bc9b888..feature`` (note that ``bc9b888`` is the `merge-base
<https://git-scm.com/docs/git-merge-base>`_ of ``main`` and ``feature``). The difference
here is that we rebase not on the tip of ``main`` but on commit ``c95114c``.

.. tab:: Before (2)

   .. include:: .static/examples/rebase_onto/03_repo_example1_args.rst
   .. include:: .static/examples/rebase_onto/03_repo_example1_html.rst

.. tab:: After (2)

   .. include:: .static/examples/rebase_onto/04_example1_rebase_onto1_cmd.rst
   .. include:: .static/examples/rebase_onto/04_example1_rebase_onto1_args.rst
   .. include:: .static/examples/rebase_onto/04_example1_rebase_onto1_html.rst

.. -----------------------------------------------------------------------

In case 3 we rebase again on top of ``c95114c`` but this time the range has one commit
less (we dropped commit ``C``).

.. tab:: Before (3)

   .. include:: .static/examples/rebase_onto/05_repo_example1_args.rst
   .. include:: .static/examples/rebase_onto/05_repo_example1_html.rst

.. tab:: After (3)

   .. include:: .static/examples/rebase_onto/06_example1_rebase_onto2_cmd.rst
   .. include:: .static/examples/rebase_onto/06_example1_rebase_onto2_args.rst
   .. include:: .static/examples/rebase_onto/06_example1_rebase_onto2_html.rst

.. -----------------------------------------------------------------------

Finally, in case 4, we use the last commit on the ``feature`` branch (instead of the
``feature`` branch itself) to define the range. After the rebase, the HEAD is detached
[2]_ (i.e., the ``feature`` branch didn't move). This could be considered as a useful
trick -- we perform the rebase, then move ``feature`` to point to the updated ``E``
commit ``283df08`` if we are happy with the results (see the last two tabs) [3]_.

.. tab:: Before (4)

   .. include:: .static/examples/rebase_onto/07_repo_example1_args.rst
   .. include:: .static/examples/rebase_onto/07_repo_example1_html.rst

.. tab:: After rebase (4)

   .. include:: .static/examples/rebase_onto/08_example1_rebase_onto3_cmd.rst
   .. include:: .static/examples/rebase_onto/08_example1_rebase_onto3_args.rst
   .. include:: .static/examples/rebase_onto/08_example1_rebase_onto3_html.rst

.. tab:: After update-ref (4)

   .. include:: .static/examples/rebase_onto/09_example1_move_feature_after_rebase_onto3_cmd.rst
   .. include:: .static/examples/rebase_onto/09_example1_move_feature_after_rebase_onto3_args.rst
   .. include:: .static/examples/rebase_onto/09_example1_move_feature_after_rebase_onto3_html.rst

.. tab:: After switch (4)

   .. include:: .static/examples/rebase_onto/10_example1_switch_feature_cmd.rst
   .. include:: .static/examples/rebase_onto/10_example1_switch_feature_args.rst
   .. include:: .static/examples/rebase_onto/10_example1_switch_feature_html.rst

Example 2
~~~~~~~~~~

In the second example we reuse the repository from section "More Interesting Rebases" in
`Git Branching - Rebasing <https://git-scm.com/book/en/v2/Git-Branching-Rebasing>`_,
however we perform a different sequence of operations.

Suppose that, to add some server-side functionality, Elena commits ``998d091`` (``C3``)
on a feature branch ``server``. A bit later Marina, adds related client-side
functionality on a ``client`` branch. Then both of them continue working on their
implementations. Meanwhile, ``main`` has evolved and Elena decides to rebase ``server``
on it (lets assume that she resolved a conflict in the ``C3`` commit). The result is
depicted in the second tab below.

At that point Marina wants to sync her ``client`` branch with the updated ``server``
branch, but she doesn't want to resolve the same conflict with ``C3`` (after all, it has
already been resolved by Elena). So she uses the ``--onto`` flag of ``git rebase`` as
shown in the third tab below. Note that the range ``998d091..client`` doesn't include
``998d091`` -- in effect, she only rebases her own work (commits ``C8`` and ``C9``).

.. tab:: Initial repo

   .. include:: .static/examples/rebase_onto/11_repo_example2_args.rst
   .. include:: .static/examples/rebase_onto/11_repo_example2_html.rst

.. tab:: Rebase server on main

   .. include:: .static/examples/rebase_onto/12_example2_rebase_server_cmd.rst
   .. include:: .static/examples/rebase_onto/12_example2_rebase_server_args.rst
   .. include:: .static/examples/rebase_onto/12_example2_rebase_server_html.rst

.. tab:: Rebase client on server

   .. include:: .static/examples/rebase_onto/13_example2_rebase_client_cmd.rst
   .. include:: .static/examples/rebase_onto/13_example2_rebase_client_args.rst
   .. include:: .static/examples/rebase_onto/13_example2_rebase_client_html.rst

.. [1] The ``-u`` flag (of ``git dag``) enables the display of unreachable commits.

.. [2] Note that if we check out the last commit on a branch (instead of the branch
       itself), the HEAD is detached as well.

.. [3] Of course, if we want the original three commits to remain reachable, we could
       simply create a branch (say ``feature-backup``) pointing to the tip of
       ``feature`` before starting the rebase.
