
.. code-block:: bash
    :caption: Create a blob from the content of a string

    echo 'test content' | git hash-object -w --stdin

.. code-block:: console
    :caption: Output

    d670460b4b4aece5915caf5c68d12f560a9fe3e4
