## 設定リファレンス（Configuration Reference）

このセクションは `tools/generate_config_docs.py` によって自動生成されています。

レイアウト設定のカスタマイズ方法については、[CONFIGURABLE_LAYOUT.md](./CONFIGURABLE_LAYOUT.md) を参照してください。

### Layout Settings（レイアウト設定）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `layout.label_width` | float | 105 | ラベルの幅 (mm) | 0 < x ≤ 300 |
| `layout.label_height` | float | 122 | ラベルの高さ (mm)。実測値122mm（枠外側）に基づく。セクション高さの合計と一致させること | 0 < x ≤ 500 |
| `layout.margin_top` | float | 7 | セクション内の上部マージン (mm) | 0 ≤ x ≤ 50 |
| `layout.margin_left` | float | 5 | セクション内の左右マージン (mm) | 0 ≤ x ≤ 50 |
| `layout.draw_border` | bool | true | デバッグ用の枠線を描画するか | - |
| `layout.layout_mode` | Literal | "center" | レイアウトモード: center=中央配置, grid_4up=4丁付 | - |

### Font Sizes（フォントサイズ）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `fonts.label` | int | 9 | フィールドラベルのフォントサイズ (pt) | 0 < x ≤ 72 |
| `fonts.postal_code` | int | 13 | 郵便番号のフォントサイズ (pt) | 0 < x ≤ 72 |
| `fonts.address` | int | 11 | 住所のフォントサイズ (pt) | 0 < x ≤ 72 |
| `fonts.name` | int | 14 | 氏名のフォントサイズ (pt) | 0 < x ≤ 72 |
| `fonts.honorific` | int | None | null | 敬称のフォントサイズ (pt)。Noneの場合は名前より2pt小さい | 0 < x ≤ 72 |
| `fonts.phone` | int | 13 | 電話番号のフォントサイズ (pt) | 0 < x ≤ 72 |

### Spacing（スペーシング）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `spacing.section_spacing` | int | 15 | セクション間の間隔 (px) | 0 ≤ x ≤ 100 |
| `spacing.address_line_height` | int | 18 | 住所の行間 (px) | 0 ≤ x ≤ 100 |
| `spacing.address_name_gap` | int | 27 | 住所と名前セクションの間隔 (px) | 0 ≤ x ≤ 100 |
| `spacing.name_phone_gap` | int | 36 | 名前と電話番号セクションの間隔 (px) | 0 ≤ x ≤ 100 |
| `spacing.postal_box_offset_x` | int | 15 | 郵便番号ボックスのX軸オフセット (px) | -100 ≤ x ≤ 100 |
| `spacing.postal_box_offset_y` | int | -2 | 郵便番号ボックスのY軸オフセット (px) | -100 ≤ x ≤ 100 |
| `spacing.dotted_line_text_offset` | int | 4 | 点線からテキストまでのオフセット (px) | 0 ≤ x ≤ 50 |

### Postal Box（郵便番号ボックス）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `postal_box.box_size` | float | 5 | ボックスのサイズ (mm) | 0 < x ≤ 20 |
| `postal_box.box_spacing` | float | 1 | ボックス間の間隔 (mm) | 0 ≤ x ≤ 10 |
| `postal_box.line_width` | float | 0.5 | 枠線の太さ (pt) | 0 < x ≤ 5 |
| `postal_box.text_vertical_offset` | float | 2 | 数字の垂直オフセット (pt) | -10 ≤ x ≤ 10 |

### Address Layout（住所レイアウト）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `address.max_length` | int | 35 | 1行の最大文字数 | 0 < x ≤ 100 |
| `address.max_lines` | int | 3 | 最大行数 | 0 < x ≤ 10 |

### Dotted Line（点線）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `dotted_line.dash_length` | float | 2 | 線の長さ (mm) | 0 < x ≤ 10 |
| `dotted_line.dash_spacing` | float | 2 | 線の間隔 (mm) | 0 < x ≤ 10 |
| `dotted_line.color_r` | float | 0.5 | RGB の R 値 | 0 ≤ x ≤ 1 |
| `dotted_line.color_g` | float | 0.5 | RGB の G 値 | 0 ≤ x ≤ 1 |
| `dotted_line.color_b` | float | 0.5 | RGB の B 値 | 0 ≤ x ≤ 1 |

### Sama（「様」設定）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `sama.width` | float | 8 | 「様」用のスペース (mm) | 0 < x ≤ 50 |
| `sama.offset` | float | 2 | 点線からのオフセット (mm) | 0 ≤ x ≤ 20 |

### Border（枠線）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `border.color_r` | float | 0.8 | RGB の R 値 | 0 ≤ x ≤ 1 |
| `border.color_g` | float | 0.8 | RGB の G 値 | 0 ≤ x ≤ 1 |
| `border.color_b` | float | 0.8 | RGB の B 値 | 0 ≤ x ≤ 1 |
| `border.line_width` | float | 0.5 | 線の幅 | 0 < x ≤ 10 |

### Phone（電話番号）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `phone.offset_x` | int | 30 | 電話番号の左からのオフセット (px) | 0 ≤ x ≤ 200 |

### Section Heights（セクション高さ）

| パラメータ | 型 | デフォルト | 説明 | 範囲 |
|-----------|-----|-----------|------|------|
| `section_height.to_section_height` | float | 69 | お届け先セクションの高さ (mm) | 0 < x ≤ 200 |
| `section_height.from_section_height` | float | 53 | ご依頼主セクションの高さ (mm) | 0 < x ≤ 200 |
| `section_height.divider_line_width` | float | 2.5 | 区切り線の太さ (pt) | 0 < x ≤ 10 |
| `section_height.from_section_font_scale` | float | 0.7 | ご依頼主セクションのフォントサイズスケール（1.0=100%） | 0 < x ≤ 1 |
| `section_height.from_address_max_lines` | int | 2 | ご依頼主セクションの住所の最大行数 | 0 < x ≤ 10 |
| `section_height.from_address_name_gap` | int | 9 | ご依頼主セクションの住所と名前の間隔 (px) | 0 ≤ x ≤ 100 |
| `section_height.from_name_phone_gap` | int | 12 | ご依頼主セクションの名前と電話番号の間隔 (px) | 0 ≤ x ≤ 100 |
| `section_height.from_address_font_size_adjust` | int | 2 | ご依頼主セクションの住所フォントサイズ調整 (+pt) | 0 ≤ x ≤ 10 |

