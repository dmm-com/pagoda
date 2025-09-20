# AirOne Plugin Examples

This directory contains example plugins demonstrating how to create external plugins for AirOne using the pagoda-plugin-sdk framework.

## Plugin Development Workflow

### 1. Prerequisites

Ensure you have the pagoda-plugin-sdk package available:

```bash
# Option A: Install from PyPI (when published)
pip install pagoda-plugin-sdk

# Option B: Install development version locally
cd ../sdk
make install-dev
```

### 2. Creating a New Plugin

For real plugin development, create a **separate repository** with this structure:

```
your-plugin/
├── README.md
├── setup.py                    # Package configuration
├── Makefile                    # Development commands
├── your_plugin_package/
│   ├── __init__.py
│   ├── plugin.py              # Main plugin class
│   ├── hooks.py               # Hook implementations
│   ├── apps.py                # Django app configuration
│   └── api_v2/                # API endpoints
│       ├── __init__.py
│       ├── urls.py
│       └── views.py
```

### 3. Development Process

#### Step 1: Initialize Plugin Project
```bash
# Create new directory for your plugin
mkdir my-airone-plugin
cd my-airone-plugin

# Copy structure from example
cp -r airone-hello-world-plugin/* .

# Customize for your plugin
# - Update setup.py
# - Rename directories/modules
# - Implement your plugin logic
```

#### Step 2: Development Setup
```bash
# Install your plugin in development mode
pip install -e .

# Test plugin loading
python -c "from your_plugin.plugin import YourPlugin; print('✓ Plugin loads')"
```

#### Step 3: Integration Testing
```bash
# Test with AirOne (from AirOne repository root)
export AIRONE_PLUGINS_ENABLED=true
poetry run python manage.py shell -c "
from airone.plugins.registry import plugin_registry
from your_plugin.plugin import YourPlugin
plugin = plugin_registry.register(YourPlugin)
print(f'✓ Plugin registered: {plugin.name}')
"
```

#### Step 4: Distribution
```bash
# Build distribution
python -m build

# Publish to PyPI (or private repository)
twine upload dist/*
```

### 4. Plugin Structure Explanation

#### plugin.py
```python
from pagoda_plugin_sdk import Plugin

class YourPlugin(Plugin):
    # Required metadata
    id = "your-plugin-id"
    name = "Your Plugin Name"
    version = "1.0.0"

    # Django integration
    django_apps = ["your_plugin_package"]

    # API endpoints
    api_v2_patterns = "your_plugin_package.api_v2.urls"

    # Hook registrations
    hooks = {
        "entry.after_create": "your_plugin_package.hooks.after_create_handler",
    }
```

#### setup.py
```python
setup(
    name='your-airone-plugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pagoda-plugin-sdk>=1.0.0',  # Core dependency
        'Django>=3.2',
    ],
    entry_points={
        'airone_plugins': [
            'your-plugin = your_plugin_package.plugin:YourPlugin',
        ],
    },
)
```

## Available Examples

### airone-hello-world-plugin
A basic example demonstrating:
- Plugin registration
- Hook system integration
- API v2 endpoints
- Django app configuration

## Testing Your Plugin

### Unit Testing
```bash
# In your plugin directory
python -m pytest tests/
```

### Integration Testing
```bash
# Test with AirOne
cd /path/to/airone
export AIRONE_PLUGINS_ENABLED=true
poetry run python manage.py test --settings=airone.settings_test
```

### Manual Testing
```bash
# Start AirOne with your plugin
export AIRONE_PLUGINS_ENABLED=true
poetry run python manage.py runserver

# Check plugin status
curl http://localhost:8000/api/v2/plugins/your-plugin/status
```

## Distribution Strategies

### 1. PyPI (Recommended)
```bash
# Publish to public PyPI
twine upload dist/*

# Users install with:
pip install your-airone-plugin
```

### 2. GitHub Releases
```bash
# Create release with built packages
git tag v1.0.0
git push origin v1.0.0

# Users install with:
pip install https://github.com/you/your-plugin/releases/download/v1.0.0/your_plugin-1.0.0-py3-none-any.whl
```

### 3. Private Package Repository
```bash
# Upload to private repository
twine upload --repository-url https://your-repo.com/simple dist/*

# Users install with:
pip install --index-url https://your-repo.com/simple your-airone-plugin
```

## Best Practices

1. **Version pinning**: Pin pagoda-plugin-sdk version in setup.py
2. **Testing**: Include comprehensive tests
3. **Documentation**: Add clear README and API documentation
4. **Compatibility**: Test with supported AirOne versions
5. **Security**: Follow security best practices for hooks and API endpoints