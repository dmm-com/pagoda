# 設計文書

## 概要

DjangoバックエンドのプラグインシステムはPythonパッケージベースのアーキテクチャを採用し、**完全に外部のリポジトリ・プロジェクト**として開発可能なプラグインシステムを提供します。本体（AirOne）は公開APIとSDKを提供し、プラグイン開発者は本体のコードベースに一切触れることなく機能拡張を実現できます。

## アーキテクチャ

### 1. 本体の公開API構造

```
airone-core/                    # 本体を独立パッケージとして公開
├── airone_core/
│   ├── __init__.py
│   ├── api/                    # プラグイン向け公開API
│   │   ├── __init__.py
│   │   ├── models.py           # モデルAPI
│   │   ├── services.py         # サービスAPI
│   │   ├── jobs.py             # ジョブAPI
│   │   ├── permissions.py      # 権限API
│   │   └── hooks.py            # フックAPI
│   ├── plugins/                # プラグインフレームワーク
│   │   ├── __init__.py
│   │   ├── base.py             # プラグインベースクラス
│   │   ├── decorators.py       # デコレータ
│   │   ├── mixins.py           # ミックスイン
│   │   └── exceptions.py       # 例外クラス
│   └── sdk/                    # 開発者向けSDK
│       ├── __init__.py
│       ├── testing.py          # テストユーティリティ
│       └── cli.py              # CLI ツール
```

### 2. 外部プラグインプロジェクト構造

```
my-custom-plugin/               # 完全に独立したリポジトリ
├── pyproject.toml
├── README.md
├── my_custom_plugin/
│   ├── __init__.py
│   ├── plugin.py               # プラグインエントリポイント
│   ├── models.py               # 独自モデル
│   ├── api_v2/                 # API v2エンドポイント
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── serializers.py
│   ├── tasks.py                # Celeryタスク
│   ├── hooks.py                # フック実装
│   ├── migrations/             # マイグレーション
│   ├── static/                 # 静的ファイル
│   └── templates/              # テンプレート
├── tests/
└── docs/
```

### 3. 本体でのプラグイン統合システム

```
airone/                         # 本体プロジェクト
├── plugins/
│   ├── __init__.py
│   ├── registry.py             # プラグイン登録・管理
│   ├── loader.py               # 外部パッケージローダー
│   ├── discovery.py            # プラグイン自動発見
│   └── integration.py          # Django統合
```

## コンポーネントと インターフェース

### 1. 公開APIパッケージ（pagoda-core）

外部プラグインが依存する公開APIパッケージ：

```python
# pagoda_core/api/__init__.py - プラグイン向け統一API
from .models import ModelAPI
from .services import ServiceAPI
from .permissions import PermissionAPI
from .jobs import JobAPI

class PagodaAPI:
    """プラグイン向けの統一APIインターフェース"""
    def __init__(self):
        self.models = ModelAPI()
        self.services = ServiceAPI()
        self.permissions = PermissionAPI()
        self.jobs = JobAPI()

# pagoda_core/api/models.py - モデルAPI
class ModelAPI:
    """本体モデルへの安全なアクセスを提供"""
    
    def get_entry_model(self):
        """Entryモデルクラスを取得"""
        # 実際のモデルは本体で定義、APIは抽象化
        from pagoda_core.models import Entry
        return Entry
    
    def get_entity_model(self):
        """Entityモデルクラスを取得"""
        from pagoda_core.models import Entity
        return Entity
    
    def create_entry(self, entity, name, user, **kwargs):
        """エントリ作成の安全なAPI"""
        Entry = self.get_entry_model()
        # バリデーションとセキュリティチェック
        return Entry.objects.create(
            schema=entity, name=name, created_user=user, **kwargs
        )
    
    def get_entries(self, entity=None, user=None, **filters):
        """エントリ取得の安全なAPI"""
        Entry = self.get_entry_model()
        queryset = Entry.objects.filter(**filters)
        if entity:
            queryset = queryset.filter(schema=entity)
        # 権限チェック
        return queryset

# pagoda_core/api/jobs.py - ジョブAPI
class JobAPI:
    """プラグイン向けジョブ管理API"""
    
    def create_job(self, operation, user, target=None, **kwargs):
        """ジョブ作成API"""
        from pagoda_core.models import Job
        return Job.objects.create(
            user=user,
            target=target,
            operation=operation,
            **kwargs
        )
    
    def get_job_model(self):
        """Jobモデルクラスを取得"""
        from pagoda_core.models import Job
        return Job

# pagoda_core/models.py - 公開モデル抽象化
class Entry:
    """Entryモデルの公開インターフェース"""
    # 実際の実装は本体側で注入される
    objects = None
    
    @classmethod
    def _get_real_model(cls):
        # 実行時に本体のモデルを取得
        from django.apps import apps
        return apps.get_model('entry', 'Entry')

class Entity:
    """Entityモデルの公開インターフェース"""
    objects = None
    
    @classmethod
    def _get_real_model(cls):
        from django.apps import apps
        return apps.get_model('entity', 'Entity')
```

### 2. サンプルプラグインの実装

#### サンプルプラグイン1: Hello World Plugin

```toml
# plugin_samples/hello_world_plugin/pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pagoda-plugin-hello-world"
version = "1.0.0"
description = "Hello World sample plugin for Pagoda"
authors = [{name = "Pagoda Team", email = "dev@example.com"}]
dependencies = [
    "pagoda-core>=2.0.0,<3.0.0",  # 本体の公開APIに依存
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
]

[project.entry-points."pagoda.plugins"]
hello_world = "hello_world_plugin.plugin:HelloWorldPlugin"

[project.optional-dependencies]
dev = ["pytest", "pytest-django", "pagoda-core[testing]"]
```

