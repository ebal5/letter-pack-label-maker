"""
レイアウトパラメータ調整用Flask WebUIツール

リアルタイムでレイアウト設定を調整し、PDFプレビューを確認できます。
"""

import io
from datetime import datetime
from pathlib import Path

import yaml
from flask import Flask, jsonify, render_template, request, send_file

from letterpack.label import AddressInfo, LabelLayoutConfig, create_label, load_layout_config

app = Flask(__name__)

# デフォルト設定のパス
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "label_layout.yaml"

# サンプルデータ
SAMPLE_TO = AddressInfo(
    postal_code="100-0001",
    address1="東京都千代田区千代田",
    address2="1-1",
    address3="",
    name="山田 太郎",
    phone="03-1234-5678",
)

SAMPLE_FROM = AddressInfo(
    postal_code="530-0001",
    address1="大阪府大阪市北区梅田",
    address2="1-1-1",
    address3="",
    name="田中 花子",
    phone="06-9876-5432",
)


@app.route("/")
def index():
    """パラメータ調整フォームを表示"""
    # デフォルト設定が存在すれば読み込み、なければデフォルト値を使用
    if DEFAULT_CONFIG_PATH.exists():
        config = load_layout_config(str(DEFAULT_CONFIG_PATH))
    else:
        config = LabelLayoutConfig()

    return render_template("label_adjuster.html", config=config)


@app.route("/preview", methods=["POST"])
def preview():
    """フォームデータからPDFを生成"""
    # フォームデータを辞書に変換
    config_dict = form_to_config_dict(request.form)

    # PDFを生成
    pdf_buffer = io.BytesIO()
    create_label(SAMPLE_TO, SAMPLE_FROM, pdf_buffer, config_dict=config_dict)
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, mimetype="application/pdf")


