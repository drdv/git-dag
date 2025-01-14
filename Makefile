PYTHON := python
VENV_NAME := .venv
VENV_ACTIVATE := source ${VENV_NAME}/bin/activate

PYLINT := pylint

help: URL := github.com/drdv/makefile-doc/releases/latest/download/makefile-doc.awk
help: DIR := $(HOME)/.local/share/makefile-doc
help: SCR := $(DIR)/makefile-doc.awk
help: ## show this help
	@test -f $(SCR) || wget -q -P $(DIR) $(URL)
	@awk -f $(SCR) $(MAKEFILE_LIST)

# ----------------------------------------------------------------

## Lint code
lint: lint-run

## Run mypy check
mypy: mypy-run

## Editable install in venv
install-local: setup-venv
	$(VENV_ACTIVATE) && pip install -e .[dev]

pre-commit: ## Execute pre-commit on all files
	@pre-commit run -a

# ----------------------------------------------------------------

lint-run:
	$(PYLINT) src/git_dag/* > .pylint_report.json || exit 0
	pylint_report .pylint_report.json -o .pylint_report.html

mypy-run:
	mypy || exit 0

setup-venv: ## Install dependencies in a venv
	${PYTHON} -m venv ${VENV_NAME} && $(VENV_ACTIVATE) && pip install --upgrade pip

.PHONY: dist-local
## Build package
dist-local: setup-venv
	$(VENV_ACTIVATE) && pip install build && ${PYTHON} -m build

.PHONY: publish
##! Publish to PyPi
publish: dist-local
	$(VENV_ACTIVATE) && pip install twine && twine upload dist/* --verbose

.PHONY: clean
clean: ##! Clean all
	rm -rf build
	rm -rf .mypy_cache .mypy-html
	rm -rf src/git_dag.egg-info
	rm -rf src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf *.egg-info dist .pytest_cache .coverage
	rm -rf .venv
	rm -rf .pylint_report*