```python
# plugin_samples/hello_world_plugin/hello_world_plugin/plugin.py
from pagoda_core.plugins.base import Plugin
from pagoda_core.api import PagodaAPI

class HelloWorldPlugin(Plugin):
    """Hello Worldサンプルプラグイン"""
    
    # プラグイン基本情報
    id = "hello-world-plugin"
    name = "Hello World Plugin"
    version = "1.0.0"
    description = "A simple Hello World plugin demonstrating basic functionality"
    author = "Pagoda Team"
    
    # 依存関係
    dependencies = ["pagoda-core>=2.0.0,<3.0.0"]
    
    # Django設定
    django_apps = ["hello_world_plugin"]
    url_patterns = "hello_world_plugin.urls"
    
    # API v2エンドポイント
    api_v2_patterns = "hello_world_plugin.api_v2.urls"
    
    # 独自ジョブ操作
    job_operations = {
        1001: {
            "name": "HELLO_WORLD_TASK",
            "task": "hello_world_plugin.tasks.hello_world_task",
            "parallelizable": True,
            "cancelable": True,
        }
    }
    
    # 拡張ポイント
    hooks = {
        "entry.after_create": "hello_world_plugin.hooks.greet_new_entry",
    }
    
    def initialize(self, api: PagodaAPI):
        """プラグイン初期化"""
        self.api = api
        print(f"Hello World Plugin initialized!")
```

#### サンプルプラグイン2: Entry Analytics Plugin

```toml
# plugin_samples/entry_analytics_plugin/pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pagoda-plugin-entry-analytics"
version = "1.0.0"
description = "Entry analytics sample plugin for Pagoda"
authors = [{name = "Pagoda Team", email = "dev@example.com"}]
dependencies = [
    "pagoda-core>=2.0.0,<3.0.0",
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
    "pandas>=1.5.0",  # データ分析用
]

[project.entry-points."pagoda.plugins"]
entry_analytics = "entry_analytics_plugin.plugin:EntryAnalyticsPlugin"

[project.optional-dependencies]
dev = ["pytest", "pytest-django", "pagoda-core[testing]"]
```

```python
# plugin_samples/entry_analytics_plugin/entry_analytics_plugin/plugin.py
from pagoda_core.plugins.base import Plugin
from pagoda_core.api import PagodaAPI

class EntryAnalyticsPlugin(Plugin):
    """エントリ分析サンプルプラグイン"""
    
    # プラグイン基本情報
    id = "entry-analytics-plugin"
    name = "Entry Analytics Plugin"
    version = "1.0.0"
    description = "Provides analytics and reporting for entries"
    author = "Pagoda Team"
    
    # 依存関係
    dependencies = ["pagoda-core>=2.0.0,<3.0.0"]
    
    # Django設定
    django_apps = ["entry_analytics_plugin"]
    url_patterns = "entry_analytics_plugin.urls"
    
    # API v2エンドポイント
    api_v2_patterns = "entry_analytics_plugin.api_v2.urls"
    
    # 独自ジョブ操作
    job_operations = {
        1101: {
            "name": "GENERATE_ANALYTICS_REPORT",
            "task": "entry_analytics_plugin.tasks.generate_analytics_report",
            "parallelizable": False,
            "cancelable": True,
        },
        1102: {
            "name": "EXPORT_ANALYTICS_DATA",
            "task": "entry_analytics_plugin.tasks.export_analytics_data",
            "parallelizable": True,
            "cancelable": True,
        }
    }
    
    # 拡張ポイント
    hooks = {
        "entry.after_create": "entry_analytics_plugin.hooks.track_entry_creation",
        "entry.after_update": "entry_analytics_plugin.hooks.track_entry_update",
    }
    
    # 設定オプション
    settings = {
        "ANALYTICS_RETENTION_DAYS": {"type": "int", "default": 365},
        "ENABLE_REAL_TIME_TRACKING": {"type": "bool", "default": True},
    }
    
    def initialize(self, api: PagodaAPI):
        """プラグイン初期化"""
        self.api = api
        print(f"Entry Analytics Plugin initialized!")
        self.setup_analytics_tracking()
    
    def setup_analytics_tracking(self):
        """分析トラッキングのセットアップ"""
        # 分析用のセットアップ処理
        pass
```

### 3. サンプルプラグインでのAPI v2エンドポイント実装

#### Hello World Plugin API

```python
# plugin_samples/hello_world_plugin/hello_world_plugin/api_v2/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("hello/", views.HelloView.as_view(), name="hello"),
    path("greet/<str:name>/", views.GreetView.as_view(), name="greet"),
]

# plugin_samples/hello_world_plugin/hello_world_plugin/api_v2/views.py
from rest_framework import status
from rest_framework.response import Response
from pagoda_core.api import PagodaAPI
from pagoda_core.plugins.mixins import PluginAPIViewMixin

class HelloView(PluginAPIViewMixin):
    """シンプルなHello World API"""
    
    def __init__(self):
        super().__init__()
        self.api = PagodaAPI()
    
    def get(self, request):
        return Response({
            "message": "Hello from Hello World Plugin!",
            "plugin": "hello-world-plugin",
            "version": "1.0.0"
        })
    
    def post(self, request):
        # Hello Worldジョブを実行
        job = self.api.jobs.create_job(
            operation=1001,  # HELLO_WORLD_TASK
            user=request.user,
            params={"message": request.data.get("message", "Hello World!")}
        )
        
        return Response({
            "job_id": job.id,
            "message": "Hello World task queued!",
            "plugin": "hello-world-plugin"
        }, status=status.HTTP_201_CREATED)

class GreetView(PluginAPIViewMixin):
    """パーソナライズされた挨拶API"""
    
    def get(self, request, name):
        return Response({
            "greeting": f"Hello, {name}! Welcome to Pagoda!",
            "plugin": "hello-world-plugin",
            "timestamp": request.META.get('HTTP_DATE')
        })
```

#### Entry Analytics Plugin API

