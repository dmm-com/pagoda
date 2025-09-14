.PHONY: help clean build install install-dev test publish publish-test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build distribution packages
	python -m build

install: ## Install from source (production)
	pip install .

install-dev: ## Install in development mode
	pip install -e .

test: ## Run tests (placeholder)
	@echo "Tests would run here"
	python -c "import pagoda_core; print('✓ Package imports successfully')"

publish-test: build ## Publish to TestPyPI
	@echo "Publishing to TestPyPI..."
	python -m twine upload --repository testpypi dist/*
	@echo "Install with: pip install -i https://test.pypi.org/simple/ pagoda-core"

publish: build ## Publish to PyPI
	@echo "Publishing to PyPI..."
	python -m twine upload dist/*
	@echo "Install with: pip install pagoda-core"

check-deps: ## Check if required tools are installed
	@echo "Checking required dependencies..."
	@python -c "import build" || (echo "❌ 'build' not found. Install with: pip install build" && exit 1)
	@python -c "import twine" || (echo "❌ 'twine' not found. Install with: pip install twine" && exit 1)
	@echo "✓ All required tools are installed"

version: ## Show current version
	@python setup.py --version

# Development workflow commands
dev-setup: ## Set up development environment
	pip install -e .
	pip install build twine
	@echo "✓ Development environment ready"

dev-test: ## Test development installation
	python -c "from pagoda_core import Plugin; print('✓ pagoda-core development install working')"