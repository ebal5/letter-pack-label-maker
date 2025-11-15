# Tools Directory

このディレクトリには、レターパックラベル生成プロジェクトの開発補助ツールが含まれています。

## レイアウト調整ツール (label_adjuster.py)

レイアウトパラメータをリアルタイムで調整し、PDFプレビューを確認できるFlask WebUIツールです。

### 機能

- **パラメータ調整フォーム**: 10セクションの全パラメータを調整可能
  1. Layout Settings (レイアウト設定)
  2. Font Sizes (フォントサイズ)
  3. Spacing (スペーシング)
  4. Postal Box (郵便番号ボックス)
  5. Address Layout (住所レイアウト)
  6. Dotted Line (点線)
  7. Sama (「様」設定)
  8. Border (枠線)
  9. Phone (電話番号)
  10. Section Heights (セクション高さ)

- **リアルタイムPDFプレビュー**: パラメータ変更後に「プレビュー更新」ボタンでPDF生成
- **設定保存**: 調整した設定をYAMLファイルとして保存（タイムスタンプ付き）
- **デフォルトリセット**: ボタンクリックでデフォルト設定に戻す

### 起動方法

```bash
# プロジェクトルートで実行
python tools/label_adjuster.py

# または
uv run python tools/label_adjuster.py
```

ブラウザで以下のURLを開きます：
```
http://localhost:5001
```

### 使い方

1. **パラメータ調整**
   - 左側のフォームでパラメータを調整
   - アコーディオンで各セクションを開閉可能

2. **プレビュー更新**
   - 「プレビュー更新」ボタンをクリック
   - 右側のプレビューエリアにPDFが表示される

3. **設定保存**
   - 「設定を保存」ボタンをクリック
   - `config/label_layout_custom_YYYYMMDD_HHMMSS.yaml` として保存される

4. **デフォルトに戻す**
   - 「デフォルトに戻す」ボタンをクリック
   - `config/label_layout.yaml` の設定が読み込まれる

### サンプルデータ

プレビュー生成時には、以下のサンプルデータが使用されます：

**お届け先:**
- 郵便番号: 100-0001
- 住所: 東京都千代田区千代田 1-1
- 名前: 山田 太郎
- 電話番号: 03-1234-5678

**ご依頼主:**
- 郵便番号: 530-0001
- 住所: 大阪府大阪市北区梅田 1-1-1
- 名前: 田中 花子
- 電話番号: 06-9876-5432

### 技術スタック

- **Flask**: Webフレームワーク
- **Bootstrap 5**: UIフレームワーク
- **ReportLab**: PDF生成
- **PyYAML**: YAML設定ファイル処理

### エンドポイント

- `GET /`: パラメータ調整フォームを表示
- `POST /preview`: フォームデータからPDFを生成して返す
- `POST /save`: フォームデータをYAMLファイルとして保存
- `GET /reset`: デフォルト設定を返す（JSON）

### ファイル構成

```
tools/
├── label_adjuster.py          # Flaskアプリケーション
├── templates/
│   └── label_adjuster.html    # Bootstrap UIテンプレート
└── README.md                   # このファイル
```

## その他のツール

### check_japanese_code.py

日本語コードのチェックツールです。

```bash
python tools/check_japanese_code.py
```

## 注意事項

- レイアウト調整ツールはポート5001を使用します
- Webサーバー版（`letterpack-web`）はポート5000を使用するため、競合しません
- デバッグモードで実行されるため、本番環境での使用は避けてください
- 設定保存時は `config/` ディレクトリに書き込み権限が必要です

## トラブルシューティング

### ポートが使用中の場合

```bash
# ポート5001を使用しているプロセスを確認
lsof -i :5001

# プロセスを終了
kill -9 <PID>
```

### フォントが見つからない場合

Docker環境での実行を推奨します：

```bash
# Docker環境でWebサーバー版を起動
docker compose up -d

# ブラウザで http://localhost:5000 を開く
```

### プレビューが表示されない場合

1. ブラウザのコンソールでエラーを確認
2. Flaskのログを確認
3. 入力値が範囲内かチェック（例: 0-300mm、1-72pt等）

## 開発者向け

### コード品質チェック

```bash
# Ruffでリントチェック
uv run ruff check tools/label_adjuster.py

# 自動修正
uv run ruff check --fix tools/label_adjuster.py

# フォーマット
uv run ruff format tools/label_adjuster.py
```

### 新しいパラメータの追加

1. `src/letterpack/label.py` のPydanticモデルに追加
2. `tools/label_adjuster.py` の `form_to_config_dict()` 関数に追加
3. `tools/templates/label_adjuster.html` のフォームに入力欄を追加
4. `config/label_layout.yaml` にデフォルト値を追加

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。
