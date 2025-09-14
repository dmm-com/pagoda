---
title: Plugin System
weight: 0
---

## Overview

AirOneのプラグインシステムは、**3層アーキテクチャ**により完全に独立した外部プラグインによる拡張を可能にします。このシステムは、コア機能からプラグインを分離し、安定した拡張ポイントを提供します。

### 3層アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Core Layer    │    │   Plugin Layer   │    │Extended App Layer│
│                 │    │                  │    │                  │
│   pagoda-core   │◄───│  External Plugin │◄───│     AirOne       │
│                 │    │                  │    │                  │
│ • Interfaces    │    │ • Plugin Logic   │    │ • Bridge Impl.   │
│ • Base Classes  │    │ • API Endpoints  │    │ • URL Integration│
│ • Common Hooks  │    │ • Hook Handlers  │    │ • Django Setup   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### Core Capabilities

プラグインによって以下の拡張が可能です：

- **API v2エンドポイント**: RESTfulなAPI拡張
- **フックベース拡張**: コア操作への介入・拡張
- **カスタムビジネスロジック**: 独自の処理とデータ操作
- **認証・認可統合**: AirOneの権限システム活用

## Architecture Deep Dive

### Layer 1: pagoda-core (Core Framework)

独立したPyPIパッケージとして提供される基盤層：

```python
# pagoda_core provides:
from pagoda_core import Plugin, PluginAPIViewMixin
from pagoda_core.interfaces import AuthInterface, DataInterface, HookInterface
from pagoda_core.interfaces import COMMON_HOOKS
```

**特徴:**
- PyPI経由で配布可能
- Django/DRFに依存するが、AirOneに依存しない
- 標準化されたインターフェース定義
- 27個の共通フック定義

### Layer 2: External Plugin (Independent Extension)

pagoda-coreのみに依存する完全独立プラグイン：

```python
from pagoda_core import Plugin

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

### Layer 3: AirOne (Host Application)

ブリッジパターンでインターフェースを具体実装に接続：

```python
# AirOne provides concrete implementations
from airone.plugins.bridge import AirOneAuthBridge, AirOneDataBridge, AirOneHookBridge
from airone.plugins.bridge_manager import bridge_manager

# Bridges connect generic interfaces to AirOne specifics
bridge_manager.auth    # -> AirOneAuthBridge
bridge_manager.data    # -> AirOneDataBridge
bridge_manager.hooks   # -> AirOneHookBridge
```

## Getting Started

### Prerequisites

```bash
# pagoda-core のインストール (プラグイン開発用)
pip install pagoda-core

# または開発版 (ローカル開発時)
cd pagoda-core/
make install-dev
```

### Enabling Plugin System

デフォルトでは無効になっています。有効化するには：

```bash
export AIRONE_PLUGINS_ENABLED=true
```

### Starting Server with Plugins

```bash
# Poetry環境での起動
AIRONE_PLUGINS_ENABLED=true poetry run python manage.py runserver

# 環境変数設定後の起動
export AIRONE_PLUGINS_ENABLED=true
poetry run python manage.py runserver
```

**重要**: `AIRONE_PLUGINS_ENABLED=true` の設定なしでは、プラグインのURLパターンが統合されず404エラーになります。

## Verifying Plugin Operation

### Startup Logs

プラグインシステムが正常動作している場合のログ：

```
[INFO] Initializing plugin system...
[INFO] Starting plugin discovery...
[INFO] Loaded external plugin: hello-world
[INFO] Registered plugin: hello-world-plugin v1.0.0
[INFO] Connected Entry model signals to hook system
[INFO] AirOne bridge manager initialized successfully
[INFO] Registered 2 hooks for plugin hello-world-plugin
[INFO] Plugin discovery completed. Found 1 plugins.
[INFO] Plugin system initialized successfully
```

### Testing Plugin APIs

サンプルプラグインのAPIエンドポイント：

```bash
# 認証不要テストエンドポイント（動作確認用）
curl http://localhost:8000/api/v2/plugins/hello-world-plugin/test/

# 認証必要エンドポイント
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
mkdir my-airone-plugin
cd my-airone-plugin

