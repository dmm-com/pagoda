---
title: Plugin Development Quick Start Guide
weight: 2
---

## 5分で始めるプラグイン開発

このガイドは、AirOneプラグインシステムを使って最初のプラグインを作成・動作確認するまでの最短手順を提供します。

### ステップ 1: 環境準備 (2分)

#### 1.1 AirOne環境でのpagoda-core準備

```bash
cd /path/to/airone

# pagoda-coreの開発版インストール
cd pagoda-core/
make install-dev

# インストール確認
python -c "import pagoda_core; print('✓ pagoda-core ready')"
```

#### 1.2 サンプルプラグインで動作確認

```bash
# プラグイン有効化してサーバー起動
AIRONE_PLUGINS_ENABLED=true poetry run python manage.py runserver 8080 &

# 別ターミナルで動作確認
curl http://localhost:8080/api/v2/plugins/hello-world-plugin/test/
```

**期待するレスポンス:**
```json
{
  "message": "External Hello World Plugin is working via pagoda-core!",
  "plugin": {
    "id": "hello-world-plugin",
    "name": "Hello World Plugin",
    "version": "1.0.0",
    "type": "external",
    "core": "pagoda-core"
  }
}
```

✅ **ここまで正常に動作すれば環境準備完了です！**

### ステップ 2: 最初のプラグイン作成 (3分)

#### 2.1 プラグインプロジェクト作成

```bash
# 作業ディレクトリ作成
mkdir my-first-plugin
cd my-first-plugin

# サンプルからコピーして開始
cp -r ../airone/plugin_examples/airone-hello-world-plugin/* .

# プラグイン名をカスタマイズ
sed -i 's/hello-world-plugin/my-first-plugin/g' setup.py
sed -i 's/airone_hello_world_plugin/my_first_plugin/g' setup.py
```

#### 2.2 プラグイン構造をリネーム

```bash
# ディレクトリ・ファイル名変更
mv airone_hello_world_plugin my_first_plugin
```

#### 2.3 プラグインクラスをカスタマイズ

```python
# my_first_plugin/plugin.py
from pagoda_core import Plugin

class MyFirstPlugin(Plugin):
    id = "my-first-plugin"
    name = "My First Plugin"
    version = "1.0.0"
    description = "My very first AirOne plugin"
    author = "Your Name"

    django_apps = ["my_first_plugin"]
    api_v2_patterns = "my_first_plugin.api_v2.urls"

    hooks = {
        "entry.after_create": "my_first_plugin.hooks.after_entry_create",
    }
```

#### 2.4 APIエンドポイントをカスタマイズ

```python
# my_first_plugin/api_v2/views.py
from datetime import datetime
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from pagoda_core import PluginAPIViewMixin

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

#### 2.5 フックハンドラーをカスタマイズ

```python
# my_first_plugin/hooks.py
import logging

logger = logging.getLogger(__name__)

def after_entry_create(sender, instance, created, **kwargs):
    """Entry作成後に実行されるフック"""
    if created:
        logger.info(f"🎉 New entry created via My First Plugin: {instance.name}")
        print(f"My First Plugin detected new entry: {instance.name}")
```

### ステップ 3: プラグインテスト・インストール

#### 3.1 プラグインのインストール

```bash
# 開発用インストール
poetry run pip install -e .

# インストール確認
poetry run python -c "
from my_first_plugin.plugin import MyFirstPlugin
plugin = MyFirstPlugin()
print(f'✓ Plugin ready: {plugin.name} v{plugin.version}')
"
```

#### 3.2 AirOneでのテスト

```bash
# AirOneサーバー再起動（新プラグイン認識のため）
pkill -f "manage.py runserver"
AIRONE_PLUGINS_ENABLED=true poetry run python manage.py runserver 8080 &

# プラグインエンドポイントテスト
curl http://localhost:8080/api/v2/plugins/my-first-plugin/test/
```

**成功時のログ:**
```
[INFO] Registered plugin: my-first-plugin v1.0.0
[INFO] Registered 1 hooks for plugin my-first-plugin
[INFO] Plugin discovery completed. Found 2 plugins.
```

## 実践的トラブルシューティング

### 問題 1: 404エラー - プラグインが見つからない

**症状:**
```bash
curl http://localhost:8080/api/v2/plugins/my-plugin/test/
# 404 Not Found
```

**診断手順:**

```bash
# 1. プラグインシステムが有効か確認
poetry run python manage.py shell -c "
from django.conf import settings
print('Plugin system enabled:', settings.AIRONE.get('PLUGINS', {}).get('ENABLED', False))
"

# 2. プラグイン登録状況確認
AIRONE_PLUGINS_ENABLED=true poetry run python manage.py shell -c "
from airone.plugins.integration import plugin_integration
plugin_integration.initialize()
plugins = plugin_integration.get_enabled_plugins()
for p in plugins:
    print(f'Plugin: {p.id} - {p.name}')
"

# 3. Entry points確認
poetry run python -c "
import pkg_resources
entries = list(pkg_resources.iter_entry_points('airone.plugins'))
print(f'Found {len(entries)} entry points:')
for ep in entries:
    print(f'  {ep.name} -> {ep.module_name}')
"
```

**解決法:**
```bash
# 最も多い原因: 環境変数不足
❌ poetry run python manage.py runserver
✅ AIRONE_PLUGINS_ENABLED=true poetry run python manage.py runserver

# 次に多い原因: プラグインが未インストール
poetry run pip install -e .

# Entry pointsパス間違い
# setup.pyを確認して正しいパス指定に修正
```

### 問題 2: Import エラー - モジュールが見つからない

**症状:**
```
[ERROR] Failed to load external plugin: No module named 'my_plugin'
```

**診断・解決手順:**

```bash
# 1. プラグインが正しくインストールされているか
poetry run pip list | grep my-plugin

# 2. モジュール構造を確認
tree my-plugin/
# 期待される構造:
# my-plugin/
# ├── setup.py
# └── my_plugin/
#     ├── __init__.py
#     └── plugin.py

# 3. Entry pointsパスを確認・修正
# setup.py内で:
entry_points={
    'airone.plugins': [
        'my-plugin = my_plugin.plugin:MyPlugin',  # ← 正確なパス
    ],
}

# 4. 再インストール
pip uninstall -y my-plugin
rm -rf build/ dist/ *.egg-info/
poetry run pip install -e .
```

### 問題 3: Hook実行エラー

**症状:**
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

### ブリッジ経由でのAirOneデータアクセス

```python
# プラグインからAirOneデータにアクセス
from pagoda_core import PluginAPIViewMixin

class DataAccessView(PluginAPIViewMixin):
    def get(self, request):
        # Bridge経由でEntityデータ取得
        try:
            from airone.plugins.bridge_manager import bridge_manager
            entity = bridge_manager.data.get_entity(123)
            return Response({"entity": entity})
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

```python
# setup.py - 本格版
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="my-airone-plugin",
    version="1.0.0",
    author="Your Name",
    author_email="you@example.com",
    description="A powerful AirOne plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/youruser/my-airone-plugin",
    packages=find_packages(),
    classifiers=[
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
    ],
    python_requires=">=3.8",
    install_requires=[
        "pagoda-core>=1.0.0,<2.0.0",
        "Django>=3.2",
        "djangorestframework>=3.12",
    ],
    entry_points={
        "airone.plugins": [
            "my-plugin = my_plugin.plugin:MyPlugin",
        ],
    },
)
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
        pip install pagoda-core
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