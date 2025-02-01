# init
init () {
    git init
}

# add filename [file-content] (use when we want to create a conflict)
add () {
    echo $2 > $1
    git add $1
}

# cm commit-messages
cm () {
    for commit_message in $@; do
	git commit --allow-empty -m $commit_message
    done
}

# co branch-name
co () {
    git switch $1
}

# br branch-name
br () {
    git switch -c $1
}

# brD branch-name
brD () {
    git branch -D $1
}

# mg branch-name [merge-commit-message]
mg () {
    git merge -X theirs $1 -m ${2:-"m"}
}
