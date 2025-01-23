PYTHON := python
VENV := .venv
VENV_ACTIVATE := source ${VENV}/bin/activate

PYLINT := pylint

help: URL := github.com/drdv/makefile-doc/releases/latest/download/makefile-doc.awk
help: DIR := $(HOME)/.local/share/makefile-doc
help: SCR := $(DIR)/makefile-doc.awk
help: ## show this help
	@test -f $(SCR) || wget -q -P $(DIR) $(URL)
	@awk -f $(SCR) $(MAKEFILE_LIST)

##@
##@----- Code quality -----
##@

## Lint code
.PHONY: lint
lint:
	$(PYLINT) src/git_dag/*

## Run mypy check
.PHONY: mypy
mypy: mypy-run

## Execute pre-commit on all files
.PHONY: pre-commit
pre-commit:
	@pre-commit run -a

.PHONY: mypy-run
mypy-run:
	mypy || exit 0

##@
##@----- Installation and packaging -----
##@

## Editable install in venv
.PHONY: install
install: | $(VENV)
	$(VENV_ACTIVATE) && pip install -e .[dev]

$(VENV):
	${PYTHON} -m venv $@ && $(VENV_ACTIVATE) && pip install --upgrade pip

## Build package
.PHONY: package
package: | $(VENV)
	$(VENV_ACTIVATE) && pip install build && ${PYTHON} -m build

.PHONY: release
## Create github release at latest tag
release: LATEST_TAG != git describe --tags
release: RELEASE_NOTES := release_notes.md
release:
	@test -f $($(RELEASE_NOTES)) && \
	gh release create $(LATEST_TAG) makefile-doc.awk \
		--generate-notes \
		--notes-file release_notes.md -t '$(LATEST_TAG)' || \
	echo "No file $(RELEASE_NOTES)"

##! Publish on PyPi
.PHONY: publish
publish: package
	$(VENV_ACTIVATE) && pip install twine && twine upload dist/* --verbose

##@
##@----- Other -----
##@

.PHONY: clean
clean: ##! Clean all
	rm -rf .mypy_cache .mypy-html
	rm -rf src/git_dag.egg-info
	rm -rf src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf package .pytest_cache .coverage
	rm -rf .venv
