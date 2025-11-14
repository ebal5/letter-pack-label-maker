# Font Diagnostic Skill - 使用方法

## 概要

このSkillは、フォント関連の問題を診断し、解決策を提案するClaude Code Skillです。
このプロジェクトは環境によって異なるフォント（Noto CJK、IPA、Heiseiフォント）を使用するため、フォント問題の診断を自動化します。

## Skillの起動方法

Claude Codeに以下のような指示をすると自動的にこのSkillが起動します：

- 「フォントが見つからない」
- 「フォント診断をして」
- 「日本語が表示されない」
- 「PDFにフォントが埋め込まれていない」
- 「どのフォントが使えるか確認したい」
- 「フォント環境を確認してください」

## 診断される項目

### 実行環境
- ✅ プラットフォーム（Windows、macOS、Linux）
- ✅ Docker環境かどうか
- ✅ Pyodide環境かどうか
- ✅ Pythonバージョン

### フォント情報
- ✅ ReportLabに登録されているフォント
- ✅ システムにインストールされているフォント
  - Noto CJKフォント（Docker環境推奨）
  - Noto Sansフォント（Pyodide環境推奨）
  - IPAフォント（ローカル環境推奨）
  - Heiseiフォント（フォールバック）
- ✅ フォントフォールバックの優先順序
- ✅ PDF内に埋め込まれているフォント（PDFがある場合）

## 診断結果の見方

診断完了後、以下のようなレポートが出力されます：

### 正常な場合（Docker環境）

```
==================================================
🔍 フォント診断レポート
==================================================

【実行環境】
- プラットフォーム: Linux
- Docker環境: はい ✅
- Pyodide環境: いいえ
- Python: 3.12.0

【ReportLab登録フォント】
✅ Helvetica (標準フォント)
✅ Times-Roman (標準フォント)
✅ Courier (標準フォント)
✅ IPAGothic (登録済み)

【システムフォント】
✅ Noto CJK: NotoSansCJK-Regular.ttc
   ... 他 3 個

【フォントフォールバック設定】
label.py内での優先順序:
1. Noto Sans CJK JP (ゴシック体) ✅
2. IPA Gothic (フォールバック) ✅
3. Heisei フォント ✅
4. Helvetica (最終フォールバック) ✅

【診断結果】
✅ Docker環境でNoto CJKフォントが利用可能
✅ 日本語PDFの生成に問題ありません

【推奨事項】
✅ Docker環境での実行を継続してください

==================================================
```

### 問題がある場合（ローカル環境、フォント未インストール）

```
==================================================
🔍 フォント診断レポート
==================================================

【実行環境】
- プラットフォーム: Linux
- Docker環境: いいえ
- Pyodide環境: いいえ
- Python: 3.11.0

【ReportLab登録フォント】
✅ Helvetica (標準フォント)
✅ Times-Roman (標準フォント)
✅ Courier (標準フォント)
❌ IPAGothic (未登録)

【システムフォント】
❌ 日本語フォントが見つかりません

【フォントフォールバック設定】
label.py内での優先順序:
1. Noto Sans CJK JP (ゴシック体) ❌
2. IPA Gothic (フォールバック) ❌
3. Heisei フォント ❌
4. Helvetica (最終フォールバック) ✅

【診断結果】
❌ 日本語フォント（Noto/IPA/Heisei）が利用できません
❌ PDF生成時にフォント警告が表示されます

【推奨事項】
緊急: フォント環境がセットアップされていません

以下のいずれかの方法で解決してください:

1. **Docker環境の使用（推奨）**
   docker compose up -d

2. **IPAフォントのインストール**

   Linux:
   Ubuntu/Debian: sudo apt-get install fonts-ipafont
   Fedora/RHEL: sudo dnf install ipa-gothic-fonts

   macOS:
   brew install --cask font-ipa

   Windows:
   - https://moji.or.jp/ipafont/ からダウンロード
   - Fontsフォルダに配置

3. **フォントパスを手動指定**
   create_label(..., font_path='/path/to/font.ttf')

==================================================
```

## 実装の詳細

このSkillは2つのファイルで構成されています：

### 1. skill.md
- Skillの定義ファイル
- Claude Codeでこのスキルを起動する際の指示を含む
- 診断項目の説明と出力例

