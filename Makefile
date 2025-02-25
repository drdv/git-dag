PYTHON := python
VENV := .venv
VENV_ACTIVATE := source ${VENV}/bin/activate

INTEGRATION_TEST_DIR := integration_tests
INTEGRATION_TEST_REPOS_DIR := $(INTEGRATION_TEST_DIR)/repos
INTEGRATION_TEST_OUT_DIR := $(INTEGRATION_TEST_DIR)/out
INTEGRATION_TEST_REFS_DIR := $(INTEGRATION_TEST_DIR)/references

PYLINT := pylint

define clone_repo
	@cd ${INTEGRATION_TEST_REPOS_DIR} && git clone $1 $2
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
	$(PYLINT) src/git_dag/*

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
	mypy || exit 0

test-run:
	coverage run -m pytest -v -s src
	coverage html

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

## Clone integration test data
get-integration-test-data: clone-integration-test-references clone-integration-test-repos

## Clone repos for integration test
clone-integration-test-repos:
	mkdir -p ${INTEGRATION_TEST_REPOS_DIR}
	-$(call clone_repo, https://github.com/drdv/git)
	-$(call clone_repo, https://github.com/drdv/magit)
	-$(call clone_repo, https://github.com/drdv/pydantic)
	-$(call clone_repo, https://github.com/drdv/casadi)

## Clone references for integration test
# I don't want to add them as a submodule
clone-integration-test-references:
	mkdir -p ${INTEGRATION_TEST_REPOS_DIR} ${INTEGRATION_TEST_REFS_DIR}
	-$(call clone_repo, https://github.com/drdv/git-dag-integration-tests, ../references)

## Process integration test repositories
process-integration-test-repos:
	@rm -rf ${INTEGRATION_TEST_OUT_DIR}
	@mkdir -p ${INTEGRATION_TEST_OUT_DIR}
	@for repo in $(notdir $(shell find ${INTEGRATION_TEST_REPOS_DIR} -mindepth 1 -maxdepth 1 -type d)); do \
		echo -e "--------\n$$repo\n--------"; \
		$(VENV_ACTIVATE) && time git dag -p ${INTEGRATION_TEST_REPOS_DIR}/$$repo \
		-lrtH -n 1000 -f ${INTEGRATION_TEST_OUT_DIR}/$$repo.gv ; \
	done

.PHONY: clean
clean: ##! Clean all
	rm -rf .mypy_cache .mypy-html
	rm -rf src/git_dag.egg-info
	rm -rf src/git_dag/_version.py
	find . -name "__pycache__" | xargs rm -rf
	rm -rf package .pytest_cache .coverage
	rm -rf .venv
