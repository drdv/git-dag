Quickstart
===========

After :doc:`installing <install>` ``git-dag``, one can create a configuration file [1]_ using

.. code-block:: bash
    :caption: Create config file ``~/.git-dag.yml``

    git dag --config-create

Parameters are organized in sections:

+ ``public`` contains most :doc:`command-line <cli>` arguments
+ ``dag_node_colors``: node colors
+ ``dag_global`` global attributes of the DAG
+ ``dag_node``: node attributes
+ ``dag_edge``: edge attributes

The user can define arbitrary parameters in the latter three section, which are passed
to the graph backend (currently only graphviz is supported).

There is no need to keep all parameters in the config file (any of them can be deleted).
The default values of missing parameters are defined in the :mod:`git_dag.parameters`
module. Command-line arguments take precedence over parameters in the config file.

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

.. [1] The name of the configuration file is taken from the ``GIT_DAG_CONFIG_FILE``
       environment variable, or if not set, it is ``~/.git-dag.yml`` by default.