```python
# plugin_samples/entry_analytics_plugin/entry_analytics_plugin/api_v2/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("analytics/summary/", views.AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("analytics/report/", views.GenerateReportView.as_view(), name="generate-report"),
    path("analytics/entries/<int:entity_id>/", views.EntityAnalyticsView.as_view(), name="entity-analytics"),
]

# plugin_samples/entry_analytics_plugin/entry_analytics_plugin/api_v2/views.py
from rest_framework import status
from rest_framework.response import Response
from pagoda_core.api import PagodaAPI
from pagoda_core.plugins.mixins import PluginAPIViewMixin
from datetime import datetime, timedelta

class AnalyticsSummaryView(PluginAPIViewMixin):
    """分析サマリーAPI"""
    
    def __init__(self):
        super().__init__()
        self.api = PagodaAPI()
    
    def get(self, request):
        # 本体のAPIを使用してエントリ統計を取得
        Entry = self.api.models.get_entry_model()
        
        # 過去30日間の統計
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_entries = Entry.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        total_entries = Entry.objects.count()
        
        return Response({
            "total_entries": total_entries,
            "recent_entries": recent_entries,
            "period": "30 days",
            "plugin": "entry-analytics-plugin",
            "generated_at": datetime.now().isoformat()
        })

class GenerateReportView(PluginAPIViewMixin):
    """レポート生成API"""
    
    def __init__(self):
        super().__init__()
        self.api = PagodaAPI()
    
    def post(self, request):
        # レポート生成ジョブを作成
        job = self.api.jobs.create_job(
            operation=1101,  # GENERATE_ANALYTICS_REPORT
            user=request.user,
            params={
                "report_type": request.data.get("report_type", "summary"),
                "date_range": request.data.get("date_range", 30)
            }
        )
        
        return Response({
            "job_id": job.id,
            "status": "queued",
            "message": "Analytics report generation started",
            "plugin": "entry-analytics-plugin"
        }, status=status.HTTP_201_CREATED)

class EntityAnalyticsView(PluginAPIViewMixin):
    """エンティティ別分析API"""
    
    def __init__(self):
        super().__init__()
        self.api = PagodaAPI()
    
    def get(self, request, entity_id):
        # 特定エンティティの分析データ
        Entity = self.api.models.get_entity_model()
        Entry = self.api.models.get_entry_model()
        
        try:
            entity = Entity.objects.get(id=entity_id)
            entries = Entry.objects.filter(schema=entity)
            
            analytics_data = {
                "entity_id": entity_id,
                "entity_name": entity.name,
                "total_entries": entries.count(),
                "active_entries": entries.filter(is_active=True).count(),
                "plugin": "entry-analytics-plugin"
            }
            
            return Response(analytics_data)
            
        except Entity.DoesNotExist:
            return Response({
                "error": "Entity not found",
                "plugin": "entry-analytics-plugin"
            }, status=status.HTTP_404_NOT_FOUND)
```

### 4. サンプルプラグインでの独自ジョブ実装

#### Hello World Plugin ジョブ

```python
# plugin_samples/hello_world_plugin/hello_world_plugin/tasks.py
from celery import shared_task
from pagoda_core.api import PagodaAPI
from pagoda_core.plugins.mixins import PluginJobMixin
import time

@shared_task(bind=True, base=PluginJobMixin)
def hello_world_task(self, job_id):
    """Hello Worldタスク - シンプルなデモンストレーション"""
    job = self.get_job(job_id)
    api = PagodaAPI()
    
    try:
        message = job.params.get("message", "Hello World!")
        
        self.update_progress(10, "Hello Worldタスク開始")
        
        # シンプルな処理のシミュレーション
        time.sleep(1)
        self.update_progress(30, f"メッセージ処理中: {message}")
        
        time.sleep(1)
        self.update_progress(60, "挨拶を準備中...")
        
        # 本体APIを使用してユーザー情報取得
        user = job.user
        greeting = f"{message} from {user.username}!"
        
        time.sleep(1)
        self.update_progress(90, "最終処理中")
        
        # 結果をジョブに保存
        job.text = f"Hello World task completed! Greeting: {greeting}"
        job.save()
        
        self.update_progress(100, "Hello Worldタスク完了")
        
    except Exception as e:
        self.handle_error(e)
        raise
```

#### Entry Analytics Plugin ジョブ

