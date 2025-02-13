#
# Example git repositories
#

source ./git_utils.sh

# --------------------------------------------------------------------------------------
# Examples from [ex1](https://stackoverflow.com/a/15915431)
# --------------------------------------------------------------------------------------

repo_ex1_1 () {
    init; cm A
    br topic; cm D
    br feature; cm F; add file G; cm G
    co topic; add file E; cm E; mg feature; cm H
    co main; cm B C; brD feature
    co topic

    tg 0.1 main -m T1
    tg 0.2 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    tg 0.5 -m "Summary line" -m "Body:\n * First line\n * Second line\n * Third line"
    tg 0.6 -m "Test:                    €."
    tg 0.3 main
    tg 0.4
    tg -d 0.5
    tg -d 0.4
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
