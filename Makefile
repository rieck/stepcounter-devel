.PHONY: help install install-dev format lint check

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install the package with development dependencies
	pip install -e ".[dev]"

format:  ## Format code with Black and isort
	black .
	isort .

lint:  ## Run linting with flake8
	flake8 .

check: format lint  ## Run formatting and linting