"""
Webインターフェース (Flask)
"""

import os
import sys
import tempfile

import yaml
from flask import (
    Flask,
    after_this_request,
    flash,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)

from .label import AddressInfo, create_label

app = Flask(__name__)

# 環境変数からシークレットキーを取得
# 本番環境では必ず SECRET_KEY 環境変数を設定してください
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    print(
        "警告: SECRET_KEY 環境変数が設定されていません。",
        "開発用のランダムキーを使用します。",
        "本番環境では必ず SECRET_KEY を設定してください。",
        file=sys.stderr,
    )
    secret_key = os.urandom(24)

app.secret_key = secret_key


# HTMLテンプレート
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>レターパックラベル作成</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .subtitle {
            opacity: 0.9;
            font-size: 14px;
        }
        .content {
            padding: 40px;
        }
        .section {
            margin-bottom: 35px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn-container {
            text-align: center;
            margin-top: 30px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 50px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .alert {
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 6px;
            font-size: 14px;
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
        footer {
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
            background: #f8f9fa;
        }
        .example {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }
        .loading {
            color: #667eea;
            font-size: 12px;
            margin-top: 4px;
        }
        .address-choices {
            margin-top: 8px;
            padding: 12px;
            background: #f0f0f0;
            border-radius: 6px;
            border: 1px solid #ddd;
        }
        .address-choice-button {
            display: block;
            width: 100%;
            padding: 10px;
            margin-bottom: 8px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            text-align: left;
            font-size: 14px;
            transition: all 0.2s;
        }
        .address-choice-button:hover {
            background: #f8f9fa;
            border-color: #667eea;
            transform: translateX(4px);
        }
        .address-choice-close {
            display: block;
            width: 100%;
            padding: 8px;
            background: #999;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 4px;
        }
        .address-choice-close:hover {
            background: #777;
        }
        .address-choice-label {
            font-size: 13px;
            color: #555;
            margin-bottom: 8px;
            font-weight: 500;
        }
    </style>
    <script>
        // 複数の住所候補がある場合に選択肢を表示する関数
        function showAddressChoices(addressFieldId, addresses) {
            // 既存の選択肢があれば削除
            const existingChoices = document.getElementById(addressFieldId + '_choices');
            if (existingChoices) {
                existingChoices.remove();
            }

            const addressField = document.getElementById(addressFieldId);
            const container = addressField.parentElement;

            // 選択肢を表示するコンテナを作成
            const choicesDiv = document.createElement('div');
            choicesDiv.id = addressFieldId + '_choices';
            choicesDiv.className = 'address-choices';

            // ラベルを追加
            const label = document.createElement('div');
            label.className = 'address-choice-label';
            label.textContent = '複数の住所が見つかりました。選択してください：';
            choicesDiv.appendChild(label);

            // 各住所の選択ボタンを作成
            addresses.forEach(function(addr) {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'address-choice-button';
                const fullAddress = addr.ja.prefecture + addr.ja.address1 + addr.ja.address2 + (addr.ja.address3 || '');
                button.textContent = fullAddress;
                button.onclick = function() {
                    addressField.value = fullAddress;
                    choicesDiv.remove();
                };
                choicesDiv.appendChild(button);
            });

            // 閉じるボタンを追加
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'address-choice-close';
            closeButton.textContent = '✕ 閉じる';
            closeButton.onclick = function() {
                choicesDiv.remove();
            };
            choicesDiv.appendChild(closeButton);

            container.appendChild(choicesDiv);
        }

        // 郵便番号から住所を自動補完する関数
        async function searchAddress(postalCode, addressFieldId) {
            // 住所フィールドの要素を取得
            const addressField = document.getElementById(addressFieldId);

            // 住所が既に入力されている場合は何もしない
            if (addressField.value.trim() !== '') {
                return;
            }

            // 既存の選択肢があれば削除
            const existingChoices = document.getElementById(addressFieldId + '_choices');
            if (existingChoices) {
                existingChoices.remove();
            }

            // 郵便番号のフォーマットをクリーンアップ（ハイフンを除去）
            const cleanPostalCode = postalCode.replace(/[－ー\-]/g, '');

            // 7桁でない場合は検索しない
            if (cleanPostalCode.length !== 7) {
                return;
            }

            try {
                // ttskch/jp-postal-code-api を使用して住所を検索
                const response = await fetch('https://jp-postal-code-api.ttskch.com/api/v1/' + cleanPostalCode + '.json');

                // エラー時は何も表示しない（コンソールにログを出すだけ）
                if (!response.ok) {
                    console.error('住所の取得に失敗しました: HTTP ' + response.status);
                    return;
                }

                const data = await response.json();

                if (data.addresses && data.addresses.length > 0) {
                    if (data.addresses.length === 1) {
                        // 1つの結果の場合は直接入力
                        const addr = data.addresses[0].ja;
                        const address = addr.prefecture + addr.address1 + addr.address2 + (addr.address3 || '');
                        // 住所フィールドが空の場合のみ自動補完
                        if (addressField.value.trim() === '') {
                            addressField.value = address;
                        }
                    } else {
                        // 複数の結果がある場合は選択肢を表示
                        showAddressChoices(addressFieldId, data.addresses);
                    }
                }
            } catch (error) {
                // エラーをコンソールに出すだけで、ユーザーには表示しない
                console.error('住所の取得に失敗しました:', error);
            }
        }

        // ページ読み込み後にイベントリスナーを設定
        document.addEventListener('DOMContentLoaded', function() {
            // お届け先の郵便番号フィールド
            const toPostalField = document.getElementById('to_postal');
            toPostalField.addEventListener('blur', function() {
                searchAddress(this.value, 'to_address');
            });

            // ご依頼主の郵便番号フィールド
            const fromPostalField = document.getElementById('from_postal');
            fromPostalField.addEventListener('blur', function() {
                searchAddress(this.value, 'from_address');
            });
        });
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📮 レターパックラベル作成</h1>
            <p class="subtitle">情報を入力してPDFラベルを生成</p>
        </header>

        <div class="content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST" action="{{ url_for('generate_pdf') }}">
                <div class="section">
                    <h2>📬 お届け先</h2>
                    <div class="form-group">
                        <label for="to_postal">郵便番号 *</label>
                        <input type="text" id="to_postal" name="to_postal"
                               placeholder="例: 123-4567" required>
                    </div>
                    <div class="form-group">
                        <label for="to_address">住所 *</label>
                        <input type="text" id="to_address" name="to_address"
                               placeholder="例: 東京都渋谷区XXX 1-2-3 XXXビル4F" required>
                    </div>
                    <div class="form-group">
                        <label for="to_name">氏名 *</label>
                        <input type="text" id="to_name" name="to_name"
                               placeholder="例: 山田 太郎" required>
                    </div>
                    <div class="form-group">
                        <label for="to_phone">電話番号 *</label>
                        <input type="text" id="to_phone" name="to_phone"
                               placeholder="例: 03-1234-5678" required>
                    </div>
                </div>

                <div class="section">
                    <h2>📤 ご依頼主</h2>
                    <div class="form-group">
                        <label for="from_postal">郵便番号 *</label>
                        <input type="text" id="from_postal" name="from_postal"
                               placeholder="例: 987-6543" required>
                    </div>
                    <div class="form-group">
                        <label for="from_address">住所 *</label>
                        <input type="text" id="from_address" name="from_address"
                               placeholder="例: 大阪府大阪市YYY 4-5-6" required>
                    </div>
                    <div class="form-group">
                        <label for="from_name">氏名 *</label>
                        <input type="text" id="from_name" name="from_name"
                               placeholder="例: 田中 花子" required>
                    </div>
                    <div class="form-group">
                        <label for="from_phone">電話番号 *</label>
                        <input type="text" id="from_phone" name="from_phone"
                               placeholder="例: 06-9876-5432" required>
                    </div>
                </div>

                <div class="section">
                    <h2>⚙️ レイアウト設定</h2>
                    <div class="form-group">
                        <label for="layout_mode">レイアウトモード</label>
                        <select id="layout_mode" name="layout_mode">
                            <option value="center">中央配置（1枚）</option>
                            <option value="grid_4up">4丁付（2×2グリッド、同じラベル4枚）</option>
                        </select>
                        <p class="example">※ 4丁付を選択すると、A4用紙に同じラベルが4つ印刷されます</p>
                    </div>
                </div>

                <div class="btn-container">
                    <button type="submit">📄 PDFを生成</button>
                </div>
            </form>
        </div>

        <footer>
            Letter Pack Label Maker v0.1.0 | MIT License
        </footer>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    """トップページ"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/generate", methods=["POST"])
def generate_pdf():
    """PDF生成処理"""
    try:
        # フォームデータ取得
        to_postal = request.form.get("to_postal", "").strip()
        to_address = request.form.get("to_address", "").strip()
        to_name = request.form.get("to_name", "").strip()
        to_phone = request.form.get("to_phone", "").strip()

        from_postal = request.form.get("from_postal", "").strip()
        from_address = request.form.get("from_address", "").strip()
        from_name = request.form.get("from_name", "").strip()
        from_phone = request.form.get("from_phone", "").strip()

        # レイアウトモード取得
        layout_mode = request.form.get("layout_mode", "center").strip()

        # AddressInfo作成（バリデーション含む）
        to_info = AddressInfo(
            postal_code=to_postal, address=to_address, name=to_name, phone=to_phone
        )

        from_info = AddressInfo(
            postal_code=from_postal, address=from_address, name=from_name, phone=from_phone
        )

        # レイアウト設定ファイルを一時作成（デフォルト以外の場合のみ）
        config_path = None
        if layout_mode != "center":
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".yaml", encoding="utf-8"
            ) as tmp_config:
                config_data = {"layout": {"layout_mode": layout_mode}}
                yaml.dump(config_data, tmp_config)
                config_path = tmp_config.name

        # 一時ファイルにPDF生成
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            output_path = tmp_file.name

        create_label(to_info, from_info, output_path, config_path=config_path)

        # レスポンス送信後に一時ファイルを削除するコールバックを登録
        @after_this_request
        def remove_temp_file(response):
            try:
                os.remove(output_path)
            except Exception as e:
                # ログに記録するが、エラーを無視してレスポンスは返す
                print(
                    f"警告: 一時ファイルの削除に失敗: {output_path}, エラー: {e}", file=sys.stderr
                )
            # 設定ファイルも削除
            if config_path:
                try:
                    os.remove(config_path)
                except Exception as e:
                    print(
                        f"警告: 一時設定ファイルの削除に失敗: {config_path}, エラー: {e}",
                        file=sys.stderr,
                    )
            return response

        # PDFを送信
        return send_file(
            output_path,
            as_attachment=True,
            download_name="letterpack_label.pdf",
            mimetype="application/pdf",
        )

    except ValueError as e:
        flash(f"入力エラー: {e}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"PDF生成エラー: {e}", "error")
        return redirect(url_for("index"))


def main():
    """Webサーバーのメインエントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="レターパックラベル作成 Webサーバー")
    parser.add_argument("--host", default="127.0.0.1", help="ホスト名（デフォルト: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=5000, help="ポート番号（デフォルト: 5000）")
    parser.add_argument("--debug", action="store_true", help="デバッグモードで起動")

    args = parser.parse_args()

    print("Webサーバーを起動中...")
    print(f"アクセス: http://{args.host}:{args.port}")
    print("終了するには Ctrl+C を押してください")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
