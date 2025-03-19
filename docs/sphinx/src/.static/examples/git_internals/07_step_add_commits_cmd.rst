
.. code-block:: bash
    :caption: Create three commits

    GIT_AUTHOR_NAME="First Last"
    GIT_AUTHOR_EMAIL="first.last.mail.com"
    GIT_COMMITTER_NAME="Nom Prenom"
    GIT_COMMITTER_EMAIL="nom.prenom@mail.com"

    SHA_FIRST_COMMIT=$(echo 'First commit' | git commit-tree d8329f)
    SHA_SECOND_COMMIT=$(echo 'Second commit' | git commit-tree 0155eb -p $SHA_FIRST_COMMIT)
    SHA_THIRD_COMMIT=$(echo 'Third commit' | git commit-tree 3c4e9c -p $SHA_SECOND_COMMIT)

    echo $SHA_FIRST_COMMIT
    echo $SHA_SECOND_COMMIT
    echo $SHA_THIRD_COMMIT

.. code-block:: console
    :caption: Output

    dca3f7dc874da24de0e4d8ad2cb1db72b9ed78bc
    6f3fd5c2a9e0be0844be6690e5c72d5b6986f3f6
    c024a6449c2d7426043e97c5be753ca623258a5d
