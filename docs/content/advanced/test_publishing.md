# 実験的パッケージ公開ガイド (@syucream)

PRをマージせずに@syucreamリポジトリでパッケージを実験的に公開する手順

## 方法1: GitHub Actions 経由での公開 (推奨)

### 重要：ワークフローが表示されない理由

現在 `release-plugin-sdk.yml` ワークフローはfeature branchにのみ存在するため、GitHub ActionsページのAll workflowsリストには表示されません。しかし、**タグをプッシュすることで直接実行可能**です。

### タグ経由での公開（最も簡単）

```bash
# 1. 現在のブランチ（feature/backend-plugins）で実行
git tag plugin-sdk-1.0.0-alpha.1
git push origin plugin-sdk-1.0.0-alpha.1

# 2. GitHub ActionsでWorkflowが自動実行される
# https://github.com/syucream/airone/actions で確認可能
```

### 代替方法：ワークフローファイルをmasterに追加

ワークフローをActionsページに表示させたい場合：

```bash
# 1. masterブランチに一時的にワークフローファイルを追加
git checkout master
cp .github/workflows/release-plugin-sdk.yml /tmp/
git checkout feature/backend-plugins
git checkout master
mv /tmp/release-plugin-sdk.yml .github/workflows/
git add .github/workflows/release-plugin-sdk.yml
git commit -m "Add plugin SDK release workflow for testing"
git push origin master

# 2. 手動実行が可能になる
```

## 方法2: 手動での公開（バックアップ）

### 1. 前提条件

GitHub Personal Access Token with `write:packages`, `read:packages`, `repo` スコープ

### 2. 手動公開コマンド

```bash
cd plugin/sdk
python -m build
twine upload --repository-url https://pypi.pkg.github.com/syucream/ \
  --username syucream --password $GITHUB_TOKEN dist/*
```

### 2. 他の開発者がパッケージを使用する方法

#### pip経由でのインストール

```bash
# 認証設定（1回のみ）
pip config set global.extra-index-url https://pypi.pkg.github.com/syucream/simple/

# パッケージインストール
pip install --index-url https://pypi.pkg.github.com/syucream/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pagoda-plugin-sdk==1.0.0-alpha.1
```

#### poetry経由でのインストール

```bash
# ソースを追加
poetry source add syucream-github https://pypi.pkg.github.com/syucream/simple/ --secondary

# パッケージ追加
poetry add --source syucream-github pagoda-plugin-sdk==1.0.0-alpha.1
```

### 3. 認証情報の設定

#### pip用の認証設定

```bash
# ~/.pypirc ファイルを作成
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi
    github

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__

[github]
repository = https://pypi.pkg.github.com/syucream/
username = syucream
password = $GITHUB_TOKEN
EOF
```

#### twine用の設定

```bash
# twineでの公開（.pypirc を使用）
twine upload --repository github dist/*
```

## 注意事項

1. **実験的バージョン**: `1.0.0-alpha.1` として公開し、実験であることを明示
2. **認証**: GitHub Packagesは認証が必要なため、使用者もGitHubトークンが必要
3. **プライベート**: @syucreamのプライベートパッケージとして公開される
4. **テスト後の削除**: 実験後は不要なパッケージバージョンを削除可能

## トラブルシューティング

### 認証エラー

```bash
# トークンの権限確認
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# パッケージリストの確認
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/packages?package_type=pypi
```

### パッケージが見つからない

1. GitHub Packagesは認証が必要
2. パブリックリポジトリでもパッケージはプライベート
3. 正しいURLとトークンを使用する

## 後片付け

実験終了後：

1. GitHub → Settings → Packages から該当パッケージを削除
2. 設定ファイルから実験用設定を削除
3. 本番リリース時は正式なバージョン番号を使用