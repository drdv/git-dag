
.. code-block:: bash
    :caption: Create three commits

    GIT_AUTHOR_NAME="First Last"
    GIT_AUTHOR_EMAIL="first.last.mail.com"
    GIT_COMMITTER_NAME="Nom Prenom"
    GIT_COMMITTER_EMAIL="nom.prenom@mail.com"

    SHA_FIRST_COMMIT=$(echo 'First commit' | git commit-tree d8329fc)
    SHA_SECOND_COMMIT=$(echo 'Second commit' | git commit-tree 0155eb4 -p $SHA_FIRST_COMMIT)
    SHA_THIRD_COMMIT=$(echo 'Third commit' | git commit-tree 3c4e9cd -p $SHA_SECOND_COMMIT)

    echo $SHA_FIRST_COMMIT
    echo $SHA_SECOND_COMMIT
    echo $SHA_THIRD_COMMIT

.. code-block:: console
    :caption: Output

    fa26b470d9508bebe2029623de8770215ebb26a0
    03c5025d075bbe625608593e3bf4671daebebcc4
    aa6ef7bc380e3e98362b4276d24b8046b1f4f758
