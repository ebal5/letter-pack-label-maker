# Letter Pack Label Maker

レターパック用のラベルPDFを簡単に作成するツール

## 概要

テキスト、CSV、またはWebフォーム入力から、レターパック用のラベルPDF（A4サイズ）を生成します。
生成されるラベルは汎用的なTo/Fromフォーマットで、実際のレターパックの印刷範囲内に収まるように設計されています。

## 機能

- ✅ コマンドラインからPDF生成
- ✅ Webブラウザからの入力・生成
- 🔜 CSVファイルからの一括生成（予定）
- 🔜 品名フィールドの追加（予定）

## インストール

このプロジェクトは [uv](https://github.com/astral-sh/uv) を使用して依存関係を管理しています。

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/letter-pack-label-maker.git
cd letter-pack-label-maker

# uvで依存関係をインストール
uv sync

# または開発用依存関係も含めてインストール
uv sync --all-extras
```

## 使い方

### CLI（コマンドライン）

```bash
# 対話形式で入力
uv run python -m letterpack.cli

# 引数で指定
uv run python -m letterpack.cli --output label.pdf \
  --to-name "山田太郎" \
  --to-postal "123-4567" \
  --to-address "東京都渋谷区XXX 1-2-3" \
  --to-phone "03-1234-5678" \
  --from-name "田中花子" \
  --from-postal "987-6543" \
  --from-address "大阪府大阪市YYY 4-5-6" \
  --from-phone "06-9876-5432"
```

### Web インターフェース

```bash
# Webサーバーを起動
uv run python -m letterpack.web

# ブラウザで http://localhost:5000 を開く
```

## 必要な情報

- **お届け先**
  - 郵便番号
  - 住所
  - 氏名
  - 電話番号

- **ご依頼主**
  - 郵便番号
  - 住所
  - 氏名
  - 電話番号

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## 使用ライブラリ

- [ReportLab](https://www.reportlab.com/) (BSD License) - PDF生成
- [Flask](https://flask.palletsprojects.com/) (BSD License) - Webインターフェース

## ラベル配置調整ツール

レターパックラベルのレイアウト（マージン、フォントサイズ、要素間隔など）を視覚的に調整できるツールが用意されています。

### 使い方

```bash
# 調整ツールを起動
uv run python tools/label_adjuster.py

# ブラウザで http://localhost:8080 を開く
```

### 機能

- **リアルタイムプレビュー**: レイアウトパラメータを変更すると、即座にPDFプレビューが更新されます
- **設定の保存**: 調整した設定を `config/label_layout.yaml` に保存できます
- **テストデータ**: あらかじめ用意されたテストデータで動作確認できます

### オプション

```bash
# ポート番号を指定
uv run python tools/label_adjuster.py --port 8000

# ホストを指定
uv run python tools/label_adjuster.py --host 0.0.0.0 --port 8080
```

**注意**: このツールはローカル開発環境での使用を想定しています。外部ネットワークに公開しないでください。

## 開発

```bash
# 開発用依存関係を含めてインストール
uv sync --all-extras

# テストの実行
uv run pytest

# コードチェックと自動修正
uv run ruff check --fix src tests

# コードフォーマット
uv run ruff format src tests
```

## 注意事項

- 生成されるPDFはA4サイズです
- ラベル自体はA5相当のサイズで中央に配置されます
- 実際のレターパックに印刷する場合は、プリンターの設定を確認してください
