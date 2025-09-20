# Pagoda Hello World Plugin

A sample external plugin demonstrating the Pagoda plugin system capabilities.

## Features

- **API Endpoints**: Provides REST API endpoints under `/api/v2/plugins/hello-world-plugin/`
- **Hook Integration**: Demonstrates how to extend core functionality through hooks
- **External Package**: Shows how to create plugins as separate Python packages
- **Core Library Usage**: Uses `pagoda-plugin-sdk` to access Pagoda core functionality

## Installation

### Development Installation (Editable)

```bash
# Navigate to the plugin directory
cd plugin/examples/pagoda-hello-world-plugin

# Install the plugin in editable mode
pip install -e .
```

### Production Installation

```bash
# Install from local directory
pip install plugin/examples/pagoda-hello-world-plugin/

# Or install from a remote repository
pip install git+https://github.com/user/pagoda-hello-world-plugin.git
```

## Configuration

Enable the plugin explicitly using the environment variable:

```bash
export ENABLED_PLUGINS=hello-world
```

For multiple plugins:
```bash
export ENABLED_PLUGINS=hello-world,another-plugin
```

## API Endpoints

The plugin provides the following API endpoints:

- `GET /api/v2/plugins/hello-world-plugin/hello/` - Basic hello world message
- `POST /api/v2/plugins/hello-world-plugin/hello/` - Execute hello world job
- `GET /api/v2/plugins/hello-world-plugin/greet/<name>/` - Personalized greeting
- `GET /api/v2/plugins/hello-world-plugin/status/` - Plugin status information
- `GET /api/v2/plugins/hello-world-plugin/test/` - Authentication-free test endpoint

## Usage Examples

### Basic Hello World

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/hello/
```

### Personalized Greeting

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/greet/John/
```

### Plugin Status

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/status/
```

### Test Without Authentication

```bash
curl http://localhost:8000/api/v2/plugins/hello-world-plugin/test/
```

## Hook System

The plugin demonstrates hook integration with:

- `entry.after_create` - Called after an entry is created
- `entry.before_update` - Called before an entry is updated

## Development

### Project Structure

```
pagoda-hello-world-plugin/
├── pyproject.toml              # Modern package configuration
├── README.md                   # This file
└── pagoda_hello_world_plugin/  # Main package
    ├── __init__.py             # Package exports
    ├── plugin.py               # Main plugin class
    ├── apps.py                 # Django app configuration
    ├── hooks.py                # Hook implementations
    └── api_v2/                 # API endpoints
        ├── __init__.py
        ├── views.py            # API views
        └── urls.py             # URL patterns
```

### Dependencies

- Django >= 3.2
- Django REST Framework >= 3.12
- pagoda-plugin-sdk >= 1.0.0

**Important**: This plugin uses the `pagoda-plugin-sdk` which provides the core functionality for external plugins. The plugin must be installed in the same Python environment as the host application to access these libraries.

### Plugin Discovery

This plugin uses Python entry points for discovery:

```toml
[project.entry-points."pagoda.plugins"]
hello-world = "pagoda_hello_world_plugin.plugin:HelloWorldPlugin"
```

## License

MIT License - See the main Pagoda project for details.

## Contributing

This is a sample plugin for demonstration purposes. For real plugin development:

1. Fork this plugin as a template
2. Rename the package and update metadata in `pyproject.toml`
3. Update the entry point name in `[project.entry-points."pagoda.plugins"]`
4. Implement your specific functionality
5. Test thoroughly with your Pagoda installation using `ENABLED_PLUGINS=your-plugin`
6. Package and distribute as needed

### Quick Development Setup

```bash
# Clone and setup
git clone https://github.com/user/my-plugin-repo.git
cd my-plugin-repo

# Install in development mode
pip install -e .

# Test with host application
export ENABLED_PLUGINS=my-plugin
python manage.py runserver
```