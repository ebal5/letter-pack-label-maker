"""
レターパックラベル生成のコアロジック
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def load_layout_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """
    レイアウト設定ファイルを読み込む

    Args:
        config_path: 設定ファイルのパス（Noneの場合はデフォルト）

    Returns:
        設定辞書
    """
    if config_path is None:
        # デフォルトパス: プロジェクトルート/config/label_layout.yaml
        current_dir = Path(__file__).parent
        config_path = current_dir / ".." / ".." / "config" / "label_layout.yaml"

    config_path = Path(config_path).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


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

    def __init__(self, font_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Args:
            font_path: 日本語フォントのパス（Noneの場合はシステムフォントを試行）
            config_path: レイアウト設定ファイルのパス（Noneの場合はデフォルト）
        """
        self.font_name = "HeiseiKakuGo-W5"  # デフォルトフォント
        self.font_path = font_path
        self.config = load_layout_config(config_path)
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

        # デフォルトフォント: ReportLabのCJKフォントを登録
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
            self.font_name = "HeiseiKakuGo-W5"
        except Exception as e:
            print(f"警告: HeiseiKakuGo-W5の登録に失敗しました: {e}")
            # フォールバック: Helvetica（日本語は表示できないが動作する）
            self.font_name = "Helvetica"

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

        # 設定からレイアウト情報を取得
        layout = self.config["layout"]
        label_width = layout["label_width"] * mm
        label_height = layout["label_height"] * mm

        # 中央配置のためのオフセット計算
        if layout["x_offset"] == "auto":
            x_offset = (width - label_width) / 2
        else:
            x_offset = layout["x_offset"] * mm

        if layout["y_offset"] == "auto":
            y_offset = (height - label_height) / 2
        else:
            y_offset = layout["y_offset"] * mm

        # 枠線（デバッグ用）
        if layout.get("draw_border", True):
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
        layout = self.config["layout"]
        fonts = self.config["fonts"]
        spacing = self.config["spacing"]

        margin = layout["margin"] * mm

        # セクションラベル
        c.setFont(self.font_name, fonts["section_label"])
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(x + margin, y + height - margin - spacing["section_label_offset"], label)

        # 郵便番号
        c.setFont(self.font_name, fonts["postal_code"])
        c.setFillColorRGB(0, 0, 0)
        postal_y = y + height - margin - spacing["postal_offset"]
        c.drawString(x + margin, postal_y, f"〒 {address.postal_code}")

        # 住所（複数行対応）
        address_lines = self._split_address(address.address)
        address_y = postal_y - spacing["address_offset"]
        c.setFont(self.font_name, fonts["address"])
        for line in address_lines:
            c.drawString(x + margin, address_y, line)
            address_y -= spacing["address_line_height"]

        # 氏名
        name_y = address_y - spacing["name_offset"]
        c.setFont(self.font_name, fonts["name"])
        c.drawString(x + margin, name_y, address.name)

        # 電話番号（右下）
        c.setFont(self.font_name, fonts["phone"])
        c.setFillColorRGB(0.3, 0.3, 0.3)
        phone_margin = spacing["phone_margin"] * mm
        c.drawRightString(x + width - margin, y + phone_margin, f"TEL: {address.phone}")

    def _split_address(self, address: str, max_length: Optional[int] = None) -> list[str]:
        """
        住所を適切な長さで分割

        Args:
            address: 住所文字列
            max_length: 1行の最大文字数（Noneの場合は設定から取得）

        Returns:
            分割された住所のリスト
        """
        if max_length is None:
            max_length = self.config["address"]["max_length"]

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
    config_path: Optional[str] = None,
) -> str:
    """
    ラベルPDFを生成する便利関数

    Args:
        to_address: お届け先情報
        from_address: ご依頼主情報
        output_path: 出力PDFファイルパス
        font_path: 日本語フォントのパス
        config_path: レイアウト設定ファイルのパス

    Returns:
        生成されたPDFファイルのパス
    """
    generator = LabelGenerator(font_path=font_path, config_path=config_path)
    return generator.generate(to_address, from_address, output_path)
