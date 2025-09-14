.PHONY: help clean build install install-dev test test-integration publish publish-test

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

build: clean ## Build distribution packages
	python -m build

install: ## Install from source (production)
	pip install .

install-dev: ## Install in development mode
	pip install -e .
	@echo "✓ Plugin installed in development mode"

test: ## Run plugin unit tests
	@echo "Testing plugin import..."
	python -c "from $(PLUGIN_PACKAGE).plugin import HelloWorldPlugin; p = HelloWorldPlugin(); print(f'✓ {p.name} v{p.version} loaded successfully')"
	@echo "Testing plugin hooks..."
	python -c "from $(PLUGIN_PACKAGE).hooks import after_entry_create; print('✓ Hook functions importable')"

test-integration: ## Test integration with AirOne
	@echo "Testing plugin registration with AirOne..."
	@cd ../../../ && AIRONE_PLUGINS_ENABLED=true poetry run python -c "\
import sys; \
sys.path.insert(0, 'plugin_examples/$(PLUGIN_NAME)'); \
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airone.settings'); \
import django; django.setup(); \
from airone.plugins.registry import plugin_registry; \
from $(PLUGIN_PACKAGE).plugin import HelloWorldPlugin; \
plugin = plugin_registry.register(HelloWorldPlugin); \
print(f'✓ Plugin {plugin.name} registered with AirOne'); \
enabled = plugin_registry.get_enabled_plugins(); \
print(f'✓ {len(enabled)} enabled plugin(s) found'); \
"

test-hooks: ## Test hook execution
	@echo "Testing hook execution..."
	@cd ../../../ && AIRONE_PLUGINS_ENABLED=true poetry run python -c "\
import sys; \
sys.path.insert(0, 'plugin_examples/$(PLUGIN_NAME)'); \
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airone.settings'); \
import django; django.setup(); \
from airone.plugins.registry import plugin_registry; \
from $(PLUGIN_PACKAGE).plugin import HelloWorldPlugin; \
plugin = plugin_registry.register(HelloWorldPlugin); \
results = plugin_registry.call_hook('entry.after_create', entry_id=123, name='test'); \
print(f'✓ Hook executed, {len(results)} handlers called'); \
"

check-deps: ## Check if pagoda-core is available
	@echo "Checking pagoda-core dependency..."
	@python -c "import pagoda_core; print(f'✓ pagoda-core version: {pagoda_core.__version__ if hasattr(pagoda_core, \"__version__\") else \"unknown\"}')" || (echo "❌ pagoda-core not found. Install with: cd ../../pagoda-core && make install-dev" && exit 1)

dev-setup: check-deps install-dev ## Set up development environment
	pip install build twine pytest
	@echo "✓ Development environment ready"
	@echo "  Run 'make test' to test the plugin"
	@echo "  Run 'make test-integration' to test with AirOne"

publish-test: build ## Publish to TestPyPI
	@echo "Publishing to TestPyPI..."
	python -m twine upload --repository testpypi dist/*
	@echo "Install with: pip install -i https://test.pypi.org/simple/ $(PLUGIN_NAME)"

publish: build ## Publish to PyPI
	@echo "Publishing to PyPI..."
	python -m twine upload dist/*
	@echo "Install with: pip install $(PLUGIN_NAME)"

version: ## Show current version
	@python setup.py --version

# Demo commands
demo-install: ## Demo: Install plugin and test with AirOne
	@echo "=== Plugin Development Demo ==="
	@echo "1. Installing plugin in development mode..."
	make install-dev
	@echo "2. Testing plugin loading..."
	make test
	@echo "3. Testing AirOne integration..."
	make test-integration
	@echo "✓ Demo completed successfully!"

demo-workflow: ## Demo: Complete development workflow
	@echo "=== Complete Plugin Development Workflow ==="
	@echo "1. Cleaning previous builds..."
	make clean
	@echo "2. Setting up development environment..."
	make dev-setup
	@echo "3. Running tests..."
	make test
	@echo "4. Testing integration..."
	make test-integration
	@echo "5. Building distribution..."
	make build
	@echo "✓ Plugin ready for distribution!"
	@echo "  - Built packages are in dist/"
	@echo "  - Run 'make publish-test' to publish to TestPyPI"