```python
# plugin_samples/entry_analytics_plugin/entry_analytics_plugin/tasks.py
from celery import shared_task
from pagoda_core.api import PagodaAPI
from pagoda_core.plugins.mixins import PluginJobMixin
from datetime import datetime, timedelta
import json

@shared_task(bind=True, base=PluginJobMixin)
def generate_analytics_report(self, job_id):
    """分析レポート生成タスク"""
    job = self.get_job(job_id)
    api = PagodaAPI()
    
    try:
        params = job.params
        report_type = params.get("report_type", "summary")
        date_range = params.get("date_range", 30)
        
        self.update_progress(10, "分析レポート生成開始")
        
        # 本体APIを使用してデータ取得
        Entry = api.models.get_entry_model()
        Entity = api.models.get_entity_model()
        
        # 日付範囲の設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        self.update_progress(30, "データ収集中...")
        
        # エントリ統計の収集
        entries_in_range = Entry.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        total_entries = entries_in_range.count()
        
        self.update_progress(50, "エンティティ別分析中...")
        
        # エンティティ別統計
        entity_stats = {}
        for entity in Entity.objects.all():
            entity_entries = entries_in_range.filter(schema=entity)
            entity_stats[entity.name] = {
                "count": entity_entries.count(),
                "active": entity_entries.filter(is_active=True).count()
            }
        
        self.update_progress(70, "レポート生成中...")
        
        # レポートデータの構築
        report_data = {
            "report_type": report_type,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": date_range
            },
            "summary": {
                "total_entries": total_entries,
                "entities_analyzed": len(entity_stats)
            },
            "entity_breakdown": entity_stats,
            "generated_at": datetime.now().isoformat(),
            "plugin": "entry-analytics-plugin"
        }
        
        self.update_progress(90, "レポート保存中...")
        
        # レポートをジョブに保存
        job.text = json.dumps(report_data, indent=2)
        job.save()
        
        self.update_progress(100, f"分析レポート生成完了 ({total_entries}エントリ分析)")
        
    except Exception as e:
        self.handle_error(e)
        raise

@shared_task(bind=True, base=PluginJobMixin)
def export_analytics_data(self, job_id):
    """分析データエクスポートタスク"""
    job = self.get_job(job_id)
    api = PagodaAPI()
    
    try:
        params = job.params
        export_format = params.get("format", "json")
        entity_ids = params.get("entity_ids", [])
        
        self.update_progress(10, "データエクスポート開始")
        
        # 本体APIを使用してデータ取得
        Entry = api.models.get_entry_model()
        Entity = api.models.get_entity_model()
        
        export_data = []
        
        if entity_ids:
            entities = Entity.objects.filter(id__in=entity_ids)
        else:
            entities = Entity.objects.all()
        
        total_entities = entities.count()
        
        for i, entity in enumerate(entities):
            self.update_progress(
                int(20 + (i / total_entities) * 60), 
                f"エンティティ処理中: {entity.name}"
            )
            
            entries = Entry.objects.filter(schema=entity)
            
            entity_data = {
                "entity_id": entity.id,
                "entity_name": entity.name,
                "entries": []
            }
            
            for entry in entries:
                entity_data["entries"].append({
                    "id": entry.id,
                    "name": entry.name,
                    "created_at": entry.created_at.isoformat(),
                    "is_active": entry.is_active
                })
            
            export_data.append(entity_data)
        
        self.update_progress(85, "エクスポートファイル生成中...")
        
        # エクスポートデータの保存
        if export_format == "json":
            export_content = json.dumps(export_data, indent=2)
        else:
            # 他の形式のサポート（CSV等）
            export_content = self.convert_to_format(export_data, export_format)
        
        job.text = export_content
        job.save()
        
        self.update_progress(100, f"データエクスポート完了 ({len(export_data)}エンティティ)")
        
    except Exception as e:
        self.handle_error(e)
        raise
    
    def convert_to_format(self, data, format_type):
        """データを指定形式に変換"""
        if format_type == "csv":
            # CSV変換ロジック
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # ヘッダー
            writer.writerow(["Entity ID", "Entity Name", "Entry ID", "Entry Name", "Created At", "Is Active"])
            
            # データ
            for entity_data in data:
                for entry in entity_data["entries"]:
                    writer.writerow([
                        entity_data["entity_id"],
                        entity_data["entity_name"],
                        entry["id"],
                        entry["name"],
                        entry["created_at"],
                        entry["is_active"]
                    ])
            
            return output.getvalue()
        
        # デフォルトはJSON
        return json.dumps(data, indent=2)
```

### 5. プラグインベースクラスとミックスイン

```python
# airone/plugins/api/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from airone.plugins.security import PluginSecurityMixin

class PluginAPIView(PluginSecurityMixin, APIView):
    """プラグイン用APIビューベースクラス"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.validate_plugin_permissions()

# airone/plugins/jobs.py
from celery import Task
from job.models import Job

class PluginJobMixin(Task):
    """プラグインジョブ用ミックスイン"""
    
    def get_job(self, job_id):
        return Job.objects.get(id=job_id)
    
    def update_progress(self, progress, message=""):
        job = self.get_job(self.request.id)
        job.update_progress(progress, message)
    
    def handle_error(self, error):
        job = self.get_job(self.request.id)
        job.update_status(Job.STATUS.FAILURE, str(error))
```

### 6. プラグインレジストリ（拡張版）

```python
class PluginRegistry:
    def __init__(self):
        self._plugins = {}
        self._hooks = HookRegistry()
        self._job_operations = {}
        self._api_v2_patterns = []
    
    def register(self, plugin_class):
        """プラグインを登録"""
        plugin = plugin_class()
        self._validate_plugin(plugin)
        self._plugins[plugin.id] = plugin
        self._register_hooks(plugin)
        self._register_job_operations(plugin)
        self._register_api_v2_patterns(plugin)
    
    def _register_job_operations(self, plugin):
        """プラグインのジョブ操作を登録"""
        for op_id, config in plugin.job_operations.items():
            if op_id in self._job_operations:
                raise PluginError(f"Job operation {op_id} already registered")
            
            # プラグイン用操作ID範囲チェック（200-999）
            if not (200 <= op_id <= 999):
                raise PluginError(f"Invalid job operation ID {op_id}. Must be 200-999")
            
            self._job_operations[op_id] = {
                "plugin_id": plugin.id,
                "name": config["name"],
                "task": config["task"],
                "parallelizable": config.get("parallelizable", False),
                "cancelable": config.get("cancelable", True),
                "downloadable": config.get("downloadable", False),
            }
    
    def _register_api_v2_patterns(self, plugin):
        """プラグインのAPI v2パターンを登録"""
        if plugin.api_v2_patterns:
            self._api_v2_patterns.append({
                "plugin_id": plugin.id,
                "patterns": plugin.api_v2_patterns,
                "prefix": f"plugins/{plugin.id}/"
            })
    
    def get_installed_apps(self):
        """Django INSTALLED_APPSに追加するアプリ一覧"""
        apps = []
        for plugin in self._plugins.values():
            if plugin.is_enabled():
                apps.extend(plugin.django_apps)
        return apps
    
    def get_url_patterns(self):
        """URLパターンを取得"""
        patterns = []
        for plugin in self._plugins.values():
            if plugin.is_enabled() and plugin.url_patterns:
                patterns.append(
                    path(f"plugin/{plugin.id}/", 
                         include(plugin.url_patterns))
                )
        return patterns
    
    def get_api_v2_patterns(self):
        """API v2のURLパターンを取得"""
        patterns = []
        for pattern_config in self._api_v2_patterns:
            plugin = self._plugins[pattern_config["plugin_id"]]
            if plugin.is_enabled():
                patterns.append(
                    path(pattern_config["prefix"], 
                         include(pattern_config["patterns"]))
                )
        return patterns
    
    def get_job_operations(self):
        """登録されたジョブ操作を取得"""
        return self._job_operations.copy()
    
    def register_job_operation(self, operation_id, task_name, **options):
        """実行時にジョブ操作を登録（API経由）"""
        if operation_id in self._job_operations:
            raise PluginError(f"Job operation {operation_id} already registered")
        
        self._job_operations[operation_id] = {
            "name": options.get("name", f"PLUGIN_OPERATION_{operation_id}"),
            "task": task_name,
            "parallelizable": options.get("parallelizable", False),
            "cancelable": options.get("cancelable", True),
            "downloadable": options.get("downloadable", False),
        }

# グローバルレジストリインスタンス
plugin_registry = PluginRegistry()
```

