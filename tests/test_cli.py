"""
CLIのテスト
"""

import csv
import io
import subprocess


def test_cli_sample_option():
    """--sample オプションでサンプルCSVが出力されることをテスト"""
    # CLIをサブプロセスで実行して標準出力をキャプチャ
    result = subprocess.run(
        ["python", "-m", "letterpack.cli", "--sample"],
        capture_output=True,
        text=True,
    )

    # 終了コードが0であることを確認
    assert result.returncode == 0

    # 標準出力の内容をCSVとしてパース
    csv_reader = csv.DictReader(io.StringIO(result.stdout))

    # ヘッダーの確認
    expected_headers = [
        "to_postal",
        "to_address1",
        "to_address2",
        "to_address3",
        "to_name",
        "to_phone",
        "to_honorific",
        "from_postal",
        "from_address1",
        "from_address2",
        "from_address3",
        "from_name",
        "from_phone",
        "from_honorific",
    ]
    assert csv_reader.fieldnames == expected_headers

    # サンプル行が2つあることを確認
    rows = list(csv_reader)
    assert len(rows) == 2

    # 1行目のチェック
    assert rows[0]["to_postal"] == "123-4567"
    assert rows[0]["to_name"] == "山田 太郎"
    assert rows[0]["from_postal"] == "987-6543"
    assert rows[0]["from_name"] == "田中 花子"

    # 2行目のチェック
    assert rows[1]["to_postal"] == "111-2222"
    assert rows[1]["to_name"] == "佐藤 次郎"
    assert rows[1]["to_honorific"] == "様"
    assert rows[1]["from_name"] == "鈴木 美咲"
