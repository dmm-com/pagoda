# Pagoda Plugin SDK

Core library for the Pagoda plugin system. This package provides the foundation classes and interfaces that all Pagoda plugins must use.

## Overview

Pagoda Plugin SDK implements a clean separation between the core framework, plugins, and extended applications through a three-tier architecture:

1. **Core Layer (pagoda-plugin-sdk)** - This package
2. **Plugin Layer** - External plugins that depend only on pagoda-plugin-sdk
3. **Extended App Layer** - Applications like AirOne that integrate plugins

## Features

- **Plugin Base Classes** - Foundation classes for creating plugins
- **Standard Interfaces** - Well-defined interfaces for authentication, data access, and hooks
- **API Mixins** - Ready-to-use mixins for creating REST API endpoints
- **Independent Distribution** - Complete independence from any specific application

## Installation

```bash
# For plugin development
pip install pagoda-plugin-sdk

# For local development (from source)
pip install -e .
```

## Quick Start

### Creating a Plugin

```python
from pagoda_plugin_sdk import Plugin

class MyPlugin(Plugin):
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"

    django_apps = ["my_plugin"]
    api_v2_patterns = "my_plugin.api_v2.urls"
```

### Creating API Views

```python
from pagoda_plugin_sdk import PluginAPIViewMixin
from rest_framework.response import Response

class MyView(PluginAPIViewMixin):
    def get(self, request):
        return Response({"message": "Hello from my plugin!"})
```

## Architecture

Pagoda Plugin SDK provides interfaces that plugins use to interact with the host application:

- **AuthInterface** - User authentication and authorization
- **DataInterface** - Data access and manipulation
- **HookInterface** - Extension points and event handling

The host application (like AirOne) implements these interfaces to provide concrete functionality.

## Plugin Development

External plugins should:

1. Depend only on `pagoda-plugin-sdk`
2. Use provided interfaces for host application interaction
3. Be installable as independent Python packages
4. Define entry points for automatic discovery

## Development

### Setting up Development Environment

```bash
# Clone and setup pagoda-plugin-sdk for development
git clone https://github.com/dmm-com/pagoda.git
cd pagoda/plugin/sdk

# Install development dependencies
make dev-setup

# Test installation
make test
```

### Building and Publishing

```bash
# Build distribution packages
make build

# Publish to TestPyPI (for testing)
make publish-test

# Publish to PyPI (production)
make publish
```

### Available Make Commands

```bash
make help          # Show available commands
make clean         # Clean build artifacts
make build         # Build distribution packages
make install       # Install from source
make install-dev   # Install in development mode
make test          # Run tests
make publish-test  # Publish to TestPyPI
make publish       # Publish to PyPI
make check-deps    # Check required tools
make dev-setup     # Set up development environment
```

### Version Management

Update version in both:
- `setup.py`
- `pyproject.toml`

Then tag the release:
```bash
git tag v1.0.1
git push origin v1.0.1
```

## Plugin Development Workflow

### 1. Install pagoda-plugin-sdk

```bash
# Option A: From PyPI (recommended)
pip install pagoda-plugin-sdk

# Option B: From source (development)
cd pagoda-plugin-sdk
make install-dev
```

### 2. Create Plugin Structure

```bash
mkdir my-airone-plugin
cd my-airone-plugin

# Create setup.py
cat > setup.py << EOF
from setuptools import setup, find_packages

setup(
    name='my-airone-plugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pagoda-plugin-sdk>=1.0.0',
        'Django>=3.2',
    ],
    entry_points={
        'airone_plugins': [
            'my-plugin = my_plugin.plugin:MyPlugin',
        ],
    },
)
EOF
```

### 3. Implement Plugin

```python
# my_plugin/plugin.py
from pagoda_plugin_sdk import Plugin

class MyPlugin(Plugin):
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    django_apps = ["my_plugin"]
    api_v2_patterns = "my_plugin.api_v2.urls"
    hooks = {
        "entry.after_create": "my_plugin.hooks.after_create",
    }
```

### 4. Test and Distribute

```bash
# Install in development mode
pip install -e .

# Test with host application (e.g., AirOne)
export AIRONE_PLUGINS_ENABLED=true
python manage.py test

# Build and publish
python -m build
twine upload dist/*
```

## Host Application Integration

For applications wanting to support Pagoda plugins:

1. Install pagoda-plugin-sdk
2. Implement the required interfaces (AuthInterface, DataInterface, HookInterface)
3. Create bridge classes connecting interfaces to your application
4. Set up plugin discovery and registration

See the AirOne implementation for a complete example.

## Requirements

- Python >= 3.8
- Django >= 3.2
- djangorestframework >= 3.12

## License

MIT License

## Contributing

This package is part of the Pagoda ecosystem. For development guidelines and contribution information, see the main Pagoda repository.

### Development Tools Required

```bash
# Install required tools for development/publishing
pip install build twine pytest
```