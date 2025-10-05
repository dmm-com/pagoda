---
title: Plugin Development Quick Start Guide
weight: 2
---

## Plugin Development in 5 Minutes

This guide provides the shortest steps to create and verify your first plugin using the Pagoda plugin system.

### Step 1: Environment Setup (2 minutes)

#### 1.1 Setting up pagoda-plugin-sdk in Pagoda Environment

```bash
cd /path/to/pagoda

# Install development version of pagoda-plugin-sdk
cd plugin/sdk/
make install-dev

# インストール確認
python -c "import pagoda_plugin_sdk; print('✓ pagoda-plugin-sdk ready')"
```

#### 1.2 Verify Operation with Sample Plugin

```bash
# Enable plugin and start server
ENABLED_PLUGINS=hello-world python manage.py runserver 8080 &

# Verify operation in separate terminal
curl http://localhost:8080/api/v2/plugins/hello-world-plugin/test/
```

**Expected Response:**
```json
{
  "message": "External Hello World Plugin is working via pagoda-plugin-sdk!",
  "plugin": {
    "id": "hello-world-plugin",
    "name": "Hello World Plugin",
    "version": "1.0.0",
    "type": "external",
    "core": "pagoda-plugin-sdk"
  }
}
```

✅ **If everything works correctly up to this point, environment setup is complete!**

### Step 2: Creating Your First Plugin (3 minutes)

#### 2.1 Create Plugin Project

```bash
# Create working directory
mkdir my-first-plugin
cd my-first-plugin

# Copy from sample to start
cp -r ../plugin/examples/pagoda-hello-world-plugin/* .

# Customize plugin name
sed -i 's/hello-world-plugin/my-first-plugin/g' pyproject.toml
sed -i 's/pagoda_hello_world_plugin/my_first_plugin/g' pyproject.toml
```

#### 2.2 Rename Plugin Structure

```bash
# Change directory and file names
mv pagoda_hello_world_plugin my_first_plugin
```

#### 2.3 Customize Plugin Class

```python
# my_first_plugin/plugin.py
from pagoda_plugin_sdk import Plugin

class MyFirstPlugin(Plugin):
    id = "my-first-plugin"
    name = "My First Plugin"
    version = "1.0.0"
    description = "My very first Pagoda plugin"
    author = "Your Name"

    django_apps = ["my_first_plugin"]
    api_v2_patterns = "my_first_plugin.api_v2.urls"

    hooks = {
        "entry.after_create": "my_first_plugin.hooks.after_entry_create",
    }
```

#### 2.4 Customize API Endpoints

```python
# my_first_plugin/api_v2/views.py
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from pagoda_plugin_sdk import PluginAPIViewMixin

class MyFirstView(PluginAPIViewMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "message": "Hello from My First Plugin!",
            "plugin": {
                "id": "my-first-plugin",
                "name": "My First Plugin",
                "version": "1.0.0"
            },
            "custom_data": {
                "greeting": "Welcome to plugin development!",
                "tips": "Check the documentation for advanced features"
            },
            "timestamp": datetime.now().isoformat()
        })
```

```python
# my_first_plugin/api_v2/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.MyFirstView.as_view(), name="test"),
    path("hello/", views.MyFirstView.as_view(), name="hello"),
]
```

#### 2.5 Customize Hook Handlers

```python
# my_first_plugin/hooks.py
import logging

logger = logging.getLogger(__name__)

def after_entry_create(sender, instance, created, **kwargs):
    """Hook executed after Entry creation"""
    if created:
        logger.info(f"🎉 New entry created via My First Plugin: {instance.name}")
        print(f"My First Plugin detected new entry: {instance.name}")
```

### Step 3: Plugin Testing & Installation

#### 3.1 Plugin Installation

```bash
# Development installation
pip install -e .

# インストール確認
python -c "
from my_first_plugin.plugin import MyFirstPlugin
plugin = MyFirstPlugin()
print(f'✓ Plugin ready: {plugin.name} v{plugin.version}')
"
```

#### 3.2 Testing with Pagoda

```bash
# Restart Pagoda server (to recognize new plugin)
pkill -f "manage.py runserver"
ENABLED_PLUGINS=my-first-plugin python manage.py runserver 8080 &

# Test plugin endpoint
curl http://localhost:8080/api/v2/plugins/my-first-plugin/test/
```

