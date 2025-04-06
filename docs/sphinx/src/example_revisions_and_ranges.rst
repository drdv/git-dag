Revisions and ranges
----------------------

Understanding *revisions* and *ranges* is essential as many git commands take them as
arguments.

.. epigraph::

   Depending on the command, revisions denote a specific commit or, for commands which
   walk the revision graph ... all commits which are reachable from that commit.

   -- `man gitrevisions <https://git-scm.com/docs/gitrevisions>`_

The example below is based on a repository due to Jon Loeliger (from the above man
page). For convenience, with every commit we associate a branch whose name is the same
as the (one-letter) commit message. Having branches is convenient as their names can be
used to express revisions and ranges succinctly.

Revisions
~~~~~~~~~~

The first two tabs below depict our example repository without and with branches (local
branches can be visualized by passing the ``-l`` flag). The third tab includes
annotations (each one is passed using the ``-a`` flag) with example uses of the caret
(``^``) and tilde (``~``) symbols:

+ ``<rev>~<n>``: the ``n``-th generation ancestor of ``<rev>``, following only the first parents
+ ``<rev>^<n>``: the ``n``-th parent of ``<rev>``.

There are other ways to specify revisions. Some of them are shown in the last tab.

.. tab:: Example repository

   .. include:: .static/examples/revisions_and_ranges/01_example_revisions_args.rst
   .. include:: .static/examples/revisions_and_ranges/01_example_revisions_html.rst

.. tab:: With branches

   .. include:: .static/examples/revisions_and_ranges/02_example_revisions_args.rst
   .. include:: .static/examples/revisions_and_ranges/02_example_revisions_html.rst

.. tab:: With annotations

   .. include:: .static/examples/revisions_and_ranges/03_example_revisions_args.rst
   .. include:: .static/examples/revisions_and_ranges/03_example_revisions_html.rst

.. tab:: With more annotations

   .. include:: .static/examples/revisions_and_ranges/04_example_revisions_args.rst
   .. include:: .static/examples/revisions_and_ranges/04_example_revisions_html.rst

Ranges
~~~~~~~

.. epigraph::

   History traversing commands such as git log operate on a **set** of commits, not just a
   single commit.

   -- `man gitrevisions <https://git-scm.com/docs/gitrevisions>`_

Below we give examples with four ways to define such a set:

+ ``<rev>``: commits reachable from ``<rev>``
    + ``<rev1> <rev2>``: union of commits reachable from ``<rev1>`` and ``<rev2>``, etc.
+ ``<rev1>..<rev2>``: commits reachable from ``<rev2>`` but not from ``<rev1>``
+ ``<rev1>...<rev2>``: commits reachable from either ``<rev1>`` or ``<rev2>`` but not from both
+ ``<rev>^@``: all (direct/indirect) parents of ``<rev>``.

In addition, the last two tabs depict the effect of using ``--ancestry-path`` in
combination with a range [1]_. For example, range ``D..A`` includes all reachable
commits from ``A`` that are not reachable from ``D`` (i.e., ``{A, B, C, E, F, I, J}``),
while passing as well ``--ancestry-path=F``, filters-out commit ``E`` from that set,
because ``E`` cannot be reached from ``F`` and ``F`` cannot be reached from ``E``.

.. tab:: ``<rev1> <rev2>``

   .. include:: .static/examples/revisions_and_ranges/05_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/05_example_ranges_html.rst

.. tab:: ``<rev1>..<rev2>``

   .. include:: .static/examples/revisions_and_ranges/06_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/06_example_ranges_html.rst

.. tab:: ``<rev1>...<rev2>``

   .. include:: .static/examples/revisions_and_ranges/07_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/07_example_ranges_html.rst

.. tab:: ``<rev>^@``

   .. include:: .static/examples/revisions_and_ranges/08_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/08_example_ranges_html.rst

.. tab:: ``D..A``

   .. include:: .static/examples/revisions_and_ranges/09_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/09_example_ranges_html.rst

.. tab:: ``D..A --ancestry-path=F``

   .. include:: .static/examples/revisions_and_ranges/10_example_ranges_args.rst
   .. include:: .static/examples/revisions_and_ranges/10_example_ranges_html.rst


A ``diff`` particularity
~~~~~~~~~~~~~~~~~~~~~~~~~

It is worth pointing out that in the context of the ``git diff`` command,
``<rev1>..<rev2>`` and ``<rev1>...<rev2>`` do not represent ranges:

.. epigraph::

   However, diff is about comparing two endpoints, not ranges, and the range
   notations ... do not mean a range

   -- `man git-diff <https://git-scm.com/docs/git-diff>`_

A nice summary of using the range notation with ``git log`` and ``git diff`` can be
found `here <https://stackoverflow.com/a/46345364>`_.

.. [1] Note that the argument of the ``-R`` flag is passed verbatim to ``git rev-list``
       (arguments that include spaces should be quoted).
