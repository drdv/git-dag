Fetch & merge or rebase
-------------------------

A ``git pull`` defaults to ``git fetch`` followed by ``git merge origin/main`` (assuming
that we are working on branch ``main`` and the remote is called ``origin``). The
following example compares this fetch-merge strategy vs. a fetch-rebase strategy.

Initial state
~~~~~~~~~~~~~~

Elena and Marina collaborate on a project (hosted on GitHub). Elena has already pushed
three commits (``A``, ``B`` and ``C``). Marina has pulled them and pushed two commits of
her own (``D`` and ``E``). Meanwhile Elena has committed ``F`` and ``G`` locally and has
executed a ``git fetch``. The state of the three repositories (on Elena's and Marina's
local machines as well as the one on GitHub) at this point is depicted in the three tabs
below. Note that, when visualizing Elena's repository, we passed ``-R ..@{u}`` [1]_ to
``git dag`` which marks the commits reachable from ``origin/main`` but not from
``main``.

Elena has to decide what to do about the diverging histories. Git provides two standard
mechanisms to combine them: a merge and a rebase.

.. tab:: Marina

   .. include:: .static/examples/fetch_merge_rebase/01_example_initial_state-marina_args.rst
   .. include:: .static/examples/fetch_merge_rebase/01_example_initial_state-marina_html.rst

.. tab:: GitHub

   .. include:: .static/examples/fetch_merge_rebase/02_example_initial_state-server_args.rst
   .. include:: .static/examples/fetch_merge_rebase/02_example_initial_state-server_html.rst

.. tab:: Elena

   .. include:: .static/examples/fetch_merge_rebase/03_example_initial_state-elena_args.rst
   .. include:: .static/examples/fetch_merge_rebase/03_example_initial_state-elena_html.rst

Elena merges
~~~~~~~~~~~~~

If first Elena performs a merge (``git merge origin/main``) followed by a ``git push``
and then Marina executes ``git pull``, the state of the three repositories would be as
depicted below. Since a `fast-forward merge
<https://git-scm.com/docs/git-merge#_fast_forward_merge>`_ is not possible (due to the
diverging histories), a `true merge <https://git-scm.com/docs/git-merge#_true_merge>`_
is performed -- it creates a new "merge-commit" ``m``. Having such a merge-commit can be
avoided if Elena rebases her work.

.. tab:: Marina

   .. include:: .static/examples/fetch_merge_rebase/04_example_merge-marina_args.rst
   .. include:: .static/examples/fetch_merge_rebase/04_example_merge-marina_html.rst

.. tab:: GitHub

   .. include:: .static/examples/fetch_merge_rebase/05_example_merge-server_args.rst
   .. include:: .static/examples/fetch_merge_rebase/05_example_merge-server_html.rst

.. tab:: Elena

   .. include:: .static/examples/fetch_merge_rebase/06_example_merge-elena_args.rst
   .. include:: .static/examples/fetch_merge_rebase/06_example_merge-elena_html.rst

Elena rebases
~~~~~~~~~~~~~~

If, instead of a merge, Elena first performs a rebase (``git rebase origin/main``), the
linear history of the repository would be preserved (for the current setup, this would
be the preferred approach most of the time). Note how the rebase operation recreated
Elena's ``G`` and ``F`` commits (and preserved their messages) on top of Marina's commit
``E``. The original ``G`` and ``F`` commits are unreachable and can be found only on
Elena's machine. Comparing the tooltips of e.g., the two ``F`` commits we see that they
have different "committer" dates and the same author date.

The fetch-rebase strategy can be enforced using ``git pull --rebase``.

.. tab:: Marina

   .. include:: .static/examples/fetch_merge_rebase/07_example_rebase-marina_args.rst
   .. include:: .static/examples/fetch_merge_rebase/07_example_rebase-marina_html.rst

.. tab:: GitHub

   .. include:: .static/examples/fetch_merge_rebase/08_example_rebase-server_args.rst
   .. include:: .static/examples/fetch_merge_rebase/08_example_rebase-server_html.rst

.. tab:: Elena

   .. include:: .static/examples/fetch_merge_rebase/09_example_rebase-elena_args.rst
   .. include:: .static/examples/fetch_merge_rebase/09_example_rebase-elena_html.rst

.. [1] Equivalently, we could have used ``-R ..origin/main`` or ``-R
       HEAD..origin/main``.