**Logs on Success:**
```
[INFO] Registered plugin: my-first-plugin v1.0.0
[INFO] Registered 1 hooks for plugin my-first-plugin
[INFO] Plugin discovery completed. Found 2 plugins.
```

## Practical Troubleshooting

### Issue 1: 404 Error - Plugin Not Found

**Symptoms:**
```bash
curl http://localhost:8080/api/v2/plugins/my-plugin/test/
# 404 Not Found
```

**Diagnostic Steps:**

```bash
# 1. プラグインシステムが有効か確認
python manage.py shell -c "
from django.conf import settings
print('Plugin system enabled:', bool(getattr(settings, 'ENABLED_PLUGINS', [])))
"

# 2. プラグイン登録状況確認
ENABLED_PLUGINS=my-first-plugin python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
plugins = plugin_integration.get_enabled_plugins()
for p in plugins:
    print(f'Plugin: {p.id} - {p.name}')
"

# 3. Entry points確認
python -c "
import pkg_resources
entries = list(pkg_resources.iter_entry_points('pagoda.plugins'))
print(f'Found {len(entries)} entry points:')
for ep in entries:
    print(f'  {ep.name} -> {ep.module_name}')
"
```

**解決法:**
```bash
# 最も多い原因: 環境変数不足
❌ python manage.py runserver
✅ ENABLED_PLUGINS=my-first-plugin python manage.py runserver

# 次に多い原因: プラグインが未インストール
pip install -e .

# Entry pointsパス間違い
# pyproject.tomlを確認して正しいパス指定に修正
```

### 問題 2: Import エラー - モジュールが見つからない

**Symptoms:**
```
[ERROR] Failed to load external plugin: No module named 'my_plugin'
```

**診断・解決手順:**

```bash
# 1. プラグインが正しくインストールされているか
pip list | grep my-plugin

# 2. モジュール構造を確認
tree my-plugin/
# 期待される構造:
# my-plugin/
# ├── setup.py
# └── my_plugin/
#     ├── __init__.py
#     └── plugin.py

# 3. Entry pointsパスを確認・修正
# pyproject.toml内で:
[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"  # ← 正確なパス

# 4. 再インストール
pip uninstall -y my-plugin
rm -rf build/ dist/ *.egg-info/
pip install -e .
```

### 問題 3: Hook実行エラー

**Symptoms:**
```
[ERROR] Hook entry.after_create failed: missing required arguments
```

**解決法:**
```python
# ❌ 間違ったシグネチャ
def after_entry_create():
    pass

# ❌ 引数不足
def after_entry_create(instance):
    pass

# ✅ 正しいシグネチャ
def after_entry_create(sender, instance, created, **kwargs):
    """
    sender: Djangoモデルクラス (entry.models.Entry)
    instance: 作成されたEntryインスタンス
    created: 新規作成フラグ (True/False)
    **kwargs: その他のDjango signal引数
    """
    if created:
        print(f"New entry: {instance.name}")
```

## Accessing Host Application Models

### Overview

Plugins can access Pagoda's models (Entity, Entry, User, etc.) through the plugin SDK's model injection mechanism. This provides type-safe access to host application data.

### Basic Model Import

```python
# Import models from the plugin SDK
from pagoda_plugin_sdk.models import Entity, Entry, User

class MyPluginView(PluginAPIViewMixin):
    def get(self, request):
        # Access models directly
        entities = Entity.objects.filter(is_active=True)
        entries = Entry.objects.filter(schema__name="MyEntity")
```

### Entity Access Examples

**List All Entities:**

```python
from pagoda_plugin_sdk.models import Entity
from rest_framework.response import Response

class EntityListView(PluginAPIViewMixin):
    def get(self, request):
        # Get all active entities
        entities = Entity.objects.filter(is_active=True)

        # Convert to response format
        entity_list = []
        for entity in entities:
            entity_list.append({
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "created_user": entity.created_user.username if entity.created_user else None,
            })

        return Response({"entities": entity_list, "count": len(entity_list)})
```

**Get Entity Details:**

