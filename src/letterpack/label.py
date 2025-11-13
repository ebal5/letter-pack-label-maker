"""
レターパックラベル生成のコアロジック
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


@dataclass
class AddressInfo:
    """住所情報を保持するデータクラス"""

    postal_code: str  # 郵便番号（例: "123-4567"）
    address: str  # 住所
    name: str  # 氏名
    phone: Optional[str] = None  # 電話番号
    honorific: Optional[str] = None  # 敬称（Noneまたは空文字列で敬称なし）

    def __post_init__(self):
        """バリデーション"""
        if not self.postal_code:
            raise ValueError("郵便番号は必須です")
        if not self.address:
            raise ValueError("住所は必須です")
        if not self.name:
            raise ValueError("氏名は必須です")


# レイアウト設定のPydanticモデル


class LayoutConfig(BaseModel):
    """ラベルの基本寸法設定"""

    label_width: float = Field(default=105, gt=0, le=300, description="ラベルの幅 (mm)")
    label_height: float = Field(default=148, gt=0, le=500, description="ラベルの高さ (mm)")
    margin: float = Field(default=8, ge=0, le=50, description="セクション内のマージン (mm)")
    draw_border: bool = Field(default=True, description="デバッグ用の枠線を描画するか")
    layout_mode: Literal["center", "grid_4up"] = Field(
        default="center", description="レイアウトモード: center=中央配置, grid_4up=4丁付"
    )


class FontsConfig(BaseModel):
    """フォントサイズ設定"""

    label: int = Field(default=9, gt=0, le=72, description="フィールドラベルのフォントサイズ (pt)")
    postal_code: int = Field(default=13, gt=0, le=72, description="郵便番号のフォントサイズ (pt)")
    address: int = Field(default=11, gt=0, le=72, description="住所のフォントサイズ (pt)")
    name: int = Field(default=14, gt=0, le=72, description="氏名のフォントサイズ (pt)")
    honorific: Optional[int] = Field(
        default=None,
        gt=0,
        le=72,
        description="敬称のフォントサイズ (pt)。Noneの場合は名前より2pt小さい",
    )
    phone: int = Field(default=13, gt=0, le=72, description="電話番号のフォントサイズ (pt)")


class SpacingConfig(BaseModel):
    """要素間のスペーシング設定"""

    section_spacing: int = Field(default=15, ge=0, le=100, description="セクション間の間隔 (px)")
    address_line_height: int = Field(default=18, ge=0, le=100, description="住所の行間 (px)")
    address_name_gap: int = Field(
        default=27, ge=0, le=100, description="住所と名前セクションの間隔 (px)"
    )
    name_phone_gap: int = Field(
        default=36, ge=0, le=100, description="名前と電話番号セクションの間隔 (px)"
    )
    postal_box_offset_x: int = Field(
        default=15, ge=-100, le=100, description="郵便番号ボックスのX軸オフセット (px)"
    )
    postal_box_offset_y: int = Field(
        default=-2, ge=-100, le=100, description="郵便番号ボックスのY軸オフセット (px)"
    )
    dotted_line_text_offset: int = Field(
        default=4, ge=0, le=50, description="点線からテキストまでのオフセット (px)"
    )


class PostalBoxConfig(BaseModel):
    """郵便番号ボックス設定"""

    box_size: float = Field(default=5, gt=0, le=20, description="ボックスのサイズ (mm)")
    box_spacing: float = Field(default=1, ge=0, le=10, description="ボックス間の間隔 (mm)")
    line_width: float = Field(default=0.5, gt=0, le=5, description="枠線の太さ (pt)")
    text_vertical_offset: float = Field(
        default=2, ge=-10, le=10, description="数字の垂直オフセット (pt)"
    )


class AddressLayoutConfig(BaseModel):
    """住所レイアウト設定"""

    max_length: int = Field(default=35, gt=0, le=100, description="1行の最大文字数")
    max_lines: int = Field(default=3, gt=0, le=10, description="最大行数")


class DottedLineConfig(BaseModel):
    """点線スタイル設定"""

    dash_length: float = Field(default=2, gt=0, le=10, description="線の長さ (mm)")
    dash_spacing: float = Field(default=2, gt=0, le=10, description="線の間隔 (mm)")
    color_r: float = Field(default=0.5, ge=0, le=1, description="RGB の R 値")
    color_g: float = Field(default=0.5, ge=0, le=1, description="RGB の G 値")
    color_b: float = Field(default=0.5, ge=0, le=1, description="RGB の B 値")


class SamaConfig(BaseModel):
    """「様」の配置設定"""

    width: float = Field(default=8, gt=0, le=50, description="「様」用のスペース (mm)")
    offset: float = Field(default=2, ge=0, le=20, description="点線からのオフセット (mm)")


class BorderConfig(BaseModel):
    """枠線スタイル設定（デバッグ用）"""

    color_r: float = Field(default=0.8, ge=0, le=1, description="RGB の R 値")
    color_g: float = Field(default=0.8, ge=0, le=1, description="RGB の G 値")
    color_b: float = Field(default=0.8, ge=0, le=1, description="RGB の B 値")
    line_width: float = Field(default=0.5, gt=0, le=10, description="線の幅")


class PhoneConfig(BaseModel):
    """電話番号の配置設定"""

    offset_x: int = Field(default=30, ge=0, le=200, description="電話番号の左からのオフセット (px)")


class LabelLayoutConfig(BaseModel):
    """レターパックラベルのレイアウト全体設定"""

    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    fonts: FontsConfig = Field(default_factory=FontsConfig)
    spacing: SpacingConfig = Field(default_factory=SpacingConfig)
    postal_box: PostalBoxConfig = Field(default_factory=PostalBoxConfig)
    address: AddressLayoutConfig = Field(default_factory=AddressLayoutConfig)
    dotted_line: DottedLineConfig = Field(default_factory=DottedLineConfig)
    sama: SamaConfig = Field(default_factory=SamaConfig)
    border: BorderConfig = Field(default_factory=BorderConfig)
    phone: PhoneConfig = Field(default_factory=PhoneConfig)


def load_layout_config(config_path: Optional[str] = None) -> LabelLayoutConfig:
    """
    レイアウト設定をYAMLファイルから読み込む

    Args:
        config_path: 設定ファイルのパス（Noneの場合はデフォルト設定を使用）

    Returns:
        LabelLayoutConfig: レイアウト設定

    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
        ValueError: 設定ファイルの形式が不正な場合
    """
    if config_path is None:
        # デフォルト設定を使用
        return LabelLayoutConfig()

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    try:
        with open(config_file, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            # 空のYAMLファイルの場合はデフォルト設定を使用
            return LabelLayoutConfig()

        return LabelLayoutConfig(**config_data)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML形式が不正です: {e}") from e
    except Exception as e:
        raise ValueError(f"設定ファイルの読み込みに失敗しました: {e}") from e


class LabelGenerator:
    """レターパックラベルPDF生成クラス"""

    def __init__(self, font_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Args:
            font_path: 日本語フォントのパス（Noneの場合はシステムフォントを試行）
            config_path: レイアウト設定ファイルのパス（Noneの場合はデフォルト設定を使用）
        """
        self.font_name = "IPAGothic"  # デフォルトフォント（_setup_fontで設定される）
        self.font_path = font_path
        self.config = load_layout_config(config_path)
        self._setup_font()

    def _setup_font(self):
        """フォント設定"""
        # 太字フォントのデフォルト（後で上書きされる可能性あり）
        self.bold_font_name = None

        if self.font_path and os.path.exists(self.font_path):
            # カスタムフォントを登録
            try:
                pdfmetrics.registerFont(TTFont("CustomFont", self.font_path))
                self.font_name = "CustomFont"
                self.bold_font_name = "CustomFont"  # 太字版がない場合は通常フォントを使用
                return
            except Exception as e:
                print(f"警告: カスタムフォントの読み込みに失敗しました: {e}")
                print("デフォルトフォントを使用します")

        # デフォルトフォント: IPAフォント（完全な日本語サポート）
        # システムにインストールされている日本語フォントを探す
        ipa_font_paths = [
            "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/usr/share/fonts/truetype/ipafont/ipag.ttf",
        ]

        # IPAGothic太字版のパス
        ipa_bold_font_paths = [
            "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
            "/usr/share/fonts/truetype/ipafont/ipagp.ttf",
        ]

        for font_path in ipa_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("IPAGothic", font_path))
                    self.font_name = "IPAGothic"
                    # 太字フォントも探す
                    for bold_font_path in ipa_bold_font_paths:
                        if os.path.exists(bold_font_path):
                            try:
                                pdfmetrics.registerFont(TTFont("IPAGothicBold", bold_font_path))
                                self.bold_font_name = "IPAGothicBold"
                                break
                            except Exception:
                                continue
                    # 太字フォントが見つからない場合は通常フォントを使用
                    if not self.bold_font_name:
                        self.bold_font_name = "IPAGothic"
                    return
                except Exception as e:
                    print(f"警告: IPAGothic ({font_path}) の登録に失敗しました: {e}")
                    continue

        # フォールバック: ReportLabのCJKフォント
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
            self.font_name = "HeiseiMin-W3"
            self.bold_font_name = "HeiseiMin-W3"
            print(
                "警告: IPAフォントが見つかりません。HeiseiMin-W3を使用します（一部の文字が表示されない可能性があります）"
            )
        except Exception as e:
            print(f"警告: HeiseiMin-W3の登録に失敗しました: {e}")
            # 最終フォールバック: HeiseiKakuGo-W5を試す
            try:
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
                self.font_name = "HeiseiKakuGo-W5"
                self.bold_font_name = "HeiseiKakuGo-W5"
                print(
                    "警告: HeiseiKakuGo-W5を使用します（一部の文字が表示されない可能性があります）"
                )
            except Exception as e2:
                print(f"警告: HeiseiKakuGo-W5の登録にも失敗しました: {e2}")
                # 最終フォールバック: Helvetica（日本語は表示できないが動作する）
                self.font_name = "Helvetica"
                self.bold_font_name = "Helvetica-Bold"
                print("警告: 日本語フォントが利用できません。Helveticaを使用します")

    def generate(self, to_address: AddressInfo, from_address: AddressInfo, output_path: str) -> str:
        """
        ラベルPDFを生成

        Args:
            to_address: お届け先情報
            from_address: ご依頼主情報
            output_path: 出力PDFファイルパス

        Returns:
            生成されたPDFファイルのパス
        """
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        # 設定からラベルサイズを取得
        label_width = self.config.layout.label_width * mm
        label_height = self.config.layout.label_height * mm

        # レイアウトモードに応じて処理を分岐
        if self.config.layout.layout_mode == "grid_4up":
            # 4丁付レイアウト（2×2グリッド）
            positions = [
                (0, height / 2),  # 左上
                (width / 2, height / 2),  # 右上
                (0, 0),  # 左下
                (width / 2, 0),  # 右下
            ]
            for x_offset, y_offset in positions:
                self._draw_single_label(
                    c, to_address, from_address, x_offset, y_offset, label_width, label_height
                )
        else:
            # 中央配置レイアウト（デフォルト）
            x_offset = (width - label_width) / 2
            y_offset = (height - label_height) / 2
            self._draw_single_label(
                c, to_address, from_address, x_offset, y_offset, label_width, label_height
            )

        c.save()
        return output_path

    def _draw_single_label(
        self,
        c: canvas.Canvas,
        to_address: AddressInfo,
        from_address: AddressInfo,
        x_offset: float,
        y_offset: float,
        label_width: float,
        label_height: float,
    ):
        """
        1つのラベルを描画

        Args:
            c: Canvas オブジェクト
            to_address: お届け先情報
            from_address: ご依頼主情報
            x_offset: X座標のオフセット
            y_offset: Y座標のオフセット
            label_width: ラベルの幅
            label_height: ラベルの高さ
        """
        # 枠線（デバッグ用）
        if self.config.layout.draw_border:
            c.setStrokeColorRGB(
                self.config.border.color_r,
                self.config.border.color_g,
                self.config.border.color_b,
            )
            c.setLineWidth(self.config.border.line_width)
            c.rect(x_offset, y_offset, label_width, label_height)

        # ラベルを上下2分割（お届け先が上、ご依頼主が下）
        section_height = label_height / 2

        # 区切り線
        c.setStrokeColorRGB(0, 0, 0)  # 黒に戻す
        c.setLineWidth(1)
        c.line(
            x_offset, y_offset + section_height, x_offset + label_width, y_offset + section_height
        )

        # お届け先（上半分）
        self._draw_address_section(
            c,
            to_address,
            x_offset,
            y_offset + section_height,
            label_width,
            section_height,
            "お届け先",
        )

        # ご依頼主（下半分）
        self._draw_address_section(
            c, from_address, x_offset, y_offset, label_width, section_height, "ご依頼主"
        )

    def _draw_postal_boxes(self, c: canvas.Canvas, postal_code: str, x: float, y: float):
        """
        郵便番号を3-4の区切り形式で描画

        Args:
            c: Canvas オブジェクト
            postal_code: 郵便番号（例: "123-4567"）
            x, y: 開始座標
        """
        # ハイフンを除去して数字のみ抽出
        digits = postal_code.replace("-", "").replace("〒", "").strip()

        # 設定からボックスのサイズと枠線の太さを取得
        box_size = self.config.postal_box.box_size * mm
        box_spacing = self.config.postal_box.box_spacing * mm
        box_line_width = self.config.postal_box.line_width
        text_vertical_offset = self.config.postal_box.text_vertical_offset
        postal_font_size = self.config.fonts.postal_code

        # 太字フォントを使用（利用可能な場合）
        bold_font_name = getattr(self, "bold_font_name", self.font_name)

        # 枠線の太さを設定
        c.setLineWidth(box_line_width)

        # 最初の3つのボックスを描画
        for i in range(3):
            box_x = x + i * (box_size + box_spacing)
            # ボックスの枠
            c.rect(box_x, y, box_size, box_size)

            # 数字を中央に描画（垂直オフセット付き）
            if i < len(digits):
                c.setFont(bold_font_name, postal_font_size)
                # 文字を中央揃え
                text_width = c.stringWidth(digits[i], bold_font_name, postal_font_size)
                text_x = box_x + (box_size - text_width) / 2
                text_y = y + (box_size - postal_font_size) / 2 + text_vertical_offset
                c.drawString(text_x, text_y, digits[i])

        # 区切り線（ハイフン）を描画
        separator_x = x + 3 * (box_size + box_spacing)
        separator_y = y + box_size / 2
        separator_width = box_spacing * 1.5  # ハイフンの長さ
        c.setLineWidth(box_line_width)
        c.line(separator_x, separator_y, separator_x + separator_width, separator_y)

        # 残りの4つのボックスを描画
        offset_x = separator_x + separator_width + box_spacing
        for i in range(4):
            box_x = offset_x + i * (box_size + box_spacing)
            # ボックスの枠
            c.rect(box_x, y, box_size, box_size)

            # 数字を中央に描画（垂直オフセット付き）
            digit_index = i + 3
            if digit_index < len(digits):
                c.setFont(bold_font_name, postal_font_size)
                # 文字を中央揃え
                text_width = c.stringWidth(digits[digit_index], bold_font_name, postal_font_size)
                text_x = box_x + (box_size - text_width) / 2
                text_y = y + (box_size - postal_font_size) / 2 + text_vertical_offset
                c.drawString(text_x, text_y, digits[digit_index])

        # 線の太さをリセット
        c.setLineWidth(1)

    def _draw_dotted_line(self, c: canvas.Canvas, x1: float, y: float, x2: float):
        """
        点線を描画

        Args:
            c: Canvas オブジェクト
            x1: 開始x座標
            y: y座標
            x2: 終了x座標
        """
        # 設定から点線スタイルを取得
        c.setDash(self.config.dotted_line.dash_length, self.config.dotted_line.dash_spacing)
        c.setStrokeColorRGB(
            self.config.dotted_line.color_r,
            self.config.dotted_line.color_g,
            self.config.dotted_line.color_b,
        )
        c.line(x1, y, x2, y)
        c.setDash()  # 点線をリセット（実線に戻す）
        c.setStrokeColorRGB(0, 0, 0)  # 線の色を黒に戻す

    def _draw_address_section(
        self,
        c: canvas.Canvas,
        address: AddressInfo,
        x: float,
        y: float,
        width: float,
        height: float,
        label: str,
    ):
        """
        住所セクションを描画

        Args:
            c: Canvas オブジェクト
            address: 住所情報
            x, y: 左下の座標
            width, height: セクションのサイズ
            label: セクションラベル（"お届け先" or "ご依頼主"）
        """
        # 設定から値を取得
        margin = self.config.layout.margin * mm
        current_y = y + height - margin

        label_font_size = self.config.fonts.label
        address_font_size = self.config.fonts.address
        name_font_size = self.config.fonts.name
        phone_font_size = self.config.fonts.phone

        section_spacing = self.config.spacing.section_spacing
        address_line_height = self.config.spacing.address_line_height
        address_name_gap = self.config.spacing.address_name_gap
        name_phone_gap = self.config.spacing.name_phone_gap
        postal_box_offset_x = self.config.spacing.postal_box_offset_x
        postal_box_offset_y = self.config.spacing.postal_box_offset_y
        dotted_line_text_offset = self.config.spacing.dotted_line_text_offset

        # 郵便番号（〒記号付き）
        c.setFont(self.font_name, label_font_size)
        c.setFillColorRGB(0, 0, 0)
        postal_y = current_y  # 〒記号の位置を記録
        c.drawString(x + margin, postal_y, "〒")

        # 郵便番号ボックス（〒記号と同じ高さに配置）
        c.setFont(self.font_name, self.config.fonts.postal_code)
        c.setFillColorRGB(0, 0, 0)
        self._draw_postal_boxes(
            c,
            address.postal_code,
            x + margin + postal_box_offset_x,
            postal_y + postal_box_offset_y,
        )

        current_y -= section_spacing

        current_y -= section_spacing

        # 住所記入エリア（複数行の点線）
        address_lines = self._split_address(
            address.address, max_length=self.config.address.max_length
        )
        for line in address_lines[: self.config.address.max_lines]:
            self._draw_dotted_line(c, x + margin, current_y, x + width - margin)
            c.setFont(self.font_name, address_font_size)
            c.drawString(
                x + margin + dotted_line_text_offset, current_y + dotted_line_text_offset, line
            )
            current_y -= address_line_height

        # 追加の点線（空欄）
        for _ in range(self.config.address.max_lines - len(address_lines)):
            self._draw_dotted_line(c, x + margin, current_y, x + width - margin)
            current_y -= address_line_height

        current_y -= address_name_gap

        # 名前記入エリア（敬称がある場合は点線を短くしてスペースを確保）
        honorific = address.honorific if address.honorific else ""
        if honorific:
            sama_width = self.config.sama.width * mm
            name_line_end = x + width - margin - sama_width
        else:
            name_line_end = x + width - margin

        self._draw_dotted_line(c, x + margin, current_y, name_line_end)

        # 名前を描画
        c.setFont(self.font_name, name_font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(
            x + margin + dotted_line_text_offset, current_y + dotted_line_text_offset, address.name
        )

        # 敬称を点線の右側に表示（敬称が指定されている場合のみ）
        if honorific:
            # 敬称のフォントサイズを取得（Noneの場合は名前より2pt小さい）
            honorific_font_size = (
                self.config.fonts.honorific
                if self.config.fonts.honorific is not None
                else max(name_font_size - 2, 1)
            )
            c.setFont(self.font_name, honorific_font_size)
            c.setFillColorRGB(0, 0, 0)
            sama_x = name_line_end + self.config.sama.offset * mm
            c.drawString(sama_x, current_y + dotted_line_text_offset, honorific)

        current_y -= name_phone_gap

        # Tel.（電話番号がある場合のみ描画）
        if address.phone:
            c.setFont(self.font_name, label_font_size)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x + margin, current_y, "Tel.")

            current_y -= section_spacing

            # 電話番号記入エリア（括弧付き）
            c.setFont(self.font_name, phone_font_size)
            c.setFillColorRGB(0, 0, 0)
            phone_text = f"( {address.phone} )"
            c.drawString(x + margin + self.config.phone.offset_x, current_y, phone_text)

    def _split_address(self, address: str, max_length: int = 30) -> list[str]:
        """
        住所を適切な長さで分割

        Args:
            address: 住所文字列
            max_length: 1行の最大文字数

        Returns:
            分割された住所のリスト
        """
        if len(address) <= max_length:
            return [address]

        lines = []
        current_line = ""

        for char in address:
            if len(current_line) >= max_length:
                lines.append(current_line)
                current_line = char
            else:
                current_line += char

        if current_line:
            lines.append(current_line)

        return lines

    def generate_batch(
        self, label_pairs: list[tuple[AddressInfo, AddressInfo]], output_path: str
    ) -> str:
        """
        複数のラベルを4upレイアウトで複数ページのPDFとして生成

        Args:
            label_pairs: (お届け先, ご依頼主) のタプルのリスト
            output_path: 出力PDFファイルパス

        Returns:
            生成されたPDFファイルのパス
        """
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        label_width = self.config.layout.label_width * mm
        label_height = self.config.layout.label_height * mm

        # 4upレイアウトの位置定義
        positions = [
            (0, height / 2),  # 左上
            (width / 2, height / 2),  # 右上
            (0, 0),  # 左下
            (width / 2, 0),  # 右下
        ]

        # 4件ごとにページを作成
        for page_start in range(0, len(label_pairs), 4):
            # 1ページ分のラベル（最大4件）
            page_labels = label_pairs[page_start : page_start + 4]

            # 各位置にラベルを配置
            for i, (to_addr, from_addr) in enumerate(page_labels):
                x_offset, y_offset = positions[i]
                self._draw_single_label(
                    c, to_addr, from_addr, x_offset, y_offset, label_width, label_height
                )

            # ページを確定
            c.showPage()

        c.save()
        return output_path


