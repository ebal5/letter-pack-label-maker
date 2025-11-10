# Issue: レターパックラベルのレイアウトを設定可能にする

## 概要

現在のレターパックラベル生成機能は、詳細なデザイン（郵便番号ボックス、点線、「様」付加など）が実装されていますが、レイアウトパラメータ（マージン、フォントサイズ、要素間隔など）がコード内にハードコードされています。これらを外部設定ファイルで管理できるようにすることで、異なる印刷環境やレイアウト要件に柔軟に対応できるようにします。

## 背景

- 現在の実装（`src/letterpack/label.py`）では、約30箇所以上のレイアウト値がハードコードされている
- 印刷環境やプリンターの違いにより、微調整が必要になるケースがある
- 開発者以外がレイアウトを調整するのが困難

## 目標

1. **設定の外部化**: レイアウトパラメータをYAMLファイルで管理
2. **バリデーション**: Pydanticによる設定値の検証
3. **後方互換性**: 既存のAPIを壊さない
4. **プレビュー機能**: 調整結果をリアルタイムで確認できるツール（オプション）

## 技術的なアプローチ

### 1. 設定ファイルの構造

`config/label_layout.yaml`を作成し、以下のパラメータを管理：

```yaml
# ラベルの基本寸法
layout:
  label_width: 148  # mm - A5サイズの幅
  label_height: 210  # mm - A5サイズの高さ
  margin: 8  # mm - セクション内のマージン
  draw_border: true  # デバッグ用の枠線

# フォントサイズ
fonts:
  label: 9  # pt - フィールドラベル（おところ、おなまえ等）
  postal_code: 10  # pt - 郵便番号
  address: 11  # pt - 住所
  name: 14  # pt - 氏名
  phone: 11  # pt - 電話番号

# 要素間のスペーシング
spacing:
  label_offset: 0  # px - トップからラベルまで
  section_spacing: 15  # px - セクション間の間隔
  address_line_height: 12  # px - 住所の行間
  name_spacing: 15  # px - 氏名セクションの上マージン
  phone_spacing: 15  # px - 電話番号セクションの上マージン

# 郵便番号ボックス
postal_box:
  box_size: 5  # mm - 1つのボックスのサイズ
  box_spacing: 1  # mm - ボックス間の間隔
  offset_x: 15  # px - 左からのオフセット
  offset_y: -5  # px - 上からのオフセット

# その他
address:
  max_length: 35  # 1行の最大文字数
  max_lines: 3  # 最大行数

dotted_line:
  dash_pattern: [2, 2]  # mm - 点線パターン [線, 空白]
  color: [0.5, 0.5, 0.5]  # RGB

sama:
  width: 8  # mm - 「様」用のスペース
  offset: 2  # mm - 点線からのオフセット
```

### 2. Pydanticモデルの実装

```python
from pydantic import BaseModel, Field

class LayoutConfig(BaseModel):
    label_width: float = Field(gt=0, le=300)
    label_height: float = Field(gt=0, le=500)
    margin: float = Field(ge=0, le=50)
    draw_border: bool = True

class FontsConfig(BaseModel):
    label: int = Field(gt=0, le=72)
    postal_code: int = Field(gt=0, le=72)
    address: int = Field(gt=0, le=72)
    name: int = Field(gt=0, le=72)
    phone: int = Field(gt=0, le=72)

# ... その他のセクション

class LabelLayoutConfig(BaseModel):
    layout: LayoutConfig
    fonts: FontsConfig
    spacing: SpacingConfig
    postal_box: PostalBoxConfig
    address: AddressConfig
    dotted_line: DottedLineConfig
    sama: SamaConfig
```

### 3. LabelGeneratorクラスの修正

```python
class LabelGenerator:
    def __init__(self, font_path: Optional[str] = None, config_path: Optional[str] = None):
        self.font_name = "IPAGothic"
        self.font_path = font_path
        self.config = load_layout_config(config_path)  # 設定を読み込み
        self._setup_font()

    def _draw_address_section(self, ...):
        # ハードコードされた値を設定から取得
        margin = self.config["layout"]["margin"] * mm
        label_font_size = self.config["fonts"]["label"]
        # ...
```

### 4. プレビューツール（オプション）

`tools/label_adjuster.py`を実装：

- Flask Webインターフェース
- パラメータ調整フォーム
- PyMuPDFによるリアルタイムプレビュー
- 設定ファイルへの保存機能

