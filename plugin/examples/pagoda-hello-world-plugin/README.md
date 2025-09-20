# AirOne Hello World Plugin

A sample external plugin demonstrating the AirOne plugin system capabilities.

## Features

- **API Endpoints**: Provides REST API endpoints under `/api/v2/plugins/hello-world-plugin/`
- **Hook Integration**: Demonstrates how to extend core functionality through hooks
- **External Package**: Shows how to create plugins as separate Python packages
- **Core Library Usage**: Uses `airone.libs` to access AirOne core functionality

## Installation

### Development Installation (Editable)

```bash
# Navigate to the plugin directory
cd external_plugins/airone-hello-world-plugin

# Install the plugin in editable mode
pip install -e .
```

### Production Installation

```bash
# Install from local directory
pip install external_plugins/airone-hello-world-plugin/

# Or install from a remote repository (future)
# pip install airone-hello-world-plugin
```

## Configuration

Ensure that the AirOne plugin system is enabled:

```bash
export AIRONE_PLUGINS_ENABLED=true
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
airone-hello-world-plugin/
├── setup.py                    # Package configuration
├── README.md                   # This file
└── airone_hello_world_plugin/  # Main package
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
- AirOne core system (for accessing `airone.libs`)

**Important**: This plugin imports from `airone.libs` which provides the core functionality for external plugins. The plugin must be installed in the same Python environment as AirOne to access these libraries.

### Plugin Discovery

This plugin uses Python entry points for automatic discovery:

```python
entry_points={
    'airone.plugins': [
        'hello-world = airone_hello_world_plugin:HelloWorldPlugin',
    ],
}
```

## License

MIT License - See the main AirOne project for details.

## Contributing

This is a sample plugin for demonstration purposes. For real plugin development:

1. Fork this plugin as a template
2. Rename the package and update metadata in `setup.py`
3. Implement your specific functionality
4. Test thoroughly with your AirOne installation
5. Package and distribute as needed