Quickstart
===========

After :doc:`installing <install>` ``git-dag``, one can create a configuration file with
all user-parameters using

.. code-block:: bash
    :caption: Create config file ``~/.git-dag.yml``

    git dag --config-create

By default there are 7 sections. The most useful one is ``public:`` which contains most
:doc:`command-line <cli>` arguments. There is no need to keep all parameters in the
config file (any of them can be deleted). The default values of missing parameters are
defined in the :mod:`git_dag.parameters` module. Command-line arguments take precedence
over parameters in the config file.

Generate a DAG
~~~~~~~~~~~~~~~

Assuming that we are in a folder with a git repository, running

.. code-block:: bash

   git dag -lrstH -n 500

would generate ``git-dag.gv`` (a graphviz dot file) and ``git-dag.gv.svg`` containing a
DAG with the 500 most recent commits, including:

+ ``-l`` local branches
+ ``-r`` remote branches
+ ``-s`` stashes
+ ``-t`` tags
+ ``-H`` HEAD

Setting ``-n 0`` would include all commits (even unreachable ones if ``-u`` is passed as
well). Trees and blobs can be displayed using ``-T`` and ``-B`` (this is recommended
only for small repositories).

See the :doc:`examples <examples>`.