## 実装範囲の提案

### Phase 1: 最小限の設定化（推奨）

**対象パラメータ**:
- マージン
- 主要フォントサイズ（5種類）
- 基本的なスペーシング（3-4箇所）
- 住所の最大文字数

**作業量**: 中（3-5時間）
**影響範囲**: 限定的
**メリット**: 最も頻繁に調整が必要な項目に対応

### Phase 2: 完全な設定化

**対象パラメータ**:
- 郵便番号ボックスの詳細
- 点線のスタイル
- 「様」の配置
- すべての色とオフセット

**作業量**: 大（8-12時間）
**影響範囲**: 広範囲
**メリット**: 完全な柔軟性

### Phase 3: プレビューツール

**内容**:
- Web UIの実装
- リアルタイムプレビュー
- 設定の保存/読み込み

**作業量**: 中（4-6時間）
**依存**: Phase 1 または Phase 2

## 参考実装

このIssueの参考実装が以下のブランチにあります：

```
ブランチ: claude/adjust-label-positioning-011CUzUH2vMPuQGPFeTBNk76
```

**含まれる実装**:
- ✅ YAML設定ファイル（`config/label_layout.yaml`）
- ✅ Pydanticバリデーションモデル
- ✅ `load_layout_config()`関数
- ✅ 設定値のバリデーション
- ✅ プレビューツール（`tools/label_adjuster.py`）
- ✅ テストケース

**注意**: この実装は古いシンプルなデザインをベースにしているため、そのまま使用はできません。現在のmainブランチの詳細デザインに統合する必要があります。

### 参考ファイル

1. **設定ファイル例**:
   - `config/label_layout.yaml`（ブランチ内）

2. **Pydanticモデル**:
   - `src/letterpack/label.py`の冒頭部分（LayoutConfig, FontsConfig等）

3. **設定読み込みロジック**:
   - `load_layout_config()`関数

4. **プレビューツール**:
   - `tools/label_adjuster.py`全体

5. **テスト**:
   - `tests/test_label.py`の`test_load_layout_config()`
   - `tests/test_label.py`の`test_invalid_config_values()`

## 実装時の注意点

### 1. 現在のmainブランチとの違い

origin/mainには以下の詳細機能があります：
- `_draw_postal_boxes()`: 郵便番号ボックスの描画
- `_draw_dotted_line()`: 点線の描画
- 「おところ:」「おなまえ:」「電話番号:」ラベル
- 「様」の自動付加
- IPAフォントのサポート

これらの機能を維持しながら、設定可能にする必要があります。

### 2. ハードコードされた値の場所

主なハードコード箇所：
- `_draw_address_section()`: margin (8*mm), label_font_size (9), current_y減算値 (15, 12, 18等)
- `_draw_postal_boxes()`: box_size (5*mm), box_spacing (1*mm)
- `_draw_dotted_line()`: dash pattern (2,2), color (0.5,0.5,0.5)
- その他20箇所以上

### 3. 後方互換性の維持

既存のAPI：
```python
create_label(to_address, from_address, output_path, font_path=None)
```

新しいAPI（推奨）：
```python
create_label(to_address, from_address, output_path, font_path=None, config_path=None)
```

`config_path=None`の場合はデフォルト設定を使用することで、既存コードを壊さない。

### 4. テスト

以下のテストを追加：
- 設定ファイルの読み込みテスト
- 不正な値のバリデーションテスト
- デフォルト設定でのPDF生成テスト
- カスタム設定でのPDF生成テスト
- 住所分割ロジックのテスト（境界条件含む）

## 期待される効果

1. **印刷環境への柔軟な対応**: プリンターやレイアウト要件に応じた調整が可能
2. **保守性の向上**: 設定変更がコード修正不要
3. **デバッグの容易化**: 視覚的なプレビューツールによる調整
4. **バージョン管理**: 設定ファイルをgitで管理
5. **再現性**: 同じ設定ファイルで同じレイアウトを再現可能

## 関連資料

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)

## まとめ

このIssueは、レターパックラベル生成機能の柔軟性と保守性を向上させるための重要な改善です。Phase 1（最小限の設定化）から始めることを推奨しますが、プロジェクトの要件に応じてPhase 2やPhase 3まで進めることもできます。

参考ブランチには完全な実装例がありますが、現在のmainブランチの詳細デザインとは異なるため、統合作業が必要です。
