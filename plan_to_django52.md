# Django 5.2 LTS Upgrade Plan

AirOne を Django 4.2.28 から Django 5.2 LTS へアップグレードするための計画書。

## Current State (現状)

| Item | Version |
|---|---|
| Django | 4.2.28 |
| Python | 3.12+ |
| DRF | 3.15.2 |
| Celery | 5.5.3 |
| django-replicated | 2.7 (archived) |
| django-configurations | 2.5 |
| whitenoise | 5.2.0 |
| django-debug-toolbar | 3.2.4 |
| django-filter | 24.3 |
| django-import-export | 3.3.1 |
| django-simple-history | 3.11.0 |
| django-storages | 1.14.1 |
| drf-spectacular | 0.29.0 |

## Risk Assessment (リスク評価)

### Critical Risk (対応必須)

- **django-replicated 2.7**: リポジトリが 2025年1月にアーカイブ化済み。Django 5.x 対応なし。最終リリースは 2020年4月。AirOne では settings, middleware, router で使用しており、代替実装が必要

### High Risk (要アップグレード)

| Package | Issue | Target |
|---|---|---|
| whitenoise | 5.2.0 は Django 5.x 未対応 | 6.x |
| djangorestframework | 3.15 は Django 5.2 非公式 | 3.16+ |
| django-debug-toolbar | 3.2.4 は古すぎる | 4.x+ |
| django-configurations | 2.5 の Django 5.2 対応未確認 | latest |
| django-import-export | 3.3.1 の Django 5.2 対応未確認 | latest |
| django-filter | 24.3 は Django 5.2 以前のリリース | 25.x |

### Code Changes Required (コード修正が必要)

- **pytz → zoneinfo 移行**: 7ファイルで `pytz` を使用中 (Django 5.0 で pytz サポート削除)
  - `job/models.py`
  - `airone/lib/test.py`
  - `entry/api_v1/views.py`
  - `api_v1/tests/test_api.py`
  - `api_v1/tests/entry/test_update_history.py`
  - `api_v1/entry/views.py`
  - `api_v1/auth.py`

### Already Compliant (対応済み)

以下は Django 5.0〜5.2 で削除・変更された機能だが、AirOne では既に対応済みまたは使用なし:

| Breaking Change | 削除バージョン | AirOne の状態 |
|---|---|---|
| `STORAGES` 辞書設定 | 5.1 で旧設定削除 | 済み (`settings_common.py:220`) |
| `DEFAULT_AUTO_FIELD` | 5.0 で必須化 | 明示的に設定済み (`settings_common.py:479`) |
| `USE_TZ = True` | 5.0 でデフォルト変更 | 済み (`settings_common.py:204`) |
| `DEFAULT_FILE_STORAGE` 設定 | 5.1 で削除 | `STORAGES["default"]` に移行済み |
| `STATICFILES_STORAGE` 設定 | 5.1 で削除 | `STORAGES["staticfiles"]` に移行済み |
| `get_storage_class()` | 5.1 で削除 | 使用なし |
| `index_together` | 5.1 で削除 | 使用なし (indexes/UniqueConstraint を使用) |
| `url()` | 4.0 で削除 | 使用なし (re_path/path を使用) |
| `USE_L10N` 設定 | 5.0 で削除 | 使用なし |
| `Model.save()` 位置引数 | 5.1 で deprecation | 使用なし |
| `assertQuerysetEqual` 旧シグネチャ | 5.1 で削除 | 使用なし |
| `assertFormsetError` 旧シグネチャ | 5.1 で削除 | 使用なし |
| MySQL charset utf8mb4 デフォルト化 | 5.2 | 既に `utf8mb4` を使用 (`settings_common.py:153`) |

---

## Why Skip Intermediate Versions (中間バージョンをスキップする根拠)

Django 公式は段階的アップグレード (4.2→5.0→5.1→5.2) を一般論として推奨しているが、AirOne では **4.2 → 5.2 への直接移行** が適切である。

