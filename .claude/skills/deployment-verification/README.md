# Deployment Verification Skill

デプロイメント検証スキルは、Letter Pack Label Makerプロジェクトの3つのデプロイメント方法（GitHub Pages、Docker環境、ローカル環境）を自動的に検証し、リンク切れ、パフォーマンス問題、環境固有の問題を早期に発見します。

## 目次

- [概要](#概要)
- [機能](#機能)
- [使い方](#使い方)
- [検証項目](#検証項目)
- [設定](#設定)
- [CI/CD統合](#cicd統合)
- [トラブルシューティング](#トラブルシューティング)

## 概要

このスキルは、以下のような問題を自動的に検出します：

- ✅ **リンク切れ**: ドキュメントやWebページの壊れたリンク
- ✅ **デプロイメント失敗**: GitHub PagesやDockerの起動失敗
- ✅ **パフォーマンス低下**: ページロードやPyodide初期化の遅延
- ✅ **環境固有の問題**: フォント不足、依存関係エラーなど

## 機能

### 1. GitHub Pages検証

- **アクセシビリティチェック**: ページが正常にアクセス可能か確認
- **Pyodide初期化**: ブラウザでPythonが正常に動作するか検証
- **フォームチェック**: ラベル生成フォームが正しく表示されるか確認
- **リンクチェック**: すべてのリンクが有効か検証（内部・外部）
- **パフォーマンス計測**: ページロード時間、Pyodide初期化時間

### 2. Docker環境検証

- **ビルド検証**: Dockerイメージが正常にビルドできるか確認
- **イメージサイズチェック**: イメージサイズが適切か確認（警告: >500MB）
- **ヘルスチェック**: コンテナが正常に起動し、ヘルシーになるか検証
- **フォント確認**: Noto CJKフォントがインストールされているか確認
- **Webサーバーテスト**: Flaskサーバーが正常に応答するか確認

### 3. ローカル環境検証

- **CLI動作確認**: CLIが正常に動作するか検証
- **Webサーバー起動**: Flaskサーバーがローカルで起動するか確認
- **PDF生成テスト**: サンプルCSVからPDFを生成できるか確認

### 4. パフォーマンス監視

- **ベースライン比較**: 過去のパフォーマンスと比較
- **回帰検出**: パフォーマンスが低下していないか確認
- **レポート生成**: Markdown形式でレポートを生成

## 使い方

### Claude Codeでの使用

Claude Codeと会話する際に、以下のようなフレーズで自動的にスキルが起動します：

**日本語:**
```
デプロイメントを検証して
GitHub Pagesが正しく動作しているか確認して
リンク切れをチェックして
パフォーマンスを計測して
Docker環境をテストして
```

**English:**
```
Verify the deployment
Check if GitHub Pages is working
Check for broken links
Measure performance
Test the Docker environment
```

### コマンドラインでの使用

スクリプトを直接実行することもできます：

```bash
# すべてのデプロイメントターゲットを検証
uv run python tools/deployment_verifier.py --target all

# GitHub Pagesのみ検証
uv run python tools/deployment_verifier.py --target github-pages

# Dockerのみ検証
uv run python tools/deployment_verifier.py --target docker

# リンクチェックのみ実行
uv run python tools/deployment_verifier.py --target github-pages --check-links-only

# パフォーマンス計測
uv run python tools/performance_metrics.py --target all

# レポートをファイルに出力
uv run python tools/deployment_verifier.py --target all --output-file report.md
```

### pytestでの使用

テストフレームワークとして使用：

```bash
# GitHub Pages検証テスト
uv run pytest tests/test_deployment_verification.py -v

# Docker検証テスト（Dockerデーモンが必要）
uv run pytest tests/test_docker_deployment.py -v -m docker

# パフォーマンステスト
uv run pytest tests/test_performance.py -v -m performance

# 特定のテストのみ実行
uv run pytest tests/test_deployment_verification.py::TestGitHubPagesDeployment::test_link_integrity -v
```

## 検証項目

### GitHub Pages

| 項目 | 説明 | 閾値 |
|------|------|------|
| ページアクセス | HTTPステータスコードが200か | 必須 |
| ページロード時間 | 初回ロード時間 | <3秒 |
| Pyodide初期化 | Pyodideの起動時間 | <90秒 |
| フォントダウンロード | Noto Sans JPのダウンロード | <30秒 |
| フォーム表示 | label-formが表示されるか | 必須 |
| リンクチェック | すべてのリンクが有効か | 推奨 |

### Docker

| 項目 | 説明 | 閾値 |
|------|------|------|
| イメージビルド | Dockerイメージがビルドできるか | 必須 |
| イメージサイズ | ビルドしたイメージのサイズ | <500MB（警告） |
| コンテナ起動 | コンテナが起動するか | 必須 |
| ヘルスチェック | ヘルシーになるまでの時間 | <30秒 |
| Noto CJKフォント | フォントがインストールされているか | 必須 |
| Webサーバー応答 | / にアクセスして200が返るか | 必須 |

### パフォーマンス

| メトリクス | 説明 | 警告閾値 | エラー閾値 |
|----------|------|---------|----------|
| 回帰率 | ベースラインからの変化 | +10% | +20% |
| ページロード | GitHub Pagesの読み込み | 3秒 | 5秒 |
| Pyodide初期化 | Pyodideの起動 | 90秒 | 120秒 |
| PDF生成 | PDF生成時間 | 5秒 | 10秒 |

## 設定

設定ファイル: `.claude/skills/deployment-verification/config.yaml`

### 主要な設定項目

```yaml
# GitHub Pages URL（自動的に検出されます）
github_pages:
  production_url: "https://your-username.github.io/your-repo/"

# パフォーマンス閾値
github_pages:
  performance_thresholds:
    page_load_ms: 3000       # ページロード時間
    pyodide_init_ms: 90000   # Pyodide初期化時間
    font_download_ms: 30000  # フォントダウンロード時間

# リンクチェック設定
github_pages:
  link_check:
    follow_external: true         # 外部リンクもチェック
    external_as_warning: true     # 外部リンクのエラーは警告のみ
    ignore_patterns:
      - "mailto:"
      - "#"

# Docker設定
docker:
  image_name: "letterpack-web"
  health_check_timeout: 30
  image_size_warning_mb: 500

# パフォーマンス設定
performance:
  regression_warning_threshold: 10  # 10%以上の低下で警告
  regression_error_threshold: 20    # 20%以上の低下でエラー
```

### カスタマイズ

設定をカスタマイズするには、`config.yaml`を編集してください：

```bash
# 設定ファイルを開く
vim .claude/skills/deployment-verification/config.yaml

# または
code .claude/skills/deployment-verification/config.yaml
```

## CI/CD統合

GitHub Actionsワークフローが自動的に設定されます。

### 自動実行タイミング

1. **GitHub Pagesデプロイ後**: deploy-pagesワークフロー完了時
2. **PR作成・更新時**: deployment-verificationに関連するファイル変更時
3. **毎日のヘルスチェック**: 毎日9:00 UTC（18:00 JST）
4. **手動トリガー**: GitHub Actionsページから手動実行

### 手動実行

GitHub Actionsページから手動で実行できます：

1. GitHubリポジトリの「Actions」タブを開く
2. 「Deployment Verification」ワークフローを選択
3. 「Run workflow」をクリック
4. 検証タイプを選択：
   - `all`: すべての環境
   - `github-pages`: GitHub Pagesのみ
   - `docker`: Dockerのみ
   - `performance`: パフォーマンス計測のみ

### Artifactsのダウンロード

検証レポートはGitHub Actions Artifactsとしてダウンロードできます：

- **保持期間**: 30日間
- **ファイル形式**: Markdownレポート
- **ダウンロード方法**: ワークフロー実行ページから

## トラブルシューティング

### よくある問題と解決策

#### 1. Pyodideの初期化がタイムアウトする

**症状**: `Pyodide initialization timed out after 90000ms`

**解決策**:
```yaml
# config.yamlで閾値を増やす
github_pages:
  performance_thresholds:
    pyodide_init_ms: 120000  # 90秒 → 120秒
```

#### 2. リンクチェックで外部リンクが頻繁に失敗する

**症状**: `External link check failed: https://example.com`

**解決策**:
```yaml
# 外部リンクのエラーを警告に変更
github_pages:
  link_check:
    external_as_warning: true

# または特定のパターンを無視
    ignore_patterns:
      - "mailto:"
      - "https://example.com/*"
```

#### 3. Dockerデーモンが実行されていない

**症状**: `Cannot connect to the Docker daemon`

**解決策**:
```bash
# Dockerデーモンを起動
sudo systemctl start docker

# または Docker Desktopを起動（Mac/Windows）
```

#### 4. Playwrightがインストールされていない

**症状**: `Playwright executable doesn't exist`

**解決策**:
```bash
# Playwrightをインストール
uv run playwright install chromium
uv run playwright install-deps chromium
```

#### 5. パフォーマンスメトリクスが不安定

**症状**: 実行ごとにメトリクスが大きく変動する

**解決策**:
- CI環境のリソース変動を考慮
- 閾値を少し緩める
- 複数回計測して平均を取る

### デバッグモード

詳細なログを確認するには、デバッグモードを有効にします：

```yaml
# config.yamlでデバッグモードを有効化
debug:
  enabled: true
  verbose_logging: true
  save_screenshots: true
```

### サポート

問題が解決しない場合は、以下の情報とともにissueを作成してください：

1. エラーメッセージ
2. 実行コマンド
3. 環境情報（OS、Pythonバージョン、Dockerバージョン）
4. config.yamlの設定
5. デバッグログ（可能であれば）

## 今後の機能拡張

以下の機能拡張が検討されています：

- [ ] **アクセシビリティテスト**: WCAG準拠チェック
- [ ] **セキュリティスキャン**: 脆弱性検出
- [ ] **SEO検証**: メタタグとSEO最適化チェック
- [ ] **ビジュアル回帰テスト**: スクリーンショット比較
- [ ] **モバイルテスト**: レスポンシブデザイン検証
- [ ] **クロスブラウザテスト**: Firefox、Safari対応
- [ ] **通知機能**: Slack/Discord通知
- [ ] **メトリクスダッシュボード**: パフォーマンス推移の可視化

## ライセンス

このスキルは、Letter Pack Label Makerプロジェクトのライセンスに従います。

## 貢献

バグ報告や機能リクエストは、GitHubのissueで受け付けています。
