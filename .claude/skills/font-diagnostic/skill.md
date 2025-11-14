# Font Diagnostic Skill

このSkillは、フォント関連の問題を診断し、解決策を提案します。

## 使用方法

ユーザーが以下のような問題に直面した際に、このSkillを起動してください：
- 「フォントが見つからない」
- 「日本語が文字化けする」
- 「PDFにフォントが埋め込まれていない」
- 「どのフォントが使えるか確認したい」
- 「フォント環境を診断して」

## 診断項目

このSkillは以下の項目を自動的に診断します：

### 1. 実行環境の特定
- **プラットフォーム**: Linux、macOS、Windowsのいずれか
- **Docker環境**: コンテナ内で実行されているか
- **Pyodide環境**: ブラウザ（WebAssembly）で実行されているか
- **Pythonバージョン**: 動作環境のバージョン情報

### 2. ReportLabのフォント設定確認
- **登録済みフォント**: ReportLabに登録されているフォント一覧
- **フォントパス**: フォントが配置されているディレクトリ
- **フォントキャッシュ**: キャッシュの状態確認

### 3. システムフォントの確認
- **Noto CJKフォント**: Docker環境用の高品質フォント
- **IPAフォント**: ローカル環境のデフォルトフォント
- **Heiseiフォント**: ReportLabのフォールバック

### 4. フォントフォールバックの動作確認
- `src/letterpack/label.py`のフォント選択ロジック
- フォールバック順序の検証
- 各環境での推奨フォント

### 5. PDF内のフォント確認（生成されたPDFがある場合）
- 生成されたPDFに埋め込まれているフォント
- サブセット化の状態
- テキスト抽出可能性

## 実装手順

実装時に確認すべき手順：

1. 環境の特定
   - Dockerコンテナ内かチェック（`/.dockerenv`の存在）
   - Pyodide環境かチェック（`sys.platform == 'emscripten'`）
   - OSの種類を特定

2. ReportLabの設定を確認
   - `reportlab.pdfbase.pdfmetrics.getRegisteredFontNames()`
   - フォントメトリクスの確認

3. システムフォントを検索
   - Linux: `/usr/share/fonts/`
   - macOS: `/System/Library/Fonts/`, `/Library/Fonts/`
   - Windows: `C:\Windows\Fonts\`
   - Noto CJKフォントの検索
   - IPAフォントの検索

4. `src/letterpack/label.py`のフォント設定を読み取る
   - フォント登録ロジック（208-284行目）
   - フォールバック順序の確認

5. 診断レポートを生成
   - 環境情報の表示
   - 利用可能なフォントの一覧
   - 問題の特定

6. 問題があれば解決策を提示
   - 環境に応じた具体的な対処方法
   - インストールコマンド（必要な場合）

## 出力例

### 正常な場合

```
🔍 フォント診断レポート

【実行環境】
- プラットフォーム: Linux
- Docker環境: はい ✅
- Python: 3.12.0

【ReportLab登録フォント】
✅ IPAGothic (登録済み)
✅ Helvetica (標準フォント)

【システムフォント】
✅ Noto Sans CJK JP: /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
✅ Noto Serif CJK JP: /usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc
✅ IPAGothic: /usr/share/fonts/truetype/ipa-gothic/ipag.ttf

【フォントフォールバック設定】
1. Noto Sans CJK JP (ゴシック体) ✅
2. IPA Gothic (フォールバック) ✅
3. Helvetica (最終フォールバック) ✅

【診断結果】
✅ すべてのフォントが正しく設定されています
✅ 日本語PDFの生成に問題はありません

【推奨事項】
なし
```

### 問題がある場合

```
🔍 フォント診断レポート

【実行環境】
- プラットフォーム: Linux
- Docker環境: いいえ
- Python: 3.11.0

【ReportLab登録フォント】
❌ IPAGothic (未登録)
✅ Helvetica (標準フォント)

【システムフォント】
❌ Noto CJK フォントが見つかりません
❌ IPAフォントが見つかりません
⚠️ Heiseiフォントのみ利用可能

【フォントフォールバック設定】
1. Noto Sans CJK JP (ゴシック体) ❌ 見つかりません
2. IPA Gothic (フォールバック) ❌ 見つかりません
3. Helvetica (最終フォールバック) ✅

【診断結果】
⚠️ 日本語フォント（Noto/IPA）が利用できません
⚠️ 生成されるPDFはHeiseiフォントで出力されます（環境依存）

【解決策】
以下のいずれかの方法で解決できます：

1. **Docker環境の使用（推奨）**
   ```bash
   docker compose up -d
   ```
   → Noto CJKフォントがプリインストールされています

2. **IPAフォントのインストール（ローカル環境）**

   Ubuntu/Debian:
   ```bash
   sudo apt-get update
   sudo apt-get install fonts-ipafont
   ```

   Fedora/RHEL:
   ```bash
   sudo dnf install ipa-gothic-fonts
   ```

   macOS:
   ```bash
   brew install --cask font-ipa
   ```

   Windows:
   - IPAフォントダウンロード：https://moji.or.jp/ipafont/
   - ダウンロード後、Fontsフォルダにコピー

3. **フォントパスを手動指定**
   ```python
   from letterpack.label import create_label
   create_label(
       to_address=to_addr,
       from_address=from_addr,
       output_path="output.pdf",
       font_path="/path/to/your/font.ttf"  # フォントを直接指定
   )
   ```

4. **環境を確認**
   - 本番環境ではDocker環境を使用してください
   - 公開ツール（Webサイト）では静的HTML版（Pyodide）を使用してください
   - ローカル開発環境ではIPAフォントのインストールを推奨
```

## 診断スクリプトの実装

このSkillの診断処理は `tools/font_diagnostic.py` で実装されています。

### 主な関数

- `diagnose_fonts()`: フォント環境全体を診断
- `detect_environment()`: 実行環境を特定
- `check_reportlab_fonts()`: ReportLabのフォント設定を確認
- `find_system_fonts()`: システムフォントを検索
- `check_font_fallback()`: フォントフォールバックを検証
- `analyze_pdf_fonts()`: PDF内のフォントを分析（PDFがある場合）

## 関連ドキュメント

- `CLAUDE.md` - フォント戦略の説明（256-278行目）
- `DOCKER.md` - Docker環境のフォント設定
- `STATIC_VERSION.md` - Pyodide環境のフォント設定
- `src/letterpack/label.py` - フォント実装（208-284行目）

## 参考資料

- [ReportLab Font Handling](https://www.reportlab.com/docs/reportlab-userguide.pdf) (Chapter 3)
- [Noto CJK Fonts](https://github.com/notofonts/noto-cjk)
- [IPA Fonts](https://moji.or.jp/ipafont/)
- [日本郵便 - レターパック](https://www.post.japanpost.jp/)

## 期待される効果

1. **問題解決の迅速化**: フォント問題を即座に診断
2. **環境依存の問題を軽減**: 適切な環境選択をサポート
3. **ユーザーサポートの向上**: 具体的な解決策を自動提示
4. **ドキュメント化**: 診断結果を記録として保存可能