### 根拠 1: 影響のある breaking change が pytz 削除のみ

Django 5.0/5.1/5.2 で削除された機能のうち、AirOne に実際に影響するのは **pytz サポート削除 (5.0)** のみ。これは Phase 0 で Django 4.2 上で先に対応するため、5.2 への切り替え時にはコード変更が不要。

### 根拠 2: コミュニティでも LTS→LTS 直接移行が一般的

- **Python.org**: `django-upgrade --target-version 5.2` で一括変換し LTS に直接移行 ([scriptr.dev/blog/python-org-django-5-upgrade](https://scriptr.dev/blog/python-org-django-5-upgrade))
- **Open edX**: 4.2 互換のまま準備を完了し、5.2 に切り替え。中間バージョンでの停止なし ([discuss.openedx.org](https://discuss.openedx.org/t/django-5-2-upgrade-plan/15397))

### 根拠 3: 中間バージョンに留まるメリットがない

Django 5.0, 5.1 は非 LTS であり、セキュリティサポート期間が短い。中間バージョンでデプロイ・テストする工数（PR、レビュー、ステージング検証 x 3回）に見合うリスク軽減効果がない。

### 根拠 4: `django-upgrade` ツールで安全に一括変換可能

```bash
pip install django-upgrade
django-upgrade --target-version 5.2 **/*.py
```

Django 公式が推奨するこのツールが、5.0/5.1/5.2 で必要なコード変更を自動検出・修正する。

---

## Upgrade Phases (アップグレード手順)

### Phase 0: Preparation (準備) — Django 4.2 のまま

**Goal**: Django 4.2 上で非推奨警告を解消し、依存パッケージを Django 5.x 互換バージョンに上げる

#### Step 0-1: pytz → zoneinfo 移行

Django 5.0 で pytz サポートが完全に削除されるため、先に移行する。Django 4.2 でも `zoneinfo` は使用可能。

```python
# Before
import pytz
from pytz import timezone
tz = pytz.timezone("Asia/Tokyo")
dt = datetime.now(tz)

# After
from zoneinfo import ZoneInfo
tz = ZoneInfo("Asia/Tokyo")
dt = datetime.now(tz)
```

対象ファイル:
- `job/models.py` — `import pytz`
- `airone/lib/test.py` — `from pytz import timezone`
- `entry/api_v1/views.py` — `from pytz import timezone`
- `api_v1/tests/test_api.py` — `import pytz`
- `api_v1/tests/entry/test_update_history.py` — `import pytz`
- `api_v1/entry/views.py` — `import pytz`
- `api_v1/auth.py` — `import pytz`

**Verification**: `uv run python manage.py test` で全テスト通過を確認

#### Step 0-2: 依存パッケージのアップグレード (Django 4.2 互換を保ちつつ)

以下のパッケージを Django 4.2/5.x 両方に対応するバージョンに上げる:

| Package | From | To | Note |
|---|---|---|---|
| whitenoise | 5.2.0 | 6.x | Django 4.2 + 5.x 対応 |
| djangorestframework | 3.15.2 | 3.16+ | Django 4.2 + 5.2 公式対応 |
| django-debug-toolbar | 3.2.4 | 4.x+ | Django 4.2 + 5.x 対応 |
| django-filter | 24.3 | 25.x | 最新版確認 |
| django-import-export | 3.3.1 | latest | Django 5.x 対応確認 |
| django-configurations | 2.5 | latest | Django 5.x 対応確認 |
| django-storages | 1.14.1 | latest | Django 5.x 対応確認 |

**Verification**: `uv run python manage.py test` で全テスト通過を確認

#### Step 0-3: django-upgrade の実行

```bash
pip install django-upgrade
django-upgrade --target-version 5.2 **/*.py
```

自動変換されたコードをレビューし、必要に応じて手動修正。

#### Step 0-4: Deprecation warnings の確認

```bash
uv run python -W error::DeprecationWarning manage.py test 2>&1 | grep -i deprecat
```

全ての Django 4.2 deprecation warning を解消する。

**Deploy point**: Phase 0 完了後にデプロイ可能。既存の Django 4.2 上での安全な変更のみ。

---

### Phase 1: django-replicated の代替実装

**Goal**: アーカイブ済みの django-replicated を django-multidb-router で置き換える

これは最も大きな変更であり、Django バージョンを上げる前に行う。

#### Step 1-1: django-multidb-router のインストールと設定

```diff
# pyproject.toml
- "django-replicated==2.7",
+ "django-multidb-router>=0.11",
```

```python
# airone/settings_common.py

# Before
from django_replicated import settings

DATABASE_ROUTERS = ["django_replicated.router.ReplicationRouter"]
REPLICATED_DATABASE_SLAVES = ["default"]
REPLICATED_CACHE_BACKEND = settings.REPLICATED_CACHE_BACKEND
REPLICATED_DATABASE_DOWNTIME = settings.REPLICATED_DATABASE_DOWNTIME
REPLICATED_VIEWS_OVERRIDES = settings.REPLICATED_VIEWS_OVERRIDES
REPLICATED_READ_ONLY_DOWNTIME = settings.REPLICATED_READ_ONLY_DOWNTIME
REPLICATED_READ_ONLY_TRIES = settings.REPLICATED_READ_ONLY_TRIES
REPLICATED_FORCE_MASTER_COOKIE_NAME = settings.REPLICATED_FORCE_MASTER_COOKIE_NAME
REPLICATED_FORCE_MASTER_COOKIE_MAX_AGE = settings.REPLICATED_FORCE_MASTER_COOKIE_MAX_AGE
REPLICATED_FORCE_STATE_HEADER = settings.REPLICATED_FORCE_STATE_HEADER
REPLICATED_CHECK_STATE_ON_WRITE = settings.REPLICATED_CHECK_STATE_ON_WRITE
REPLICATED_FORCE_MASTER_COOKIE_STATUS_CODES = (302, 303)
REPLICATED_MANAGE_ATOMIC_REQUESTS = settings.REPLICATED_MANAGE_ATOMIC_REQUESTS

if os.environ.get("AIRONE_MYSQL_SLAVE_URL", False):
    DATABASES["slave"] = env.db("AIRONE_MYSQL_SLAVE_URL")
    REPLICATED_DATABASE_SLAVES = ["slave"]

# After
DATABASE_ROUTERS = ["multidb.PinningReplicaRouter"]
REPLICA_DATABASES = ["default"]
MULTIDB_PINNING_SECONDS = 5
MULTIDB_PINNING_COOKIE = "just_updated"

if os.environ.get("AIRONE_MYSQL_SLAVE_URL", False):
    DATABASES["slave"] = env.db("AIRONE_MYSQL_SLAVE_URL")
    REPLICA_DATABASES = ["slave"]
```

django-multidb-router を選定した理由:
- Django 4.2, 5.1, 5.2 公式テスト済み (v0.11, 2025年7月リリース)
- `PinningReplicaRouter` + `PinningRouterMiddleware` が django-replicated の中核機能 (cookie ベース master pinning) と同等
- Active にメンテナンスされている (325 stars)
- 他の代替 (django-database-routing, django-pindb) は不活発で Django 5.x 未対応

#### Step 1-2: Middleware の書き換え

```python
# airone/middleware/db.py

# Before
from django_replicated.middleware import ReplicationMiddleware
from django_replicated.utils import routers

class AirOneReplicationMiddleware(ReplicationMiddleware):
    def handle_redirect_after_write(self, request, response):
        if routers.state() == "master":
            log.debug("set force master cookie for %s", request.path)
            self.set_force_master_cookie(response)

# After
from multidb.middleware import PinningRouterMiddleware

class AirOneReplicationMiddleware(PinningRouterMiddleware):
    # PinningRouterMiddleware は write リクエスト (POST/PUT/DELETE/PATCH) 検知時に
    # 自動で cookie を設定する。AirOne の handle_redirect_after_write は
    # 「master state なら全 response に cookie」だが、
    # write リクエスト = master state なので結果は同一。
    pass
```

#### Step 1-3: テストの書き換え

`airone/tests/test_db.py` を django-multidb-router の API に合わせて書き直す:
- `multidb.pinning.pin_this_thread()` / `unpin_this_thread()` の状態検証
- Response cookie (`just_updated`) の設定有無検証

#### Step 1-4: pyproject.toml から django-replicated を削除

**Verification**:
- `uv run python manage.py test` で全テスト通過
- ステージング環境で master/slave ルーティングが正常に動作することを確認

**Deploy point**: Phase 1 完了後にデプロイ可能。Django 4.2 のまま、django-replicated のみ除去。

---

### Phase 2: Django 5.2 LTS への移行 (一括)

**Goal**: Django 4.2 → 5.2 LTS への直接移行

Phase 0 で非推奨機能は全て解消済み、Phase 1 で django-replicated は除去済みのため、ここではバージョン番号の変更と動作確認のみ。

#### Step 2-1: Django バージョン変更

```diff
- "django==4.2.28",
+ "django==5.2.3",
```

(5.2 の最新パッチバージョンを使用)

#### Step 2-2: Breaking changes の最終確認

Phase 0 で対応済みだが、念のため確認するポイント:

| Change | Version | AirOne Status |
|---|---|---|
| pytz サポート削除 | 5.0 | Phase 0-1 で対応済み |
| `USE_L10N` 削除 | 5.0 | 使用なし |
| `DEFAULT_FILE_STORAGE` 削除 | 5.1 | `STORAGES` 移行済み |
| `STATICFILES_STORAGE` 削除 | 5.1 | `STORAGES` 移行済み |
| `index_together` 削除 | 5.1 | 使用なし |
| MySQL utf8mb4 デフォルト | 5.2 | 既に utf8mb4 使用 |
| `UniqueConstraint` violation_error 動作変更 | 5.2 | `entry/models.py` で使用 — テストで確認 |
| `HttpRequest.accepted_types` ソート変更 | 5.2 | API 動作テストで確認 |
| LogoutView GET 削除 | 5.0 | API ベースのため影響なし (要確認) |

#### Step 2-3: 最終確認

- `uv run python manage.py test` で全テスト通過
- ステージング環境での E2E テスト
- パフォーマンス確認

**Verification**: `uv run python manage.py test` + ステージング環境検証

**Deploy point**: Phase 2 完了後にデプロイ — Django 5.2 LTS 移行完了

---

## Phase 間の依存関係と並行開発

```
Phase 0 ──→ Phase 1 ──┐
              │        ├──→ Phase 2 (Django 5.2)
Phase 0 ──→ Phase 2 ──┘
              ↑
     (開発は並行可能、デプロイは Phase 1 完了後)
```

**Phase 1 と Phase 2 は並行開発が可能。** 両者のコード変更は独立しており、別ブランチで同時に作業できる:

| | Phase 1 (django-replicated 代替) | Phase 2 (Django 5.2) |
|---|---|---|
| 主な変更対象 | `middleware/db.py`, `settings_common.py` (REPLICATED_* 設定), `tests/test_db.py` | `pyproject.toml` (Django version) |
| 変更の性質 | ライブラリ差し替え + middleware 書き換え | Django バージョン変更 + 動作確認 |
| Django バージョン | 4.2 のまま | 5.2 に変更 |

**ただしデプロイ順序には制約がある**: django-replicated は Django 5.0+ で動作しないため、Phase 2 のデプロイ (マージ) は Phase 1 の完了が前提。

推奨ワークフロー:
1. Phase 0 を完了・デプロイ
2. Phase 1 と Phase 2 を **別ブランチで並行開発**
3. Phase 1 を先にマージ・デプロイ
4. Phase 2 のブランチを Phase 1 の結果にリベースしてマージ・デプロイ

---

## Dependency Version Matrix (最終的な依存パッケージ)

| Package | Current | Target | Django 5.2 Support |
|---|---|---|---|
| django | 4.2.28 | 5.2.x | — |
| djangorestframework | 3.15.2 | 3.16+ | Official (3.16.0 で 5.2 公式対応) |
| celery | 5.5.3 | 5.5.x (keep) | Compatible |
| django-replicated | 2.7 | **削除** | N/A |
| django-multidb-router | — | 0.11+ | Official (4.2, 5.1, 5.2 テスト済み) |
| django-configurations | 2.5 | latest | Confirm |
| whitenoise | 5.2.0 | 6.x+ | Official |
| django-debug-toolbar | 3.2.4 | 4.x+ | Official |
| django-filter | 24.3 | 25.x | Official |
| django-import-export | 3.3.1 | latest | Confirm |
| django-simple-history | 3.11.0 | 3.11+ (keep) | Official (4.2-6.0) |
| django-storages | 1.14.1 | latest | Official |
| drf-spectacular | 0.29.0 | 0.29+ (keep) | Official |
| social-auth-app-django | 5.4.3 | 5.4+ (keep) | Official |

## Rollback Strategy (ロールバック戦略)

- 各 Phase は独立してデプロイ・ロールバック可能
- Phase 0, 1 は Django 4.2 上の変更なので、Django バージョンに関わるリスクなし
- Phase 2 は Django バージョン変更のため、`pyproject.toml` の Django バージョンを戻すだけでロールバック可能
- データベースマイグレーション: Django 5.x で新しいマイグレーションが生成される場合、`migrate --run-syncdb` ではなく通常の `migrate` を使用し、reverse migration が可能な状態を維持する

## Timeline Summary (タイムライン)

```
Phase 0: Preparation (Django 4.2 のまま)
  ├─ Step 0-1: pytz → zoneinfo
  ├─ Step 0-2: 依存パッケージのアップグレード
  ├─ Step 0-3: django-upgrade --target-version 5.2 の実行
  └─ Step 0-4: Deprecation warnings 解消
  → Deploy ✓
                       ┌─────────────────────────────────────────────┐
                       │  並行開発可能 (デプロイは Phase 1 → 2 の順) │
                       ├─────────────────────────────────────────────┤
Phase 1:               │  Phase 2:                                   │
django-replicated 代替 │  Django 5.2 LTS (一括移行)                  │
(Django 4.2 のまま)    │                                             │
  ├─ Step 1-1          │    ├─ Step 2-1: Django 5.2.x に変更         │
  ├─ Step 1-2          │    ├─ Step 2-2: Breaking changes 最終確認   │
  ├─ Step 1-3          │    └─ Step 2-3: E2E テスト                  │
  └─ Step 1-4          │                                             │
                       └─────────────────────────────────────────────┘
  → Deploy ✓ (先)        → Rebase & Deploy ✓ (後, Final)
```

## Notes

- Django 5.2 は LTS (Long Term Support) であり、2028年4月までセキュリティサポートが提供される
- Phase 0-1 の作業量が最も大きい（特に django-replicated の代替）。Phase 2 は軽量（バージョン変更 + 動作確認のみ）
- Phase 1 と Phase 2 の並行開発により、全体のリードタイムを短縮可能
- 中間バージョン (5.0, 5.1) を経由しない理由: AirOne に影響する breaking change が pytz 削除のみであり、Phase 0 で対応済みのため
- `django-upgrade` ツールにより、5.0/5.1/5.2 の全 breaking changes を自動検出・修正可能
- 各 Phase のデプロイ間隔は数日〜1週間程度を推奨。問題が発生した場合の調査・修正の時間を確保する

## References

- [Django 5.0 Release Notes](https://docs.djangoproject.com/en/5.2/releases/5.0/)
- [Django 5.1 Release Notes](https://docs.djangoproject.com/en/5.2/releases/5.1/)
- [Django 5.2 Release Notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Django Upgrading Guide](https://docs.djangoproject.com/en/5.2/howto/upgrade-version/)
- [Python.org Django 5 Upgrade Case Study](https://scriptr.dev/blog/python-org-django-5-upgrade)
- [Open edX Django 5.2 Upgrade Plan](https://discuss.openedx.org/t/django-5-2-upgrade-plan/15397)
- [DRF 3.16 Release Notes](https://www.django-rest-framework.org/community/3.16-announcement/)
- [django-multidb-router](https://github.com/jbalogh/django-multidb-router)

---

## Appendix: Phase 1 Deep Dive — django-replicated 代替の詳細調査

### A1. django-replicated のアーカイブ経緯

| Item | Detail |
|---|---|
| リポジトリ | [yandex/django_replicated](https://github.com/yandex/django_replicated) (355 stars, 65 forks) |
| アーカイブ日 | 2025年1月29日 (Yandex により read-only 化) |
| 最終リリース | 2020年4月10日 (v2.7) — 5年間新規リリースなし |
| Django 5.x 互換性 | なし。`MiddlewareMixin.__init__()` の `get_response` 必須化などに未対応 |

[Issue #61](https://github.com/yandex/django_replicated/issues/61) では「Django 組み込みの DATABASE_ROUTERS と何が違うのか？」という問いに対して「レプリケーションラグへの対処が異なる」と回答されている。つまりこのライブラリの核心的価値は **cookie ベースの read-after-write 一貫性保証** にある。

### A2. AirOne における django-replicated の利用実態

#### A2.1 使用箇所の全量

| File | Usage |
|---|---|
| `airone/settings_common.py:11` | `from django_replicated import settings` — デフォルト設定値のインポート |
| `airone/settings_common.py:157-175` | `DATABASE_ROUTERS`, `REPLICATED_*` 設定 12項目 |
| `airone/middleware/db.py:3-4` | `ReplicationMiddleware`, `routers` のインポートと継承 |
| `airone/auth/ldap.py:52` | slave DB でのユーザー作成回避ロジック (コメントのみ) |
| `airone/tests/test_db.py` | ルーティング動作のテスト (4テストケース) |

#### A2.2 利用している機能の範囲

**実際に使っている機能** (代替実装が必要):

1. **ReplicationRouter** — `db_for_read()` / `db_for_write()` による master/slave 自動振り分け
2. **ReplicationMiddleware** — HTTP メソッドに基づく routing 状態の初期化
3. **Cookie-based master pinning** — write 後に cookie で一定期間 master を強制
4. **Thread-local state management** — `routers.state()` による現在の状態取得

**使っていない機能** (実装不要):

- `REPLICATED_VIEWS_OVERRIDES` — 空 dict (`{}`)、ビューごとのオーバーライド未使用
- `REPLICATED_MANAGE_ATOMIC_REQUESTS` — `False` (デフォルト)
- `ReadOnlyMiddleware` — 未使用
- `@use_master` / `@use_slave` デコレータ — 未使用
- `REPLICATED_FORCE_STATE_HEADER` による HTTP ヘッダーオーバーライド — 設定はあるが実質未使用

#### A2.3 AirOne 固有のカスタマイズ

`AirOneReplicationMiddleware.handle_redirect_after_write()` のオーバーライド:

```python
# django-replicated オリジナル:
#   POST の 302/303 レスポンスにのみ cookie を設定
#   2回目の GET で cookie を削除

# AirOne カスタム:
#   routers.state() == "master" ならステータスコードに関係なく全 response に cookie 設定
#   Cookie は MAX_AGE (デフォルト 5秒) で自動削除、明示的な削除ロジックなし
#   理由: レプリケーション遅延が大きい環境への対応
```

#### A2.4 Request/Response フロー (現在の動作)

```
1. Request 受信
   ↓
2. ReplicationMiddleware.process_request()
   - GET/HEAD/OPTIONS/TRACE → routers.init("slave")
   - POST/PUT/DELETE/PATCH  → routers.init("master")
   - Cookie "just_updated" == "true" なら → "master" に上書き
   ↓
3. View 処理
   - ORM read  → db_for_read()  → state に従い master or slave
   - ORM write → db_for_write() → 常に "default" (master)
   ↓
4. AirOneReplicationMiddleware.handle_redirect_after_write()
   - routers.state() == "master" → cookie "just_updated" を設定 (max_age=5s)
   ↓
5. ReplicationMiddleware.process_response()
   - routers.reset() で Thread-local 状態をクリア
   ↓
6. Response 返送
```

#### A2.5 Slave DB の設定状況

```python
# デフォルト: slave == master (同じ "default" DB)
REPLICATED_DATABASE_SLAVES = ["default"]

# 環境変数で slave を明示指定した場合のみ分離
if os.environ.get("AIRONE_MYSQL_SLAVE_URL", False):
    DATABASES["slave"] = env.db("AIRONE_MYSQL_SLAVE_URL")
    REPLICATED_DATABASE_SLAVES = ["slave"]
```

**重要**: `AIRONE_MYSQL_SLAVE_URL` が設定されていない環境では、master と slave が同一の DB を指す。つまり **レプリケーション機能は事実上の no-op** になる。これは代替実装時にも保持すべき挙動。

### A3. 代替パッケージの比較

| Package | Stars | Last Release | Django 5.2 | Cookie Pinning | Recommendation |
|---|---|---|---|---|---|
| **django-multidb-router** | 325 | 2025/07 (v0.11) | Yes (公式テスト済み) | Yes | **Best option** |
| django-database-routing | 15 | 2022/08 | Unknown | No | Not recommended |
| django-pindb | 9 | Inactive (Django 1.4 世代) | No | Yes | Not viable |

django-multidb-router (v0.11) の機能:
- `ReplicaRouter` — 全読み取りをレプリカにラウンドロビン、書き込みは default (master)
- `PinningReplicaRouter` — `ReplicaRouter` + 書き込み後は cookie ベースで master 固定
- `PinningRouterMiddleware` — 書き込み検知 + cookie 設定
- `use_primary_db` デコレータ/コンテキストマネージャ
- 設定: `MULTIDB_PINNING_SECONDS`, `MULTIDB_PINNING_COOKIE`, `REPLICA_DATABASES`

### A4. 既知のリスクと注意点

#### Risk 1: Celery タスクでのレプリケーションラグ

Celery タスクが replica DB から読み取ると、master への書き込みがまだ反映されていない可能性がある。

**対策**: Celery タスク内で `Model.objects.using("default").get()` のように明示的に master から読み取るか、`AIRONE_MYSQL_SLAVE_URL` 未設定環境 (master only) で運用する場合は影響なし。

#### Risk 2: トランザクション内の read routing

`transaction.atomic()` 内での読み取りが replica に向くと、未コミットデータが見えない問題が発生する。

**django-multidb-router の対応**: `PinningReplicaRouter` は write リクエスト全体を pin するため、atomic ブロック内の read も master に向く。

#### Risk 3: Cookie の切り替え時のセッション不整合

**対策**: cookie 名を `just_updated` のまま維持する (`MULTIDB_PINNING_COOKIE = "just_updated"`)。django-multidb-router も cookie 値として `"y"` を設定するが、`PinningRouterMiddleware` は cookie の存在のみをチェックするため、既存の `"true"` 値でも問題なく動作する。
