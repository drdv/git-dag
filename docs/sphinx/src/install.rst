Install
========

The recommended way to install ``git-dag`` is using

.. code-block:: bash

   pip install git-dag

or, for a development version (with all optional dependencies)

.. code-block:: bash

   pip install git-dag[dev]

or, an editable install (in a venv)

.. code-block:: bash

   git clone https://github.com/drdv/git-dag
   cd git-dag && make install

In addition, a working installation of `graphviz <https://graphviz.org/download/>`_ is
required. For example:

+ fedora: ``dnf install graphviz``
+ ubuntu: ``apt install graphviz``
+ macos: ``brew install graphviz``

The code has been tested on fedora 41, ubuntu 24.04.2 LTS, macos Sequoia.
