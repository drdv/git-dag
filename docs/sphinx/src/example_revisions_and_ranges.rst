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

.. tab:: Annotations

   .. include:: .static/examples/revisions_and_ranges/03_example_revisions_args.rst
   .. include:: .static/examples/revisions_and_ranges/03_example_revisions_html.rst

.. tab:: More annotations

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
