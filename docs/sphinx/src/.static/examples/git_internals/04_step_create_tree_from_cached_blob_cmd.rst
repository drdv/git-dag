
.. code-block:: bash
    :caption: Create a tree from a cached blob

    git update-index --add --cacheinfo 100644 83baae61804e65cc73a7201a7252750c76066a30 test.txt
    git write-tree

.. code-block:: console
    :caption: Output

    d8329fc1cc938780ffdd9f94e0d364e0ea74f579
