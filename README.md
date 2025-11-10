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

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/letter-pack-label-maker.git
cd letter-pack-label-maker

# 依存関係をインストール
pip install -r requirements.txt

# または開発モードでインストール
pip install -e .
```

## 使い方

### CLI（コマンドライン）

```bash
# 対話形式で入力
python -m letterpack.cli

# 引数で指定
python -m letterpack.cli --output label.pdf \
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
python -m letterpack.web

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

## 開発

```bash
# テストの実行
pytest

# 開発モードでインストール
pip install -e ".[dev]"
```

## 注意事項

- 生成されるPDFはA4サイズです
- ラベル自体はA5相当のサイズで中央に配置されます
- 実際のレターパックに印刷する場合は、プリンターの設定を確認してください
