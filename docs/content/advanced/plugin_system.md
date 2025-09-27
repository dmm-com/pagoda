---
title: Plugin System
weight: 0
---

## Overview

Pagoda's plugin system enables extension through completely independent external plugins using a **3-layer architecture**. This system separates plugins from core functionality and provides stable extension points.

### 3-Layer Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Core Layer    │    │   Plugin Layer   │    │Extended App Layer│
│                 │    │                  │    │                  │
│pagoda-plugin-sdk│◄───│  External Plugin │◄───│     Pagoda       │
│                 │    │                  │    │                  │
│ • Interfaces    │    │ • Plugin Logic   │    │ • Bridge Impl.   │
│ • Base Classes  │    │ • API Endpoints  │    │ • URL Integration│
│ • Common Hooks  │    │ • Hook Handlers  │    │ • Django Setup   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### Core Capabilities

Plugins enable the following extensions:

- **API v2 Endpoints**: RESTful API extensions
- **Hook-Based Extensions**: Intervention and extension of core operations
- **Custom Business Logic**: Unique processing and data manipulation
- **Authentication & Authorization Integration**: Utilizing Pagoda's permission system

## Architecture Deep Dive

### Layer 1: pagoda-plugin-sdk (Core Framework)

Foundation layer provided as an independent PyPI package:

```python
# pagoda_plugin_sdk provides:
from pagoda_plugin_sdk import Plugin, PluginAPIViewMixin
from pagoda_plugin_sdk.interfaces import AuthInterface, DataInterface, HookInterface
from pagoda_plugin_sdk.interfaces import COMMON_HOOKS
```

**Features:**
- Distributable via PyPI
- Depends on Django/DRF but not on Pagoda application
- Standardized interface definitions
- 27 common hook definitions

### Layer 2: External Plugin (Independent Extension)

Completely independent plugin that depends only on pagoda-plugin-sdk:

```python
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

### Layer 3: Pagoda Application (Host Application)

Connects interfaces to concrete implementations using the bridge pattern:

```python
# Pagoda provides concrete implementations
from airone.plugins.bridge import PagodaAuthBridge, PagodaDataBridge, PagodaHookBridge
from airone.plugins.bridge_manager import bridge_manager

# Bridges connect generic interfaces to Pagoda specifics
bridge_manager.auth    # -> PagodaAuthBridge
bridge_manager.data    # -> PagodaDataBridge
bridge_manager.hooks   # -> PagodaHookBridge
```

## Getting Started

### Prerequisites

```bash
# Install pagoda-plugin-sdk (for plugin development)
pip install pagoda-plugin-sdk

# Or development version (for local development)
cd plugin/sdk/
pip install -e .
```

### Plugin Enablement

The plugin system loads only manually specified plugins:

```bash
# Enable a single plugin
export ENABLED_PLUGINS=my-plugin

# Enable multiple plugins (comma-separated)
export ENABLED_PLUGINS=my-plugin,another-plugin
```

### Starting Server with Plugins

```bash
# Start with uv environment (recommended)
ENABLED_PLUGINS=my-plugin uv run python manage.py runserver

# Start with pip environment
ENABLED_PLUGINS=my-plugin python manage.py runserver

# Start after setting environment variable
export ENABLED_PLUGINS=my-plugin
python manage.py runserver
```

**Important**: Only plugins explicitly specified in `ENABLED_PLUGINS` are loaded. If none are specified, the plugin system is disabled.

## Verifying Plugin Operation

### Startup Logs

Logs when the plugin system is operating normally:

```
[INFO] Initializing plugin system...
[INFO] Starting plugin discovery...
[INFO] Loaded external plugin: hello-world
[INFO] Registered plugin: hello-world-plugin v1.0.0
[INFO] Connected Entry model signals to hook system
[INFO] Pagoda bridge manager initialized successfully
[INFO] Registered 2 hooks for plugin hello-world-plugin
[INFO] Plugin discovery completed. Found 1 plugins.
[INFO] Plugin system initialized successfully
```

### Testing Plugin APIs

Sample plugin API endpoints:

```bash
# Authentication-free test endpoint (for verification)
curl http://localhost:8000/api/v2/plugins/hello-world-plugin/test/

