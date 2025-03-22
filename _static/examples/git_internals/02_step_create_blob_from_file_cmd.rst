
.. code-block:: bash
    :caption: Create a blob from the content of a file

    echo 'version 1' > test.txt
    git hash-object -w test.txt

.. code-block:: console
    :caption: Output

    83baae61804e65cc73a7201a7252750c76066a30