# Copy from example
cp -r ../airone/plugin_examples/airone-hello-world-plugin/* .
```

#### 2. Plugin Package Structure

```
my-airone-plugin/
├── setup.py                    # PyPI配布用設定
├── Makefile                    # 開発用コマンド
├── README.md                   # プラグイン説明書
└── my_plugin_package/          # メインパッケージ
    ├── __init__.py
    ├── plugin.py               # プラグインクラス定義
    ├── hooks.py                # フックハンドラー
    ├── apps.py                 # Django app設定
    └── api_v2/                 # API エンドポイント
        ├── __init__.py
        ├── urls.py             # URL設定
        └── views.py            # API view実装
```

#### 3. setup.py Configuration

```python
from setuptools import setup, find_packages

setup(
    name='my-airone-plugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pagoda-core>=1.0.0',  # Core dependency only
        'Django>=3.2',
        'djangorestframework>=3.12',
    ],
    entry_points={
        'airone.plugins': [
            'my-plugin = my_plugin_package.plugin:MyPlugin',  # 正確なパス指定
        ],
    },
)
```

#### 4. Plugin Class Implementation

```python
from pagoda_core import Plugin

class MyPlugin(Plugin):
    # Required metadata
    id = "my-plugin"
    name = "My Plugin"
    version = "1.0.0"
    description = "My custom AirOne plugin"
    author = "Your Name"

    # Django integration
    django_apps = ["my_plugin_package"]
    api_v2_patterns = "my_plugin_package.api_v2.urls"

    # Hook registrations
    hooks = {
        "entry.after_create": "my_plugin_package.hooks.after_create",
        "entry.before_update": "my_plugin_package.hooks.before_update",
    }

    # Job operations (optional)
    job_operations = {}
```

#### 5. API View Implementation

```python
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pagoda_core import PluginAPIViewMixin

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

プラグインディレクトリでの開発用Makeコマンド：

```bash
make help              # 利用可能コマンド表示
make dev-setup         # 開発環境セットアップ
make install-dev       # 開発モードインストール
make test              # プラグインテスト
make test-integration  # AirOne統合テスト
make build             # 配布パッケージビルド
make publish-test      # TestPyPI公開
make publish           # PyPI公開
```

### Distribution Strategies

#### 1. PyPI Distribution

```bash
# ビルドして公開
make build
make publish

# ユーザー側でインストール
pip install my-airone-plugin
```

#### 2. GitHub Releases

```bash
# タグ作成・リリース
git tag v1.0.0
git push origin v1.0.0

# ユーザー側でインストール
pip install https://github.com/user/my-plugin/releases/download/v1.0.0/my_plugin-1.0.0-py3-none-any.whl
```

#### 3. Development Installation

```bash
# 開発用editable install
pip install -e .

# Poetry環境での開発用インストール
poetry run pip install -e .
```

## Sample Plugin Reference

### Available Example

`plugin_examples/airone-hello-world-plugin/` に完全なサンプルプラグインがあります：

**エンドポイント:**
- `GET /api/v2/plugins/hello-world-plugin/test/` - 認証不要テスト
- `GET /api/v2/plugins/hello-world-plugin/hello/` - 基本Hello API
- `POST /api/v2/plugins/hello-world-plugin/hello/` - カスタムメッセージAPI
- `GET /api/v2/plugins/hello-world-plugin/greet/<name>/` - パーソナライズ挨拶
- `GET /api/v2/plugins/hello-world-plugin/status/` - プラグインステータス

**フック:**
- `entry.after_create` - Entry作成後処理
- `entry.before_update` - Entry更新前処理

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIRONE_PLUGINS_ENABLED` | `false` | プラグインシステム有効化 |

### Django Settings Integration

```python
# airone/settings_common.py
AIRONE_PLUGINS_ENABLED = env.bool("AIRONE_PLUGINS_ENABLED", False)

AIRONE = {
    "PLUGINS": {
        "ENABLED": AIRONE_PLUGINS_ENABLED,
    }
}

# Plugin apps are dynamically added to INSTALLED_APPS
if AIRONE_PLUGINS_ENABLED:
    INSTALLED_APPS.extend(plugin_integration.get_installed_apps())
```

## Troubleshooting

### Common Issues and Solutions

#### 1. 404 Error on Plugin Endpoints

**症状**: `curl http://localhost:8000/api/v2/plugins/my-plugin/test/` が404

**原因と解決法**:

```bash
# 原因1: プラグインシステム無効
❌ poetry run python manage.py runserver
✅ AIRONE_PLUGINS_ENABLED=true poetry run python manage.py runserver

# 原因2: プラグイン未インストール（poetry環境）
❌ pip install -e plugin_examples/my-plugin/
✅ cd plugin_examples/my-plugin/ && poetry run pip install -e .

# 原因3: Entry pointsパス間違い
❌ 'my-plugin = my_plugin:MyPlugin'
✅ 'my-plugin = my_plugin.plugin:MyPlugin'
```

#### 2. Plugin Discovery Failures

**ログ例**:
```
[ERROR] Failed to load external plugin my-plugin: No module named 'my_plugin'
[INFO] Plugin discovery completed. Found 0 plugins.
```

**解決手順**:

1. **Entry points確認**:
```bash
poetry run python -c "
import pkg_resources
for ep in pkg_resources.iter_entry_points('airone.plugins'):
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
poetry run python -c "
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
poetry run pip install -e .

# 統合テスト実行
make test-integration
```

### Debug Commands

```bash
# プラグイン状態確認
AIRONE_PLUGINS_ENABLED=true poetry run python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
print(f'Plugins: {plugin_integration.get_enabled_plugin_count()}')
for plugin in plugin_integration.get_enabled_plugins():
    print(f'  - {plugin.name} ({plugin.id}) v{plugin.version}')
"

# URL解決テスト
poetry run python -c "
import django
django.setup()
from django.urls import get_resolver
resolver = get_resolver()
match = resolver.resolve('/api/v2/plugins/hello-world-plugin/test/')
print(f'✓ URL resolved: {match.func}')
"

# Hook統計取得
poetry run python -c "
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
   ├─ pkg_resources.iter_entry_points('airone.plugins')
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
# Core Layer: 27 common hooks + AirOne specific hooks (42 total)
COMMON_HOOKS = [
    "entity.before_create", "entity.after_create",
    "entry.before_create", "entry.after_create",
    # ... 23 more
]

# AirOne Layer: Concrete implementation
class AirOneHookBridge(HookInterface):
    def __init__(self):
        self._hooks = {}
        self._available_hooks = COMMON_HOOKS + AIRONE_SPECIFIC_HOOKS

    def execute_hook(self, hook_name, *args, **kwargs):
        # Execute all registered callbacks with error handling
```

### Bridge Pattern Implementation

```python
# Generic Interface (pagoda-core)
class DataInterface(ABC):
    @abstractmethod
    def get_entity(self, entity_id): pass

# Concrete Implementation (AirOne)
class AirOneDataBridge(DataInterface):
    def get_entity(self, entity_id):
        from entity.models import Entity
        return Entity.objects.get(id=entity_id)

# Plugin Usage
bridge_manager.data.get_entity(123)  # → AirOne Entity instance
```

## Best Practices

### 1. Plugin Development

- **Version Pinning**: `pagoda-core>=1.0.0,<2.0.0` で互換性保証
- **Testing**: 単体テスト + AirOne統合テスト の両方実装
- **Documentation**: README + API仕様書 を含める
- **Error Handling**: フックとAPIで適切な例外処理
- **Security**: 認証・認可の適切な実装

### 2. Distribution

- **Semantic Versioning**: `major.minor.patch` で適切なバージョニング
- **Changelog**: リリースノート・変更履歴の維持
- **Compatibility**: サポートするAirOne/pagoda-coreバージョンの明記
- **Dependencies**: 最小限の依存関係に抑制

### 3. Production Deployment

- **Environment Isolation**: プラグイン毎の仮想環境分離
- **Monitoring**: プラグインエラーのログ監視
- **Rollback Strategy**: プラグイン無効化手順の準備
- **Performance**: フック処理の性能影響評価

この3層アーキテクチャにより、AirOneから完全に独立したプラグインシステムが実現されています。プラグイン開発者は `pagoda-core` のみに依存して、安全で再利用可能なプラグインを作成できます。