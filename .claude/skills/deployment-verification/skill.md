# Deployment Verification Skill

## Skill Overview

このスキルは、Letter Pack Label Makerプロジェクトのデプロイメントを自動検証します。GitHub Pages、Docker環境、ローカル環境の3つのデプロイメント方法すべてに対応し、リンク切れ、パフォーマンス問題、環境固有の問題を早期に検出します。

## When to Use This Skill

このスキルは、以下のようなユーザーのリクエストに対して**自動的に**起動されるべきです：

### 日本語のトリガーフレーズ
- "デプロイメントを検証して"
- "デプロイが正しく動作しているか確認して"
- "GitHub Pagesが動いているか確認して"
- "Docker環境をテストして"
- "リンク切れをチェックして"
- "パフォーマンスを計測して"
- "デプロイメントのヘルスチェックをして"

### 英語のトリガーフレーズ
- "verify the deployment"
- "check if the deployment is working"
- "validate GitHub Pages"
- "test the Docker environment"
- "check for broken links"
- "measure performance"
- "run deployment health check"

### コンテキストに基づく自動起動

以下の状況では、ユーザーが明示的に要求しなくても、このスキルの使用を**提案**してください：

1. **デプロイ後のチェック**
   - GitHub Actionsのdeploy-pagesワークフローが完了した後
   - Docker環境の設定を変更した後
   - docker-compose.ymlやDockerfileを修正した後

2. **リンクに関する変更**
   - README.mdやSTATIC_VERSION.mdなどのドキュメントを更新した後
   - index_static.htmlやpoc_pyodide.htmlのリンクを変更した後
   - 新しいページを追加した後

3. **パフォーマンスに影響する変更**
   - Pyodideの設定を変更した後
   - 大きな依存関係を追加した後
   - PDF生成ロジックを変更した後

4. **定期的なヘルスチェック**
   - PRのレビュー前
   - mainブランチへのマージ前
   - リリース前

## How to Use This Skill

### 基本的な使用方法

1. **すべてのデプロイメントターゲットを検証**
   ```
   すべてのデプロイメントを検証して
   ```

2. **特定のターゲットのみ検証**
   ```
   GitHub Pagesだけチェックして
   Docker環境だけテストして
   ```

3. **リンクチェックのみ実行**
   ```
   リンク切れをチェックして
   ドキュメントのリンクを確認して
   ```

4. **パフォーマンス計測のみ実行**
   ```
   パフォーマンスを測定して
   GitHub Pagesの読み込み速度を確認して
   ```

### 実行フロー

このスキルを起動したら、以下の手順で処理を進めてください：

#### ステップ 1: 検証ターゲットの確認

ユーザーのリクエストから、検証するターゲットを判断します：
- **all**: すべての環境（GitHub Pages、Docker、ローカル）
- **github-pages**: GitHub Pagesのみ
- **docker**: Docker環境のみ
- **local**: ローカル環境のみ
- **links**: リンクチェックのみ
- **performance**: パフォーマンス計測のみ

明示的な指定がない場合は、コンテキストから推測するか、ユーザーに確認してください。

#### ステップ 2: 設定の読み込み

`.claude/skills/deployment-verification/config.yaml`から設定を読み込みます。

```python
import yaml

with open('.claude/skills/deployment-verification/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
```

#### ステップ 3: 検証の実行

`tools/deployment_verifier.py`を実行します：

```bash
# すべての検証を実行
uv run python tools/deployment_verifier.py --target all

# GitHub Pagesのみ検証
uv run python tools/deployment_verifier.py --target github-pages

# リンクチェックのみ
uv run python tools/deployment_verifier.py --target github-pages --check-links-only

# パフォーマンス計測
uv run python tools/performance_metrics.py --target all
```

#### ステップ 4: 結果の解析と報告

検証スクリプトの出力を解析し、ユーザーにわかりやすく報告します：

**成功の場合:**
```
✅ デプロイメント検証が完了しました

GitHub Pages:
- ステータス: ✅ 正常
- ページロード: 1.2秒
- Pyodide初期化: 45.3秒
- リンクチェック: 48個のリンク、すべて正常

Docker:
- ビルド: ✅ 成功（イメージサイズ: 380MB）
- ヘルスチェック: ✅ 正常（5.2秒）
- フォント: ✅ Noto CJK インストール済み
```

