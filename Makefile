PYTHON := python
PYLINT := pylint

VENV := .venv
DOCS_DIR := docs/sphinx

VENV_ACTIVATE := source ${VENV}/bin/activate
HTML_DIR := $(DOCS_DIR)/build/html

LINT_REPORT := .pylint_report

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
lint: .pylint_report.html lint-copy-to-docs

$(LINT_REPORT).html:
	$(PYLINT) src/git_dag/* > $(LINT_REPORT).json || exit 0
	pylint_report $(LINT_REPORT).json -o $@

lint-copy-to-docs: | mkdir-html
	rm -rf $(HTML_DIR)/$(LINT_REPORT).html
	mv -f $(LINT_REPORT).html $(HTML_DIR)
	rm $(LINT_REPORT).json

mkdir-html:
	mkdir -p $(HTML_DIR)

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

## Generate sphinx docs
.PHONY: docs
docs: # lint #rm-docs
	cd $(DOCS_DIR) && make html

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

## Open sphinx documentation
.PHONY: open
open:
	xdg-open ${HTML_DIR}/index.html

##! Delete generated docs
rm-docs:
	@rm -rf $(DOCS_DIR)/src/.autosummary $(DOCS_DIR)/build

##! Clean all
.PHONY: clean
clean: rm-docs
	rm -rf .mypy_cache .mypy-html
	rm -f .pylint_report.*
	rm -rf src/git_dag.egg-info
	rm -rf src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf package .pytest_cache .coverage
	rm -rf .venv
