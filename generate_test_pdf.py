#!/usr/bin/env python3
"""
テストデータを使用してPDFを生成するスクリプト
GitHub Actionsでの動作確認用
"""

from src.letterpack.label import AddressInfo, create_label


def main():
    """テストデータでPDFを生成"""
    # テストデータ: お届け先
    to_address = AddressInfo(
        postal_code="150-0001",
        address1="東京都渋谷区神宮前1-2-3",
        address2="サンプルビル101",
        name="山田 太郎",
        phone="03-1234-5678",
    )

    # テストデータ: ご依頼主
    from_address = AddressInfo(
        postal_code="530-0001",
        address1="大阪府大阪市北区梅田1-2-3",
        address2="テストマンション202",
        name="田中 花子",
        phone="06-9876-5432",
    )

    # PDF生成
    output_path = "test_label.pdf"
    print(f"テストPDFを生成中: {output_path}")

    result = create_label(to_address=to_address, from_address=from_address, output_path=output_path)

    print(f"✓ テストPDFを生成しました: {result}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
