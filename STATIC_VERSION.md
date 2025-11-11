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

**Noto Sans JP**をGoogle Fontsから自動的にダウンロードして使用します：

```javascript
// 初期化時にNoto Sans JPフォントをダウンロード
const fontUrl = 'https://fonts.gstatic.com/s/notosansjp/v52/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFBEi75vY0rw-oME.ttf';
const fontResponse = await fetch(fontUrl);
const fontArrayBuffer = await fontResponse.arrayBuffer();
const fontBytes = new Uint8Array(fontArrayBuffer);

// Pyodideの仮想ファイルシステムに保存
pyodide.FS.writeFile('/NotoSansJP-Regular.ttf', fontBytes);
```

Pythonコード側では、ダウンロードされたフォントを登録：

```python
# Noto Sans JPフォントを優先的に使用
if font_path:
    try:
        pdfmetrics.registerFont(TTFont("NotoSansJP", font_path))
        self.font_name = "NotoSansJP"
    except Exception as e:
        print(f"Noto Sans JPの登録に失敗: {e}")
        self._fallback_font()
else:
    self._fallback_font()
```

#### フォント選択の優先順位

1. **Noto Sans JP** (推奨) - Google Fontsから自動ダウンロード
2. **HeiseiMin-W3** (フォールバック) - ReportLabのCJKフォント
3. **HeiseiKakuGo-W5** (フォールバック) - ReportLabのCJKフォント
4. **Helvetica** (最終フォールバック) - 日本語非対応

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
- Noto Sans JPフォントのダウンロード: 約2MB
- **合計時間: 15-40秒**（ネットワーク速度に依存）

### 2回目以降
- ブラウザのキャッシュを使用（Pyodide、ReportLab、フォント）
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
- Noto Sans JPフォントのダウンロードに失敗した
- フォールバックフォント（HeiseiMin-W3など）がサポートしていない文字を使用

**対処法**:
1. ブラウザのコンソールを開いて「Noto Sans JPフォントのダウンロード完了」メッセージを確認
2. フォントのダウンロードに失敗している場合は、ページを再読み込み
3. それでも解決しない場合は、サーバー版（Flask）を使用する（IPAフォントをサポート）

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
- ✅ **完了**: Noto Sans JPフォントの自動ダウンロード
- Noto Sans JP Bold（太字）の追加
- フォントウェイトの選択機能

### パフォーマンス最適化
- Service Workerでオフライン対応を強化
- Pyodideの遅延ロード
- WebWorkerで処理をバックグラウンド化
- フォントのサブセット化（ファイルサイズ削減）

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