**問題が見つかった場合:**
```
⚠️ デプロイメント検証で問題が見つかりました

GitHub Pages:
- ステータス: ⚠️ 問題あり
- リンクチェック: 2個の壊れたリンクを発見
  - https://example.com/old-page → 404 Not Found
  - https://docs.example.com/removed → 404 Not Found

推奨アクション:
1. README.mdの古いリンクを更新してください
2. 新しいURLに置き換えるか、リンクを削除してください
```

#### ステップ 5: 次のアクション の提案

検証結果に基づいて、次のアクションを提案します：

- **問題が見つかった場合**: 修正方法を提案し、必要に応じて自動修正を申し出る
- **パフォーマンス低下が見つかった場合**: 原因の調査と最適化を提案
- **すべて正常の場合**: デプロイメントが安全であることを確認

## Implementation Details

### 使用するツールとスクリプト

1. **tools/deployment_verifier.py**
   - GitHub Pagesの検証
   - Dockerの検証
   - リンクチェック
   - ヘルスチェック

2. **tools/performance_metrics.py**
   - パフォーマンス計測
   - ベースラインとの比較
   - レポート生成

3. **tests/test_deployment_verification.py**
   - pytest統合
   - 自動テスト

### 必要な依存関係

```toml
[project.optional-dependencies]
dev = [
    "playwright>=1.40.0",
    "beautifulsoup4>=4.12.0",
    "docker>=7.0.0",
    "pyyaml>=6.0",
    "psutil>=5.9.0",
]
```

### エラーハンドリング

以下のエラーが発生する可能性があります：

1. **GitHub Pagesにアクセスできない**
   - デプロイが完了していない可能性
   - 30秒待ってから再試行を提案

2. **Dockerデーモンが実行されていない**
   - Dockerの起動を指示
   - または、Docker検証をスキップ

3. **Playwrightがインストールされていない**
   - インストールコマンドを提案：
     ```bash
     uv run playwright install chromium
     uv run playwright install-deps chromium
     ```

4. **設定ファイルが見つからない**
   - デフォルト設定で実行するか確認

## Best Practices

### 検証のタイミング

1. **必須**: mainブランチへのマージ前
2. **推奨**: PR作成時
3. **定期**: 毎日のヘルスチェック（GitHub Actionsで自動化）

### レポートの保存

検証結果は以下の場所に保存してください：
- **ローカル**: `verification_reports/`ディレクトリ
- **CI/CD**: GitHub Actions Artifacts（30日間保持）

### パフォーマンスベースラインの更新

パフォーマンスが大幅に改善された場合（20%以上）、ベースラインの更新を提案してください：

```bash
# 現在のメトリクスをベースラインとして保存
cp performance-metrics.json .github/performance-baseline.json
```

## Testing

このスキルをテストするには：

```bash
# すべてのテストを実行
uv run pytest tests/test_deployment_verification.py -v

# Docker tests (Docker daemon required)
uv run pytest tests/test_docker_deployment.py -v -m docker

# Performance tests
uv run pytest tests/test_performance.py -v -m performance
```

## Integration with CI/CD

GitHub Actionsワークフロー（`.github/workflows/deployment-verification.yml`）が設定されています。

ワークフローは以下のタイミングで自動実行されます：
- GitHub Pagesへのデプロイ完了後
- PRの作成・更新時
- 毎日のスケジュール実行（9:00 UTC）
- 手動トリガー

## Troubleshooting

### 一般的な問題と解決策

1. **Pyodideの初期化がタイムアウトする**
   - `config.yaml`の`pyodide_init_ms`を増やす（現在: 90000ms）
   - GitHub Pagesのキャッシュをクリア

2. **リンクチェックで外部リンクが頻繁に失敗する**
   - `config.yaml`の`external_as_warning`を`true`に設定
   - または特定のドメインを`ignore_patterns`に追加

3. **Dockerイメージのビルドが失敗する**
   - Dockerfileの構文を確認
   - ビルドログを確認してエラーの原因を特定

4. **パフォーマンスメトリクスが不安定**
   - 複数回計測して平均を取る
   - CI環境のリソース変動を考慮

## Future Enhancements

将来の機能拡張として、以下が検討されています：

1. **アクセシビリティテスト**: WCAG準拠チェック
2. **セキュリティスキャン**: 脆弱性検出
3. **SEO検証**: メタタグとSEO最適化
4. **ビジュアル回帰テスト**: スクリーンショット比較
5. **モバイルテスト**: レスポンシブデザイン検証
6. **クロスブラウザテスト**: Firefox、Safari対応

## Summary

このスキルを使用することで、デプロイメントの品質を自動的に保証し、問題を早期に発見できます。GitHub Pages、Docker、ローカル環境のすべてをカバーし、包括的な検証を提供します。
