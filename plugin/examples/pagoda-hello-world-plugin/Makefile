.PHONY: help clean sync install test build

PLUGIN_NAME = airone-hello-world-plugin
PLUGIN_PACKAGE = airone_hello_world_plugin

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

sync: ## Install dependencies using uv
	uv sync
	@echo "✓ Dependencies installed with uv"

install: sync ## Install plugin from source
	uv pip install -e .
	@echo "✓ Plugin installed in development mode"

test: ## Run plugin unit tests
	@echo "Testing plugin import..."
	uv run python -c "from $(PLUGIN_PACKAGE).plugin import HelloWorldPlugin; p = HelloWorldPlugin(); print(f'✓ {p.name} v{p.version} loaded successfully')"
	@echo "Testing plugin hooks..."
	uv run python -c "from $(PLUGIN_PACKAGE).hooks import after_entry_create; print('✓ Hook functions importable')"

build: clean ## Build distribution packages
	uv build

check-deps: ## Check if pagoda-plugin-sdk is available
	@echo "Checking pagoda-plugin-sdk dependency..."
	@uv run python -c "import pagoda_plugin_sdk; print(f'✓ pagoda-plugin-sdk version: {pagoda_plugin_sdk.__version__}')" || (echo "❌ pagoda-plugin-sdk not found. Run 'make sync' to install dependencies" && exit 1)