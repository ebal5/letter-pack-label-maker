"""
ラベル生成のテスト
"""

import inspect
import os
import shutil
import tempfile

import pytest
import yaml

from letterpack.label import AddressInfo, LabelGenerator, create_label, load_layout_config


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
        address1="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
    )
    assert addr.postal_code == "123-4567"
    assert addr.name == "山田太郎"


def test_address_info_without_phone():
    """電話番号なしでAddressInfoを作成するテスト（新機能：電話番号を任意に変更）"""
    # 電話番号を指定しない場合
    addr1 = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
    )
    assert addr1.phone is None

    # 電話番号にNoneを明示的に指定する場合
    addr2 = AddressInfo(
        postal_code="456-7890",
        address1="大阪府大阪市YYY 4-5-6",
        name="田中花子",
        phone=None,
    )
    assert addr2.phone is None


def test_address_info_validation():
    """AddressInfoのバリデーションテスト"""
    with pytest.raises(ValueError):
        AddressInfo(postal_code="", address1="住所", name="名前", phone="電話")

    with pytest.raises(ValueError):
        AddressInfo(postal_code="123", address1="", name="名前", phone="電話")


def test_label_generation():
    """PDF生成テスト"""
    to_addr = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address1="大阪府大阪市YYY 4-5-6",
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


