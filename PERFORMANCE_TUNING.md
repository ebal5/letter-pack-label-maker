# Pyodide パフォーマンスチューニングガイド

このドキュメントは、静的HTML版（Pyodide）のパフォーマンス最適化に関する実践的なガイドです。

## 目次

1. [パフォーマンス計測方法](#パフォーマンス計測方法)
2. [ボトルネック分析](#ボトルネック分析)
3. [最適化戦略](#最適化戦略)
4. [環境別チューニング](#環境別チューニング)
5. [ベストプラクティス](#ベストプラクティス)
6. [パフォーマンス監視](#パフォーマンス監視)

## パフォーマンス計測方法

### 1. ブラウザコンソールでの計測

```javascript
// ステップ1: メトリクスを取得
PyodideDiagnostics.logMetrics();

// ステップ2: 詳細レポートを生成
const report = await PyodideDiagnostics.generateReport();
console.log(report);

// ステップ3: JSON形式で保存
const json = JSON.stringify(report, null, 2);
console.log(json);
```

### 2. Chrome DevTools でのプロファイリング

1. **Performance タブを開く** (Ctrl+Shift+P)
2. **記録開始** をクリック
3. ページをリロード
4. 初期化完了まで待機
5. **記録停止** をクリック
6. フレームチャートを分析

### 3. ネットワークタブでの分析

1. **Network タブを開く** (Ctrl+Shift+N)
2. ページをリロード
3. 各リソースのダウンロード時間を確認：
   - `pyodide.js` - Pyodideランタイム
   - `reportlab` - ReportLabパッケージ
   - `.ttf` ファイル - フォント

## ボトルネック分析

### 典型的なパフォーマンスプロファイル

```
初回ロード（高速ネットワーク）:
┌─────────────────────────────────────────────────┐
│ Pyodide ロード               5-8秒  [████████░░]│
│ micropip ロード              1-3秒  [███░░░░░░░]│
│ ReportLab インストール      2-5秒  [█████░░░░░]│
│ フォント ダウンロード        3-8秒  [██████░░░░]│
│ フォント マウント             <1秒  [░░░░░░░░░░]│
│ Python コード ロード         <1秒  [░░░░░░░░░░]│
├─────────────────────────────────────────────────┤
│ 合計                        12-25秒              │
└─────────────────────────────────────────────────┘

2回目以降（キャッシュ活用）:
┌─────────────────────────────────────────────────┐
│ ブラウザキャッシュ使用       0秒   [フル活用]│
│ フォント IndexedDB キャッシュ <1秒  [フル活用]│
│ Pyodide 初期化               3-5秒  [██░░░░░░░░]│
├─────────────────────────────────────────────────┤
│ 合計                         3-6秒              │
└─────────────────────────────────────────────────┘
```

### ボトルネック特定フロー

```
パフォーマンスメトリクス取得
  ↓
全体時間が目標値を超えているか?
  ├─ YES → ステップ別分析へ
  └─ NO → 最適化完了

各ステップを分析:
- pyodideLoad (> 8秒)
  → ネットワーク速度が低い / CDN遅延
- reportlabInstall (> 5秒)
  → ネットワーク速度が低い
- fontDownload (> 8秒 初回 / > 1秒 キャッシュ)
  → Google Fonts 遅延
- 全体 (> 50秒)
  → メモリ不足の可能性
```

## 最適化戦略

### 1. フォント最適化（最高の効果）

**現状:**
- フォント初回: 3-8秒
- フォント2回目: <1秒（IndexedDB キャッシュ）

**最適化策:**

#### a) フォントプリロード（将来実装）

```html
<!-- HTMLの<head>セクション内 -->
<link rel="preload" as="font" href="..." crossorigin>
```

**効果:** 2-3秒短縮

#### b) フォントサブセット化（将来実装）

全フォント (2MB) の代わりに、日本語の常用字のみを含める

```javascript
// サブセット化されたフォント（約500KB）
const fontUrl = 'https://fonts.gstatic.com/s/notosansjp/subset...';
```

**効果:** 4-6秒短縮（初回）

#### c) ローカルフォント フォールバック

システムに Noto Sans JP がインストールされていれば使用

```javascript
if (await checkLocalFont('Noto Sans JP')) {
    // ダウンロードをスキップ
}
```

**効果:** 8秒短縮（初回）

### 2. Pyodide最適化

**現状:** 5-8秒

**最適化策:**

#### a) 遅延ロード（中優先度）

フォーム表示後に Pyodide をロード（部分的に平行化）

```javascript
// フォーム表示
showForm();

// バックグラウンドで初期化
initPyodideAsync();
```

**効果:** 3-5秒短縮（UX改善）

#### b) 必要なパッケージのプリロード（低優先度）

ReportLab の依存パッケージをキャッシュ

**効果:** 1-2秒短縮

### 3. ReportLab最適化

**現状:** 2-5秒

**最適化策:**

#### a) Wheel ファイル使用（中優先度）

プリコンパイル済みのパッケージを使用

```javascript
await micropip.install('reportlab-optimized.whl');
```

**効果:** 1-2秒短縮

#### b) キャッシング（高優先度）

インストール済みパッケージをキャッシュ

```javascript
// 2回目以降: キャッシュから復元
if (await isReportlabCached()) {
    // スキップ
}
```

**効果:** 2-3秒短縮（2回目以降）

### 4. ネットワーク最適化

#### a) CDN 選択最適化

複数の CDN を試して、最速なものを使用

```javascript
const cdns = [
    'https://cdn.jsdelivr.net/...',
    'https://unpkg.com/...',
    'https://esm.sh/...'
];

for (const cdn of cdns) {
    if (await testCDN(cdn) < 500) {
        useThisCDN(cdn);
        break;
    }
}
```

**効果:** 2-5秒短縮（ネットワーク遅延時）

#### b) 圧縮の活用

リソースを gzip/brotli 圧縮

**効果:** 30-50% 削減（自動的に行われる）

## 環境別チューニング

### 高速ネットワーク環境（> 50 Mbps）

```javascript
目標: 12-15秒

推奨設定:
1. ✓ フォント IndexedDB キャッシュ（デフォルト有効）
2. ✓ ブラウザキャッシュ（デフォルト有効）
3. ○ フォント プリロード（将来実装）
```

### 中速ネットワーク環境（5-50 Mbps）

```javascript
目標: 20-30秒

推奨設定:
1. ✓ フォント IndexedDB キャッシュ（デフォルト有効）
2. ✓ ブラウザキャッシュ（デフォルト有効）
3. ○ フォント プリロード（推奨）
4. ○ ReportLab キャッシング（要実装）
```

### 低速ネットワーク環境（< 5 Mbps）

```javascript
目標: 40-60秒

推奨設定:
1. ✓ フォント IndexedDB キャッシュ（デフォルト有効）
2. ✓ ブラウザキャッシュ（デフォルト有効）
3. ✓ フォント サブセット化（推奨）
4. ✓ ReportLab キャッシング（要実装）
5. ○ 遅延ロード（検討）
```

### オフライン環境（初期化後）

```javascript
目標: < 5秒

現在の実装:
✓ フォント IndexedDB キャッシュ
✓ ReportLab ブラウザキャッシュ
✓ Pyodide ブラウザキャッシュ

→ すべてのリソースがキャッシュされているため、
   完全にオフライン動作可能
```

## ベストプラクティス

### 1. ユーザーへの進捗通知

長い初期化プロセスを分かりやすく表示

```javascript
更新例:
"Pyodideを初期化中... (3/10完了)"
"ReportLabをインストール中... (5/10完了)"
"フォントをダウンロード中... (7/10完了)"
```

**効果:** ユーザーの体感時間 -20%

### 2. キャッシュの有効活用

```javascript
// デフォルト: 有効
// ユーザーがキャッシュをクリアしない限り、2回目以降は高速化

// キャッシュ削除を要求する場合:
await FontCacheManager.clear();
location.reload();
```

### 3. エラーハンドリング

初期化失敗時の自動リトライ

```javascript
async function initWithRetry(maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await initPyodide();
        } catch (e) {
            if (i < maxRetries - 1) {
                console.log(`リトライ ${i + 1}/${maxRetries}`);
                await sleep(2000 * (i + 1)); // 指数バックオフ
            } else {
                throw e;
            }
        }
    }
}
```

### 4. メモリ管理

```javascript
// PDF生成後のメモリ解放
function generateAndCleanup(data) {
    const pdf = pyodide.runPython(code);
    // ...使用...
    // メモリを解放
    pyodide.ffi.c_void_p(pdf).delete();
}
```

## パフォーマンス監視

### リアルタイムモニタリング

```javascript
// リアルタイムメトリクスを表示
const metricsInterval = setInterval(() => {
    const metrics = window.pyodideMetrics;
    console.log(`進捗: ${Math.round(metrics.total / 1000)}秒`);
}, 1000);

// 完了時に停止
onInitComplete(() => clearInterval(metricsInterval));
```

### パフォーマンス目標の設定と追跡

| 環境 | 初回 | 2回目以降 | PDF生成 |
|------|------|---------|--------|
| 目標 | 15秒 | 3秒 | 1秒 |
| 現状 | 18秒 | 4秒 | 2秒 |
| ステータス | ⚠️ | ✓ | ✓ |

### パフォーマンスレグレッション検出

```javascript
// 定期的にパフォーマンスを計測
const baseline = {
    total: 18000, // 18秒
    fontDownload: 3500 // 3.5秒
};

const current = window.pyodideMetrics;

// 20% 以上遅くなった場合は警告
if (current.total > baseline.total * 1.2) {
    console.warn('⚠️ パフォーマンスが低下しています');
}
```

## 最適化チェックリスト

- [ ] ブラウザキャッシュが有効か確認
- [ ] IndexedDB が有効か確認
- [ ] Network タブでダウンロード時間を確認
- [ ] Chrome DevTools で Performance を分析
- [ ] 複数のネットワーク速度で計測
- [ ] 異なるブラウザで計測
- [ ] 異なるデバイス（PC、スマートフォン）で計測
- [ ] 初回と2回目以降を比較
- [ ] エラー時のパフォーマンスを確認
- [ ] 低スペックマシンで計測

## トラブルシューティング

### "初期化が遅い" という報告を受けた場合

1. **環境を特定**
   ```javascript
   const report = await PyodideDiagnostics.generateReport();
   console.log('OS:', navigator.userAgent);
   console.log('ネットワーク:', navigator.connection?.effectiveType);
   ```

2. **ボトルネックを特定**
   ```javascript
   PyodideDiagnostics.logMetrics();
   ```

3. **各環境で改善案を適用**
   - ネットワーク遅延: 圧縮、CDN変更
   - メモリ不足: 遅延ロード
   - フォント問題: フォント最適化

### "パフォーマンスが低下した" という報告

1. **変更内容を確認**
   ```bash
   git log --oneline -10
   git diff HEAD~1
   ```

2. **リグレッションを特定**
   - index_static.html の変更
   - JavaScript 実装の追加
   - パッケージ依存関係の変更

3. **改善策を適用**
   - 不要なコードを削除
   - キャッシング戦略を見直す
   - 遅延ロードを活用する

## まとめ

### 期待可能な性能

| シナリオ | 初期化時間 | 備考 |
|---------|-----------|------|
| 初回（高速ネット） | 12-20秒 | フォント DL あり |
| 初回（低速ネット） | 30-50秒 | フォント DL あり |
| 2回目以降 | 3-6秒 | 完全キャッシュ |
| オフライン | <5秒 | 完全キャッシュ |
| PDF生成 | 1-3秒 | 処理時間 |

### 今後の改善案

- ✓ Phase 1: 診断・計測ツール（完了）
- ✓ Phase 2: フォント最適化・キャッシング（完了）
- ◇ Phase 3: フォントサブセット化
- ◇ Phase 4: 遅延ロード
- ◇ Phase 5: Service Worker オフライン対応

## 関連資料

- [PYODIDE_DEBUG_GUIDE.md](./PYODIDE_DEBUG_GUIDE.md) - デバッグガイド
- [STATIC_VERSION.md](./STATIC_VERSION.md) - 技術詳細
- [Pyodide Docs](https://pyodide.org/en/stable/) - Pyodide ドキュメント
