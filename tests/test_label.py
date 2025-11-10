"""
ラベル生成のテスト
"""

import inspect
import os
import shutil
import tempfile

import pytest

from letterpack.label import AddressInfo, LabelGenerator, create_label


def save_to_test_output(pdf_path, test_name=None):
    """
    CI環境用にPDFを保存するヘルパー関数

    TEST_OUTPUT_DIR環境変数が設定されている場合、
    生成されたPDFをそのディレクトリにコピーします。
    """
    output_dir = os.getenv("TEST_OUTPUT_DIR")
    if output_dir and os.path.exists(pdf_path):
        os.makedirs(output_dir, exist_ok=True)
        if test_name is None:
            # 呼び出し元の関数名を取得
            frame = inspect.currentframe().f_back
            test_name = frame.f_code.co_name
        dest_path = os.path.join(output_dir, f"{test_name}.pdf")
        shutil.copy(pdf_path, dest_path)


def test_address_info_creation():
    """AddressInfoの作成テスト"""
    addr = AddressInfo(
        postal_code="123-4567",
        address="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
    )
    assert addr.postal_code == "123-4567"
    assert addr.name == "山田太郎"


def test_address_info_validation():
    """AddressInfoのバリデーションテスト"""
    with pytest.raises(ValueError):
        AddressInfo(postal_code="", address="住所", name="名前", phone="電話")

    with pytest.raises(ValueError):
        AddressInfo(postal_code="123", address="", name="名前", phone="電話")


def test_label_generation():
    """PDF生成テスト"""
    to_addr = AddressInfo(
        postal_code="123-4567",
        address="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address="大阪府大阪市YYY 4-5-6",
        name="田中花子",
        phone="06-9876-5432",
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name

    try:
        result = create_label(to_addr, from_addr, output_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_label_generator_class():
    """LabelGeneratorクラスのテスト"""
    generator = LabelGenerator()
    assert generator is not None

    to_addr = AddressInfo(
        postal_code="100-0001",
        address="東京都千代田区千代田1-1",
        name="テスト太郎",
        phone="03-0000-0000",
    )
    from_addr = AddressInfo(
        postal_code="530-0001",
        address="大阪府大阪市北区梅田1-1",
        name="テスト花子",
        phone="06-0000-0000",
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name

    try:
        result = generator.generate(to_addr, from_addr, output_path)
        assert os.path.exists(result)

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_load_layout_config():
    """レイアウト設定の読み込みテスト"""
    from letterpack.label import load_layout_config

    config = load_layout_config()
    assert config is not None
    assert "layout" in config
    assert "fonts" in config
    assert "spacing" in config
    assert "address" in config

    # レイアウト設定の検証
    layout = config["layout"]
    assert "label_width" in layout
    assert "label_height" in layout
    assert "margin" in layout
    assert layout["label_width"] > 0
    assert layout["label_height"] > 0

    # フォント設定の検証
    fonts = config["fonts"]
    assert "section_label" in fonts
    assert "postal_code" in fonts
    assert "address" in fonts
    assert "name" in fonts
    assert "phone" in fonts


def test_load_layout_config_with_invalid_path():
    """存在しない設定ファイルのテスト"""
    from letterpack.label import load_layout_config

    with pytest.raises(FileNotFoundError):
        load_layout_config("/nonexistent/path.yaml")


def test_label_generation_with_custom_config():
    """カスタム設定パスでのラベル生成テスト"""
    # デフォルト設定を使用してラベルを生成
    to_addr = AddressInfo(
        postal_code="123-4567",
        address="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address="大阪府大阪市YYY 4-5-6",
        name="田中花子",
        phone="06-9876-5432",
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name

    try:
        # config_pathを明示的に指定（デフォルト設定を使用）
        result = create_label(to_addr, from_addr, output_path, config_path=None)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_label_generator_with_config():
    """LabelGeneratorのconfig_path引数のテスト"""
    # config_pathを指定してジェネレーターを作成
    generator = LabelGenerator(config_path=None)  # Noneの場合はデフォルト設定
    assert generator.config is not None
    assert "layout" in generator.config

    to_addr = AddressInfo(
        postal_code="100-0001",
        address="東京都千代田区千代田1-1",
        name="テスト太郎",
        phone="03-0000-0000",
    )
    from_addr = AddressInfo(
        postal_code="530-0001",
        address="大阪府大阪市北区梅田1-1",
        name="テスト花子",
        phone="06-0000-0000",
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name

    try:
        result = generator.generate(to_addr, from_addr, output_path)
        assert os.path.exists(result)

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
