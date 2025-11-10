"""
コマンドラインインターフェース
"""

import argparse
import sys

from .label import AddressInfo, create_label


def interactive_input() -> tuple[AddressInfo, AddressInfo, str]:
    """
    対話形式で情報を入力

    Returns:
        (お届け先, ご依頼主, 出力ファイルパス) のタプル
    """
    print("=" * 60)
    print("レターパックラベル作成ツール")
    print("=" * 60)
    print()

    print("【お届け先情報】")
    to_postal = input("郵便番号（例: 123-4567）: ").strip()
    to_address = input("住所: ").strip()
    to_name = input("氏名: ").strip()
    to_phone = input("電話番号: ").strip()
    print()

    print("【ご依頼主情報】")
    from_postal = input("郵便番号（例: 987-6543）: ").strip()
    from_address = input("住所: ").strip()
    from_name = input("氏名: ").strip()
    from_phone = input("電話番号: ").strip()
    print()

    output = input("出力ファイル名（デフォルト: label.pdf）: ").strip()
    if not output:
        output = "label.pdf"

    to_info = AddressInfo(postal_code=to_postal, address=to_address, name=to_name, phone=to_phone)

    from_info = AddressInfo(
        postal_code=from_postal, address=from_address, name=from_name, phone=from_phone
    )

    return to_info, from_info, output


def main():
    """CLIのメインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="レターパック用のラベルPDFを生成します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 対話形式で入力
  %(prog)s

  # 引数で指定
  %(prog)s --output label.pdf \\
    --to-name "山田太郎" \\
    --to-postal "123-4567" \\
    --to-address "東京都渋谷区XXX 1-2-3" \\
    --to-phone "03-1234-5678" \\
    --from-name "田中花子" \\
    --from-postal "987-6543" \\
    --from-address "大阪府大阪市YYY 4-5-6" \\
    --from-phone "06-9876-5432"
        """,
    )

    parser.add_argument(
        "-o", "--output", default="label.pdf", help="出力PDFファイル名（デフォルト: label.pdf）"
    )

    # お届け先
    parser.add_argument("--to-name", help="お届け先 氏名")
    parser.add_argument("--to-postal", help="お届け先 郵便番号")
    parser.add_argument("--to-address", help="お届け先 住所")
    parser.add_argument("--to-phone", help="お届け先 電話番号")

    # ご依頼主
    parser.add_argument("--from-name", help="ご依頼主 氏名")
    parser.add_argument("--from-postal", help="ご依頼主 郵便番号")
    parser.add_argument("--from-address", help="ご依頼主 住所")
    parser.add_argument("--from-phone", help="ご依頼主 電話番号")

    # フォント
    parser.add_argument("--font", help="日本語フォントファイルのパス（.ttf）")

    args = parser.parse_args()

    # 引数チェック: 全て指定されているか、全て未指定か
    to_args = [args.to_name, args.to_postal, args.to_address, args.to_phone]
    from_args = [args.from_name, args.from_postal, args.from_address, args.from_phone]
    all_args = to_args + from_args

    all_specified = all(arg is not None for arg in all_args)
    none_specified = all(arg is None for arg in all_args)

    try:
        if all_specified:
            # 引数から生成
            to_info = AddressInfo(
                postal_code=args.to_postal,
                address=args.to_address,
                name=args.to_name,
                phone=args.to_phone,
            )
            from_info = AddressInfo(
                postal_code=args.from_postal,
                address=args.from_address,
                name=args.from_name,
                phone=args.from_phone,
            )
            output_path = args.output

        elif none_specified:
            # 対話形式で入力
            to_info, from_info, output_path = interactive_input()

        else:
            print("エラー: 住所情報は全て指定するか、全て未指定にしてください", file=sys.stderr)
            parser.print_help()
            sys.exit(1)

        # PDF生成
        print(f"\nPDFを生成中: {output_path}")
        result_path = create_label(
            to_address=to_info, from_address=from_info, output_path=output_path, font_path=args.font
        )

        print(f"✓ PDFを生成しました: {result_path}")
        return 0

    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