### 3. 拡張ポイント（フック）システム

```python
class HookRegistry:
    def __init__(self):
        self._hooks = defaultdict(list)
    
    def register(self, hook_name, callback):
        """フックを登録"""
        self._hooks[hook_name].append(callback)
    
    def call(self, hook_name, *args, **kwargs):
        """フックを実行"""
        results = []
        for callback in self._hooks[hook_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook {hook_name} failed: {e}")
        return results

# 使用例
@hook("entry.after_create")
def after_create_entry(entry, user):
    # カスタム処理
    pass
```

### 4. セキュリティ境界

```python
class PluginSecurityManager:
    def __init__(self):
        self.allowed_imports = [
            "django.*",
            "airone.lib.*",
            "airone.plugins.api.*",
        ]
        self.forbidden_imports = [
            "airone.settings",
            "os",
            "subprocess",
        ]
    
    def validate_plugin(self, plugin):
        """プラグインのセキュリティ検証"""
        # インポート制限チェック
        # 権限チェック
        # リソース使用量制限
        pass
```

## データモデル

### プラグイン管理モデル

```python
class InstalledPlugin(models.Model):
    plugin_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PluginDependency(models.Model):
    plugin = models.ForeignKey(InstalledPlugin, on_delete=models.CASCADE)
    dependency_id = models.CharField(max_length=100)
    version_constraint = models.CharField(max_length=100)
```

### プラグイン設定管理

```python
class PluginSetting(models.Model):
    plugin = models.ForeignKey(InstalledPlugin, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.TextField()
    encrypted = models.BooleanField(default=False)
```

## エラーハンドリング

### プラグイン例外階層

```python
class PluginError(Exception):
    """プラグイン関連の基底例外"""
    pass

class PluginLoadError(PluginError):
    """プラグインロード失敗"""
    pass

class PluginValidationError(PluginError):
    """プラグイン検証失敗"""
    pass

class PluginSecurityError(PluginError):
    """プラグインセキュリティ違反"""
    pass

class PluginDependencyError(PluginError):
    """プラグイン依存関係エラー"""
    pass
```

### エラー処理戦略

1. **分離**: プラグインエラーはコアシステムに影響しない
2. **ログ**: 詳細なエラーログとスタックトレース
3. **フォールバック**: プラグイン無効化時の代替動作
4. **通知**: 管理者への適切な通知

## テスト戦略

### 1. プラグイン開発者向けテストフレームワーク

```python
from airone.plugins.testing import PluginTestCase

class ExamplePluginTest(PluginTestCase):
    plugin_id = "example-plugin"
    
    def test_plugin_loads(self):
        """プラグインが正常にロードされる"""
        self.assertPluginLoaded(self.plugin_id)
    
    def test_hook_registration(self):
        """フックが正常に登録される"""
        self.assertHookRegistered("entry.after_create")
```

### 2. 統合テスト

```python
class PluginIntegrationTest(TestCase):
    def test_plugin_isolation(self):
        """プラグイン間の分離を確認"""
        pass
    
    def test_plugin_security(self):
        """セキュリティ境界を確認"""
        pass
    
    def test_plugin_migration(self):
        """マイグレーション処理を確認"""
        pass
```

### 3. パフォーマンステスト

- プラグインロード時間
- メモリ使用量
- フック実行オーバーヘッド

## 外部プラグイン開発の詳細設計

### 1. 公開APIパッケージの配布

```toml
# pagoda-core/pyproject.toml - 本体から分離した公開API
[project]
name = "pagoda-core"
version = "2.0.0"
description = "Pagoda Core API for plugin development"
dependencies = [
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
    "celery>=5.2.0",
]

[project.optional-dependencies]
testing = ["pytest", "pytest-django", "factory-boy"]
cli = ["click", "jinja2"]
```

### 2. プラグイン開発者向けSDK

