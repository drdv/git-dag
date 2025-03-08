## Generates the DAG of a git repository

See the online [documentation](https://drdv.github.io/git-dag).

### Install

+ `pip install git-dag`

### Examples

+ `git dag -rlst -n 20` would generate `git-dag.gv` (a [graphviz](https://graphviz.org/)
  dot file) and `git-dag.gv.svg` with:
  + the 20 most recent commits (`-n 20`, use `-n -1` to show all)
  + all local branches (`-l`)
  + all remote branches (`-r`)
  + the stash (`-s`)
  + all tags (`-t`)

+ displaying trees (`-T`) and blobs (`-B`) is recommended only for small(ish)
  repositories.

+ using `-n 10 -i my-branch my-tag` would display the 10 most recent commits accessible
  from `my-branch` or `my-tag`.
