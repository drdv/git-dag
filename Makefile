PYTHON := python
VENV := .venv
VENV_ACTIVATE := source ${VENV}/bin/activate
PYLINT := pylint
LINT_REPORT := .pylint_report
PYTEST_FLAGS :=
MYPY_FLAGS :=

DOCS_DIR := docs/sphinx
HTML_DIR := $(DOCS_DIR)/build/html

TEST_RESOURCES := src/git_dag/test/resources
INTEGR_TEST_DIR := integration_tests
REPO_DIR := repos
OUT_DIR := out
REF_DIR := references
GITHUB_DRDV := https://github.com/drdv

define clone_repo
	@cd ${INTEGR_TEST_DIR} && git clone $1 $2
endef

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

.PHONY: lint-copy-to-docs
lint-copy-to-docs: | mkdir-html
	rm -rf $(HTML_DIR)/$(LINT_REPORT).html
	mv $(LINT_REPORT).html $(HTML_DIR)
	rm $(LINT_REPORT).json

.PHONY: test-copy-to-docs
test-copy-to-docs: | mkdir-html
	rm -rf $(HTML_DIR)/.htmlcov
	rm -rf $(HTML_DIR)/.test_reports
	mv .htmlcov $(HTML_DIR)
	rm -f $(HTML_DIR)/.htmlcov/.gitignore
	mv .test_reports $(HTML_DIR)

.PHONY: mypy-copy-to-docs
mypy-copy-to-docs: | mkdir-html
	rm -rf $(HTML_DIR)/.mypy-html
	mv .mypy-html $(HTML_DIR)

.PHONY: mkdir-html
mkdir-html:
	mkdir -p $(HTML_DIR)

## Run mypy check
.PHONY: mypy
mypy: mypy-run mypy-copy-to-docs

## Run tests
.PHONY: test
test: test-run test-copy-to-docs

## Execute pre-commit on all files
.PHONY: pre-commit
pre-commit:
	@pre-commit run -a

.PHONY: mypy-run
mypy-run: DOCS_EXAMPLES_DIR := $(DOCS_DIR)/src/examples_generate
mypy-run:
	mypy $(MYPY_FLAGS) src/git_dag $(DOCS_EXAMPLES_DIR)/example_git_internals.py

.PHONY: test-run
test-run:
	coverage run -m pytest $(PYTEST_FLAGS)
	coverage html

##@
##@----- Integration tests -----
##@

## Clone integration test data
get-integr-test-data: clone-integr-test-references clone-integr-test-repos

## Clone repos for integration test
clone-integr-test-repos:
	mkdir -p $(INTEGR_TEST_DIR)/${REPO_DIR}
	-$(call clone_repo, $(GITHUB_DRDV)/git, ${REPO_DIR}/git)
	-$(call clone_repo, $(GITHUB_DRDV)/magit, ${REPO_DIR}/magit)
	-$(call clone_repo, $(GITHUB_DRDV)/pydantic, ${REPO_DIR}/pydantic)
	-$(call clone_repo, $(GITHUB_DRDV)/casadi, ${REPO_DIR}/casadi)

## Clone references for integration test
# I don't want to add them as a submodule
clone-integr-test-references:
	mkdir -p $(INTEGR_TEST_DIR)/${REF_DIR}
	-$(call clone_repo, $(GITHUB_DRDV)/git-dag-integration-tests, ${REF_DIR})

## Generate DAG for integration test repositories
process-integr-test-repos: FIND_FLAGS := -mindepth 1 -maxdepth 1 -type d
process-integr-test-repos:
	@rm -rf $(INTEGR_TEST_DIR)/${OUT_DIR}
	@mkdir -p $(INTEGR_TEST_DIR)/${OUT_DIR}
	@for repo in $(notdir $(shell find $(INTEGR_TEST_DIR)/${REPO_DIR} $(FIND_FLAGS))); do \
		echo -e "--------\n$$repo\n--------"; \
		$(VENV_ACTIVATE) && time git dag -p $(INTEGR_TEST_DIR)/${REPO_DIR}/$$repo \
		-lrtH -n 1000 -f $(INTEGR_TEST_DIR)/${OUT_DIR}/$$repo.gv ; \
	done