# Authentication-required endpoints
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/hello/

curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/greet/John/

curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v2/plugins/hello-world-plugin/status/
```

### Expected Response

```json
{
  "message": "External Hello World Plugin is working via pagoda-core!",
  "plugin": {
    "id": "hello-world-plugin",
    "name": "Hello World Plugin",
    "version": "1.0.0",
    "type": "external",
    "core": "pagoda-core"
  },
  "test": "no-auth",
  "user": {
    "username": "anonymous",
    "is_authenticated": false
  },
  "pagoda_core_version": "1.0.0",
  "timestamp": "2025-09-15T02:09:45.658756"
}
```

## Plugin Development

### Development Workflow

#### 1. Create Plugin Structure

```bash
mkdir my-pagoda-plugin
cd my-pagoda-plugin

# Copy from example
cp -r ../plugin/examples/pagoda-hello-world-plugin/* .
```

#### 2. Plugin Package Structure

```
my-pagoda-plugin/
├── pyproject.toml              # Modern package configuration
├── Makefile                    # Development commands
├── README.md                   # Plugin documentation
└── my_plugin_package/          # Main package
    ├── __init__.py
    ├── plugin.py               # Plugin class definition
    ├── hooks.py                # Hook handlers
    ├── apps.py                 # Django app configuration
    └── api_v2/                 # API endpoints
        ├── __init__.py
        ├── urls.py             # URL configuration
        └── views.py            # API view implementation
```

#### 3. pyproject.toml Configuration

```toml
[project]
name = "my-pagoda-plugin"
version = "1.0.0"
description = "My Pagoda Plugin"
dependencies = [
    "pagoda-plugin-sdk>=1.0.0",  # Core dependency only
    "Django>=3.2",
    "djangorestframework>=3.12",
]
requires-python = ">=3.8"

[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin_package.plugin:MyPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 4. Plugin Class Implementation

```python
from pagoda_plugin_sdk import Plugin

class MyPlugin(Plugin):
    # Required metadata
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    description = "My custom Pagoda plugin"
    author = "Your Name"

    # Django integration
    django_apps = ["my_plugin_package"]
    api_v2_patterns = "my_plugin_package.api_v2.urls"

    # Hook registrations
    hooks = {
        "entry.after_create": "my_plugin_package.hooks.after_create",
        "entry.before_update": "my_plugin_package.hooks.before_update",
    }

```

#### 5. API View Implementation

```python
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pagoda_plugin_sdk import PluginAPIViewMixin

class MyAPIView(PluginAPIViewMixin):
    permission_classes = [AllowAny]  # For testing

    def get(self, request):
        return Response({
            "message": "Hello from my plugin!",
            "plugin": {
                "id": self.plugin_id,
                "name": "My Plugin",
                "version": "1.0.0"
            },
            "timestamp": datetime.now().isoformat()
        })
```

### Development Commands

Development Make commands in plugin directory:

```bash
make help              # Show available commands
make dev-setup         # Set up development environment
make install-dev       # Install in development mode
make test              # Run plugin tests
make test-integration  # Run Pagoda integration tests
make build             # Build distribution packages
make publish-test      # Publish to TestPyPI
make publish           # Publish to PyPI
```

### Distribution Strategies

#### 1. PyPI Distribution

```bash
# Build and publish
make build
make publish

# ユーザー側でインストール
pip install my-pagoda-plugin
```

#### 2. GitHub Releases

```bash
# Create tag and release
git tag v1.0.0
git push origin v1.0.0

# ユーザー側でインストール
pip install https://github.com/user/my-plugin/releases/download/v1.0.0/my_plugin-1.0.0-py3-none-any.whl
```

#### 3. Development Installation

```bash
# Development editable install
pip install -e .

# Development install in Poetry environment
pip install -e .
```

## Sample Plugin Reference

### Available Example

A complete sample plugin is available at `plugin/examples/pagoda-hello-world-plugin/`:

**Endpoints:**
- `GET /api/v2/plugins/hello-world-plugin/test/` - Authentication-free test
- `GET /api/v2/plugins/hello-world-plugin/hello/` - Basic Hello API
- `POST /api/v2/plugins/hello-world-plugin/hello/` - Custom message API
- `GET /api/v2/plugins/hello-world-plugin/greet/<name>/` - Personalized greeting
- `GET /api/v2/plugins/hello-world-plugin/status/` - Plugin status

**Hooks:**
- `entry.after_create` - Post-Entry creation processing
- `entry.before_update` - Pre-Entry update processing

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLED_PLUGINS` | `[]` | List of plugins to enable (comma-separated) |

### Django Settings Integration

```python
# airone/settings_common.py
ENABLED_PLUGINS = env.list("ENABLED_PLUGINS", default=[])

# Plugin system is automatically enabled if any plugins are specified
PLUGINS_ENABLED = bool(ENABLED_PLUGINS)

# Plugin apps are dynamically added to INSTALLED_APPS
if PLUGINS_ENABLED:
    INSTALLED_APPS.extend(plugin_integration.get_installed_apps())
```

### Manual Plugin Control

The plugin system adopts explicit control:

- **No Automatic Discovery**: Does not automatically load available plugins
- **Explicit Specification**: Only loads plugins specified in `ENABLED_PLUGINS`
- **Security**: Prevents loading of unintended plugins
- **Controllability**: Easy plugin control in development and production environments

## Troubleshooting

### Common Issues and Solutions

#### 1. 404 Error on Plugin Endpoints

**Symptoms**: `curl http://localhost:8000/api/v2/plugins/my-plugin/test/` returns 404

**Causes and Solutions**:

```bash
# Cause 1: Plugin not specified
❌ python manage.py runserver
✅ ENABLED_PLUGINS=my-plugin python manage.py runserver

# Cause 2: Plugin not installed
❌ pip install -e plugin_examples/my-plugin/
✅ cd plugin_examples/my-plugin/ && pip install -e .

# Cause 3: Incorrect Entry points path
❌ 'my-plugin = my_plugin:MyPlugin'
✅ 'my-plugin = my_plugin.plugin:MyPlugin'

# Cause 4: Incorrect Entry points group name
❌ [project.entry-points."airone.plugins"]
✅ [project.entry-points."pagoda.plugins"]
```

#### 2. Plugin Discovery Failures

**Log Example**:
```
[ERROR] Failed to load external plugin my-plugin: No module named 'my_plugin'
[INFO] Plugin discovery completed. Found 0 plugins.
```

**Resolution Steps**:

1. **Check Entry points**:
```bash
python -c "
import pkg_resources
for ep in pkg_resources.iter_entry_points('pagoda.plugins'):
    print(f'{ep.name} -> {ep.module_name}:{ep.attrs[0]}')
    try:
        plugin_class = ep.load()
        print(f'✓ Load successful: {plugin_class}')
    except Exception as e:
        print(f'✗ Load failed: {e}')
"
```

2. **プラグイン再インストール**:
```bash
cd my-plugin/
pip uninstall -y my-plugin
rm -rf build/ dist/ *.egg-info/
pip install -e .
```

3. **パスとモジュール確認**:
```bash
python -c "
import sys
sys.path.insert(0, 'plugin_examples/my-plugin')
from my_plugin.plugin import MyPlugin
print(f'✓ Direct import works: {MyPlugin().name}')
"
```

#### 3. Hook Execution Errors

**ログ例**:
```
[ERROR] Hook entry.after_create failed: after_entry_create() missing required arguments
```

**解決法**: フックハンドラーのシグネチャを正しく実装
```python
# ❌ 間違い
def after_entry_create():
    pass

# ✅ 正解
def after_entry_create(sender, instance, created, **kwargs):
    # senderはDjangoモデルクラス
    # instanceは作成されたEntryインスタンス
    # createdは新規作成フラグ
    print(f"New entry created: {instance.name}")
```

#### 4. Plugin Development Environment Issues

**Poetry環境での開発**:
```bash
# pagoda-coreが見つからない
cd pagoda-core/
make install-dev

# プラグイン開発用インストール
cd ../plugin_examples/my-plugin/
pip install -e .

# 統合テスト実行
make test-integration
```

### Debug Commands

```bash
# プラグイン状態確認
ENABLED_PLUGINS=hello-world python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
print(f'Plugins: {plugin_integration.get_enabled_plugin_count()}')
for plugin in plugin_integration.get_enabled_plugins():
    print(f'  - {plugin.name} ({plugin.id}) v{plugin.version}')
"

# URL解決テスト
python -c "
import django
django.setup()
from django.urls import get_resolver
resolver = get_resolver()
match = resolver.resolve('/api/v2/plugins/hello-world-plugin/test/')
print(f'✓ URL resolved: {match.func}')
"

# Hook統計取得
python -c "
from airone.plugins.bridge_manager import bridge_manager
bridge_manager.initialize()
stats = bridge_manager.hooks.get_hook_statistics()
print(f'Total hooks: {stats[\"total_hooks\"]}')
print(f'Registered hooks: {stats[\"registered_hooks\"]}')
"
```

## Architecture Details

### Plugin Discovery Process

```
1. External Plugin Discovery (Entry Points)
   ├─ pkg_resources.iter_entry_points('pagoda.plugins')
   ├─ Load plugin class from entry point
   └─ Register with plugin_registry

2. Example Plugin Discovery (Directory Scan)
   ├─ Scan plugin_examples/ directory
   ├─ Import plugin.py from each plugin directory
   └─ Register discovered plugin classes

3. Plugin Integration
   ├─ Django Apps → INSTALLED_APPS integration
   ├─ URL Patterns → api_v2/urls.py integration
   ├─ Hook Registration → bridge_manager.hooks
   └─ Bridge System Initialization
```

### Hook System Architecture

```python
# Core Layer: 27 common hooks + Pagoda specific hooks (42 total)
COMMON_HOOKS = [
    "entity.before_create", "entity.after_create",
    "entry.before_create", "entry.after_create",
    # ... 23 more
]

# Pagoda Layer: Concrete implementation
class PagodaHookBridge(HookInterface):
    def __init__(self):
        self._hooks = {}
        self._available_hooks = COMMON_HOOKS + PAGODA_SPECIFIC_HOOKS

    def execute_hook(self, hook_name, *args, **kwargs):
        # Execute all registered callbacks with error handling
```

### Bridge Pattern Implementation

```python
# Generic Interface (pagoda-core)
class DataInterface(ABC):
    @abstractmethod
    def get_entity(self, entity_id): pass

# Concrete Implementation (Pagoda)
class PagodaDataBridge(DataInterface):
    def get_entity(self, entity_id):
        from entity.models import Entity
        return Entity.objects.get(id=entity_id)

# Plugin Usage
bridge_manager.data.get_entity(123)  # → Pagoda Entity instance
```

## Best Practices

### 1. Plugin Development

- **Version Pinning**: `pagoda-core>=1.0.0,<2.0.0` で互換性保証
- **Testing**: 単体テスト + Pagoda統合テスト の両方実装
- **Documentation**: README + API仕様書 を含める
- **Error Handling**: フックとAPIで適切な例外処理
- **Security**: 認証・認可の適切な実装

### 2. Distribution

- **Semantic Versioning**: `major.minor.patch` で適切なバージョニング
- **Changelog**: リリースノート・変更履歴の維持
- **Compatibility**: サポートするPagoda/pagoda-plugin-sdkバージョンの明記
- **Dependencies**: 最小限の依存関係に抑制

### 3. Production Deployment

- **Environment Isolation**: プラグイン毎の仮想環境分離
- **Monitoring**: プラグインエラーのログ監視
- **Rollback Strategy**: プラグイン無効化手順の準備
- **Performance**: フック処理の性能影響評価

この3層アーキテクチャにより、Pagodaから完全に独立したプラグインシステムが実現されています。プラグイン開発者は `pagoda-plugin-sdk` のみに依存して、安全で再利用可能なプラグインを作成できます。