```python
# pagoda_core/sdk/cli.py - プラグイン開発CLI
import click
from pathlib import Path
from jinja2 import Template

@click.group()
def cli():
    """Pagoda Plugin Development CLI"""
    pass

@cli.command()
@click.argument('plugin_name')
@click.option('--author', default='Plugin Developer')
@click.option('--description', default='A custom Pagoda plugin')
def create(plugin_name, author, description):
    """新しいプラグインプロジェクトを作成"""
    plugin_dir = Path(plugin_name.replace('-', '_'))
    
    # プロジェクト構造を生成
    create_plugin_structure(plugin_dir, {
        'plugin_name': plugin_name,
        'plugin_module': plugin_name.replace('-', '_'),
        'author': author,
        'description': description,
    })
    
    click.echo(f"Plugin '{plugin_name}' created successfully!")

def create_plugin_structure(plugin_dir, context):
    """プラグインの基本構造を作成"""
    # pyproject.toml
    pyproject_template = Template('''
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{{ plugin_name }}"
version = "1.0.0"
description = "{{ description }}"
authors = [{name = "{{ author }}"}]
dependencies = [
    "pagoda-core>=2.0.0,<3.0.0",
    "django>=4.2.0",
    "djangorestframework>=3.14.0",
]

[project.entry-points."pagoda.plugins"]
{{ plugin_module }} = "{{ plugin_module }}.plugin:{{ plugin_module.title() }}Plugin"

[project.optional-dependencies]
dev = ["pytest", "pytest-django", "pagoda-core[testing]"]
''')
    
    # plugin.py テンプレート
    plugin_template = Template('''
from pagoda_core.plugins.base import Plugin
from pagoda_core.api import PagodaAPI

class {{ plugin_module.title() }}Plugin(Plugin):
    id = "{{ plugin_name }}"
    name = "{{ plugin_name.title() }}"
    version = "1.0.0"
    description = "{{ description }}"
    author = "{{ author }}"
    
    dependencies = ["pagoda-core>=2.0.0,<3.0.0"]
    django_apps = ["{{ plugin_module }}"]
    url_patterns = "{{ plugin_module }}.urls"
    api_v2_patterns = "{{ plugin_module }}.api_v2.urls"
    
    job_operations = {
        # プラグイン固有のジョブ操作ID（1000番台を使用）
        # 1001: {
        #     "name": "CUSTOM_OPERATION",
        #     "task": "{{ plugin_module }}.tasks.custom_operation",
        #     "parallelizable": True,
        # }
    }
    
    def initialize(self, api: PagodaAPI):
        self.api = api
        # 初期化処理
''')
    
    # ファイル生成
    plugin_dir.mkdir(exist_ok=True)
    (plugin_dir / 'pyproject.toml').write_text(pyproject_template.render(**context))
    
    module_dir = plugin_dir / context['plugin_module']
    module_dir.mkdir(exist_ok=True)
    (module_dir / 'plugin.py').write_text(plugin_template.render(**context))
    
    # 他のテンプレートファイルも生成...
```

### 3. 本体でのプラグイン自動発見と統合

```python
# airone/plugins/discovery.py - プラグイン自動発見
import pkg_resources
from importlib import import_module
from .registry import plugin_registry
import logging

logger = logging.getLogger(__name__)

def discover_plugins():
    """インストールされたプラグインを自動発見"""
    # pagoda.plugins エントリポイントからプラグインを発見
    for entry_point in pkg_resources.iter_entry_points('pagoda.plugins'):
        try:
            plugin_class = entry_point.load()
            plugin_registry.register(plugin_class)
            logger.info(f"Successfully loaded plugin: {entry_point.name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {entry_point.name}: {e}")
    
    # plugin_samples ディレクトリからサンプルプラグインを発見
    discover_sample_plugins()

def discover_sample_plugins():
    """サンプルプラグインを自動発見"""
    import os
    from pathlib import Path
    
    # plugin_samples ディレクトリを探索
    base_dir = Path(__file__).parent.parent.parent  # airone/
    samples_dir = base_dir / "plugin_samples"
    
    if not samples_dir.exists():
        return
    
    for plugin_dir in samples_dir.iterdir():
        if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
            try:
                # プラグインモジュールをインポート
                plugin_module_name = f"plugin_samples.{plugin_dir.name}.{plugin_dir.name}.plugin"
                plugin_module = import_module(plugin_module_name)
                
                # プラグインクラスを探す
                for attr_name in dir(plugin_module):
                    attr = getattr(plugin_module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, 'id') and 
                        attr_name.endswith('Plugin')):
                        plugin_registry.register(attr)
                        logger.info(f"Successfully loaded sample plugin: {plugin_dir.name}")
                        break
                        
            except Exception as e:
                logger.error(f"Failed to load sample plugin {plugin_dir.name}: {e}")

# airone/plugins/integration.py - Django統合
from django.conf import settings
from django.urls import path, include
from .discovery import discover_plugins
from .registry import plugin_registry

class PluginIntegration:
    """プラグインのDjango統合管理"""
    
    def __init__(self):
        self.initialized = False
    
    def initialize(self):
        """プラグインシステムを初期化"""
        if not self.initialized:
            discover_plugins()
            self.initialized = True
    
    def get_installed_apps(self):
        """INSTALLED_APPSに追加するアプリ一覧"""
        self.initialize()
        apps = []
        
        # 外部プラグインのアプリ
        apps.extend(plugin_registry.get_installed_apps())
        
        # サンプルプラグインのアプリ
        for plugin in plugin_registry.get_enabled_plugins():
            if plugin.id.startswith('hello-world-plugin') or plugin.id.startswith('entry-analytics-plugin'):
                # サンプルプラグインの場合、plugin_samples パスを追加
                sample_apps = [f"plugin_samples.{app.split('.')[-1]}.{app.split('.')[-1]}" 
                              for app in plugin.django_apps]
                apps.extend(sample_apps)
        
        return apps
    
    def get_url_patterns(self):
        """URLパターンを取得"""
        self.initialize()
        patterns = []
        
        # 通常のURLパターン
        for plugin in plugin_registry.get_enabled_plugins():
            if plugin.url_patterns:
                patterns.append(
                    path(f"plugins/{plugin.id}/", 
                         include(plugin.url_patterns))
                )
        
        return patterns
    
    def get_api_v2_patterns(self):
        """API v2のURLパターンを取得"""
        self.initialize()
        patterns = []
        
        for plugin in plugin_registry.get_enabled_plugins():
            if plugin.api_v2_patterns:
                patterns.append(
                    path(f"plugins/{plugin.id}/", 
                         include(plugin.api_v2_patterns))
                )
        
        return patterns

# グローバルインスタンス
plugin_integration = PluginIntegration()
```

