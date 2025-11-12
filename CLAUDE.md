# Claude Code Guide

このドキュメントは、Claude Codeでこのプロジェクトを扱う際の専用ガイドです。

共通のAIエージェント向けガイドラインは [AGENTS.md](./AGENTS.md) を参照してください。

## プロジェクトの構成

このプロジェクトは、3つのインターフェースを提供しています：

### 1. CLI版（コマンドライン）
- ターミナルから直接ラベル生成
- 対話形式または引数指定で実行
- CSV一括生成にも対応（4upレイアウト、複数ページ）
- 用途：ローカル開発、バッチ処理

### 2. Webサーバー版（Flask）
- ブラウザからフォーム入力でラベル生成
- サーバー起動が必要（Flask）
- Docker環境での実行を推奨（フォント統一）
- 用途：内部ツール、サーバー環境での利用

### 3. 静的HTML版（Pyodide）⭐ 推奨
- サーバー不要、HTMLファイルをブラウザで開くだけ
- Pyodide（WebAssembly）でPythonをブラウザ実行
- GitHub Pagesで公開可能
- 完全オフライン対応（初回ロード後）
- 用途：公開ツール、サーバーレス環境

詳細は各ドキュメントを参照：
- `README.md` - 全体概要と使い方
- `DOCKER.md` - Docker環境でのWebサーバー版
- `STATIC_VERSION.md` - 静的HTML版の技術詳細

## Claude Code固有の設定

### プロジェクトのセットアップ

Claude Codeでこのプロジェクトに初めて取り組む際は、以下の手順を実行してください：

```bash
# 依存関係のインストール（開発用含む）
uv sync --all-extras

# 動作確認
uv run pytest
```

### 推奨ワークフロー

1. **変更前の確認**
   - 関連するファイルを読んで現在の実装を理解
   - 既存のテストを確認

2. **実装**
   - コードの変更を行う
   - 必要に応じてテストを追加・更新

3. **検証**
   - Ruffでコードチェック: `uv run ruff check --fix src tests`
   - フォーマット: `uv run ruff format src tests`
   - テスト実行: `uv run pytest`

4. **コミット**
   - 明確なコミットメッセージで変更をコミット
   - 複数の関連する変更は1つのコミットにまとめる

5. **GitHub Actionsとの統合**
   - PRを作成すると自動的にテストが実行される（`.github/workflows/main.yml`）
   - 静的HTML版を変更すると自動的にPlaywrightテストが実行される（`.github/workflows/test-static-webui.yml`）
   - mainブランチにマージすると自動的にGitHub Pagesにデプロイされる（`.github/workflows/deploy-pages.yml`）

## Claude Codeの得意な作業

### 推奨タスク
- ✅ バグ修正
- ✅ 新機能の実装
- ✅ テストの追加
- ✅ ドキュメントの更新
- ✅ リファクタリング
- ✅ コードレビュー

### 注意が必要なタスク
- ⚠️ PDF生成ロジックの大幅な変更（実際のレターパックのフォーマットとの整合性確認が必要）
- ⚠️ 依存関係の大規模なアップグレード（動作確認が重要）

## コンテキスト管理のヒント

### 重要なファイル
プロジェクトを理解するために、まず以下のファイルを確認してください：

- `README.md` - プロジェクト概要と使い方
- `pyproject.toml` - プロジェクト設定と依存関係
- `src/letterpack/` - メインのコードベース
- `tests/` - テストコード

### 日本語の扱い
- このプロジェクトは日本語のドキュメントとコメントを使用
- Claude Codeは日本語を理解できるので、自然に日本語でコミュニケーション可能
- ユーザーとのやりとりは日本語でも英語でもOK（ユーザーの言語に合わせる）

## 具体的な作業例

### 新機能の追加

**例: 予定機能の実装（品名フィールドなど）**

品名フィールドは `ISSUE_CONFIGURABLE_LAYOUT.md` に記載されている予定機能です。実装する場合：

