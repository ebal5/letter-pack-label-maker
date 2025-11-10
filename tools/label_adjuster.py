#!/usr/bin/env python3
"""
レターパックラベルのレイアウト調整ツール

リアルタイムプレビュー付きで設定を調整できるWebインターフェース
"""

import base64
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import yaml
from flask import Flask, flash, jsonify, redirect, render_template_string, request, url_for

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from letterpack.label import AddressInfo, create_label  # noqa: E402

app = Flask(__name__)
app.secret_key = "label-adjuster-secret-key"

# 設定ファイルのパス
CONFIG_PATH = project_root / "config" / "label_layout.yaml"

# サンプルデータ
SAMPLE_TO = AddressInfo(
    postal_code="123-4567",
    address="東京都渋谷区サンプル町1-2-3 サンプルビル4F",
    name="山田 太郎",
    phone="03-1234-5678",
)

SAMPLE_FROM = AddressInfo(
    postal_code="987-6543",
    address="大阪府大阪市テスト区テスト町4-5-6",
    name="田中 花子",
    phone="06-9876-5432",
)


# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>レターパックラベル調整ツール</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 14px;
        }
        .main-content {
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 20px;
            align-items: start;
        }
        .settings-panel {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 20px;
            max-height: calc(100vh - 40px);
            overflow-y: auto;
        }
        .preview-panel {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-height: 600px;
        }
        .section {
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 1px solid #eee;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section h2 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #333;
            font-weight: 600;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            color: #555;
            font-size: 13px;
            font-weight: 500;
        }
        input[type="number"],
        input[type="text"],
        select {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.3s;
        }
        input[type="number"]:focus,
        input[type="text"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        input[type="checkbox"] {
            margin-right: 8px;
        }
        .checkbox-label {
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        .btn-container {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        button.secondary {
            background: #6c757d;
        }
        #preview-image {
            width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .alert {
            padding: 12px 16px;
            margin-bottom: 20px;
            border-radius: 6px;
            font-size: 13px;
        }
        .alert-error {
            background: #fee;
            color: #c33;
            border-left: 4px solid #c33;
        }
        .alert-success {
            background: #efe;
            color: #3c3;
            border-left: 4px solid #3c3;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .input-unit {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .input-unit input {
            flex: 1;
        }
        .input-unit .unit {
            color: #999;
            font-size: 12px;
            min-width: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔧 レターパックラベル調整ツール</h1>
            <p class="subtitle">設定を調整してリアルタイムでプレビュー表示</p>
        </header>

        <div class="main-content">
            <div class="settings-panel">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <form id="settings-form" method="POST" action="{{ url_for('update_preview') }}">
                    <div class="section">
                        <h2>📐 ラベル寸法</h2>
                        <div class="form-group">
                            <label>ラベル幅</label>
                            <div class="input-unit">
                                <input type="number" name="layout.label_width"
                                       value="{{ config.layout.label_width }}" step="1" required>
                                <span class="unit">mm</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>ラベル高さ</label>
                            <div class="input-unit">
                                <input type="number" name="layout.label_height"
                                       value="{{ config.layout.label_height }}" step="1" required>
                                <span class="unit">mm</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>マージン</label>
                            <div class="input-unit">
                                <input type="number" name="layout.margin"
                                       value="{{ config.layout.margin }}" step="0.5" required>
                                <span class="unit">mm</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" name="layout.draw_border"
                                       {% if config.layout.draw_border %}checked{% endif %}>
                                デバッグ用枠線を表示
                            </label>
                        </div>
                    </div>

                    <div class="section">
                        <h2>🔤 フォントサイズ</h2>
                        <div class="form-group">
                            <label>セクションラベル（お届け先/ご依頼主）</label>
                            <div class="input-unit">
                                <input type="number" name="fonts.section_label"
                                       value="{{ config.fonts.section_label }}" step="1" required>
                                <span class="unit">pt</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>郵便番号</label>
                            <div class="input-unit">
                                <input type="number" name="fonts.postal_code"
                                       value="{{ config.fonts.postal_code }}" step="1" required>
                                <span class="unit">pt</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>住所</label>
                            <div class="input-unit">
                                <input type="number" name="fonts.address"
                                       value="{{ config.fonts.address }}" step="1" required>
                                <span class="unit">pt</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>氏名</label>
                            <div class="input-unit">
                                <input type="number" name="fonts.name"
                                       value="{{ config.fonts.name }}" step="1" required>
                                <span class="unit">pt</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>電話番号</label>
                            <div class="input-unit">
                                <input type="number" name="fonts.phone"
                                       value="{{ config.fonts.phone }}" step="1" required>
                                <span class="unit">pt</span>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h2>📏 スペーシング</h2>
                        <div class="form-group">
                            <label>セクションラベルオフセット</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.section_label_offset"
                                       value="{{ config.spacing.section_label_offset }}" step="1" required>
                                <span class="unit">px</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>郵便番号オフセット</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.postal_offset"
                                       value="{{ config.spacing.postal_offset }}" step="1" required>
                                <span class="unit">px</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>住所オフセット</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.address_offset"
                                       value="{{ config.spacing.address_offset }}" step="1" required>
                                <span class="unit">px</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>住所行間</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.address_line_height"
                                       value="{{ config.spacing.address_line_height }}" step="1" required>
                                <span class="unit">px</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>氏名オフセット</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.name_offset"
                                       value="{{ config.spacing.name_offset }}" step="1" required>
                                <span class="unit">px</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>電話番号マージン</label>
                            <div class="input-unit">
                                <input type="number" name="spacing.phone_margin"
                                       value="{{ config.spacing.phone_margin }}" step="0.5" required>
                                <span class="unit">mm</span>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <h2>📝 住所設定</h2>
                        <div class="form-group">
                            <label>1行の最大文字数</label>
                            <div class="input-unit">
                                <input type="number" name="address.max_length"
                                       value="{{ config.address.max_length }}" step="1" required>
                                <span class="unit">文字</span>
                            </div>
                        </div>
                    </div>

                    <div class="btn-container">
                        <button type="button" id="preview-btn">👁️ プレビュー更新</button>
                        <button type="submit" class="secondary">💾 設定を保存</button>
                    </div>
                </form>
            </div>

            <div class="preview-panel">
                <h2 style="margin-bottom: 20px;">プレビュー</h2>
                <div id="preview-container">
                    {% if preview_image %}
                        <img id="preview-image" src="data:image/png;base64,{{ preview_image }}" alt="Label Preview">
                    {% else %}
                        <div class="loading">
                            <p>プレビューを生成するには「プレビュー更新」ボタンをクリックしてください</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('settings-form');
        const previewBtn = document.getElementById('preview-btn');
        const previewContainer = document.getElementById('preview-container');

        previewBtn.addEventListener('click', async () => {
            previewBtn.disabled = true;
            previewBtn.textContent = '⏳ 生成中...';

            previewContainer.innerHTML = '<div class="loading"><p>プレビューを生成中...</p></div>';

            const formData = new FormData(form);

            try {
                const response = await fetch('{{ url_for("preview") }}', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    previewContainer.innerHTML = `<img id="preview-image" src="data:image/png;base64,${data.image}" alt="Label Preview">`;
                } else {
                    previewContainer.innerHTML = `<div class="alert alert-error">エラー: ${data.error}</div>`;
                }
            } catch (error) {
                previewContainer.innerHTML = `<div class="alert alert-error">プレビュー生成に失敗しました: ${error}</div>`;
            } finally {
                previewBtn.disabled = false;
                previewBtn.textContent = '👁️ プレビュー更新';
            }
        });

        // 初回プレビュー生成
        window.addEventListener('load', () => {
            if (!document.getElementById('preview-image')) {
                previewBtn.click();
            }
        });
    </script>
</body>
</html>
"""


def load_config():
    """設定ファイルを読み込む"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config):
    """設定ファイルを保存する"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def form_to_config(form_data):
    """
    フォームデータを設定辞書に変換し、バリデーションを行う

    Args:
        form_data: フォームデータ

    Returns:
        バリデーション済みの設定辞書

    Raises:
        ValueError: バリデーションエラーが発生した場合
    """
    config = {"layout": {}, "fonts": {}, "spacing": {}, "address": {}}

    try:
        for key, value in form_data.items():
            if "." not in key:
                continue

            section, param = key.split(".", 1)

            # チェックボックスの特別処理
            if param == "draw_border":
                config[section][param] = True
                continue

            # 数値変換（エラーチェック付き）
            try:
                if param in ["label_width", "label_height", "margin", "phone_margin"]:
                    config[section][param] = float(value)
                elif param in ["max_length"]:
                    config[section][param] = int(value)
                else:
                    config[section][param] = int(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"'{param}' の値 '{value}' が不正です: {e}") from e

        # チェックボックスがオフの場合の処理
        if "layout.draw_border" not in form_data:
            config["layout"]["draw_border"] = False

        # x_offset と y_offset は常に auto
        config["layout"]["x_offset"] = "auto"
        config["layout"]["y_offset"] = "auto"

        # Pydanticでバリデーション
        from letterpack.label import LabelLayoutConfig

        validated = LabelLayoutConfig(**config)
        return validated.model_dump()

    except Exception as e:
        raise ValueError(f"設定の変換に失敗しました: {e}") from e


def generate_preview_image(config):
    """設定を使ってプレビュー画像を生成"""
    temp_config_path = None
    temp_pdf_path = None

    try:
        # 一時設定ファイルを作成
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f, allow_unicode=True)
            temp_config_path = f.name

        # PDFを生成
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf_path = f.name

        create_label(SAMPLE_TO, SAMPLE_FROM, temp_pdf_path, config_path=temp_config_path)

        # PDFを画像に変換
        doc = fitz.open(temp_pdf_path)
        try:
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("png")
        finally:
            doc.close()

        # Base64エンコード
        img_base64 = base64.b64encode(img_data).decode("utf-8")

        return img_base64

    finally:
        # 一時ファイルを削除
        if temp_config_path:
            Path(temp_config_path).unlink(missing_ok=True)
        if temp_pdf_path:
            Path(temp_pdf_path).unlink(missing_ok=True)


@app.route("/")
def index():
    """トップページ"""
    config = load_config()
    return render_template_string(HTML_TEMPLATE, config=config, preview_image=None)


@app.route("/preview", methods=["POST"])
def preview():
    """プレビュー生成API"""
    try:
        config = form_to_config(request.form)
        img_base64 = generate_preview_image(config)
        return jsonify({"success": True, "image": img_base64})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/update", methods=["POST"])
def update_preview():
    """設定を保存"""
    try:
        config = form_to_config(request.form)
        save_config(config)
        flash("設定を保存しました！", "success")
    except Exception as e:
        flash(f"設定の保存に失敗しました: {e}", "error")

    return redirect(url_for("index"))


def main():
    """メインエントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="レターパックラベル調整ツール")
    parser.add_argument("--host", default="127.0.0.1", help="ホスト名（デフォルト: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=5001, help="ポート番号（デフォルト: 5001）")

    args = parser.parse_args()

    print("=" * 60)
    print("レターパックラベル調整ツール")
    print("=" * 60)
    print(f"\nアクセス: http://{args.host}:{args.port}")
    print("\n使い方:")
    print("  1. ブラウザで上記URLを開く")
    print("  2. 設定を調整して「プレビュー更新」をクリック")
    print("  3. 満足したら「設定を保存」をクリック")
    print("  4. 保存後、変更をコミット&プッシュ")
    print("\n終了するには Ctrl+C を押してください")
    print("=" * 60)

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
