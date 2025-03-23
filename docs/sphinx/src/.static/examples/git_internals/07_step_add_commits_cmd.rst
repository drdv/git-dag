
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

    89d48e2d82dc8b351afdf65bc477d46ab30b1163
    ce29b5d39756a5dff91c556e632199cc88e909ed
    5ed380ef1d428a13bac2fa5fefc82d5a9c414818
