PYTHON := python
VENV := .venv
VENV_ACTIVATE := source ${VENV}/bin/activate
PYLINT := pylint

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
lint:
	$(PYLINT) src/git_dag/* || exit 0

## Run mypy check
.PHONY: mypy
mypy: mypy-run

## Run tests
.PHONY: test
test: test-run

## Execute pre-commit on all files
.PHONY: pre-commit
pre-commit:
	@pre-commit run -a

.PHONY: mypy-run
mypy-run:
	mypy

.PHONY: test-run
test-run:
	coverage run -m pytest -v -s src
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

.PHONY: clean
clean: ##! Clean all
	rm -rf .mypy_cache .mypy-html .htmlcov .pytest_cache .coverage
	rm -rf src/git_dag.egg-info src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf .venv dist $(INTEGR_TEST_DIR)/${OUT_DIR}
