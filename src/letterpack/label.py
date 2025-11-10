"""
レターパックラベル生成のコアロジック
"""

import os
from dataclasses import dataclass
from typing import Optional

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
    phone: str  # 電話番号

    def __post_init__(self):
        """バリデーション"""
        if not self.postal_code:
            raise ValueError("郵便番号は必須です")
        if not self.address:
            raise ValueError("住所は必須です")
        if not self.name:
            raise ValueError("氏名は必須です")
        if not self.phone:
            raise ValueError("電話番号は必須です")


class LabelGenerator:
    """レターパックラベルPDF生成クラス"""

    def __init__(self, font_path: Optional[str] = None):
        """
        Args:
            font_path: 日本語フォントのパス（Noneの場合はシステムフォントを試行）
        """
        self.font_name = "IPAGothic"  # デフォルトフォント（_setup_fontで設定される）
        self.font_path = font_path
        self._setup_font()

    def _setup_font(self):
        """フォント設定"""
        if self.font_path and os.path.exists(self.font_path):
            # カスタムフォントを登録
            try:
                pdfmetrics.registerFont(TTFont("CustomFont", self.font_path))
                self.font_name = "CustomFont"
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

        for font_path in ipa_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("IPAGothic", font_path))
                    self.font_name = "IPAGothic"
                    return
                except Exception as e:
                    print(f"警告: IPAGothic ({font_path}) の登録に失敗しました: {e}")
                    continue

        # フォールバック: ReportLabのCJKフォント
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
            self.font_name = "HeiseiMin-W3"
            print(
                "警告: IPAフォントが見つかりません。HeiseiMin-W3を使用します（一部の文字が表示されない可能性があります）"
            )
        except Exception as e:
            print(f"警告: HeiseiMin-W3の登録に失敗しました: {e}")
            # 最終フォールバック: HeiseiKakuGo-W5を試す
            try:
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
                self.font_name = "HeiseiKakuGo-W5"
                print(
                    "警告: HeiseiKakuGo-W5を使用します（一部の文字が表示されない可能性があります）"
                )
            except Exception as e2:
                print(f"警告: HeiseiKakuGo-W5の登録にも失敗しました: {e2}")
                # 最終フォールバック: Helvetica（日本語は表示できないが動作する）
                self.font_name = "Helvetica"
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

        # A5サイズのラベルをA4の中央に配置
        # A5 = 148mm x 210mm
        label_width = 148 * mm
        label_height = 210 * mm

        # 中央配置のためのオフセット計算
        x_offset = (width - label_width) / 2
        y_offset = (height - label_height) / 2

        # 枠線（デバッグ用 - 本番では不要かもしれません）
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.rect(x_offset, y_offset, label_width, label_height)

        # ラベルを上下2分割（お届け先が上、ご依頼主が下）
        section_height = label_height / 2

        # 区切り線
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

        c.save()
        return output_path

    def _draw_postal_boxes(self, c: canvas.Canvas, postal_code: str, x: float, y: float):
        """
        郵便番号を7つのボックスで描画

        Args:
            c: Canvas オブジェクト
            postal_code: 郵便番号（例: "123-4567"）
            x, y: 開始座標
        """
        # ハイフンを除去して数字のみ抽出
        digits = postal_code.replace("-", "").replace("〒", "").strip()

        # ボックスのサイズ
        box_size = 5 * mm
        box_spacing = 1 * mm

        # 7つのボックスを描画
        for i in range(7):
            box_x = x + i * (box_size + box_spacing)
            # ボックスの枠
            c.rect(box_x, y, box_size, box_size)

            # 数字を中央に描画
            if i < len(digits):
                c.setFont(self.font_name, 10)
                # 文字を中央揃え
                text_width = c.stringWidth(digits[i], self.font_name, 10)
                text_x = box_x + (box_size - text_width) / 2
                text_y = y + (box_size - 10) / 2
                c.drawString(text_x, text_y, digits[i])

    def _draw_dotted_line(self, c: canvas.Canvas, x1: float, y: float, x2: float):
        """
        点線を描画

        Args:
            c: Canvas オブジェクト
            x1: 開始x座標
            y: y座標
            x2: 終了x座標
        """
        c.setDash(2, 2)  # 点線パターン（2mm線、2mm空白）
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
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
        margin = 8 * mm
        current_y = y + height - margin

        # フィールドラベルのフォントサイズ
        label_font_size = 9

        # おところ: / Address
        c.setFont(self.font_name, label_font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + margin, current_y, "おところ:")
        c.setFont("Helvetica", label_font_size)
        c.drawString(x + margin + 35, current_y, "Address")

        current_y -= 15

        # 郵便番号ボックス
        c.setFont(self.font_name, 10)
        c.setFillColorRGB(0, 0, 0)
        self._draw_postal_boxes(c, address.postal_code, x + margin + 15, current_y - 5)

        current_y -= 15

        # 住所記入エリア（複数行の点線）
        address_lines = self._split_address(address.address, max_length=35)
        for i, line in enumerate(address_lines[:3]):  # 最大3行
            if i == 0:
                # 1行目は少し上に
                self._draw_dotted_line(c, x + margin, current_y, x + width - margin)
                c.setFont(self.font_name, 11)
                c.drawString(x + margin + 2, current_y + 2, line)
                current_y -= 12
            else:
                self._draw_dotted_line(c, x + margin, current_y, x + width - margin)
                c.setFont(self.font_name, 11)
                c.drawString(x + margin + 2, current_y + 2, line)
                current_y -= 12

        # 追加の点線（空欄）
        for _ in range(3 - len(address_lines)):
            self._draw_dotted_line(c, x + margin, current_y, x + width - margin)
            current_y -= 12

        current_y -= 8

        # おなまえ: / Name
        c.setFont(self.font_name, label_font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + margin, current_y, "おなまえ:")
        c.setFont("Helvetica", label_font_size)
        c.drawString(x + margin + 40, current_y, "Name")

        current_y -= 15

        # 名前記入エリア（点線を短くして「様」のスペースを確保）
        sama_width = 8 * mm  # 「様」用のスペース
        name_line_end = x + width - margin - sama_width
        self._draw_dotted_line(c, x + margin, current_y, name_line_end)

        # 名前を描画
        c.setFont(self.font_name, 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + margin + 2, current_y + 2, address.name)

        # 「様」を点線の右側に表示
        c.setFont(self.font_name, 14)
        c.setFillColorRGB(0, 0, 0)
        sama_x = name_line_end + 2 * mm  # 点線の終点から2mm右
        c.drawString(sama_x, current_y + 2, "様")

        current_y -= 18

        # 電話番号: / Telephone Number
        c.setFont(self.font_name, label_font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + margin, current_y, "電話番号:")
        c.setFont("Helvetica", label_font_size)
        c.drawString(x + margin + 42, current_y, "Telephone Number")

        current_y -= 15

        # 電話番号記入エリア（括弧付き）
        c.setFont(self.font_name, 11)
        c.setFillColorRGB(0, 0, 0)
        phone_text = f"( {address.phone} )"
        c.drawString(x + margin + 30, current_y, phone_text)

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


def create_label(
    to_address: AddressInfo,
    from_address: AddressInfo,
    output_path: str = "label.pdf",
    font_path: Optional[str] = None,
) -> str:
    """
    ラベルPDFを生成する便利関数

    Args:
        to_address: お届け先情報
        from_address: ご依頼主情報
        output_path: 出力PDFファイルパス
        font_path: 日本語フォントのパス

    Returns:
        生成されたPDFファイルのパス
    """
    generator = LabelGenerator(font_path=font_path)
    return generator.generate(to_address, from_address, output_path)
