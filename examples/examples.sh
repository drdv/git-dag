#
# Example git repositories
#

source ./git_aliases.sh

# --------------------------------------------------------------------------------------
# Examples from [ex1](https://stackoverflow.com/a/15915431)
# --------------------------------------------------------------------------------------

repo_ex1_1 () {
    init; cm A
    br topic; cm D
    br feature; cm F; add file G; cm G
    co topic; add file E; cm E; mg feature
    tg 0.1 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    tg 0.2 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    cm H
    co main; cm B C; brD feature
    co topic

    tg 0.3 main -m T1
    tg 0.4 main
    tg 0.5 main
    tg -d 0.1
    tg -d 0.4

    br bugfix; cm I
    tg 0.6 -m "Test:                    €."
    cm J
    co topic
    brD bugfix
}

repo_ex1_tmp () {
    git init
    git commit --allow-empty -m "A" -m "Body:\n * First line\n * Second line\n * Third line"
    git switch -c topic
    git commit --allow-empty -m "D"
    git switch -c feature
    git commit --allow-empty -m "F"
    echo "G" > file
    git add file
    git commit -m "G"

    git switch topic

    echo "E" > file
    git add file
    git commit -m "E"
    git merge -X theirs feature -m "m"
    git tag 0.1 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    git tag 0.2 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    git commit --allow-empty -m "H"

    git switch main
    git commit --allow-empty -m "B"
    git commit --allow-empty -m "C"

    git branch -D feature
    git switch topic

    git tag 0.3 main -m "T1"
    git tag 0.4 main
    git tag 0.5 main
    git tag -d 0.1
    git tag -d 0.4

    git switch -c bugfix
    git commit --allow-empty -m "I"

    git tag 0.6 -m "Test:                    €."
    git commit --allow-empty -m "J"

    git switch topic
    git branch -D bugfix
}

repo_ex1_2 () {
    init; cm A
    br topic
    br feature; cm F; add file G; cm G
    co topic; cm D; add file E; cm E; mg feature; cm H
    co main; cm B C; brD feature
    co topic
}

repo_ex1_3 () {
    init; cm A
    br topic
    co main; cm B; add file C; cm C
    co topic; add file E; cm E; mg main; cm F
    co main; cm D
    co topic
}

repo_ex1_4 () {
    init; cm A
    br feature; cm E F
    co main; cm B
    co feature
    br topic; mg main m1; cm H
    co feature; cm G
    co main; cm C; mg feature m2; cm D; brD feature
    co topic
}

# --------------------------------------------------------------------------------------
# Examples from [ex2](https://stackoverflow.com/a/56533595)
# --------------------------------------------------------------------------------------

repo_ex2_1 () {
    init; cm o x
    br branch; cm A B
    br feature; cm E F
    co branch; cm C D; mg feature G; cm H
    co main; cm o o; brD feature
    co branch
}

repo_ex2_2 () {
    init; cm o
    br feature; cm C D E
    co main; cm x
    br branch; cm A B; mg feature F; cm G
    co main; cm o o; brD feature
    co branch
}
