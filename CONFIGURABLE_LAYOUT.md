# レイアウトカスタマイズガイド

このドキュメントでは、レターパックラベル生成ツールのレイアウト設定をカスタマイズする方法を詳しく解説します。

## 目次

- [概要](#概要)
- [クイックスタート](#クイックスタート)
- [設定ファイルのリファレンス](#設定ファイルのリファレンス)
- [カスタマイズ例](#カスタマイズ例)
- [実測値に基づくデフォルト設定](#実測値に基づくデフォルト設定)
- [トラブルシューティング](#トラブルシューティング)
- [技術詳細](#技術詳細)
- [プレビューツールの使い方](#プレビューツールの使い方)

---

## 概要

### レイアウトカスタマイズ機能の目的

レターパックラベル生成ツールは、実際のレターパックの寸法（実測値）に基づいたデフォルトレイアウトを提供していますが、使用する環境や印刷機の特性、個人の好みに応じて、細かくカスタマイズすることができます。

### 対象読者

- **初心者**: 基本的なYAMLファイルの編集ができる方（フォントサイズや色を変更したい方）
- **上級ユーザー**: Pythonコードから設定を動的に変更したい方、レイアウトを詳細にカスタマイズしたい方

### このドキュメントで学べること

- 設定ファイル（`config/label_layout.yaml`）の使い方
- 10個のセクション別の詳細なパラメータ説明
- 実際のユースケース別のカスタマイズ例（6-10例）
- トラブルシューティング方法
- プレビューツールの使い方

---

## クイックスタート

### 基本的な使い方

設定ファイルは `config/label_layout.yaml` にあります。このファイルを編集するか、カスタム設定ファイルを作成してください。

#### CLI版での使用

```bash
# デフォルト設定を使用（config/label_layout.yamlを自動読み込み）
uv run python -m letterpack.cli

# カスタム設定ファイルを指定
uv run python -m letterpack.cli --config custom_config.yaml
```

#### Pythonコードからの使用

```python
from letterpack.label import create_label, AddressInfo

to_address = AddressInfo(
    postal_code="100-0001",
    address1="東京都千代田区千代田 1-1",
    name="山田 太郎",
    phone="03-1234-5678",
    honorific="様"
)

from_address = AddressInfo(
    postal_code="530-0001",
    address1="大阪府大阪市北区梅田 1-1-1",
    name="田中 花子",
    phone="06-9876-5432"
)

# カスタム設定ファイルを使用
create_label(
    to_address,
    from_address,
    "output.pdf",
    config_path="custom_config.yaml"
)

# または、辞書で設定を渡す
config_dict = {
    "fonts": {"name": 16, "address": 13},
    "layout": {"draw_border": False}
}
create_label(
    to_address,
    from_address,
    "output.pdf",
    config_dict=config_dict
)
```

### よくあるカスタマイズパターン

#### パターン1: フォントサイズを全体的に大きくする

```yaml
fonts:
  name: 16      # デフォルト: 14pt
  address: 13   # デフォルト: 11pt
  phone: 15     # デフォルト: 13pt
```

#### パターン2: デバッグ用枠線を非表示にする（本番環境向け）

```yaml
layout:
  draw_border: false
```

#### パターン3: 4upレイアウトで一括印刷

```yaml
layout:
  layout_mode: grid_4up  # デフォルト: center
```

#### パターン4: カスタムカラースキーム（点線を青系に変更）

```yaml
dotted_line:
  color_r: 0.3  # デフォルト: 0.5 (グレー)
  color_g: 0.3
  color_b: 0.8  # 青っぽい点線
```

#### パターン5: ご依頼主セクションのフォントを大きくする

```yaml
section_heights:
  from_section_font_scale: 0.8  # デフォルト: 0.7 (70%)
  from_address_font_size_adjust: 3  # デフォルト: 2pt
```

---

## 設定ファイルのリファレンス

### 1. Layout Settings（レイアウト設定）

ラベルの基本的な寸法とレイアウトモードを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `label_width` | 105 | mm | 90-120mm | ラベルの幅 |
| `label_height` | 122 | mm | 100-150mm | ラベルの高さ（実測値ベース、枠外側） |
| `margin_top` | 7 | mm | 3-15mm | セクション上部マージン |
| `margin_left` | 5 | mm | 2-10mm | セクション左右マージン |
| `draw_border` | true | - | - | デバッグ用枠線を表示するかどうか |
| `layout_mode` | center | - | center/grid_4up | 配置モード（center=中央配置、grid_4up=4丁付） |

#### 注意事項

- `label_height` は `to_section_height + from_section_height` と一致させる必要があります
- 本番環境では `draw_border: false` を推奨（枠線が印刷されないようにするため）

#### 例

```yaml
layout:
  label_width: 105
  label_height: 122
  margin_top: 7
  margin_left: 5
  draw_border: true  # 本番環境ではfalseに変更
  layout_mode: center
```

---

### 2. Font Sizes（フォントサイズ）

各要素のフォントサイズを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `label` | 9 | pt | 7-12pt | フィールドラベル（「お届け先」「ご依頼主」など） |
| `postal_code` | 13 | pt | 10-16pt | 郵便番号 |
| `address` | 11 | pt | 9-14pt | 住所 |
| `name` | 14 | pt | 12-18pt | 氏名 |
| `honorific` | null | pt | 10-16pt | 敬称（nullの場合は名前-2pt） |
| `phone` | 13 | pt | 10-16pt | 電話番号 |

#### 注意事項

- `honorific` を `null` に設定すると、自動的に `name` のフォントサイズより2pt小さくなります
- フォントサイズを大きくしすぎると、文字がセクションからはみ出る可能性があります

#### 例

```yaml
fonts:
  label: 9
  postal_code: 13
  address: 11
  name: 14
  honorific: null  # 名前より2pt小さい（12pt）
  phone: 13
```

---

### 3. Spacing（スペーシング）

要素間の間隔を設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `section_spacing` | 15 | px | 10-25px | セクション内の基本スペーシング |
| `address_line_height` | 18 | px | 12-25px | 住所の行間 |
| `address_name_gap` | 27 | px | 15-40px | 住所と名前の間隔 |
| `name_phone_gap` | 36 | px | 20-50px | 名前と電話番号の間隔 |
| `postal_box_offset_x` | 15 | px | 0-30px | 郵便番号ボックスの水平オフセット |
| `postal_box_offset_y` | -2 | px | -10 to 10px | 郵便番号ボックスの垂直オフセット |
| `dotted_line_text_offset` | 4 | px | 2-10px | 点線からテキストまでのオフセット |

#### 注意事項

- `postal_box_offset_y` は負の値で上に移動、正の値で下に移動します
- スペーシングを大きくしすぎると、セクション内に収まらなくなる可能性があります

#### 例

```yaml
spacing:
  section_spacing: 15
  address_line_height: 18
  address_name_gap: 27
  name_phone_gap: 36
  postal_box_offset_x: 15
  postal_box_offset_y: -2
  dotted_line_text_offset: 4
```

---

### 4. Postal Box（郵便番号ボックス）

郵便番号ボックスのスタイルを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `box_size` | 5 | mm | 4-8mm | ボックスのサイズ（正方形） |
| `box_spacing` | 1 | mm | 0.5-2mm | ボックス間の間隔 |
| `line_width` | 0.5 | pt | 0.3-1.5pt | 枠線の太さ |
| `text_vertical_offset` | 2 | pt | 0-5pt | 数字の垂直オフセット（数字を下に移動） |

#### 注意事項

- `box_size` を大きくしすぎると、郵便番号全体がラベルからはみ出る可能性があります
- `text_vertical_offset` は数字をボックス内で垂直方向に調整します（正の値で下に移動）

#### 例

```yaml
postal_box:
  box_size: 5
  box_spacing: 1
  line_width: 0.5
  text_vertical_offset: 2
```

---

### 5. Address Layout（住所レイアウト）

住所の表示ルールを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `max_length` | 35 | 文字 | 25-50文字 | 1行の最大文字数 |
| `max_lines` | 3 | 行 | 2-5行 | 最大行数（お届け先） |

#### 注意事項

- `max_lines` は「お届け先」セクションの最大行数です
- 「ご依頼主」セクションの最大行数は `section_heights.from_address_max_lines` で設定します（後述）

#### 例

```yaml
address:
  max_length: 35
  max_lines: 3
```

---

### 6. Dotted Line（点線）

点線のスタイルを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `dash_length` | 2 | mm | 1-5mm | ダッシュの長さ |
| `dash_spacing` | 2 | mm | 1-5mm | ダッシュ間の間隔 |
| `color_r` | 0.5 | 0-1 | 0-1 | RGB値のR成分（赤） |
| `color_g` | 0.5 | 0-1 | 0-1 | RGB値のG成分（緑） |
| `color_b` | 0.5 | 0-1 | 0-1 | RGB値のB成分（青） |

#### 注意事項

- RGB値は0-1の範囲で指定します（0=最も暗い、1=最も明るい）
- デフォルト（0.5, 0.5, 0.5）はグレーです

#### RGB値の例

- グレー: `(0.5, 0.5, 0.5)`
- 黒: `(0.0, 0.0, 0.0)`
- 青系: `(0.3, 0.3, 0.8)`
- 薄いグレー: `(0.7, 0.7, 0.7)`

#### 例

```yaml
dotted_line:
  dash_length: 2
  dash_spacing: 2
  color_r: 0.5
  color_g: 0.5
  color_b: 0.5
```

---

### 7. Sama（「様」設定）

敬称（「様」など）の配置を設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `width` | 8 | mm | 5-15mm | 「様」用のスペース |
| `offset` | 2 | mm | 0-5mm | 点線からのオフセット |

#### 注意事項

- 敬称が指定された場合のみ、点線が短くなってスペースが確保されます
- `width` を大きくしすぎると、名前の入力スペースが狭くなります

#### 例

```yaml
sama:
  width: 8
  offset: 2
```

---

### 8. Border（枠線）

デバッグ用枠線のスタイルを設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `color_r` | 0.8 | 0-1 | 0-1 | RGB値のR成分（赤） |
| `color_g` | 0.8 | 0-1 | 0-1 | RGB値のG成分（緑） |
| `color_b` | 0.8 | 0-1 | 0-1 | RGB値のB成分（青） |
| `line_width` | 0.5 | pt | 0.3-2pt | 枠線の太さ |

#### 注意事項

- 枠線は `layout.draw_border` が `true` の場合のみ表示されます
- 本番環境では `layout.draw_border: false` を推奨します

#### 例

```yaml
border:
  color_r: 0.8
  color_g: 0.8
  color_b: 0.8
  line_width: 0.5
```

---

### 9. Phone（電話番号）

電話番号の配置を設定します。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `offset_x` | 30 | px | 0-50px | 電話番号の水平オフセット |

#### 注意事項

- `offset_x` は電話番号を左からどれだけオフセットするかを指定します

#### 例

```yaml
phone:
  offset_x: 30
```

---

### 10. Section Heights（セクション高さ）

お届け先とご依頼主セクションの高さと、ご依頼主セクション専用のフォント設定を行います。

| パラメータ | デフォルト値 | 単位 | 推奨範囲 | 説明 |
|----------|------------|-----|---------|-----|
| `to_section_height` | 69 | mm | 60-80mm | お届け先セクションの高さ（実測値68mm） |
| `from_section_height` | 53 | mm | 40-70mm | ご依頼主セクションの高さ（実測値52mm） |
| `divider_line_width` | 1 | mm | 0.5-3mm | 区切り線の太さ（実測値1mm） |
| `from_section_font_scale` | 0.7 | - | 0.5-1.0 | ご依頼主セクションのフォントスケール（1.0=100%） |
| `from_address_max_lines` | 2 | 行 | 1-3行 | ご依頼主の住所最大行数 |
| `from_address_name_gap` | 9 | px | 5-20px | ご依頼主の住所と名前の間隔 |
| `from_name_phone_gap` | 12 | px | 5-25px | ご依頼主の名前と電話番号の間隔 |
| `from_address_font_size_adjust` | 2 | pt | -5 to 5pt | ご依頼主の住所フォントサイズ調整（+pt） |

#### 注意事項

- **重要**: `to_section_height + from_section_height` は `layout.label_height` と一致させる必要があります
  - 例: `69mm + 53mm = 122mm`（デフォルト設定）
- `from_section_font_scale` は1.0以下を推奨（ご依頼主セクションは小さく表示するため）
- `from_address_font_size_adjust` は、住所フォントサイズに加算されます（例: `address=11pt` なら `11+2=13pt`）

#### 相互関係があるパラメータ

1. **セクション高さの合計**:
   ```yaml
   layout:
     label_height: 122  # 必須: この値と下記の合計を一致させる
   section_heights:
     to_section_height: 69  # お届け先
     from_section_height: 53  # ご依頼主
     # 合計: 69 + 53 = 122mm
   ```

2. **ご依頼主セクションのフォント調整**:
   ```yaml
   fonts:
     address: 11  # ベースの住所フォントサイズ
   section_heights:
     from_section_font_scale: 0.7  # 70%スケール
     from_address_font_size_adjust: 2  # +2pt
     # 最終的なフォントサイズ: (11 + 2) * 0.7 = 9.1pt
   ```

#### 例

```yaml
section_heights:
  to_section_height: 69
  from_section_height: 53
  divider_line_width: 1
  from_section_font_scale: 0.7
  from_address_max_lines: 2
  from_address_name_gap: 9
  from_name_phone_gap: 12
  from_address_font_size_adjust: 2
```

---

## カスタマイズ例

### 例1: 小さいフォントで情報量を増やす

住所が長い場合や、より多くの情報を詰め込みたい場合に有効です。

```yaml
fonts:
  name: 12         # デフォルト: 14pt
  address: 9       # デフォルト: 11pt
  phone: 11        # デフォルト: 13pt
  postal_code: 11  # デフォルト: 13pt

spacing:
  address_line_height: 15  # デフォルト: 18px
  address_name_gap: 20     # デフォルト: 27px
  name_phone_gap: 28       # デフォルト: 36px
```

---

### 例2: 大きいフォントで読みやすく

高齢者や視力が弱い方向けに、フォントサイズを大きくします。

```yaml
fonts:
  name: 18         # デフォルト: 14pt
  address: 14      # デフォルト: 11pt
  phone: 16        # デフォルト: 13pt
  postal_code: 16  # デフォルト: 13pt

spacing:
  address_line_height: 22  # デフォルト: 18px
  address_name_gap: 32     # デフォルト: 27px
  name_phone_gap: 42       # デフォルト: 36px
```

---

### 例3: デバッグ用設定（開発環境）

開発時は枠線を表示し、レイアウトの確認をしやすくします。

```yaml
layout:
  draw_border: true  # 枠線を表示

border:
  color_r: 1.0       # 赤い枠線で目立たせる
  color_g: 0.0
  color_b: 0.0
  line_width: 1.0    # 太めの枠線

dotted_line:
  color_r: 0.0       # 青い点線でデバッグしやすく
  color_g: 0.0
  color_b: 1.0
```

---

### 例4: 本番環境用設定

本番環境では枠線を非表示にし、落ち着いた色合いにします。

```yaml
layout:
  draw_border: false  # 枠線を非表示

dotted_line:
  color_r: 0.5  # グレーの点線（デフォルト）
  color_g: 0.5
  color_b: 0.5
```

---

### 例5: 4upレイアウトで一括印刷

CSVファイルから複数のラベルを生成する際に、4upレイアウト（A4用紙に4枚配置）を使用します。

```yaml
layout:
  layout_mode: grid_4up  # 4upレイアウト（2×2グリッド）
  draw_border: false     # 本番環境では枠線を非表示
```

**CLI版での使用例:**

```bash
# CSVファイルから4upレイアウトで一括生成
uv run python -m letterpack.cli --csv addresses.csv --output labels.pdf --config config_4up.yaml
```

---

### 例6: カスタムカラースキーム（青系）

点線と枠線を青系の色に変更します。

```yaml
dotted_line:
  color_r: 0.3
  color_g: 0.3
  color_b: 0.8  # 青っぽい点線

border:
  color_r: 0.5
  color_g: 0.5
  color_b: 1.0  # 青っぽい枠線
  line_width: 0.5
```

---

### 例7: セクション高さの調整（お届け先を広く）

お届け先セクションを広くして、住所が長い場合に対応します。

```yaml
layout:
  label_height: 130  # 全体の高さを増やす

section_heights:
  to_section_height: 75   # お届け先を広く（デフォルト: 69mm）
  from_section_height: 55  # ご依頼主も調整（デフォルト: 53mm）
  # 合計: 75 + 55 = 130mm（label_heightと一致）
```

---

### 例8: ご依頼主セクションのフォントサイズを調整

ご依頼主セクションのフォントを大きくして、読みやすくします。

```yaml
section_heights:
  from_section_font_scale: 0.85  # デフォルト: 0.7 (70%)
  from_address_font_size_adjust: 3  # デフォルト: 2pt
  from_address_name_gap: 12     # デフォルト: 9px
  from_name_phone_gap: 18       # デフォルト: 12px
```

---

### 例9: 郵便番号ボックスのサイズを調整

郵便番号ボックスを大きくして、見やすくします。

```yaml
postal_box:
  box_size: 6.5       # デフォルト: 5mm
  box_spacing: 1.5    # デフォルト: 1mm
  line_width: 0.8     # デフォルト: 0.5pt
  text_vertical_offset: 3  # デフォルト: 2pt
```

---

### 例10: コンパクトレイアウト（省スペース）

全体的にコンパクトにして、小さいラベルに対応します。

```yaml
layout:
  label_width: 95      # デフォルト: 105mm
  label_height: 110    # デフォルト: 122mm
  margin_top: 5        # デフォルト: 7mm
  margin_left: 3       # デフォルト: 5mm

section_heights:
  to_section_height: 62  # デフォルト: 69mm
  from_section_height: 48  # デフォルト: 53mm
  # 合計: 62 + 48 = 110mm

fonts:
  name: 12         # デフォルト: 14pt
  address: 10      # デフォルト: 11pt
  phone: 11        # デフォルト: 13pt

spacing:
  address_line_height: 15  # デフォルト: 18px
  address_name_gap: 20     # デフォルト: 27px
  name_phone_gap: 28       # デフォルト: 36px
```

---

## 実測値に基づくデフォルト設定

### レターパックの実測値

デフォルト設定は、実際のレターパックの寸法を測定して決定されています。

| 項目 | 実測値 | デフォルト設定 | 説明 |
|-----|-------|-------------|-----|
| ラベル高さ（枠外側） | 122mm | 122mm | ラベル全体の高さ |
| お届け先セクション高さ | 68mm | 69mm | お届け先セクションの高さ（若干余裕を持たせている） |
| ご依頼主セクション高さ | 52mm | 53mm | ご依頼主セクションの高さ（若干余裕を持たせている） |
| 区切り線の太さ | 1mm | 1mm | セクション区切り線の太さ |

### デフォルト設定の根拠

1. **セクション高さ**: 実測値より1mm大きく設定し、印刷時のズレに対応
2. **フォントサイズ**: 実際のレターパックの文字サイズを参考に、読みやすさを優先
3. **スペーシング**: レターパックの余白を参考に、バランスの良い配置を実現

### カスタマイズ時の注意事項

- **セクション高さの合計を必ず一致させる**:
  ```yaml
  layout:
    label_height: 122  # この値と下記の合計を一致させる
  section_heights:
    to_section_height: 69
    from_section_height: 53
    # 合計: 69 + 53 = 122mm
  ```

- **フォントサイズを変更する場合は、スペーシングも調整**:
  - フォントサイズを大きくした場合、行間（`address_line_height`）や要素間の間隔（`address_name_gap`など）も大きくすることを推奨

- **印刷環境による調整**:
  - プリンターによっては、マージンの調整が必要な場合があります
  - 実際に印刷して確認し、必要に応じて `margin_top` や `margin_left` を調整してください

---

## トラブルシューティング

### よくあるエラーとその解決方法

#### エラー1: Pydanticのバリデーションエラー

**エラーメッセージ例:**

```
ValidationError: 1 validation error for LabelLayoutConfig
layout.label_width
  ensure this value is greater than 0 (type=value_error.number.not_gt; limit_value=0)
```

**原因**: 設定値が範囲外の値を指定しています。

**解決方法**:

- エラーメッセージを確認し、該当するパラメータの値を修正
- 推奨範囲を参考に、適切な値を設定

**例:**

```yaml
# 誤った設定
layout:
  label_width: 0  # 0以下はエラー

# 正しい設定
layout:
  label_width: 105  # 推奨範囲: 90-120mm
```

---

#### エラー2: セクション高さの合計が一致しない

**エラーメッセージ例:**

（Pydanticのバリデーションエラーではないため、エラーメッセージは表示されませんが、レイアウトが崩れます）

**原因**: `to_section_height + from_section_height` が `label_height` と一致していません。

**解決方法**:

- 以下のように合計を一致させる:

```yaml
layout:
  label_height: 130  # 全体の高さ

section_heights:
  to_section_height: 75   # お届け先
  from_section_height: 55  # ご依頼主
  # 合計: 75 + 55 = 130mm（label_heightと一致）
```

---

#### エラー3: YAMLフォーマットのミス

**エラーメッセージ例:**

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**原因**: YAMLファイルのインデントや構文が不正です。

**解決方法**:

- インデントは半角スペース2つまたは4つで統一（タブは使用しない）
- キーと値の間にコロン（`:`）を入れる
- 文字列にコロンが含まれる場合は、クォート（`"`）で囲む

**例:**

```yaml
# 誤った設定
fonts:
name: 14  # インデントが不足

# 正しい設定
fonts:
  name: 14
```

---

#### エラー4: データ型のミス

**エラーメッセージ例:**

```
ValidationError: 1 validation error for LabelLayoutConfig
fonts.name
  value is not a valid integer (type=type_error.integer)
```

**原因**: 数値を指定すべきところに文字列を指定しています。

**解決方法**:

- 数値はクォート（`"`）で囲まない
- 文字列はクォート（`"`）で囲む（YAMLでは省略可能な場合もあります）

**例:**

```yaml
# 誤った設定
fonts:
  name: "14"  # クォートで囲むと文字列になる

# 正しい設定
fonts:
  name: 14  # 数値として指定
```

---

#### エラー5: フォントが見つからない（Docker環境推奨）

**エラーメッセージ例:**

```
警告: IPAフォントが見つかりません。HeiseiMin-W3を使用します
```

**原因**: システムに日本語フォントがインストールされていません。

**解決方法**:

1. **Docker環境を使用する（推奨）**:
   ```bash
   docker compose up -d
   ```

2. **IPAフォントをインストールする**（Ubuntu/Debian）:
   ```bash
   sudo apt-get install fonts-ipafont-gothic fonts-ipafont-mincho
   ```

3. **カスタムフォントパスを指定する**:
   ```python
   from letterpack.label import create_label

   create_label(
       to_address,
       from_address,
       "output.pdf",
       font_path="/path/to/your/font.ttf"
   )
   ```

---

## 技術詳細

### Pydanticモデルの仕組み

このプロジェクトでは、レイアウト設定に[Pydantic](https://docs.pydantic.dev/)を使用しています。Pydanticは、Pythonのデータバリデーションライブラリで、型チェックとバリデーションを自動的に行います。

#### 主なPydanticモデル

1. **`LabelLayoutConfig`**: 全体の設定を統合するルートモデル
2. **`LayoutConfig`**: レイアウト設定（`layout`セクション）
3. **`FontsConfig`**: フォントサイズ設定（`fonts`セクション）
4. **`SpacingConfig`**: スペーシング設定（`spacing`セクション）
5. **`PostalBoxConfig`**: 郵便番号ボックス設定（`postal_box`セクション）
6. **`AddressLayoutConfig`**: 住所レイアウト設定（`address`セクション）
7. **`DottedLineConfig`**: 点線設定（`dotted_line`セクション）
8. **`SamaConfig`**: 「様」設定（`sama`セクション）
9. **`BorderConfig`**: 枠線設定（`border`セクション）
10. **`PhoneConfig`**: 電話番号設定（`phone`セクション）
11. **`SectionHeightConfig`**: セクション高さ設定（`section_heights`セクション）

#### Pydanticのバリデーション

Pydanticは、以下のようなバリデーションを自動的に行います：

- **型チェック**: 数値型、文字列型、ブール型など
- **範囲チェック**: `gt`（より大きい）、`ge`（以上）、`le`（以下）など
- **デフォルト値**: パラメータが指定されていない場合のデフォルト値

**例:**

```python
class LayoutConfig(BaseModel):
    label_width: float = Field(default=105, gt=0, le=300, description="ラベルの幅 (mm)")
    label_height: float = Field(
        default=122,
        gt=0,
        le=500,
        description="ラベルの高さ (mm)"
    )
```

この設定により、以下のバリデーションが行われます：

- `label_width` は 0より大きく、300以下でなければならない
- `label_height` は 0より大きく、500以下でなければならない
- デフォルト値は `label_width=105`、`label_height=122`

---

### `load_layout_config()`関数の動作

レイアウト設定を読み込む関数です。YAMLファイルまたは辞書から設定を読み込み、Pydanticモデルに変換します。

#### シグネチャ

```python
def load_layout_config(
    config_path: Optional[str] = None,
    config_dict: Optional[dict] = None
) -> LabelLayoutConfig:
    """
    レイアウト設定をYAMLファイルまたは辞書から読み込む

    Args:
        config_path: 設定ファイルのパス（Noneの場合はデフォルト設定を使用）
        config_dict: 設定辞書（将来的にUI設定やlocalStorageから取得）

    Returns:
        LabelLayoutConfig: レイアウト設定
    """
```

#### 優先順位

1. **`config_dict`（最優先）**: 辞書が渡された場合、辞書から設定を構築
2. **`config_path`**: YAMLファイルパスが渡された場合、ファイルから設定を読み込み
3. **デフォルト設定**: どちらも指定されていない場合、デフォルト設定を使用

#### 使用例

**例1: デフォルト設定を使用**

```python
config = load_layout_config()
```

**例2: YAMLファイルから読み込み**

```python
config = load_layout_config(config_path="custom_config.yaml")
```

**例3: 辞書から読み込み**

```python
config_dict = {
    "fonts": {"name": 16, "address": 13},
    "layout": {"draw_border": False}
}
config = load_layout_config(config_dict=config_dict)
```

**例4: 辞書とファイルの両方を指定（辞書が優先）**

```python
config_dict = {"fonts": {"name": 18}}
config = load_layout_config(
    config_path="custom_config.yaml",  # 無視される
    config_dict=config_dict  # こちらが優先
)
```

---

### 将来的な拡張計画

#### UI設定機能

静的HTML版（Pyodide）で、ブラウザ上でレイアウト設定を変更できる機能を追加予定です。

**想定される仕組み:**

1. **設定UI**: ブラウザでスライダーやテキストボックスで設定を変更
2. **リアルタイムプレビュー**: 変更がすぐに反映されるプレビュー機能
3. **localStorage保存**: 変更した設定をブラウザのlocalStorageに保存
4. **設定のエクスポート**: YAMLファイルとしてダウンロード可能

#### YAMLファイル読み込み（静的HTML版）

静的HTML版でYAMLファイルを読み込む機能も検討中です。

**実装方法:**

- `fetch()` APIでYAMLファイルを取得
- `js-yaml`ライブラリでYAMLをパース
- Pythonの`load_layout_config()`に渡す

---

## プレビューツールの使い方

レイアウトパラメータをリアルタイムで調整できるFlask WebUIツール（`tools/label_adjuster.py`）が利用可能です。

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

### UIの説明

#### 左側: パラメータ調整フォーム

10個のセクション別にアコーディオンで展開・折りたたみできます：

1. **Layout Settings**: ラベルの幅・高さ、マージン、レイアウトモード
2. **Font Sizes**: 各要素のフォントサイズ
3. **Spacing**: 要素間のスペーシング
4. **Postal Box**: 郵便番号ボックスのスタイル
5. **Address Layout**: 住所の最大文字数・最大行数
6. **Dotted Line**: 点線のスタイル（長さ、間隔、色）
7. **Sama**: 「様」の配置
8. **Border**: 枠線のスタイル
9. **Phone**: 電話番号の配置
10. **Section Heights**: セクション高さとご依頼主セクション専用設定

**操作方法:**

- 各セクションをクリックして展開
- 入力欄で値を変更
- 色はRGB値（0-1の範囲）で指定

#### 右側: PDFプレビューエリア

リアルタイムでPDFプレビューが表示されます。

**操作方法:**

- 「プレビュー更新」ボタンをクリック
- 数秒後、右側にPDFが表示される

### リアルタイムプレビュー機能の仕組み

1. フォームのデータを取得
2. サーバーに送信（POST `/preview`）
3. サーバーでPDFを生成（ReportLab）
4. Base64エンコードしたPDFを返す
5. ブラウザでPDFを表示（`<embed>` タグ）

### 設定の保存

調整した設定をYAMLファイルとして保存できます。

**操作方法:**

1. 「設定を保存」ボタンをクリック
2. `config/label_layout_custom_YYYYMMDD_HHMMSS.yaml` として保存される
3. CLI版やPythonコードから使用可能

**保存されたファイルの使用例:**

```bash
# CLI版で使用
uv run python -m letterpack.cli --config config/label_layout_custom_20250115_123456.yaml
```

### デフォルトに戻す

「デフォルトに戻す」ボタンをクリックすると、`config/label_layout.yaml` の設定が読み込まれます。

### サンプルデータ

プレビュー生成時には、以下のサンプルデータが使用されます：

**お届け先:**

- 郵便番号: 100-0001
- 住所: 東京都千代田区千代田 1-1
- 名前: 山田 太郎
- 電話番号: 03-1234-5678
- 敬称: 様

**ご依頼主:**

- 郵便番号: 530-0001
- 住所: 大阪府大阪市北区梅田 1-1-1
- 名前: 田中 花子
- 電話番号: 06-9876-5432
- 敬称: （なし）

### 技術スタック

- **Flask**: Webフレームワーク（ポート5001）
- **Bootstrap 5**: UIフレームワーク（アコーディオン、ボタンなど）
- **ReportLab**: PDF生成
- **PyYAML**: YAML設定ファイル処理

### エンドポイント

| エンドポイント | メソッド | 説明 |
|------------|--------|-----|
| `/` | GET | パラメータ調整フォームを表示 |
| `/preview` | POST | フォームデータからPDFを生成して返す（Base64） |
| `/save` | POST | フォームデータをYAMLファイルとして保存 |
| `/reset` | GET | デフォルト設定を返す（JSON） |

### 注意事項

- **ポート5001を使用**: Webサーバー版（`letterpack.web`）のポート5000と競合しません
- **デバッグモード**: 開発用のため、本番環境での使用は避けてください
- **書き込み権限**: `config/` ディレクトリに書き込み権限が必要です

---

## まとめ

このガイドを参考に、レターパックラベルのレイアウトを自由にカスタマイズできます。

### クイックリファレンス

| カスタマイズ内容 | 該当セクション | 推奨例 |
|--------------|-------------|-------|
| フォントサイズを大きく | `fonts` | `name: 18`, `address: 14` |
| 本番環境向け設定 | `layout` | `draw_border: false` |
| 4upレイアウト | `layout` | `layout_mode: grid_4up` |
| 点線の色を変更 | `dotted_line` | `color_r: 0.3`, `color_g: 0.3`, `color_b: 0.8` |
| セクション高さを調整 | `section_heights` | `to_section_height: 75`, `from_section_height: 55` |

### 次のステップ

1. **プレビューツールで試す**: `python tools/label_adjuster.py` で起動
2. **設定ファイルを編集**: `config/label_layout.yaml` を直接編集
3. **CLI版で確認**: `uv run python -m letterpack.cli --config custom_config.yaml`
4. **本番環境にデプロイ**: Docker環境または静的HTML版で使用

### 参考リンク

- [README.md](README.md) - プロジェクト全体のドキュメント
- [tools/README.md](tools/README.md) - プレビューツールの詳細
- [config/label_layout.yaml](config/label_layout.yaml) - デフォルト設定ファイル
- [DOCKER.md](DOCKER.md) - Docker環境での実行方法
- [STATIC_VERSION.md](STATIC_VERSION.md) - 静的HTML版の技術詳細

---

ご質問やフィードバックがあれば、お気軽にIssueを作成してください。

Happy customizing!
