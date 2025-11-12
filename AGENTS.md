# AI Agents Guide

このドキュメントは、AIエージェントがこのプロジェクトで作業する際のガイドラインです。

## プロジェクト概要

**Letter Pack Label Maker** は、日本郵便のレターパック用ラベルPDFを生成するPythonツールです。

### 3つのインターフェース

このプロジェクトは、用途に応じて3つのインターフェースを提供しています：

#### 1. CLI版（コマンドライン）
- ターミナルから直接ラベル生成
- 対話形式または引数指定で実行
- CSV一括生成にも対応（4upレイアウト、複数ページ）
- 用途：ローカル開発、バッチ処理

#### 2. Webサーバー版（Flask）
- ブラウザからフォーム入力でラベル生成
- サーバー起動が必要（Flask）
- Docker環境での実行を推奨（フォント統一）
- 用途：内部ツール、サーバー環境での利用

#### 3. 静的HTML版（Pyodide）⭐ 推奨
- サーバー不要、HTMLファイルをブラウザで開くだけ
- Pyodide（WebAssembly）でPythonをブラウザ実行
- GitHub Pagesで公開可能
- 完全オフライン対応（初回ロード後）
- 用途：公開ツール、サーバーレス環境

### 主な機能
- 単一ラベル生成（CLI/Webサーバー/静的HTML）
- CSV一括生成（4upレイアウト、複数ページ対応）
- 敬称のカスタマイズ（様、殿、省略可能）
- 複数エンコーディング対応（UTF-8、Shift_JIS）
- A4サイズPDFに汎用的なTo/Fromフォーマットのラベルを出力

### 技術スタック
- **言語**: Python 3.8.1+（ローカル）、Python 3.12（Docker）
- **PDF生成**: ReportLab
- **Webフレームワーク**: Flask（Webサーバー版）
- **ブラウザ実行**: Pyodide 0.24.1（静的HTML版）
- **コンテナ**: Docker / Docker Compose
- **パッケージ管理**: uv
- **ビルドシステム**: Hatchling
- **リンター/フォーマッター**: Ruff
- **テストフレームワーク**: pytest、Playwright（静的HTML版）
- **CI/CD**: GitHub Actions（5つのワークフロー）

## 開発環境のセットアップ

### 依存関係のインストール
```bash
# 本番用依存関係のみ
uv sync

# 開発用依存関係も含める
uv sync --all-extras
```

### プロジェクト構造
```
.
├── src/letterpack/           # メインパッケージ
│   ├── cli.py                # CLI実装
│   ├── csv_parser.py         # CSV処理
│   ├── label.py              # ラベル生成ロジック
│   └── web.py                # Flaskウェブサーバー
├── tests/                    # テストコード
│   ├── test_label.py         # ラベル生成のテスト
│   ├── test_csv_parser.py    # CSV処理のテスト
│   └── conftest.py           # pytest設定
├── .github/workflows/        # GitHub Actionsワークフロー
│   ├── main.yml              # PDF生成テスト
│   ├── test-static-webui.yml # 静的WebUIテスト（Playwright）
│   ├── deploy-pages.yml      # GitHub Pagesデプロイ
│   ├── claude.yml            # Claude統合
│   └── claude-code-review.yml# Claudeコードレビュー
├── index_static.html         # 静的HTML版（本番用）
├── poc_pyodide.html          # Pyodide PoC版
├── examples/                 # サンプル
├── config/                   # 設定ファイル
├── Dockerfile                # Dockerイメージ定義
├── docker-compose.yml        # Docker Compose設定
├── pyproject.toml            # プロジェクト設定
├── README.md                 # プロジェクト説明
├── AGENTS.md                 # AIエージェント向けガイド（このファイル）
├── CLAUDE.md                 # Claude Code固有のガイド
├── DOCKER.md                 # Docker環境の説明
└── STATIC_VERSION.md         # 静的HTML版の技術詳細
```

## コーディング規約

### スタイルガイド
- **行の長さ**: 最大100文字
- **Pythonバージョン**: 3.8以上をターゲット
- **フォーマッター**: Ruff（自動フォーマット）
- **クォート**: ダブルクォート使用
- **インデント**: スペース4つ

### リントとフォーマット
```bash
# コードのフォーマット
uv run ruff format src tests

# リントチェック
uv run ruff check src tests

# リントの自動修正
uv run ruff check --fix src tests
```

### テスト

