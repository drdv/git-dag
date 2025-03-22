
.. code-block:: bash
    :caption: Create a tree from a cached blob and a file

    echo 'new file' > new.txt
    git update-index --add --cacheinfo 100644 1f7a7a472abf3dd9643fd615f6da379c4acb3e3a test.txt
    git update-index --add new.txt
    git write-tree

.. code-block:: console
    :caption: Output

    0155eb4229851634a0f03eb265b69f5a2d56f341