@app.route("/save", methods=["POST"])
def save():
    """設定をYAMLファイルとして保存"""
    try:
        config_dict = form_to_config_dict(request.form)

        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            Path(__file__).parent.parent / "config" / f"label_layout_custom_{timestamp}.yaml"
        )

        # ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # YAMLファイルに保存
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

        return jsonify({"success": True, "path": str(output_path)})
    except OSError as e:
        return jsonify({"success": False, "error": f"ファイル保存エラー: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"予期しないエラー: {str(e)}"}), 500


@app.route("/reset")
def reset():
    """デフォルト設定に戻す"""
    if DEFAULT_CONFIG_PATH.exists():
        config = load_layout_config(str(DEFAULT_CONFIG_PATH))
    else:
        config = LabelLayoutConfig()
    return jsonify(config_to_dict(config))


def safe_float(value, default):
    """
    安全にfloat型に変換

    Args:
        value: 変換する値
        default: デフォルト値

    Returns:
        float: 変換された値、または変換失敗時はデフォルト値
    """
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default):
    """
    安全にint型に変換

    Args:
        value: 変換する値
        default: デフォルト値

    Returns:
        int: 変換された値、または変換失敗時はデフォルト値
    """
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def form_to_config_dict(form):
    """
    フォームデータを設定辞書に変換

    Args:
        form: Flask request.form オブジェクト

    Returns:
        dict: LabelLayoutConfig用の辞書
    """
    # フォームデータをパース
    config_dict = {
        "layout": {
            "label_width": safe_float(form.get("layout_label_width"), 105),
            "label_height": safe_float(form.get("layout_label_height"), 122),
            "margin_top": safe_float(form.get("layout_margin_top"), 7),
            "margin_left": safe_float(form.get("layout_margin_left"), 5),
            "draw_border": form.get("layout_draw_border") == "true",
            "layout_mode": form.get("layout_layout_mode", "center"),
        },
        "fonts": {
            "label": safe_int(form.get("fonts_label"), 9),
            "postal_code": safe_int(form.get("fonts_postal_code"), 13),
            "address": safe_int(form.get("fonts_address"), 11),
            "name": safe_int(form.get("fonts_name"), 14),
            "honorific": (
                safe_int(form.get("fonts_honorific"), None) if form.get("fonts_honorific") else None
            ),
            "phone": safe_int(form.get("fonts_phone"), 13),
        },
        "spacing": {
            "section_spacing": safe_int(form.get("spacing_section_spacing"), 15),
            "address_line_height": safe_int(form.get("spacing_address_line_height"), 18),
            "address_name_gap": safe_int(form.get("spacing_address_name_gap"), 27),
            "name_phone_gap": safe_int(form.get("spacing_name_phone_gap"), 36),
            "postal_box_offset_x": safe_int(form.get("spacing_postal_box_offset_x"), 15),
            "postal_box_offset_y": safe_int(form.get("spacing_postal_box_offset_y"), -2),
            "dotted_line_text_offset": safe_int(form.get("spacing_dotted_line_text_offset"), 4),
        },
        "postal_box": {
            "box_size": safe_float(form.get("postal_box_box_size"), 5),
            "box_spacing": safe_float(form.get("postal_box_box_spacing"), 1),
            "line_width": safe_float(form.get("postal_box_line_width"), 0.5),
            "text_vertical_offset": safe_float(form.get("postal_box_text_vertical_offset"), 2),
        },
        "address": {
            "max_length": safe_int(form.get("address_max_length"), 35),
            "max_lines": safe_int(form.get("address_max_lines"), 3),
        },
        "dotted_line": {
            "dash_length": safe_float(form.get("dotted_line_dash_length"), 2),
            "dash_spacing": safe_float(form.get("dotted_line_dash_spacing"), 2),
            "color_r": safe_float(form.get("dotted_line_color_r"), 0.5),
            "color_g": safe_float(form.get("dotted_line_color_g"), 0.5),
            "color_b": safe_float(form.get("dotted_line_color_b"), 0.5),
        },
        "sama": {
            "width": safe_float(form.get("sama_width"), 8),
            "offset": safe_float(form.get("sama_offset"), 2),
        },
        "border": {
            "color_r": safe_float(form.get("border_color_r"), 0.8),
            "color_g": safe_float(form.get("border_color_g"), 0.8),
            "color_b": safe_float(form.get("border_color_b"), 0.8),
            "line_width": safe_float(form.get("border_line_width"), 0.5),
        },
        "phone": {
            "offset_x": safe_int(form.get("phone_offset_x"), 30),
        },
        "section_height": {
            "to_section_height": safe_float(form.get("section_height_to_section_height"), 69),
            "from_section_height": safe_float(form.get("section_height_from_section_height"), 53),
            "divider_line_width": safe_float(form.get("section_height_divider_line_width"), 1),
            "from_section_font_scale": safe_float(
                form.get("section_height_from_section_font_scale"), 0.7
            ),
            "from_address_max_lines": safe_int(
                form.get("section_height_from_address_max_lines"), 2
            ),
            "from_address_name_gap": safe_int(form.get("section_height_from_address_name_gap"), 9),
            "from_name_phone_gap": safe_int(form.get("section_height_from_name_phone_gap"), 12),
            "from_address_font_size_adjust": safe_int(
                form.get("section_height_from_address_font_size_adjust"), 2
            ),
        },
    }

    return config_dict


def config_to_dict(config: LabelLayoutConfig) -> dict:
    """
    LabelLayoutConfigオブジェクトを辞書に変換

    Args:
        config: LabelLayoutConfig オブジェクト

    Returns:
        dict: フロントエンドで使用できる辞書形式
    """
    return {
        "layout": {
            "label_width": config.layout.label_width,
            "label_height": config.layout.label_height,
            "margin_top": config.layout.margin_top,
            "margin_left": config.layout.margin_left,
            "draw_border": config.layout.draw_border,
            "layout_mode": config.layout.layout_mode,
        },
        "fonts": {
            "label": config.fonts.label,
            "postal_code": config.fonts.postal_code,
            "address": config.fonts.address,
            "name": config.fonts.name,
            "honorific": config.fonts.honorific,
            "phone": config.fonts.phone,
        },
        "spacing": {
            "section_spacing": config.spacing.section_spacing,
            "address_line_height": config.spacing.address_line_height,
            "address_name_gap": config.spacing.address_name_gap,
            "name_phone_gap": config.spacing.name_phone_gap,
            "postal_box_offset_x": config.spacing.postal_box_offset_x,
            "postal_box_offset_y": config.spacing.postal_box_offset_y,
            "dotted_line_text_offset": config.spacing.dotted_line_text_offset,
        },
        "postal_box": {
            "box_size": config.postal_box.box_size,
            "box_spacing": config.postal_box.box_spacing,
            "line_width": config.postal_box.line_width,
            "text_vertical_offset": config.postal_box.text_vertical_offset,
        },
        "address": {
            "max_length": config.address.max_length,
            "max_lines": config.address.max_lines,
        },
        "dotted_line": {
            "dash_length": config.dotted_line.dash_length,
            "dash_spacing": config.dotted_line.dash_spacing,
            "color_r": config.dotted_line.color_r,
            "color_g": config.dotted_line.color_g,
            "color_b": config.dotted_line.color_b,
        },
        "sama": {
            "width": config.sama.width,
            "offset": config.sama.offset,
        },
        "border": {
            "color_r": config.border.color_r,
            "color_g": config.border.color_g,
            "color_b": config.border.color_b,
            "line_width": config.border.line_width,
        },
        "phone": {
            "offset_x": config.phone.offset_x,
        },
        "section_height": {
            "to_section_height": config.section_height.to_section_height,
            "from_section_height": config.section_height.from_section_height,
            "divider_line_width": config.section_height.divider_line_width,
            "from_section_font_scale": config.section_height.from_section_font_scale,
            "from_address_max_lines": config.section_height.from_address_max_lines,
            "from_address_name_gap": config.section_height.from_address_name_gap,
            "from_name_phone_gap": config.section_height.from_name_phone_gap,
            "from_address_font_size_adjust": config.section_height.from_address_font_size_adjust,
        },
    }


def main():
    """アプリケーションを起動"""
    import os

    # 環境変数でデバッグモードを制御（デフォルトはFalse）
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print("=" * 60)
    print("レイアウト調整ツール起動中...")
    print(f"デフォルト設定ファイル: {DEFAULT_CONFIG_PATH}")
    print(f"デバッグモード: {debug_mode}")
    print("=" * 60)
    print("\nブラウザで以下のURLを開いてください:")
    print("  http://localhost:5001")
    print("\n終了するには Ctrl+C を押してください")
    print("=" * 60)

    app.run(debug=debug_mode, port=5001)


if __name__ == "__main__":
    main()
