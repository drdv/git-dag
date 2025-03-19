
.. code-block:: bash
    :caption: Create a blob from the content of a modified file

    echo 'version 2' > test.txt
    git hash-object -w test.txt

.. code-block:: console
    :caption: Output

    1f7a7a472abf3dd9643fd615f6da379c4acb3e3a