#### pytest（Pythonコード）
```bash
# すべてのテストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=letterpack --cov-report=html

# 特定のテストのみ実行
uv run pytest tests/test_label.py
uv run pytest tests/test_csv_parser.py
```

**テストファイル：**
- `tests/test_label.py` - ラベル生成ロジックのテスト
- `tests/test_csv_parser.py` - CSV処理のテスト
- `tests/conftest.py` - pytest設定とフィクスチャ

#### Playwright（静的HTML版）

静的HTML版（Pyodide）は、Playwrightで自動的にブラウザテストされます：

```bash
# ローカルでPlaywrightテストを実行する場合
npm install -D @playwright/test
npx playwright install chromium
python -m http.server 8888 &
npx playwright test
```

**テスト内容：**
- ページのロード確認
- Pyodideの初期化（最大90秒）
- Noto Sans JPフォントのダウンロード確認
- フォーム要素の表示確認
- PoC版のロード確認

GitHub Actionsで自動実行されるため、通常はローカルで実行する必要はありません。

## コミットガイドライン

### コミットメッセージ
- 簡潔で明確な説明を書く
- 変更の理由と内容を含める
- 日本語でも英語でもOK（プロジェクトの言語に合わせる）

### プルリクエスト（PR）
- **PR説明文は日本語で記載すること**（このプロジェクトは日本語が主言語のため）
- `.github/PULL_REQUEST_TEMPLATE.md`のテンプレートに従って記載する
- 変更内容、理由、影響範囲を明確に記述する
- 関連するIssueがあれば必ずリンクする
- テストとリントチェックをパスしていることを確認する

### ブランチ戦略
- `main`: 安定版
- 機能追加やバグ修正は別ブランチで作業し、PRを作成

## デプロイメント方法

このプロジェクトは、用途に応じて3つのデプロイ方法をサポートしています：

### 1. ローカル開発・テスト

```bash
# CLI版で動作確認
uv run python -m letterpack.cli

# Webサーバー版で動作確認
uv run python -m letterpack.web
# ブラウザで http://localhost:5000 を開く
```

### 2. Docker環境（Webサーバー版）⭐ 本番推奨

Docker環境を使用することで、フォント環境が統一され、一貫したPDF出力が得られます。

```bash
# Docker Composeで起動
docker compose up -d

# 環境変数を設定
export SECRET_KEY=$(openssl rand -hex 32)
```

**メリット：**
- フォント環境の統一（Noto CJK）
- 依存関係の自動セットアップ
- 本番環境での安定動作
- ポータビリティ（Windows/Mac/Linux）

詳細は `DOCKER.md` を参照してください。

### 3. GitHub Pages（静的HTML版）⭐ 公開ツール推奨

静的HTML版は、サーバー不要で動作し、GitHub Pagesで簡単に公開できます。

**セットアップ手順：**
1. リポジトリのSettings → Pages を開く
2. Source を「GitHub Actions」に変更
3. mainブランチにpushすると自動デプロイ

**メリット：**
- サーバー不要、メンテナンスフリー
- GitHub Actionsで自動デプロイ
- 完全無料（GitHub Pagesの範囲内）
- オフライン対応（初回ロード後）
- Pyodide（WebAssembly）でブラウザ内でPython実行

詳細は `STATIC_VERSION.md` を参照してください。

## CI/CD

このプロジェクトには、5つのGitHub Actionsワークフローが設定されています：

### 1. `main.yml` - PDF生成テスト

- **トリガー**: mainブランチへのpush、PR作成・更新、手動実行
- **内容**:
  - Python 3.11をセットアップ
  - uvで依存関係をインストール
  - pytestを実行
  - テストPDFを生成（`generate_test_pdf.py`）
  - 生成されたPDFをArtifactとしてアップロード（1日保持）
- **目的**: Pythonコードの自動テストとPDF生成の検証

### 2. `test-static-webui.yml` - 静的WebUIテスト

- **トリガー**: `index_static.html`, `poc_pyodide.html`, `STATIC_VERSION.md` の変更
- **内容**:
  - Node.js 20をセットアップ
  - Playwrightをインストール
  - HTTPサーバーを起動（ポート8888）
  - Playwrightテストを実行
    - ページのロード確認
    - Pyodideの初期化（最大90秒）
    - Noto Sans JP Boldフォントのダウンロード確認
    - フォーム要素の表示確認
    - PoC版のロード確認
  - テスト結果をArtifactとしてアップロード（7日保持）
