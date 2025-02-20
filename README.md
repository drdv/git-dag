## Generates the DAG of a git repository

### Install

+ `pip install git-dag`

### Getting help

+ `git dag -h` to display help

```
usage: git-dag [-h] [-p PATH] [-f FILE] [-b {graphviz}] [--format FORMAT]
               [--dpi DPI] [-i INIT_REFS [INIT_REFS ...]]
               [-R RANGE [RANGE ...]] [-n MAX_NUMB_COMMITS]
               [--rankdir RANKDIR] [--bgcolor BGCOLOR] [-u] [-t] [-D] [-l]
               [-r] [-s] [-H] [-T] [-B] [-m COMMIT_MESSAGE_AS_LABEL] [-o]
               [--log-level {NOTSET,INFO,WARNING,ERROR,CRITICAL}]

Visualize the git DAG.

options:
  -h, --help            show this help message and exit
  -p, --path PATH       Path to git repository.
  -f, --file FILE       Output graphviz file (could include a directory e.g.,
                        mydir/myfile).
  -b, --dag-backend {graphviz}
                        Backend DAG library.
  --format FORMAT       Graphviz output format (tooltips are available only
                        with svg). If the format is set to 'gv', only the
                        graphviz source file is generated
  --dpi DPI             DPI of output figure (used with --format png).
  -i, --init-refs INIT_REFS [INIT_REFS ...]
                        A list of branches, tags, objects' SHA (commits,
                        trees, blobs) that represents a limitation from where
                        to display the DAG
  -R, --range RANGE [RANGE ...]
                        A list to commits in a range to display.
  -n, --max-numb-commits MAX_NUMB_COMMITS
                        Max number of commits (set to 0 to remove limitation).
  --rankdir RANKDIR     rankdir argument of graphviz (LR, RL, TB, BT).
  --bgcolor BGCOLOR     bgcolor argument of graphviz (e.g., transparent).
  -u                    Show unreachable commits.
  -t                    Show tags.
  -D                    Show deleted annotated tags.
  -l                    Show local branches.
  -r                    Show remote branches.
  -s                    Show stash.
  -H                    Show head.
  -T                    Show trees (WARNING: should be used only with small
                        repositories).
  -B                    Show blobs (discarded if -T is not set).
  -m, --message COMMIT_MESSAGE_AS_LABEL
                        When greater than 0, this is the number of characters
                        from the commit message to use as a commit label. The
                        commit SHA is used otherwise.
  -o, --xdg-open        Open output SVG file with xdg-open.
  --log-level {NOTSET,INFO,WARNING,ERROR,CRITICAL}
                        Log level.
```

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

### Default color-codes

|                object | [color name](https://graphviz.org/doc/info/colors.html) |
|----------------------:|:--------------------------------------------------------|
|                commit | ${\texttt{\color{#cdad00}gold3}}$                       |
|    unreachable commit | ${\texttt{\color{#ff8c00}darkorange}}$                  |
|                  tree | ${\texttt{\color{#00688b}deepskyblue4}}$                |
|        the empty tree | ${\texttt{\color{#00ced1}darkturquoise}}$               |
|                  blob | ${\texttt{\color{#bebebe}gray}}$                        |
|         annotated tag | ${\texttt{\color{#ffc0cb}pink}}$                        |
| deleted annotated tag | ${\texttt{\color{#ffc0cb}rosybrown4}}$                  |
|       lightweight tag | ${\texttt{\color{#f08080}lightcoral}}$                  |
|          local branch | ${\texttt{\color{#228b22}forestgreen}}$                 |
|         remote branch | ${\texttt{\color{#b22222}firebrick}}$                   |
|                 stash | ${\texttt{\color{#87ceeb}skyblue}}$                     |
|                  HEAD | ${\texttt{\color{#6495ed}cornflowerblue}}$              |