```python
from pagoda_plugin_sdk.models import Entity

class EntityDetailView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        try:
            entity = Entity.objects.get(id=entity_id, is_active=True)

            return Response({
                "id": entity.id,
                "name": entity.name,
                "note": entity.note,
                "is_active": entity.is_active,
                "created_time": entity.created_time.isoformat() if entity.created_time else None,
            })
        except Entity.DoesNotExist:
            return Response(
                {"error": f"Entity {entity_id} not found"},
                status=404
            )
```

### Entry Access Examples

**List Entries with Filtering:**

```python
from pagoda_plugin_sdk.models import Entry

class EntryListView(PluginAPIViewMixin):
    def get(self, request):
        # Get query parameters
        entity_id = request.GET.get("entity_id")
        limit = request.GET.get("limit", 100)

        # Build query
        queryset = Entry.objects.filter(is_active=True)

        if entity_id:
            queryset = queryset.filter(schema_id=entity_id)

        # Limit results
        entries = queryset[:int(limit)]

        # Format response
        entry_list = []
        for entry in entries:
            entry_list.append({
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                } if entry.schema else None,
                "created_user": entry.created_user.username if entry.created_user else None,
            })

        return Response({
            "entries": entry_list,
            "count": len(entry_list),
            "filters": {"entity_id": entity_id, "limit": limit}
        })
```

**Get Entry with Attributes:**

```python
from pagoda_plugin_sdk.models import Entry

class EntryDetailView(PluginAPIViewMixin):
    def get(self, request, entry_id):
        try:
            entry = Entry.objects.get(id=entry_id, is_active=True)

            # Use Entry's custom method to get attributes
            attrs = entry.get_attrs()

            return Response({
                "id": entry.id,
                "name": entry.name,
                "entity": {
                    "id": entry.schema.id,
                    "name": entry.schema.name,
                },
                "attributes": attrs,  # All entry attributes
                "created_time": entry.created_time.isoformat() if entry.created_time else None,
            })
        except Entry.DoesNotExist:
            return Response(
                {"error": f"Entry {entry_id} not found"},
                status=404
            )
```

### Working with Relationships

```python
from pagoda_plugin_sdk.models import Entity, Entry

class EntityEntriesView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        """Get an entity and all its entries"""
        try:
            # Get entity
            entity = Entity.objects.get(id=entity_id, is_active=True)

            # Get all entries for this entity
            entries = Entry.objects.filter(
                schema=entity,
                is_active=True
            ).select_related('created_user')

            # Format response
            return Response({
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                },
                "entries": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "created_user": e.created_user.username,
                    }
                    for e in entries
                ],
                "total_entries": entries.count()
            })
        except Entity.DoesNotExist:
            return Response({"error": "Entity not found"}, status=404)
```

### Model Availability Check

Always check if models are available before using them:

```python
from pagoda_plugin_sdk.models import Entity
from pagoda_plugin_sdk import models

class SafeModelView(PluginAPIViewMixin):
    def get(self, request):
        # Check if plugin system is initialized
        if not models.is_initialized():
            return Response(
                {"error": "Plugin system not initialized"},
                status=503
            )

        # Check specific model
        if Entity is None:
            return Response(
                {"error": "Entity model not available"},
                status=503
            )

        # Safe to use models
        entities = Entity.objects.all()
        return Response({"count": entities.count()})
```

### Type-Safe Model Usage

Use Protocol types for better type safety:

```python
from typing import List
from pagoda_plugin_sdk.models import Entity, Entry
from pagoda_plugin_sdk.protocols import EntityProtocol, EntryProtocol

def process_entity(entity: EntityProtocol) -> dict:
    """Process entity with type safety

    Args:
        entity: Entity instance (type-safe)

    Returns:
        Processed entity data
    """
    return {
        "id": entity.id,
        "name": entity.name,
        "note": entity.note,
    }

def get_entity_entries(entity: EntityProtocol) -> List[EntryProtocol]:
    """Get entries for entity with type hints

    Args:
        entity: Entity to get entries for

    Returns:
        List of Entry instances
    """
    return Entry.objects.filter(schema=entity, is_active=True)
```

### Error Handling Best Practices

