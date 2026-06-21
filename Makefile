# Research Paper Workflow Framework — Makefile
.PHONY: help install install-skills test test-verbose lint clean init-paper

.DEFAULT_GOAL := help

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[0;34m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install framework in development mode
	pip install -e .
	python -m paper_workflow.cli.main install-skills

install-full: ## Install with plotting dependencies
	pip install -e ".[plotting]"
	python -m paper_workflow.cli.main install-skills

install-all: ## Install with all dependencies
	pip install -e ".[full]"
	python -m paper_workflow.cli.main install-skills

install-skills: ## Compare and install missing bundled Claude/Codex skills
	python -m paper_workflow.cli.main install-skills

test: ## Run integration tests
	python tests/test_all.py

test-verbose: ## Run tests with verbose output
	python -m pytest tests/test_all.py -v

lint: ## Run Python linter
	python -m ruff check src/paper_workflow/ --select=E,F,W --ignore=E501,F401 || true

format: ## Format Python code
	python -m ruff format src/paper_workflow/

init-paper: ## Create a new paper project (usage: make init-paper IDEA="..." FIELD="..." JOURNAL="...")
	python -m paper_workflow.cli.main create-project --idea "$(IDEA)" --field "$(FIELD)" --journal "$(JOURNAL)"

status: ## Show paper status (usage: make status PAPER=<id>)
	python -m paper_workflow.cli.main status --paper $(PAPER)

run: ## Run paper pipeline (usage: make run PAPER=<id>)
	python -m paper_workflow.cli.main run-pipeline --paper $(PAPER)

integrity: ## Run integrity gates (usage: make integrity PAPER=<id>)
	python -m paper_workflow.cli.main run-integrity-gate --paper $(PAPER)

list: ## List all paper projects
	python -m paper_workflow.cli.main list-papers

clean: ## Clean Python cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
