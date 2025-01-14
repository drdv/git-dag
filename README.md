## Generates the DAG of a git repository

### Install

+ `pip install git-dag`

### Getting help

+ `git dag -h` to display help

```
usage: git-dag [-h] [-p PATH] [-f FILE] [--format FORMAT] [--dpi DPI]
               [-i INIT_REFS [INIT_REFS ...]] [-n MAX_NUMB_COMMITS]
               [--rankdir RANKDIR] [--bgcolor BGCOLOR] [-t] [-l] [-r] [-s]
               [-T] [-B] [-o]
               [--log-level {NOTSET,INFO,WARNING,ERROR,CRITICAL}]

Visualize the git DAG.

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to git repository.
  -f FILE, --file FILE  Output graphviz file (could include a directory e.g.,
                        mydir/myfile).
  --format FORMAT       Graphviz output format (tooltips are available only
                        with svg). If the format is set to 'gv', only the
                        graphviz source file is generated
  --dpi DPI             DPI of output figure (used with --format png).
  -i INIT_REFS [INIT_REFS ...], --init-refs INIT_REFS [INIT_REFS ...]
                        A list of SHA of object (commits, tags, trees, blobs)
                        that represents a limitation from where to display the
                        DAG
  -n MAX_NUMB_COMMITS, --max-numb-commits MAX_NUMB_COMMITS
                        Max number of commits (set to 0 to remove limitation).
  --rankdir RANKDIR     rankdir argument of graphviz (LR, RL, TB, BT).
  --bgcolor BGCOLOR     bgcolor argument of graphviz (e.g., transparent).
  -t                    Show tags.
  -l                    Show local branches.
  -r                    Show remote branches.
  -s                    Show stash.
  -T                    Show trees (WARNING: should be used only with small
                        repositories).
  -B                    Show blobs (discarded if -T is not set).
  -o, --xdg-open        Open output SVG file with xdg-open.
  --log-level {NOTSET,INFO,WARNING,ERROR,CRITICAL}
                        Log level.
```

### Examples

+ `git dag -rlst -n 20` would generate `git-dag.gv` (a [graphviz](https://graphviz.org/)
  dot file) and `git-dag.gv.svg` with:
  + the 20 most recent commits (`-n 20`, use `-n 0` to show all)
  + all local branches (`-l`)
  + all remote branches (`-r`)
  + the stash (`-s`)
  + all tags (`-t`)

+ displaying trees (`-T`) and blobs (`-B`) is recommended only for small(ish)
  repositories.

+ using `-n 10 -i my-branch my-tag` would display the 10 most recent commits accessible
  from `my-branch` or `my-tag`.