```python
from pagoda_plugin_sdk.models import Entity, Entry
from rest_framework.response import Response
from rest_framework import status

class RobustModelView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        try:
            # Model availability check
            if Entity is None or Entry is None:
                return Response(
                    {"error": "Models not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get entity
            entity = Entity.objects.get(id=entity_id, is_active=True)

            # Get entries
            entries = Entry.objects.filter(schema=entity, is_active=True)

            return Response({
                "entity": {"id": entity.id, "name": entity.name},
                "entry_count": entries.count()
            })

        except Entity.DoesNotExist:
            return Response(
                {"error": f"Entity {entity_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Internal error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

## 高度な開発テクニック

### プラグイン間通信

```python
# プラグインA: データ提供
class PluginA(Plugin):
    def get_shared_data(self):
        return {"key": "value"}

# プラグインB: データ消費
class PluginB(Plugin):
    def use_shared_data(self):
        from airone.plugins.registry import plugin_registry
        plugin_a = plugin_registry.get_plugin("plugin-a")
        if plugin_a:
            data = plugin_a.get_shared_data()
            return data
```

### モデル注入を使ったデータアクセス

```python
# プラグインからPagodaデータにアクセス
from pagoda_plugin_sdk import PluginAPIViewMixin
from pagoda_plugin_sdk.models import Entity, Entry

class DataAccessView(PluginAPIViewMixin):
    def get(self, request, entity_id):
        # 型安全なモデルアクセス
        try:
            if Entity is None:
                return Response(
                    {"error": "Entity model not available"},
                    status=503
                )

            entity = Entity.objects.get(id=entity_id, is_active=True)
            entries = Entry.objects.filter(schema=entity, is_active=True)

            return Response({
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                },
                "entry_count": entries.count()
            })
        except Entity.DoesNotExist:
            return Response({"error": "Entity not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
```

### 条件付きフック実行

```python
def conditional_hook(sender, instance, **kwargs):
    # 特定の条件でのみ実行
    if instance.name.startswith("special_"):
        # 特別な処理
        logger.info(f"Special entry detected: {instance.name}")

        # 外部API呼び出し例
        import requests
        try:
            response = requests.post("https://api.example.com/notify", {
                "entry_name": instance.name,
                "plugin": "my-first-plugin"
            }, timeout=5)
            logger.info(f"External API notified: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to notify external API: {e}")
```

## パフォーマンス最適化

### 非同期フック実行

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def async_hook_handler(sender, instance, **kwargs):
    """重い処理を非同期で実行"""
    def heavy_processing():
        # 重い処理（外部API、ファイル処理など）
        import time
        time.sleep(2)  # 例: 重い処理のシミュレーション
        logger.info(f"Heavy processing completed for {instance.name}")

    # バックグラウンドで実行
    executor = ThreadPoolExecutor(max_workers=2)
    executor.submit(heavy_processing)
```

### フック実行の条件分岐

```python
def optimized_hook(sender, instance, **kwargs):
    # 不要な処理をスキップ
    if not should_process(instance):
        return

    # 必要な場合のみ重い処理を実行
    if instance.name.endswith("_important"):
        heavy_processing(instance)
    else:
        light_processing(instance)

def should_process(instance):
    # 処理が必要かどうかの判定
    return hasattr(instance, 'special_flag') and instance.special_flag
```

## 本格的な配布準備

### PyPI配布用設定

```toml
# pyproject.toml - 本格版
[project]
name = "my-pagoda-plugin"
version = "1.0.0"
authors = [
    {name = "Your Name", email = "you@example.com"},
]
description = "A powerful Pagoda plugin"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Framework :: Django",
]
dependencies = [
    "pagoda-plugin-sdk>=1.0.0,<2.0.0",
    "Django>=3.2",
    "djangorestframework>=3.12",
]

[project.urls]
Homepage = "https://github.com/youruser/my-pagoda-plugin"

[project.entry-points."pagoda.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 継続的インテグレーション

```yaml
# .github/workflows/test.yml
name: Test Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install pagoda-plugin-sdk
        pip install -e .
        pip install pytest

    - name: Run tests
      run: |
        pytest tests/

    - name: Test plugin loading
      run: |
        python -c "from my_plugin.plugin import MyPlugin; print('✓ Plugin loads successfully')"
```

このクイックスタートガイドに従うことで、初心者でも5分でプラグイン開発を開始し、実践的な問題解決スキルを身につけることができます。さらに詳しい情報は、メインのPlugin Systemドキュメントとアーキテクチャ図を参照してください。