### 4. 本体設定での統合

```python
# airone/settings_common.py（修正版）
from airone.plugins.integration import plugin_integration

class Common(Configuration):
    # ... 既存設定 ...
    
    @property
    def INSTALLED_APPS(self):
        base_apps = [
            "common",
            "user", 
            "group",
            "entity",
            "acl",
            "dashboard",
            "entry",
            "job",
            "webhook",
            "role",
            # ... Django標準アプリ ...
        ]
        
        # プラグインアプリを動的に追加
        plugin_apps = plugin_integration.get_installed_apps()
        return base_apps + plugin_apps

# airone/urls.py（修正版）
from airone.plugins.integration import plugin_integration

urlpatterns = [
    # ... 既存URLパターン ...
    re_path(r"^api/v2/", include(("api_v2.urls", "api_v2"))),
]

# プラグインのURLパターンを動的に追加
urlpatterns.extend(plugin_integration.get_url_patterns())

# api_v2/urls.py（修正版）
from airone.plugins.integration import plugin_integration

urlpatterns = [
    # ... 既存API v2パターン ...
]

# プラグインのAPI v2パターンを動的に追加
urlpatterns.extend(plugin_integration.get_api_v2_patterns())
```

### 5. プラグイン開発ワークフロー

#### 外部プラグイン開発

```bash
# 1. プラグイン作成
pip install pagoda-core[cli]
pagoda-cli create my-awesome-plugin --author "Developer Name"

# 2. 開発環境セットアップ
cd my-awesome-plugin
pip install -e .[dev]

# 3. テスト実行
pytest

# 4. パッケージビルド
python -m build

# 5. 配布
twine upload dist/*

# 6. 本体での使用
pip install my-awesome-plugin
# 本体を再起動すると自動的にプラグインが発見・ロードされる
```

#### サンプルプラグイン開発（このリポジトリ内）

```bash
# 1. サンプルプラグインディレクトリ作成
mkdir -p plugin_samples/my_sample_plugin/my_sample_plugin

# 2. 基本ファイル作成
# plugin_samples/my_sample_plugin/my_sample_plugin/plugin.py
# plugin_samples/my_sample_plugin/my_sample_plugin/api_v2/
# plugin_samples/my_sample_plugin/my_sample_plugin/tasks.py

# 3. 本体の開発環境で直接テスト
python manage.py runserver
# プラグインが自動的に発見・ロードされる

# 4. API テスト
curl http://localhost:8000/api/v2/plugins/my-sample-plugin/hello/
```

### 6. 起動プロセスの設計

#### 現在の起動プロセス分析

現在のAirOneは以下の方法で起動します：

```python
# manage.py
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
    
    # 既存のEXTENSIONSシステム
    for extension in settings.AIRONE["EXTENSIONS"]:
        try:
            importlib.import_module("%s.settings" % extension)
        except ImportError:
            Logger.warning("Failed to load settings %s" % extension)
```

#### 新しい起動方法の設計

##### 1. コアのみ起動（従来通り）

```bash
# 環境変数でプラグインを無効化
export PAGODA_PLUGINS_ENABLED=false
python manage.py runserver

# または専用コマンド
python manage.py runserver --no-plugins
```

##### 2. プラグイン込み起動

```bash
# デフォルト（プラグイン有効）
python manage.py runserver

# 明示的にプラグイン有効化
export PAGODA_PLUGINS_ENABLED=true
python manage.py runserver

# 特定のプラグインのみ有効化
export PAGODA_PLUGINS_ENABLED=hello-world-plugin,entry-analytics-plugin
python manage.py runserver
```

#### 設定ファイルの修正

```python
# airone/settings_common.py（修正版）
class Common(Configuration):
    # ... 既存設定 ...
    
    # プラグイン設定
    PAGODA_PLUGINS_ENABLED = env.bool("PAGODA_PLUGINS_ENABLED", True)
    PAGODA_PLUGINS_WHITELIST = env.list("PAGODA_PLUGINS_WHITELIST", None, "")
    PAGODA_PLUGINS_BLACKLIST = env.list("PAGODA_PLUGINS_BLACKLIST", None, "")
    
    @property
    def INSTALLED_APPS(self):
        base_apps = [
            "common",
            "user", 
            "group",
            "entity",
            "acl",
            "dashboard",
            "entry",
            "job",
            "webhook",
            "role",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "django.contrib.humanize",
            "import_export",
            "rest_framework",
            "rest_framework.authtoken",
            "drf_spectacular",
            "django_filters",
            "social_django",
            "simple_history",
            "storages",
            "trigger",
            "category",
        ]
        
        # 既存のcustom_view対応
        if os.path.exists(self.BASE_DIR + "/custom_view"):
            base_apps.append("custom_view")
        
        # プラグインアプリを条件付きで追加
        if self.PAGODA_PLUGINS_ENABLED:
            from airone.plugins.integration import plugin_integration
            plugin_apps = plugin_integration.get_installed_apps()
            base_apps.extend(plugin_apps)
        
        return base_apps
    
    # 既存のEXTENSIONS設定
    AIRONE: dict[str, Any] = {
        # ... 既存設定 ...
        "EXTENSIONS": env.list("AIRONE_EXTENSIONS", None, ""),
        # プラグイン設定を追加
        "PLUGINS": {
            "ENABLED": PAGODA_PLUGINS_ENABLED,
            "WHITELIST": PAGODA_PLUGINS_WHITELIST,
            "BLACKLIST": PAGODA_PLUGINS_BLACKLIST,
        }
    }
```

#### プラグイン統合の条件分岐