##@
##@----- Docs -----
##@

#python example_git_internals.py ; cp /tmp/git-dag-examples/out/* ../.static/example_git_internals/

## Generate sphinx docs with tests lint mypy
.PHONY: docs
docs: test lint mypy docs-run

##! Generate docs examples
.PHONY: docs-examples-generate
docs-examples-generate: DOCS_EXAMPLES_DIR := $(DOCS_DIR)/src/.static
docs-examples-generate: TMP_EXAMPLES_DIR := /tmp/git-dag-examples
docs-examples-generate:
	mkdir -p $(DOCS_EXAMPLES_DIR)/examples/git_internals
	cd $(DOCS_DIR)/src/examples_generate && $(PYTHON) example_git_internals.py
	cp $(TMP_EXAMPLES_DIR)/git_internals/out/{*.rst,*.svg} $(DOCS_EXAMPLES_DIR)/examples/git_internals

##! Generate docs examples
.PHONY: docs-examples-generate
docs-examples-generate: DOCS_EXAMPLES_DIR := $(DOCS_DIR)/src/.static
docs-examples-generate: TMP_EXAMPLES_DIR := /tmp/git-dag-examples
docs-examples-generate:
	mkdir -p $(DOCS_EXAMPLES_DIR)/examples/git_internals
	cd $(DOCS_DIR)/src/examples_generate && $(PYTHON) example_git_internals.py
	cp $(TMP_EXAMPLES_DIR)/git_internals/out/{*.rst,*.svg} $(DOCS_EXAMPLES_DIR)/examples/git_internals

## Generate SVG files for the docs
.PHONY: docs-svg
docs-svg: IMAGES_DIR := $(HTML_DIR)/_static/images/ # images in the generated HTML
docs-svg: TMP_DIR := $(shell mktemp -d /tmp/git-dag-svg-XXXXXX)
docs-svg: DIR_DEFAULT := $(TMP_DIR)/default_repo
docs-svg: DIR_PYDANTIC := $(TMP_DIR)/pydantic
docs-svg:
	mkdir -p $(IMAGES_DIR)

	mkdir $(DIR_DEFAULT)
	tar xf $(TEST_RESOURCES)/default_repo.tar.gz -C $(DIR_DEFAULT)
	git dag -p $(DIR_DEFAULT) -lrtsuHTBD \
		-f $(DIR_DEFAULT)/default_repo.gv
	cp $(DIR_DEFAULT)/default_repo.gv.svg $(IMAGES_DIR)

	mkdir $(DIR_PYDANTIC)
	git dag -p $(INTEGR_TEST_DIR)/$(REPO_DIR)/pydantic -lrtsH \
		-f $(DIR_PYDANTIC)/pydantic.gv
	cp $(DIR_PYDANTIC)/pydantic.gv.svg $(IMAGES_DIR)

	rm -rf $(TMP_DIR)

## Generate sphinx docs
.PHONY: docs-run
docs-run:
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

##! Create reference dag for tests
.PHONY: test-create-reference
test-create-reference:
	cd src/git_dag && $(PYTHON) git_commands.py

## Serve sphinx documentation
.PHONY: docs-serve
docs-serve:
	$(PYTHON) -m http.server -d ${HTML_DIR}

##! Delete generated docs
rm-docs:
	@rm -rf $(DOCS_DIR)/src/.autosummary $(DOCS_DIR)/build

##! Clean all
.PHONY: clean
##! Clean all
clean: rm-docs
	rm -rf .mypy_cache .mypy-html .htmlcov .pytest_cache .coverage
	rm -rf src/git_dag.egg-info src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf .venv dist $(INTEGR_TEST_DIR)/${OUT_DIR}
