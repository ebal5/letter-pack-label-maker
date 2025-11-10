# AI Agents Guide

このドキュメントは、AIエージェントがこのプロジェクトで作業する際のガイドラインです。

## プロジェクト概要

**Letter Pack Label Maker** は、日本郵便のレターパック用ラベルPDFを生成するPythonツールです。

### 主な機能
- コマンドライン（CLI）からのラベル生成
- Webインターフェース（Flask）からのラベル生成
- A4サイズPDFに汎用的なTo/Fromフォーマットのラベルを出力

### 技術スタック
- **言語**: Python 3.8.1+
- **PDF生成**: ReportLab
- **Webフレームワーク**: Flask
- **パッケージ管理**: uv
- **ビルドシステム**: Hatchling
- **リンター/フォーマッター**: Ruff
- **テストフレームワーク**: pytest

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
├── src/letterpack/     # メインパッケージ
├── tests/              # テストコード
├── examples/           # サンプル
├── pyproject.toml      # プロジェクト設定
└── README.md           # プロジェクト説明
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
```bash
# すべてのテストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=letterpack --cov-report=html
```

## コミットガイドライン

### コミットメッセージ
- 簡潔で明確な説明を書く
- 変更の理由と内容を含める
- 日本語でも英語でもOK（プロジェクトの言語に合わせる）

### ブランチ戦略
- `main`: 安定版
- 機能追加やバグ修正は別ブランチで作業し、PRを作成

## 注意事項

### 日本語対応
- このプロジェクトは日本のレターパック向けなので、日本語対応が重要
- コメントやドキュメントは日本語が望ましい
- コード内の変数名などは英語を使用

### PDF生成
- ReportLabを使用してPDF生成
- A4サイズ（210mm × 297mm）に対応
- フォントは日本語対応フォントを使用

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

- [ReportLab ドキュメント](https://www.reportlab.com/docs/)
- [Flask ドキュメント](https://flask.palletsprojects.com/)
- [uv ドキュメント](https://github.com/astral-sh/uv)
- [Ruff ドキュメント](https://docs.astral.sh/ruff/)
