import git_dag

project = "git-dag"
author = "Dimitar Dimitrov"
copyright = f"2025, {author}"

version = git_dag.__version__
release = version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx.ext.coverage",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxarg.ext",
]

autosummary_generate = True
language = "en"
html_theme = "furo"
todo_include_todos = True

exclude_patterns = []
templates_path = [".templates"]
html_static_path = [".static"]
# https://github.com/bumbu/svg-pan-zoom
html_js_files = ["js/svg-pan-zoom.min.js", "js/custom.js"]
html_css_files = ["css/custom.css"]

html_title = "git-dag"