- **タイムアウト**: 10分（Pyodide初期化に時間がかかるため）
- **目的**: 静的HTML版の動作検証

### 3. `deploy-pages.yml` - GitHub Pagesデプロイ

- **トリガー**: mainブランチへのpush（`index_static.html`, `poc_pyodide.html`, `STATIC_VERSION.md`, `README.md` の変更時）
- **内容**:
  - 静的HTMLファイルをGitHub Pagesにデプロイ
  - `index_static.html` がルート（`/`）にデプロイ
- **公開URL**: `https://username.github.io/letter-pack-label-maker/`
- **目的**: 静的HTML版の自動公開

### 4. `claude.yml` - Claude統合

- Claude Codeとの統合ワークフロー
- Claude関連の自動化タスク

### 5. `claude-code-review.yml` - Claudeコードレビュー

- Claude Codeによる自動コードレビュー
- PRに対してレビューコメントを自動投稿

### CI/CDのベストプラクティス

- **PRを作成する前に**: ローカルでテストとリントを実行
- **静的HTML版を変更する場合**: ローカルでHTTPサーバーを起動して動作確認
- **GitHub Actionsのログ**: テスト失敗時はログを確認して原因を特定
- **Artifacts**: 生成されたPDFやテスト結果はArtifactsからダウンロード可能

## 注意事項

### 日本語対応
- このプロジェクトは日本のレターパック向けなので、日本語対応が重要
- コメントやドキュメントは日本語が望ましい
- コード内の変数名などは英語を使用

### PDF生成
- ReportLabを使用してPDF生成
- A4サイズ（210mm × 297mm）に対応
- フォントは日本語対応フォントを使用

### フォント環境
このプロジェクトは、環境によって異なるフォントを使用します：

- **静的HTML版（Pyodide）**: Noto Sans JP Bold（Google Fontsから自動ダウンロード）
- **Docker環境**: Noto Sans CJK JP、Noto Serif CJK JP（イメージに含まれる）
- **ローカル環境**: IPA/Heiseiフォント（フォールバック）

**推奨事項：**
- 本番環境ではDocker環境を使用（フォント統一）
- 公開ツールは静的HTML版を使用（高品質フォント）
- ローカル開発でもフォントの違いに注意

### 文字コーディング
- UTF-8を使用
- ソースコードファイルはすべてUTF-8で保存

## AIエージェント固有のガイドライン

### Claude Code
Claude Codeを使用する場合は、[CLAUDE.md](./CLAUDE.md)も参照してください。

### その他のAIエージェント
他のAIエージェントを使用する場合は、以下を確認してください：
- Python 3.8.1以上の互換性
- uvコマンドの利用可能性
- 日本語（UTF-8）の処理能力

## トラブルシューティング

### よくある問題

#### uvが見つからない
```bash
# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 依存関係のエラー
```bash
# ロックファイルを更新
uv lock --upgrade

# クリーンインストール
rm -rf .venv
uv sync --all-extras
```

#### テストの失敗
- テストを実行する前に依存関係がインストールされていることを確認
- `uv sync --all-extras`で開発用依存関係をインストール

## リソース

### 公式ドキュメント
- [ReportLab ドキュメント](https://www.reportlab.com/docs/) - PDF生成ライブラリ
- [Flask ドキュメント](https://flask.palletsprojects.com/) - Webフレームワーク
- [Pyodide ドキュメント](https://pyodide.org/en/stable/) - PythonをWebAssemblyで実行
- [Docker ドキュメント](https://docs.docker.com/) - コンテナ化
- [GitHub Actions ドキュメント](https://docs.github.com/en/actions) - CI/CD
- [GitHub Pages ドキュメント](https://docs.github.com/en/pages) - 静的サイトホスティング
- [uv ドキュメント](https://github.com/astral-sh/uv) - Pythonパッケージマネージャー
- [Ruff ドキュメント](https://docs.astral.sh/ruff/) - Pythonリンター/フォーマッター
- [Playwright ドキュメント](https://playwright.dev/) - ブラウザ自動テスト

### プロジェクト内ドキュメント
- `README.md` - プロジェクト概要と基本的な使い方
- `DOCKER.md` - Docker環境での実行方法
- `STATIC_VERSION.md` - 静的HTML版の技術詳細
- `CLAUDE.md` - Claude Code固有のガイド
- `ISSUE_CONFIGURABLE_LAYOUT.md` - 設定可能なレイアウトの課題
