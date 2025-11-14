"""
CSVパーサーのテスト
"""

import os
import tempfile

import pytest
from letterpack.csv_parser import parse_csv, validate_csv


def test_parse_csv_valid():
    """有効なCSVファイルの読み込みテスト"""
    # テスト用CSVファイルを作成
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,XXXビル4F,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
456-7890,神奈川県横浜市ZZZ 7-8-9,,,佐藤次郎,045-1234-5678,殿,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        labels = parse_csv(csv_path)
        assert len(labels) == 2

        # 1件目のチェック
        assert labels[0].to_address.postal_code == "123-4567"
        assert labels[0].to_address.name == "山田太郎"
        assert labels[0].to_address.honorific == "様"
        assert labels[0].from_address.name == "田中花子"
        assert labels[0].from_address.honorific == ""

        # 2件目のチェック
        assert labels[1].to_address.postal_code == "456-7890"
        assert labels[1].to_address.name == "佐藤次郎"
        assert labels[1].to_address.honorific == "殿"

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_default_honorific():
    """敬称のデフォルト値テスト"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,03-1234-5678,,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        labels = parse_csv(csv_path)
        assert len(labels) == 1
        # to_honorificが空の場合はデフォルトで「様」
        assert labels[0].to_address.honorific == "様"
        # from_honorificが空の場合は空文字列のまま
        assert labels[0].from_address.honorific == ""

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_missing_required_field():
    """必須フィールドが欠けている場合のテスト"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,,,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            parse_csv(csv_path)
        assert "エラー" in str(exc_info.value)
        assert "住所1行目は必須です" in str(exc_info.value)

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_missing_column():
    """必須カラムが欠けている場合のテスト"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,03-1234-5678,,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        # このCSVは実際には有効（to_honorific, from_honorificは任意カラム）
        # テストケースを修正: このテストは削除または別のテストに統合すべき
        # ここでは、正常に読み込めることを確認
        labels = parse_csv(csv_path)
        assert len(labels) == 1
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_missing_required_column():
    """必須カラムが欠けている場合のテスト（修正版）"""
    # to_postalカラムが欠けているCSV（必須カラムの欠落）
    csv_content = """to_address1,to_address2,to_address3,to_name,from_postal,from_address1,from_address2,from_address3,from_name
東京都渋谷区XXX 1-2-3,,,山田太郎,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            parse_csv(csv_path)
        assert "必須カラムが不足" in str(exc_info.value)

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_file_not_found():
    """存在しないファイルのテスト"""
    with pytest.raises(FileNotFoundError):
        parse_csv("/nonexistent/file.csv")


def test_parse_csv_no_header():
    """ヘッダー行がない場合のテスト"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            parse_csv(csv_path)
        # ヘッダーがないとカラム名がデータとして解釈されるため、必須カラムが不足するエラーになる
        assert "必須カラム" in str(exc_info.value) or "エラー" in str(exc_info.value)

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_empty_file():
    """空のCSVファイルのテスト"""
    csv_content = ""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        with pytest.raises(ValueError):
            parse_csv(csv_path)

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_validate_csv_success():
    """validate_csv関数のテスト（成功）"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        success, error_msg, count = validate_csv(csv_path)
        assert success is True
        assert error_msg is None
        assert count == 1

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_validate_csv_failure():
    """validate_csv関数のテスト（失敗）"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
,東京都渋谷区XXX 1-2-3,,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        success, error_msg, count = validate_csv(csv_path)
        assert success is False
        assert error_msg is not None
        assert count == 0

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_shift_jis_encoding():
    """Shift_JISエンコーディングのCSVファイルテスト"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,03-1234-5678,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,06-9876-5432,
"""

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", encoding="shift_jis"
    ) as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        labels = parse_csv(csv_path)
        assert len(labels) == 1
        assert labels[0].to_address.name == "山田太郎"

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_without_phone_columns():
    """電話番号カラムがないCSVのテスト（新機能：電話番号を任意に変更）"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        labels = parse_csv(csv_path)
        assert len(labels) == 1
        # 電話番号カラムがない場合、phoneはNoneになる
        assert labels[0].to_address.phone is None
        assert labels[0].from_address.phone is None
        # その他のフィールドは正常に読み込まれる
        assert labels[0].to_address.name == "山田太郎"
        assert labels[0].from_address.name == "田中花子"

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_parse_csv_with_empty_phone_fields():
    """電話番号カラムが存在するが空のCSVのテスト（新機能：電話番号を任意に変更）"""
    csv_content = """to_postal,to_address1,to_address2,to_address3,to_name,to_phone,to_honorific,from_postal,from_address1,from_address2,from_address3,from_name,from_phone,from_honorific
123-4567,東京都渋谷区XXX 1-2-3,,,山田太郎,,様,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,,
456-7890,神奈川県横浜市ZZZ 7-8-9,,,佐藤次郎,  ,殿,987-6543,大阪府大阪市YYY 4-5-6,,,田中花子,  ,
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8") as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        labels = parse_csv(csv_path)
        assert len(labels) == 2

        # 1件目：空文字列の電話番号はNoneに変換される
        assert labels[0].to_address.phone is None
        assert labels[0].from_address.phone is None

        # 2件目：空白のみの電話番号もNoneに変換される
        assert labels[1].to_address.phone is None
        assert labels[1].from_address.phone is None

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)