1. 仕様を確認・質問
   - レターパックのどこに表示するか？
   - 入力形式は？（自由記述？選択式？）
   - 3つのインターフェース（CLI、Webサーバー、静的HTML）すべてに実装するか？

2. 実装計画
   - データモデルの変更が必要か確認（`src/letterpack/label.py`）
   - CLI、Webサーバー、静的HTML版すべてに影響があるか確認
   - テストケースの追加が必要か確認

3. 実装
   ```bash
   # 関連ファイルの確認
   ls src/letterpack/

   # テストの確認
   ls tests/

   # 実装後の検証
   uv run ruff check --fix src tests
   uv run ruff format src tests
   uv run pytest
   ```

### バグ修正

1. 問題の再現
   - 可能であればテストケースを作成

2. 原因の特定
   - 関連コードを読む
   - デバッグ情報を確認

3. 修正と検証
   - 修正を実装
   - テストで確認
   - リグレッションがないか確認

## ツールとコマンド

### 頻繁に使用するコマンド

```bash
# プロジェクトのルートで実行

# テスト実行
uv run pytest

# 特定のテストのみ実行
uv run pytest tests/test_specific.py

# リントチェック
uv run ruff check src tests

# 自動修正
uv run ruff check --fix src tests

# フォーマット
uv run ruff format src tests

# CLIの実行
uv run python -m letterpack.cli

# Webサーバーの起動
uv run python -m letterpack.web
```

### デバッグのヒント

- エラーメッセージを確認し、スタックトレースを追う
- 必要に応じて`print()`やロギングを使用
- テストを書いて問題を再現
- ReportLabのドキュメントを参照（PDF生成関連の問題の場合）

## テストとCI/CD

### テストフレームワーク

このプロジェクトは、2種類のテストを実施しています：

#### 1. pytest（Pythonコード）
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

#### 2. Playwright（静的HTML版）
静的HTML版（Pyodide）は、Playwrightで自動テストされます：

```bash
# ローカルでPlaywrightテストを実行する場合
npm install -D @playwright/test
npx playwright install chromium
python -m http.server 8888 &
npx playwright test
```

**テスト内容：**
- Pyodideの初期化（最大90秒）
- Noto Sans JPフォントのダウンロード確認
- フォーム要素の表示確認
- PoC版のロード確認

### GitHub Actionsワークフロー

プロジェクトには5つのワークフローが設定されています：

#### 1. `main.yml` - PDF生成テスト
- **トリガー**: mainブランチへのpush、PR作成・更新
- **内容**: pytestを実行し、テストPDFを生成
- **成果物**: 生成されたPDFをArtifactとしてダウンロード可能（1日保持）

#### 2. `test-static-webui.yml` - 静的WebUIテスト
- **トリガー**: `index_static.html`, `poc_pyodide.html`, `STATIC_VERSION.md` の変更
- **内容**: Playwrightでブラウザテスト実行
- **タイムアウト**: 10分（Pyodide初期化に時間がかかるため）

#### 3. `deploy-pages.yml` - GitHub Pagesデプロイ
- **トリガー**: mainブランチへのpush
- **内容**: 静的HTML版をGitHub Pagesに自動デプロイ
- **公開URL**: `https://username.github.io/letter-pack-label-maker/`

#### 4. `claude.yml` - Claude統合
- Claude Codeとの統合ワークフロー

#### 5. `claude-code-review.yml` - Claudeコードレビュー
- Claude Codeによる自動コードレビュー

### CI/CDベストプラクティス

- PRを作成する前に、ローカルでテストとリントを実行
- 静的HTML版を変更する場合は、ローカルでHTTPサーバーを起動して動作確認
- GitHub Actionsのログを確認して、テスト失敗の原因を特定

## フォント戦略

このプロジェクトは、環境によって異なるフォントを使用します：

### 1. 静的HTML版（Pyodide）
- **Noto Sans JP Bold** - Google Fontsから自動ダウンロード（約2MB）
- JavaScriptでフォントをダウンロードし、Pyodideの仮想ファイルシステムに保存
- 高品質な日本語フォント、商用利用可能