```python
# airone/plugins/integration.py（修正版）
from django.conf import settings

class PluginIntegration:
    def __init__(self):
        self.initialized = False
        self._plugins_enabled = getattr(settings, 'PAGODA_PLUGINS_ENABLED', True)
    
    def is_plugins_enabled(self):
        """プラグインが有効かどうか"""
        return self._plugins_enabled
    
    def initialize(self):
        """プラグインシステムを初期化"""
        if not self.initialized and self.is_plugins_enabled():
            discover_plugins()
            self.initialized = True
    
    def get_installed_apps(self):
        """INSTALLED_APPSに追加するアプリ一覧"""
        if not self.is_plugins_enabled():
            return []
        
        self.initialize()
        return plugin_registry.get_installed_apps()
    
    def get_url_patterns(self):
        """URLパターンを取得"""
        if not self.is_plugins_enabled():
            return []
        
        self.initialize()
        # ... URLパターン生成ロジック ...
    
    def get_api_v2_patterns(self):
        """API v2のURLパターンを取得"""
        if not self.is_plugins_enabled():
            return []
        
        self.initialize()
        # ... API v2パターン生成ロジック ...
```

#### URL設定の条件分岐

```python
# airone/urls.py（修正版）
from django.conf import settings
from airone.plugins.integration import plugin_integration

urlpatterns = [
    # ... 既存URLパターン ...
    re_path(r"^api/v2/", include(("api_v2.urls", "api_v2"))),
]

# 既存のEXTENSIONS対応
for extension in settings.AIRONE["EXTENSIONS"]:
    urlpatterns.append(
        re_path(r"^extension/%s" % extension, include(("%s.urls" % extension, extension)))
    )

# プラグインのURLパターンを条件付きで追加
if settings.AIRONE.get("PLUGINS", {}).get("ENABLED", True):
    urlpatterns.extend(plugin_integration.get_url_patterns())

# api_v2/urls.py（修正版）
from django.conf import settings
from airone.plugins.integration import plugin_integration

urlpatterns = [
    # ... 既存API v2パターン ...
]

# プラグインのAPI v2パターンを条件付きで追加
if settings.AIRONE.get("PLUGINS", {}).get("ENABLED", True):
    urlpatterns.extend(plugin_integration.get_api_v2_patterns())
```

#### 管理コマンドの追加

```python
# airone/management/commands/plugin.py
from django.core.management.base import BaseCommand
from airone.plugins.integration import plugin_integration
from airone.plugins.registry import plugin_registry

class Command(BaseCommand):
    help = 'Plugin management commands'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Plugin actions')
        
        # プラグイン一覧
        list_parser = subparsers.add_parser('list', help='List installed plugins')
        list_parser.add_argument('--enabled-only', action='store_true', 
                               help='Show only enabled plugins')
        
        # プラグイン有効化/無効化
        enable_parser = subparsers.add_parser('enable', help='Enable a plugin')
        enable_parser.add_argument('plugin_id', help='Plugin ID to enable')
        
        disable_parser = subparsers.add_parser('disable', help='Disable a plugin')
        disable_parser.add_argument('plugin_id', help='Plugin ID to disable')
    
    def handle(self, *args, **options):
        if options['action'] == 'list':
            self.list_plugins(options.get('enabled_only', False))
        elif options['action'] == 'enable':
            self.enable_plugin(options['plugin_id'])
        elif options['action'] == 'disable':
            self.disable_plugin(options['plugin_id'])
    
    def list_plugins(self, enabled_only=False):
        plugin_integration.initialize()
        plugins = plugin_registry.get_all_plugins()
        
        if enabled_only:
            plugins = [p for p in plugins if p.is_enabled()]
        
        self.stdout.write("Installed Plugins:")
        for plugin in plugins:
            status = "✓" if plugin.is_enabled() else "✗"
            self.stdout.write(f"  {status} {plugin.id} ({plugin.version}) - {plugin.name}")
```

### 7. プラグインディレクトリ構造

```
airone/                                 # 本体プロジェクト
├── plugin_samples/                     # サンプルプラグイン集
│   ├── hello_world_plugin/             # Hello Worldサンプル
│   │   ├── pyproject.toml
│   │   ├── hello_world_plugin/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── api_v2/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── urls.py
│   │   │   │   └── views.py
│   │   │   ├── tasks.py
│   │   │   └── hooks.py
│   │   └── tests/
│   ├── entry_analytics_plugin/         # 分析サンプル
│   │   ├── pyproject.toml
│   │   ├── entry_analytics_plugin/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── api_v2/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── urls.py
│   │   │   │   └── views.py
│   │   │   ├── tasks.py
│   │   │   ├── models.py
│   │   │   └── hooks.py
│   │   └── tests/
│   └── README.md                       # サンプルプラグイン説明
├── pagoda_core/                        # 公開APIパッケージ（分離予定）
│   ├── api/
│   ├── plugins/
│   └── sdk/
├── airone/                             # 本体コード
│   ├── plugins/                        # プラグインシステム
│   │   ├── discovery.py
│   │   ├── integration.py
│   │   └── registry.py
│   └── management/
│       └── commands/
│           └── plugin.py               # プラグイン管理コマンド
└── ...
```

## 実装フェーズ

### フェーズ1: 本体のモジュール化
- AirOneAPI の実装
- ModelAPI, ServiceAPI, JobAPI の作成
- 既存コードのリファクタリング

### フェーズ2: プラグインインフラストラクチャ
- プラグインレジストリ
- プラグインローダー
- マニフェスト定義

### フェーズ3: API v2統合
- プラグイン用APIビューベースクラス
- 動的URL登録システム
- API ドキュメント統合

### フェーズ4: ジョブシステム統合
- プラグインジョブミックスイン
- 動的ジョブ操作登録
- ジョブ管理UI拡張

### フェーズ5: セキュリティとバリデーション
- セキュリティマネージャー
- プラグイン検証
- 権限管理統合

### フェーズ6: 開発者ツールとドキュメント
- プラグインスキャフォールディング
- テストフレームワーク
- 開発ガイド作成