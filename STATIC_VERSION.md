# 静的HTMLページ版について

このドキュメントでは、Pyodideを使用した静的HTMLページ版の技術詳細と使い方について説明します。

## 概要

静的HTMLページ版は、**Pyodide**（PythonをWebAssemblyにコンパイルしてブラウザで実行する技術）を使用して、サーバー不要でPDF生成を行います。

### ファイル構成

- `index_static.html` - メインの静的HTMLページ（本番用）
- `poc_pyodide.html` - Pyodide + ReportLab の動作確認用PoC

## 技術スタック

### Pyodide
- **バージョン**: 0.24.1
- **サイズ**: 約10MB（初回ロード時）
- **Python バージョン**: 3.11

### 使用ライブラリ
- **ReportLab**: PDF生成（micropip経由でインストール）
- **Pydantic**: データバリデーション（将来的に使用予定）

## 実装の詳細

### 1. 初期化フロー

```
ページロード
  ↓
Pyodideロード（CDNから、約10MB）
  ↓
micropipのロード
  ↓
ReportLabのインストール（micropip経由）
  ↓
Pythonコードの実行・登録
  ↓
フォーム表示（ユーザーが入力可能に）
```

### 2. PDF生成フロー

```
フォーム送信
  ↓
JavaScriptでフォームデータ取得
  ↓
PythonにデータをJSON形式で渡す
  ↓
Python: AddressInfoオブジェクト作成
  ↓
Python: LabelGenerator.generate() 実行
  ↓
Python: BytesIOにPDF生成
  ↓
JavaScriptにバイトデータを返す
  ↓
Blobオブジェクトを作成してダウンロード
```

### 3. フォント処理

既存のPythonコード（`label.py`）はファイルシステムから日本語フォントを読み込む仕様でしたが、Pyodide環境では以下のように簡素化しています：

```python
# ReportLabのCJKフォントを使用（フォールバック方式）
try:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    self.font_name = "HeiseiMin-W3"
except:
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        self.font_name = "HeiseiKakuGo-W5"
    except:
        self.font_name = "Helvetica"  # 最終フォールバック
```

#### フォントの制限事項

- IPAフォントは使用できない（ファイルシステムへのアクセスが必要）
- HeiseiMin-W3 または HeiseiKakuGo-W5 を使用
- 一部の記号や特殊文字が表示されない可能性がある

## 使い方

### ローカルでテスト

```bash
# プロジェクトのルートディレクトリで

# 方法1: Python標準ライブラリのHTTPサーバー
python -m http.server 8000

# 方法2: uvを使ったHTTPサーバー
python3 -m http.server 8000

# ブラウザで開く
open http://localhost:8000/index_static.html
```

### GitHub Pagesで公開

1. GitHubリポジトリの Settings > Pages を開く
2. Source を "Deploy from a branch" に設定
3. Branch を選択（例: `main`）
4. Save をクリック
5. 数分後に公開URL（`https://yourusername.github.io/letter-pack-label-maker/index_static.html`）でアクセス可能

### Netlify / Vercel で公開

単一のHTMLファイルなので、そのままドラッグ&ドロップでデプロイ可能です。

## パフォーマンス

### 初回ロード
- Pyodideのダウンロード: 約10MB
- ReportLabのインストール: 約2MB
- 合計時間: 10-30秒（ネットワーク速度に依存）

### 2回目以降
- ブラウザのキャッシュを使用
- 初期化時間: 2-5秒
- PDF生成時間: 1-2秒

## トラブルシューティング

### 初期化が失敗する

**症状**: "初期化エラー" が表示される

**原因**:
- ネットワーク接続の問題
- CDNへのアクセスが制限されている
- ブラウザのセキュリティ設定

**対処法**:
1. ブラウザのコンソールを開いてエラーメッセージを確認
2. ネットワーク接続を確認
3. 別のブラウザで試す
4. HTTPS経由でアクセスする

### PDF生成が失敗する

**症状**: "PDF生成エラー" が表示される

**原因**:
- フォームの入力値が不正
- メモリ不足
- ReportLabのエラー

**対処法**:
1. すべての必須項目が入力されているか確認
2. ブラウザのメモリを解放（他のタブを閉じる）
3. ブラウザのコンソールでエラー詳細を確認

### 日本語が正しく表示されない

**症状**: PDFで日本語が文字化けまたは空白になる

**原因**:
- HeiseiMin-W3フォントがサポートしていない文字を使用

**対処法**:
- 別のフォント（HeiseiKakuGo-W5）を試す
- 特殊な記号を避ける
- サーバー版（Flask）を使用する（IPAフォントをサポート）

## ブラウザ互換性

### サポート対象
- ✅ Chrome/Edge 90+
- ✅ Firefox 90+
- ✅ Safari 14+

### 非サポート
- ❌ Internet Explorer（すべてのバージョン）
- ❌ 古いブラウザ（WebAssembly未対応）

## セキュリティ

### データプライバシー
- ✅ すべての処理はクライアント側で実行
- ✅ データはサーバーに送信されない
- ✅ 完全にオフラインで動作可能（初回ロード後）

### 注意事項
- Pyodideは信頼できるCDN（jsdelivr）から読み込まれる
- ネットワーク接続時は外部リソースを取得する

## 将来の改善案

### フォント改善
- カスタムフォント（IPAフォントなど）をWebから読み込む
- Pyodide FSでフォントファイルを配置

### パフォーマンス最適化
- Service Workerでオフライン対応を強化
- Pyodideの遅延ロード
- WebWorkerで処理をバックグラウンド化

### 機能追加
- 複数ラベルの一括生成
- プレビュー機能（PDF.jsを使用）
- テンプレート保存機能（LocalStorage）

## ライセンス

このプロジェクトはMITライセンスです。

### 使用ライブラリのライセンス
- Pyodide: Mozilla Public License 2.0
- ReportLab: BSD License
- Flask: BSD License

## 参考リンク

- [Pyodide Documentation](https://pyodide.org/en/stable/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
