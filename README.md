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
to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,XXXビル4F,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
456-7890,神奈川県横浜市ZZZ 7-8-9,,,佐藤次郎,045-1234-5678,殿,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
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

## 設定ファイル（Configuration Files）

レターパックラベルのレイアウトは、YAML設定ファイルでカスタマイズできます。

### デフォルト設定

`config/label_layout.yaml`にデフォルト設定が含まれています。このファイルを編集するか、カスタム設定ファイルを作成してください。

### 設定ファイルの使い方

#### CLI版
```bash
uv run python -m letterpack.cli --config custom_config.yaml
```

#### Pythonコードから
```python
from letterpack.label import create_label, AddressInfo

to_address = AddressInfo(...)
from_address = AddressInfo(...)

# カスタム設定を使用
create_label(
    to_address,
    from_address,
    "output.pdf",
    config_path="custom_config.yaml"
)

# または、辞書で設定を渡す
config_dict = {
    "fonts": {"name": 16, "address": 13},
    "layout": {"draw_border": True}
}
create_label(
    to_address,
    from_address,
    "output.pdf",
    config_dict=config_dict
)
```

### プレビューツール

レイアウトパラメータをリアルタイムで調整できるWebツールが利用可能です：

```bash
python tools/label_adjuster.py
# http://localhost:5001 をブラウザで開く
```

詳細は [tools/README.md](tools/README.md) を参照してください。

## 設定リファレンス（Configuration Reference）

### Layout Settings（レイアウト設定）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `label_width` | 105 | mm | ラベルの幅 |
| `label_height` | 122 | mm | ラベルの高さ（実測値ベース） |
| `margin_top` | 7 | mm | セクション上部マージン |
| `margin_left` | 5 | mm | セクション左右マージン |
| `draw_border` | true | - | デバッグ用枠線を表示 |
| `layout_mode` | center | - | 配置モード（`center` または `grid_4up`） |

### Font Sizes（フォントサイズ）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `label` | 9 | pt | フィールドラベル |
| `postal_code` | 13 | pt | 郵便番号 |
| `address` | 11 | pt | 住所 |
| `name` | 14 | pt | 氏名 |
| `honorific` | null | pt | 敬称（nullの場合は名前-2pt） |
| `phone` | 13 | pt | 電話番号 |

### Spacing（スペーシング）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `section_spacing` | 15 | px | セクション内の基本スペーシング |
| `address_line_height` | 18 | px | 住所の行間 |
| `address_name_gap` | 27 | px | 住所と名前の間隔 |
| `name_phone_gap` | 36 | px | 名前と電話番号の間隔 |
| `postal_box_offset_x` | 15 | px | 郵便番号ボックスの水平オフセット |
| `postal_box_offset_y` | -2 | px | 郵便番号ボックスの垂直オフセット |
| `dotted_line_text_offset` | 4 | px | 点線からテキストまでのオフセット |

### Postal Box（郵便番号ボックス）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `box_size` | 5 | mm | ボックスのサイズ |
| `box_spacing` | 1 | mm | ボックス間の間隔 |
| `line_width` | 0.5 | pt | 枠線の太さ |
| `text_vertical_offset` | 2 | pt | 数字の垂直オフセット |

### Address Layout（住所レイアウト）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `max_length` | 35 | 文字 | 1行の最大文字数 |
| `max_lines` | 3 | 行 | 最大行数 |

### Dotted Line（点線）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `dash_length` | 2 | mm | ダッシュの長さ |
| `dash_spacing` | 2 | mm | ダッシュ間の間隔 |
| `color_r` | 0.5 | 0-1 | 赤成分 |
| `color_g` | 0.5 | 0-1 | 緑成分 |
| `color_b` | 0.5 | 0-1 | 青成分 |

### Sama（「様」設定）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `width` | 8 | mm | 「様」用スペース |
| `offset` | 2 | mm | 点線からのオフセット |

### Border（枠線）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `color_r` | 0.8 | 0-1 | 赤成分 |
| `color_g` | 0.8 | 0-1 | 緑成分 |
| `color_b` | 0.8 | 0-1 | 青成分 |
| `line_width` | 0.5 | pt | 枠線の太さ |

### Phone（電話番号）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `offset_x` | 30 | px | 水平オフセット |

### Section Heights（セクション高さ）

| パラメータ | デフォルト値 | 単位 | 説明 |
|----------|------------|-----|-----|
| `to_section_height` | 69 | mm | お届け先セクションの高さ（実測値68mm） |
| `from_section_height` | 53 | mm | ご依頼主セクションの高さ（実測値52mm） |
| `divider_line_width` | 1 | mm | 区切り線の太さ |
| `from_section_font_scale` | 0.7 | - | ご依頼主セクションのフォントスケール |
| `from_address_max_lines` | 2 | 行 | ご依頼主の住所最大行数 |
| `from_address_name_gap` | 9 | px | ご依頼主の住所と名前の間隔 |
| `from_name_phone_gap` | 12 | px | ご依頼主の名前と電話番号の間隔 |
| `from_address_font_size_adjust` | 2 | pt | ご依頼主の住所フォントサイズ調整 |

## カスタマイズ例（Customization Examples）

### 例1: フォントサイズを大きくする

```yaml
fonts:
  name: 16  # デフォルト: 14pt
  address: 13  # デフォルト: 11pt
  phone: 15  # デフォルト: 13pt
```

### 例2: デバッグ用枠線を非表示にする

```yaml
layout:
  draw_border: false
```

### 例3: 4upレイアウトで印刷

```yaml
layout:
  layout_mode: grid_4up  # デフォルト: center
```

### 例4: 郵便番号ボックスのサイズを調整

```yaml
postal_box:
  box_size: 6  # デフォルト: 5mm
  box_spacing: 1.5  # デフォルト: 1mm
```

### 例5: カスタムカラースキーム

```yaml
dotted_line:
  color_r: 0.3  # デフォルト: 0.5 (グレー)
  color_g: 0.3
  color_b: 0.8  # 青っぽい点線

border:
  color_r: 0.9  # デフォルト: 0.8 (薄いグレー)
  color_g: 0.9
  color_b: 0.9  # より薄い枠線
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