### 2. tools/font_diagnostic.py
- 実際の診断処理を実装したPythonスクリプト
- 以下の関数で構成：
  - `detect_environment()`: 実行環境を特定
  - `get_platform_font_dirs()`: プラットフォームに応じたフォントディレクトリを取得
  - `find_system_fonts()`: システムフォントを検索
  - `check_reportlab_fonts()`: ReportLabのフォント設定を確認
  - `read_label_py_font_config()`: label.pyのフォント設定を読み取る
  - `analyze_pdf_fonts()`: PDF内のフォント情報を分析
  - `print_diagnostic_report()`: 診断レポートを出力
  - `diagnose_fonts()`: メイン関数

## 使用例

### 例1: 基本的な診断

```bash
# ローカルで診断を実行
python tools/font_diagnostic.py

# Docker環境で診断を実行
docker compose exec app python tools/font_diagnostic.py
```

### 例2: PDFを分析して診断

```bash
# 生成されたPDFのフォント情報を確認
python tools/font_diagnostic.py --pdf output/label.pdf
```

### 例3: Claude Codeで診断

```
ユーザー: 「フォント診断をしてください」

Claude: (スクリプトを実行)
🔍 フォント診断レポート
...診断結果...
```

## 問題が見つかった場合の対処

診断結果に問題が見つかった場合、以下の情報が提供されます：

- **問題の内容**: 何が問題なのか
- **原因**: なぜそれが問題なのか
- **修正案**: どう修正すればよいか

### よくある問題と解決策

#### 問題1: IPAフォントが見つからない（ローカル環境）

**解決策:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install fonts-ipafont

# Fedora/RHEL
sudo dnf install ipa-gothic-fonts

# macOS
brew install --cask font-ipa
```

#### 問題2: Docker環境で使用したい

**解決策:**

```bash
# Docker Composeで起動
docker compose up -d

# Docker内で診断
docker compose exec app python tools/font_diagnostic.py
```

#### 問題3: フォントパスを指定したい

**解決策:**

```python
from letterpack.label import create_label, AddressInfo

to_addr = AddressInfo(
    postal_code="100-0001",
    address="東京都千代田区千代田1-1",
    name="山田太郎"
)

from_addr = AddressInfo(
    postal_code="999-9999",
    address="その他の住所",
    name="その他の名前"
)

# フォントパスを指定
create_label(
    to_address=to_addr,
    from_address=from_addr,
    output_path="output.pdf",
    font_path="/path/to/your/font.ttf"  # フォントパス指定
)
```

## 環境別の推奨フォント

### Docker環境（推奨）
- **Noto Sans CJK JP**: ゴシック体
- **Noto Serif CJK JP**: 明朝体
- **特徴**: 高品質、商用利用可能、プリインストール済み

### Pyodide環境（ブラウザ）
- **Noto Sans JP Bold**: Google Fontsから自動ダウンロード（約2MB）
- **特徴**: サーバー不要、オフライン対応、自動ダウンロード

### ローカル環境
- **IPA Gothic**: 推奨フォント
- **Heisei フォント**: フォールバック（環境依存）
- **特徴**: 標準的だが、フォント管理が必要

## 関連ドキュメント

- `CLAUDE.md` - プロジェクト全体の設定ガイド
- `DOCKER.md` - Docker環境でのセットアップ
- `STATIC_VERSION.md` - Pyodide環境の技術詳細
- `src/letterpack/label.py` - フォント実装（208-284行目）

## トラブルシューティング

### 診断スクリプトが見つからない

```bash
# ファイルが存在することを確認
ls -la tools/font_diagnostic.py

# スクリプトに実行権限を付与
chmod +x tools/font_diagnostic.py
```

### ReportLabのバージョンが古い

```bash
# 依存関係を更新
uv sync --all-extras
```

### PDFの分析に失敗する

```bash
# pypdfをインストール
pip install pypdf
```

## 期待される効果

1. **問題解決の迅速化**
   - フォント問題を即座に診断
   - 根本原因を特定

2. **環境依存の問題を軽減**
   - 適切な環境選択をサポート
   - 環境に応じた推奨フォントを提示

3. **ユーザーサポートの向上**
   - 具体的な解決策を自動提示
   - インストールコマンドを提供

4. **ドキュメント化**
   - 診断結果を記録として保存可能
   - 問題発生時の原因調査に活用

## 参考資料

- [ReportLab Font Handling](https://www.reportlab.com/docs/reportlab-userguide.pdf) (Chapter 3)
- [Noto CJK Fonts](https://github.com/notofonts/noto-cjk)
- [IPA Fonts](https://moji.or.jp/ipafont/)
- [Python - os.path](https://docs.python.org/3/library/os.path.html)
- [Python - pathlib](https://docs.python.org/3/library/pathlib.html)
