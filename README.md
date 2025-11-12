# Letter Pack Label Maker

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://ebal5.github.io/letter-pack-label-maker/)
![Deploy Pages](https://github.com/ebal5/letter-pack-label-maker/actions/workflows/deploy-pages.yml/badge.svg)

レターパック用のラベルPDFを簡単に作成するツール

## 概要

🚀 **[オンラインで試す](https://ebal5.github.io/letter-pack-label-maker/)** (サーバー不要・インストール不要)



テキスト、CSV、またはWebフォーム入力から、レターパック用のラベルPDF（A4サイズ）を生成します。
生成されるラベルは汎用的なTo/Fromフォーマットで、実際のレターパックの印刷範囲内に収まるように設計されています。

## 機能

- ✅ コマンドラインからPDF生成
- ✅ Webブラウザからの入力・生成
- ✅ CSVファイルからの一括生成（4upレイアウト、複数ページ対応）
- ✅ 静的HTMLページ（サーバー不要、Pyodide使用）
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

# CSVファイルから一括生成（4upレイアウト、複数ページ）
uv run python -m letterpack.cli --csv addresses.csv --output labels.pdf
```

#### CSVファイル形式

```csv
to_postal,to_address,to_name,to_phone,to_honorific,from_postal,from_address,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,田中花子,06-9876-5432,
456-7890,神奈川県横浜市ZZZ 7-8-9,佐藤次郎,045-1234-5678,殿,987-6543,大阪府大阪市YYY 4-5-6,田中花子,06-9876-5432,
```

- ヘッダー行必須
- 4件ごとに1ページとして生成（5件なら2ページ）
- `to_honorific`省略時は「様」、`from_honorific`省略時は敬称なし
- UTF-8またはShift_JISエンコーディング対応

### Web インターフェース

```bash
# Webサーバーを起動
uv run python -m letterpack.web

# ブラウザで http://localhost:5000 を開く
```

Webインターフェースでは以下の機能が利用できます：
- 単一ラベルの生成（フォーム入力）
- CSVファイルからの一括生成（ファイルアップロード）

#### 環境変数の設定

本番環境でWebインターフェースを使用する場合は、セキュリティのために `SECRET_KEY` 環境変数を設定してください：

```bash
# シークレットキーを生成（例）
export SECRET_KEY=$(openssl rand -hex 32)

# または .env ファイルを作成
cp .env.example .env
# .env ファイルを編集して SECRET_KEY を設定

# Webサーバーを起動
uv run python -m letterpack.web
```

開発環境では環境変数が未設定でも動作しますが、警告が表示されます。

### 静的HTMLページ（サーバー不要版）⭐ 推奨

**Pyodide**を使用した完全にフロントエンドだけで動作するバージョンです。サーバーのインストールや起動が不要で、HTMLファイルをブラウザで開くだけで使えます。

#### 使い方

```bash
# 方法1: ローカルHTTPサーバーで開く（推奨）
python -m http.server 8000
# ブラウザで http://localhost:8000/index_static.html を開く

# 方法2: 直接ファイルを開く
# index_static.html をブラウザにドラッグ&ドロップ
```

#### 特徴

- ✅ **サーバー不要**: HTMLファイルをブラウザで開くだけ
- ✅ **完全オフライン対応**: 初回ロード後はオフラインでも動作（Pyodideのキャッシュ）
- ✅ **GitHub Pagesで公開可能**: 静的ホスティングサービスで簡単に公開できる
- ✅ **Noto Sans JP使用**: Google Fontsから高品質な日本語フォントを自動ダウンロード
- ⚠️ **初回ロードが遅い**: Pyodide + フォントのダウンロード（約12MB）に時間がかかる

#### GitHub Pagesで公開する（自動デプロイ）⭐ 推奨

このリポジトリには **GitHub Actions による自動デプロイ**が設定されています。

##### 初回セットアップ

1. リポジトリのSettings → Pages を開く
2. **Source** を「**GitHub Actions**」に変更
3. mainブランチにpushすると自動的にデプロイされます

##### 自動デプロイの仕組み

- mainブランチへのpush時に自動実行（`.github/workflows/deploy-pages.yml`）
- `index_static.html` が公開URLのルート (`/`) にデプロイされます
- 変更対象: `index_static.html`, `poc_pyodide.html`, `STATIC_VERSION.md`, `README.md`

##### 公開URL

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://ebal5.github.io/letter-pack-label-maker/)

```
https://ebal5.github.io/letter-pack-label-maker/
```

**アクセス可能なページ:**
- `/` - メインのラベル作成UI（`index_static.html`）
- `/poc_pyodide.html` - PyodideのPoC版
- `/STATIC_VERSION.md` - 静的版のドキュメント
- `/README.md` - プロジェクトREADME

##### 手動デプロイ

GitHub Actionsページから手動でワークフローを実行することも可能です。

### Docker環境での実行

フォント環境を統一し、どの環境でも一貫したPDF出力を得るために、Docker環境の使用を推奨します。

```bash
# Docker Composeで起動
docker compose up

# バックグラウンドで起動
docker compose up -d

# ブラウザで http://localhost:5000 を開く
```

詳細は [DOCKER.md](DOCKER.md) を参照してください。

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

## 開発

```bash
# 開発用依存関係を含めてインストール
uv sync --all-extras

# テストの実行
uv run pytest

# コードフォーマットとリント（Ruff使用）
uv run ruff format src tests
uv run ruff check --fix src tests
```

### 静的WebUIのテスト

静的HTML版（Pyodide）は、GitHub Actionsで自動的にテストされます：

```yaml
# .github/workflows/test-static-webui.yml
# index_static.html, poc_pyodide.html, STATIC_VERSION.md の変更時に自動実行
```

**テスト内容**:
- ✅ ページが正常にロード
- ✅ Pyodideが正常に初期化（最大90秒）
- ✅ Noto Sans JPフォントのダウンロード確認
- ✅ フォーム要素の表示確認
- ✅ PoC版のロード確認

詳細なガイドラインは [AGENTS.md](AGENTS.md) および [CLAUDE.md](CLAUDE.md) を参照してください。

## 注意事項

- 生成されるPDFはA4サイズです
- ラベル自体はA5相当のサイズで中央に配置されます
- 実際のレターパックに印刷する場合は、プリンターの設定を確認してください