def create_label(
    to_address: AddressInfo,
    from_address: AddressInfo,
    output_path: str = "label.pdf",
    font_path: Optional[str] = None,
    config_path: Optional[str] = None,
) -> str:
    """
    ラベルPDFを生成する便利関数

    Args:
        to_address: お届け先情報
        from_address: ご依頼主情報
        output_path: 出力PDFファイルパス
        font_path: 日本語フォントのパス
        config_path: レイアウト設定ファイルのパス（Noneの場合はデフォルト設定を使用）

    Returns:
        生成されたPDFファイルのパス
    """
    generator = LabelGenerator(font_path=font_path, config_path=config_path)
    return generator.generate(to_address, from_address, output_path)


def create_label_batch(
    label_pairs: list[tuple[AddressInfo, AddressInfo]],
    output_path: str = "labels.pdf",
    font_path: Optional[str] = None,
    config_path: Optional[str] = None,
) -> str:
    """
    複数のラベルを4upレイアウトで1つのPDF（複数ページ）に生成する便利関数

    Args:
        label_pairs: (お届け先, ご依頼主) のタプルのリスト
        output_path: 出力PDFファイルパス
        font_path: 日本語フォントのパス
        config_path: レイアウト設定ファイルのパス（Noneの場合はデフォルト設定を使用）

    Returns:
        生成されたPDFファイルのパス
    """
    generator = LabelGenerator(font_path=font_path, config_path=config_path)
    return generator.generate_batch(label_pairs, output_path)
