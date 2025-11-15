# Pyodide Integration Agent - デバッグガイド

このドキュメントは、静的HTML版（Pyodide）でのデバッグとパフォーマンス最適化に関する詳細ガイドです。

## 目次

1. [クイックスタート](#クイックスタート)
2. [パフォーマンス計測](#パフォーマンス計測)
3. [デバッグツール](#デバッグツール)
4. [エラー診断](#エラー診断)
5. [フォント管理](#フォント管理)
6. [パフォーマンス最適化](#パフォーマンス最適化)
7. [トラブルシューティング](#トラブルシューティング)

## クイックスタート

### ブラウザコンソールでのデバッグ

1. ブラウザの開発者ツールを開く（F12キー）
2. **コンソールタブ**を選択
3. 以下のコマンドを実行してパフォーマンスメトリクスを表示：

```javascript
PyodideDiagnostics.logMetrics();
```

### 診断レポートの生成

詳細な診断レポートを取得：

```javascript
const report = await PyodideDiagnostics.generateReport();
console.log(report);
```

## パフォーマンス計測

### 計測対象項目

Pyodideの初期化プロセスは、以下のステップに分かれており、各ステップの時間を計測しています：

| メトリクス | 説明 | 期待値 |
|-----------|------|--------|
| `pyodideLoad` | Pyodideライブラリのロード | 3-8秒 |
| `micropipLoad` | micropipパッケージマネージャーのロード | 1-3秒 |
| `reportlabInstall` | ReportLabパッケージのインストール | 2-5秒 |
| `fontDownload` | Noto Sans JPフォントのダウンロード | 2-8秒（初回）、<100ms（キャッシュ時） |
| `fontMount` | フォントをPyodideの仮想ファイルシステムに配置 | <100ms |
| `pythonCodeLoad` | Pythonコードモジュールのロード | <100ms |
| `total` | **合計時間** | **10-40秒**（初回）、**2-8秒**（2回目以降） |

### コンソールでのメトリクス表示

```javascript
// 表形式で表示
PyodideDiagnostics.logMetrics();

// JSON形式で出力
console.log(window.pyodideMetrics);
```

### 出力例

```
┌─────────────────────┬──────────┐
│ pyodideLoad         │ 5234 ms  │
│ micropipLoad        │ 2156 ms  │
│ reportlabInstall    │ 3890 ms  │
│ fontDownload        │ 156 ms   │ ← キャッシュから読み込み
│ fontMount           │ 45 ms    │
│ pythonCodeLoad      │ 23 ms    │
│ total               │ 11504 ms │
└─────────────────────┴──────────┘
```

## デバッグツール

### 1. 環境情報の確認

現在の環境情報を取得：

```javascript
const report = await PyodideDiagnostics.generateReport();
console.log('環境情報:', report.environment);
```

**出力例:**
```javascript
{
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
  onLine: true,
  memoryCaps: {
    jsHeapSizeLimit: "2048MB",
    totalJSHeapSize: "450MB",
    usedJSHeapSize: "280MB"
  }
}
```

### 2. フォント状態の確認

フォントが正常にロードされたか確認：

```javascript
const report = await PyodideDiagnostics.generateReport();
console.log('フォント状態:', report.fontStatus);
```

**正常な場合:**
```javascript
{
  status: "loaded",
  path: "/NotoSansJP-Bold.ttf"
}
```

**キャッシュミスの場合:**
```javascript
{
  status: "missing",
  path: "/NotoSansJP-Bold.ttf"
}
```

### 3. エラー情報のキャプチャ

エラーが発生した場合、詳細情報が自動的にコンソールに記録されます：

```
[PyodideInitialization] Error: TypeError: Failed to fetch
Error Report: {
  context: "PyodideInitialization",
  message: "Failed to fetch",
  stack: "Error: Failed to fetch\n    at initPyodide (index_static.html:932:1)\n...",
  timestamp: "2025-11-13T19:41:26Z",
  metrics: { /* パフォーマンスメトリクス */ }
}
```

## エラー診断

### よくあるエラーと対処法

#### 1. "Failed to fetch" エラー

**原因:** ネットワーク接続の問題またはCDNへのアクセス制限

**診断:**
```javascript
// ネットワーク接続を確認
console.log('オンライン:', navigator.onLine);

// CDNへのアクセステスト
fetch('https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js')
  .then(() => console.log('CDN OK'))
  .catch(e => console.error('CDN NG:', e));
```

**対処法:**
1. インターネット接続を確認
2. ファイアウォール設定を確認
3. CDN URL をホワイトリストに追加（企業ネットワークの場合）
4. 別のブラウザで試す

#### 2. メモリ不足エラー

**症状:** "Out of memory" または "Heap quota exceeded"

**診断:**
```javascript
const report = await PyodideDiagnostics.generateReport();
const mem = report.environment.memoryCaps;
console.log(`使用メモリ: ${mem.usedJSHeapSize} / ${mem.jsHeapSizeLimit}`);
```

**対処法:**
1. 他のブラウザタブを閉じる
2. ブラウザキャッシュをクリア
3. メモリの多いブラウザに切り替え（Chrome > Firefox > Safari）

#### 3. フォントロード失敗

**症状:** "Noto Sans JP Bold のダウンロードに失敗" メッセージ

**診断:**
```javascript
// フォントキャッシュの状態を確認
const cached = await FontCacheManager.get('noto-sans-jp-bold-v52');
console.log('フォントキャッシュ:', cached ? 'あり' : 'なし');

// フォント状態を確認
const report = await PyodideDiagnostics.generateReport();
console.log('フォント状態:', report.fontStatus);
```

**対処法:**
1. フォントキャッシュをクリア：
   ```javascript
   await FontCacheManager.clear();
   location.reload();
   ```
2. Google Fonts へのアクセスを確認
3. フォールバックフォント（Heiseiフォント）が使用されます

## フォント管理

### フォントキャッシュの理解

Noto Sans JP フォント（約2MB）はIndexedDBに自動的にキャッシュされます。

```
初回アクセス:
  Google Fonts からダウンロード (2-8秒)
    ↓
  IndexedDB に保存
    ↓
  Pyodide 仮想FS に配置

2回目以降:
  IndexedDB から読み込み (<100ms)
    ↓
  Pyodide 仮想FS に配置
```

### フォントキャッシュの操作

**キャッシュをクリア:**
```javascript
await FontCacheManager.clear();
console.log('フォントキャッシュをクリアしました');
```

**キャッシュの確認:**
```javascript
const font = await FontCacheManager.get('noto-sans-jp-bold-v52');
console.log('キャッシュサイズ:', font ? font.length : 0, 'bytes');
```

### フォント選択の優先順位

1. **Noto Sans JP Bold** (推奨) - Google Fonts から自動ダウンロード
2. **HeiseiMin-W3** (フォールバック) - ReportLab組込フォント
3. **HeiseiKakuGo-W5** (フォールバック) - ReportLab組込フォント
4. **Helvetica** (最終フォールバック) - 日本語非対応

## パフォーマンス最適化

### ボトルネックの特定

1. **パフォーマンスメトリクスを表示:**
   ```javascript
   PyodideDiagnostics.logMetrics();
   ```

2. **最も時間がかかっているステップを確認**

3. **各ステップの最適化を検討**

### 最適化のヒント

#### フォントダウンロードが遅い場合

```javascript
// キャッシュをクリアして再ダウンロード
await FontCacheManager.clear();
location.reload();

// または、キャッシュから読み込み（2回目以降は自動的に高速）
// 3回目以降のアクセスで改善が見られます
```

#### ReportLabインストールが遅い場合

- ネットワーク速度を確認
- pypyパッケージを プリロード する（要実装）

#### 全体的に遅い場合

- ブラウザのハードウェアアクセラレーション設定を確認
- Chrome DevTools で Performance パネルを使用して詳細分析

### パフォーマンス目標

| 環境 | 目標時間 | 現状 |
|------|---------|------|
| 初回（高速ネットワーク） | 15秒以下 | 12-18秒 |
| 初回（低速ネットワーク） | 40秒以下 | 30-40秒 |
| 2回目以降（キャッシュ） | 5秒以下 | 3-6秒 |
| PDF生成 | 2秒以下 | 1-3秒 |

## トラブルシューティング

### シナリオ別ガイド

#### シナリオ1: ページが全く応答しない

**手順:**
1. ブラウザのコンソール（F12）を開く
2. エラーメッセージを確認
3. ネットワークタブで通信を確認
4. 以下を実行：
   ```javascript
   console.log('PyodideInitialized:', typeof pyodide !== 'undefined');
   console.log('Online:', navigator.onLine);
   ```

#### シナリオ2: 初期化は完了するが、PDFが生成できない

**手順:**
1. フォームのすべての必須項目を入力
2. コンソールのエラーメッセージを確認
3. 以下を実行してメモリを確認：
   ```javascript
   const report = await PyodideDiagnostics.generateReport();
   console.log('メモリ使用率:', report.environment.memoryCaps);
   ```
4. 必要に応じてタブを再ロード

#### シナリオ3: 日本語が文字化けしている

**手順:**
1. フォント状態を確認：
   ```javascript
   const report = await PyodideDiagnostics.generateReport();
   console.log('フォント:', report.fontStatus);
   ```
2. フォント "Noto Sans JP Bold フォント完了" ログを確認
3. ログにない場合：
   ```javascript
   await FontCacheManager.clear();
   location.reload();
   ```
4. それでも解決しない場合は、別のブラウザで試す

### ログの出力・保存

パフォーマンスレポートを JSON 形式で出力：

```javascript
// ステップ1: 診断レポートを生成
const report = await PyodideDiagnostics.generateReport();

// ステップ2: JSON文字列に変換
const json = JSON.stringify(report, null, 2);

// ステップ3: コンソールに出力
console.log(json);

// ステップ4: ファイルとして保存（ブラウザの機能）
const blob = new Blob([json], { type: 'application/json' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `pyodide-report-${new Date().toISOString()}.json`;
a.click();
```

## API リファレンス

### PyodideDiagnostics

```javascript
// パフォーマンスメトリクスをテーブル形式で表示
PyodideDiagnostics.logMetrics();

// 完全な診断レポートを生成
const report = await PyodideDiagnostics.generateReport();

// レポートをサーバーに送信（将来の実装）
await PyodideDiagnostics.sendReport('/api/diagnostics');
```

### FontCacheManager

```javascript
// フォントをキャッシュから取得
const fontData = await FontCacheManager.get('noto-sans-jp-bold-v52');

// フォントをキャッシュに保存
await FontCacheManager.set('noto-sans-jp-bold-v52', fontData);

// キャッシュをクリア
await FontCacheManager.clear();
```

### ErrorHandler

```javascript
// エラーをユーザーフレンドリーなメッセージに変換
const msg = ErrorHandler.getFriendlyMessage(error);

// エラーを詳細にログ出力
ErrorHandler.logError('ContextName', error);
```

### window.pyodideMetrics

```javascript
// パフォーマンスメトリクスに直接アクセス
console.log(window.pyodideMetrics);
// 出力例:
// {
//   pyodideLoad: 5234,
//   micropipLoad: 2156,
//   reportlabInstall: 3890,
//   fontDownload: 156,
//   fontMount: 45,
//   pythonCodeLoad: 23,
//   total: 11504,
//   startTime: 1234567890.123
// }
```

## 開発者向けヒント

### デバッグモードの有効化（将来の実装）

```javascript
// URL パラメータでデバッグモードを有効化
// example.com/index_static.html?debug=true

if (window.location.search.includes('debug=true')) {
    // 詳細ログを表示
    window.DEBUG_MODE = true;
}
```

### 詳細なトレーログ

```javascript
// すべてのPython実行をトレース（要実装）
const originalRunPython = pyodide.runPython.bind(pyodide);
pyodide.runPython = (code) => {
    console.log('[Python]', code.substring(0, 50) + '...');
    return originalRunPython(code);
};
```

## 関連資料

- [Pyodide Documentation](https://pyodide.org/en/stable/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [IndexedDB API Reference](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [STATIC_VERSION.md](./STATIC_VERSION.md) - 静的HTML版の技術詳細

## サポート

問題が解決しない場合は、以下の情報をこのデバッグガイドを参考に収集してください：

1. ブラウザ（Chrome, Firefox, Safari等）とバージョン
2. OS とバージョン
3. ネットワーク環境（速度、プロキシ設定など）
4. パフォーマンスメトリクス出力
5. ブラウザコンソールのエラーメッセージ

GitHub Issues で報告してください。