def test_label_generation_without_phone():
    """電話番号なしでPDF生成テスト（新機能：電話番号を任意に変更）"""
    to_addr = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone=None,
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address1="大阪府大阪市YYY 4-5-6",
        name="田中花子",
        phone=None,
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
        address1="東京都千代田区千代田1-1",
        name="テスト太郎",
        phone="03-0000-0000",
    )
    from_addr = AddressInfo(
        postal_code="530-0001",
        address1="大阪府大阪市北区梅田1-1",
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


# 設定関連のテスト


def test_load_default_config():
    """デフォルト設定の読み込みテスト"""
    config = load_layout_config(None)
    assert config is not None
    assert config.layout.label_width == 105
    assert config.layout.label_height == 148
    assert config.layout.margin == 8
    assert config.fonts.label == 9
    assert config.fonts.postal_code == 13
    assert config.fonts.address == 11
    assert config.fonts.name == 14
    assert config.fonts.phone == 13
    assert config.postal_box.line_width == 0.5
    assert config.postal_box.text_vertical_offset == 2
    assert config.spacing.postal_box_offset_y == -2


def test_load_custom_config():
    """カスタム設定の読み込みテスト"""
    # 一時的な設定ファイルを作成
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_file:
        config_data = {
            "layout": {"label_width": 150, "label_height": 220, "margin": 10},
            "fonts": {"label": 10, "postal_code": 12, "address": 12, "name": 16, "phone": 12},
        }
        yaml.dump(config_data, tmp_file)
        config_path = tmp_file.name

    try:
        config = load_layout_config(config_path)
        assert config.layout.label_width == 150
        assert config.layout.label_height == 220
        assert config.layout.margin == 10
        assert config.fonts.label == 10
        assert config.fonts.postal_code == 12
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


def test_load_config_file_not_found():
    """存在しない設定ファイルのテスト"""
    with pytest.raises(FileNotFoundError):
        load_layout_config("/nonexistent/config.yaml")


def test_load_empty_config():
    """空の設定ファイルのテスト"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_file:
        tmp_file.write("")  # 空のファイル
        config_path = tmp_file.name

    try:
        config = load_layout_config(config_path)
        # 空のファイルの場合はデフォルト設定が使用される
        assert config.layout.label_width == 105
        assert config.fonts.label == 9
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


def test_invalid_config_values():
    """不正な設定値のバリデーションテスト"""
    # 不正な値（負の値）を含む設定ファイル
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_file:
        config_data = {"layout": {"label_width": -100}}  # 負の値は不正
        yaml.dump(config_data, tmp_file)
        config_path = tmp_file.name

    try:
        with pytest.raises(ValueError):
            load_layout_config(config_path)
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


def test_label_generation_with_custom_config():
    """カスタム設定でのPDF生成テスト"""
    to_addr = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="設定太郎",
        phone="03-1234-5678",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address1="大阪府大阪市YYY 4-5-6",
        name="設定花子",
        phone="06-9876-5432",
    )

    # カスタム設定を作成
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_config:
        config_data = {
            "layout": {"label_width": 148, "label_height": 210, "margin": 10},
            "fonts": {"label": 10, "postal_code": 11, "address": 12, "name": 15, "phone": 12},
        }
        yaml.dump(config_data, tmp_config)
        config_path = tmp_config.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        output_path = tmp_pdf.name

    try:
        result = create_label(to_addr, from_addr, output_path, config_path=config_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(config_path):
            os.remove(config_path)


def test_label_generator_with_custom_config():
    """LabelGeneratorクラスでカスタム設定を使用するテスト"""
    # カスタム設定を作成
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_config:
        config_data = {
            "layout": {"margin": 12},
            "fonts": {"name": 16},
        }
        yaml.dump(config_data, tmp_config)
        config_path = tmp_config.name

    try:
        generator = LabelGenerator(config_path=config_path)
        assert generator.config.layout.margin == 12
        assert generator.config.fonts.name == 16
        # デフォルト値も正しく設定されているか確認
        assert generator.config.layout.label_width == 105
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


def test_grid_4up_layout():
    """4丁付レイアウトのテスト"""
    to_addr = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="4丁付太郎",
        phone="03-1234-5678",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address1="大阪府大阪市YYY 4-5-6",
        name="4丁付花子",
        phone="06-9876-5432",
    )

    # 4丁付レイアウトの設定を作成
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_config:
        config_data = {"layout": {"layout_mode": "grid_4up"}}
        yaml.dump(config_data, tmp_config)
        config_path = tmp_config.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        output_path = tmp_pdf.name

    try:
        result = create_label(to_addr, from_addr, output_path, config_path=config_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(config_path):
            os.remove(config_path)


def test_center_layout_default():
    """中央配置レイアウト（デフォルト）のテスト"""
    config = load_layout_config(None)
    assert config.layout.layout_mode == "center"


def test_create_label_batch():
    """複数ラベルの一括生成テスト"""
    # テスト用の複数ラベルを作成
    label_pairs = [
        (
            AddressInfo(
                postal_code="123-4567",
                address1="東京都渋谷区XXX 1-2-3",
                name="山田太郎",
                phone="03-1234-5678",
                honorific="様",
            ),
            AddressInfo(
                postal_code="987-6543",
                address1="大阪府大阪市YYY 4-5-6",
                name="田中花子",
                phone="06-9876-5432",
            ),
        ),
        (
            AddressInfo(
                postal_code="456-7890",
                address1="神奈川県横浜市ZZZ 7-8-9",
                name="佐藤次郎",
                phone="045-1234-5678",
                honorific="殿",
            ),
            AddressInfo(
                postal_code="987-6543",
                address1="大阪府大阪市YYY 4-5-6",
                name="田中花子",
                phone="06-9876-5432",
            ),
        ),
        (
            AddressInfo(
                postal_code="111-2222",
                address1="千葉県千葉市AAA 1-1-1",
                name="鈴木三郎",
                phone="043-1111-2222",
                honorific="御中",
            ),
            AddressInfo(
                postal_code="987-6543",
                address1="大阪府大阪市YYY 4-5-6",
                name="田中花子",
                phone="06-9876-5432",
            ),
        ),
    ]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        output_path = tmp_pdf.name

    try:
        from letterpack.label import create_label_batch

        result = create_label_batch(label_pairs, output_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_create_label_batch_5_labels():
    """5件のラベルで2ページ生成のテスト"""
    label_pairs = []
    for i in range(5):
        label_pairs.append(
            (
                AddressInfo(
                    postal_code=f"{100 + i}-0001",
                    address1=f"東京都千代田区{i}-{i}-{i}",
                    name=f"テスト{i}",
                    phone=f"03-0000-000{i}",
                ),
                AddressInfo(
                    postal_code="999-9999",
                    address1="送信元住所",
                    name="送信元",
                    phone="099-9999-9999",
                ),
            )
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        output_path = tmp_pdf.name

    try:
        from letterpack.label import create_label_batch

        result = create_label_batch(label_pairs, output_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        # CI環境用にPDFを保存
        save_to_test_output(result)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_default_honorific_font_size():
    """敬称フォントサイズのデフォルト値テスト（名前より2pt小さい）"""
    config = load_layout_config(None)
    # デフォルトではhonorificはNone
    assert config.fonts.honorific is None
    # 敬称が設定されている場合のレンダリングを確認
    to_addr = AddressInfo(
        postal_code="123-4567",
        address1="東京都渋谷区XXX 1-2-3",
        name="山田太郎",
        phone="03-1234-5678",
        honorific="様",
    )
    from_addr = AddressInfo(
        postal_code="987-6543",
        address1="大阪府大阪市YYY 4-5-6",
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


def test_custom_honorific_font_size():
    """敬称フォントサイズの指定テスト"""
    # カスタム設定ファイルを作成（敬称を10ptに指定）
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp_config:
        config_data = {
            "fonts": {"name": 14, "honorific": 10},
        }
        yaml.dump(config_data, tmp_config)
        config_path = tmp_config.name

    try:
        config = load_layout_config(config_path)
        assert config.fonts.name == 14
        assert config.fonts.honorific == 10

        to_addr = AddressInfo(
            postal_code="123-4567",
            address1="東京都渋谷区XXX 1-2-3",
            name="山田太郎",
            phone="03-1234-5678",
            honorific="様",
        )
        from_addr = AddressInfo(
            postal_code="987-6543",
            address1="大阪府大阪市YYY 4-5-6",
            name="田中花子",
            phone="06-9876-5432",
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            output_path = tmp_pdf.name

        try:
            result = create_label(to_addr, from_addr, output_path, config_path=config_path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0

            # CI環境用にPDFを保存
            save_to_test_output(result)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)