### 2. Docker環境（Webサーバー版）
- **Noto Sans CJK JP** - ゴシック体（Dockerイメージに含まれる）
- **Noto Serif CJK JP** - 明朝体（Dockerイメージに含まれる）
- フォント環境が統一され、どの環境でも一貫したPDF出力

### 3. ローカル環境（CLI、Webサーバー版）
- **IPA/Heiseiフォント** - ReportLabのCJKフォント（フォールバック）
- **Helvetica** - 最終フォールバック（日本語非対応）
- 環境に依存するため、Dockerの使用を推奨

### フォント選択のポイント
- **本番環境**: Docker環境を使用（Noto CJK）
- **公開ツール**: 静的HTML版を使用（Noto Sans JP）
- **開発環境**: ローカル環境でも動作するが、フォントが異なる可能性あり

## デプロイメント戦略

### 使い分けガイド

#### 1. ローカル開発・テスト
```bash
# CLI版で動作確認
uv run python -m letterpack.cli

# Webサーバー版で動作確認
uv run python -m letterpack.web
```

#### 2. 本番環境（Webサーバー版）
Docker環境の使用を推奨（`DOCKER.md` 参照）：
```bash
# Docker Composeで起動
docker compose up -d

# 環境変数を設定
export SECRET_KEY=$(openssl rand -hex 32)
```

**推奨理由：**
- フォント環境の統一
- 依存関係の自動セットアップ
- 本番環境での安定動作

#### 3. 公開ツール（静的HTML版）⭐ 推奨
GitHub Pagesでの公開が最も簡単（`STATIC_VERSION.md` 参照）：

1. リポジトリのSettings → Pages を開く
2. Source を「GitHub Actions」に変更
3. mainブランチにpushすると自動デプロイ

**推奨理由：**
- サーバー不要、メンテナンスフリー
- GitHub Actionsで自動デプロイ
- 完全無料（GitHub Pagesの範囲内）
- オフライン対応（初回ロード後）

## Claude Codeの制限事項

### できないこと
- 実際にブラウザでWebインターフェースを開いて動作確認
- 生成されたPDFを視覚的に確認（ファイルの生成は可能）
- 実際のレターパックとのサイズ比較

### 対処方法
- PDFの検証はユーザーに依頼
- テストで基本的な動作を確認
- 不明点はユーザーに質問

## コミュニケーション

### ユーザーとのやりとり
- 不明点は積極的に質問
- 実装前に確認が必要な場合は提案を示す
- 完了後は変更内容を簡潔に説明

### コードレビュー時
- 改善の余地がある箇所を指摘
- 代替案があれば提案
- ベストプラクティスを共有

## まとめ

Claude Codeでこのプロジェクトに取り組む際は：

1. **AGENTS.md**で共通のガイドラインを確認
2. **このファイル**でClaude Code固有の設定を確認
3. **プロジェクトの構成**を理解（CLI/Webサーバー/静的HTML版）
4. **README.md**でプロジェクトの使い方を理解
5. **pyproject.toml**で依存関係と設定を確認
6. 実装前に必要なファイルを読む
7. 変更後は必ずテストとリントを実行
8. **GitHub Actionsで自動テスト**が実行されることを確認
9. **デプロイメント戦略**を理解（Docker/GitHub Pages）
10. 不明点はユーザーに質問

### クイックリファレンス

- **ローカル開発**: `uv run pytest` → `uv run ruff check --fix src tests`
- **Docker環境**: `docker compose up -d`
- **静的HTML版**: GitHub Pagesで自動デプロイ
- **フォント**: 静的HTML版（Noto Sans JP）、Docker（Noto CJK）、ローカル（IPA/Heiseiフォント）
- **CI/CD**: 5つのGitHub Actionsワークフロー（pytest、Playwright、デプロイ、Claude統合）

Happy coding!
