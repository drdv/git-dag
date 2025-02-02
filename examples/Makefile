REPO_DIR := repo
OUT_DIR := out
FLAGS := -lo

MSG_MAX_LENGTH := 5
RANKDIR := RL

help: URL := github.com/drdv/makefile-doc/releases/latest/download/makefile-doc.awk
help: DIR := $(HOME)/.local/share/makefile-doc
help: SCR := $(DIR)/makefile-doc.awk
help: ## show this help
	@test -f $(SCR) || wget -q -P $(DIR) $(URL)
	@awk -f $(SCR) $(MAKEFILE_LIST)

## show git dag
open: mkdir-out
	@git dag -f $(OUT_DIR)/out.gv -p $(REPO_DIR) --commit-message $(MSG_MAX_LENGTH) --rankdir $(RANKDIR) ${FLAGS}

## create repository (e.g., repo_ex1_2)
repo_%: clean mkdir-repo
	@source ./examples.sh; cd $(REPO_DIR); $@

mkdir-repo:
	@mkdir -p $(REPO_DIR)

mkdir-out:
	@mkdir -p $(OUT_DIR)

clean: ##! clean all
	@rm -rf $(REPO_DIR)
	@rm -rf $(OUT_DIR)
