"""
コマンドラインインターフェース
"""

import argparse
import csv
import sys

from .csv_parser import parse_csv
from .label import AddressInfo, create_label, create_label_batch


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
    to_address1 = input("住所1行目（必須）: ").strip()
    to_address2 = input("住所2行目（任意）: ").strip() or None
    to_address3 = input("住所3行目（任意）: ").strip() or None
    to_name = input("氏名: ").strip()
    to_honorific = input("敬称（例: 様、殿、御中、行）※未入力でデフォルト「様」: ").strip()
    if not to_honorific:
        to_honorific = "様"
    to_phone = input("電話番号: ").strip()
    print()

    print("【ご依頼主情報】")
    from_postal = input("郵便番号（例: 987-6543）: ").strip()
    from_address1 = input("住所1行目（必須）: ").strip()
    from_address2 = input("住所2行目（任意）: ").strip() or None
    from_address3 = input("住所3行目（任意）: ").strip() or None
    from_name = input("氏名: ").strip()
    from_honorific = input("敬称（例: 様、殿、御中、行）※未入力で敬称なし: ").strip()
    # 未入力の場合は空文字列（敬称なし）
    from_phone = input("電話番号: ").strip()
    print()

    output = input("出力ファイル名（デフォルト: label.pdf）: ").strip()
    if not output:
        output = "label.pdf"

    to_info = AddressInfo(
        postal_code=to_postal,
        address1=to_address1,
        address2=to_address2,
        address3=to_address3,
        name=to_name,
        phone=to_phone,
        honorific=to_honorific,
    )

    from_info = AddressInfo(
        postal_code=from_postal,
        address1=from_address1,
        address2=from_address2,
        address3=from_address3,
        name=from_name,
        phone=from_phone,
        honorific=from_honorific,
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
    --to-address1 "東京都渋谷区XXX 1-2-3" \\
    --to-phone "03-1234-5678" \\
    --from-name "田中花子" \\
    --from-postal "987-6543" \\
    --from-address1 "大阪府大阪市YYY 4-5-6" \\
    --from-phone "06-9876-5432"
        """,
    )

    parser.add_argument(
        "-o", "--output", default="label.pdf", help="出力PDFファイル名（デフォルト: label.pdf）"
    )

    # お届け先
    parser.add_argument("--to-name", help="お届け先 氏名")
    parser.add_argument("--to-postal", help="お届け先 郵便番号")
    parser.add_argument("--to-address1", help="お届け先 住所1行目")
    parser.add_argument("--to-address2", help="お届け先 住所2行目（任意）")
    parser.add_argument("--to-address3", help="お届け先 住所3行目（任意）")
    parser.add_argument("--to-phone", help="お届け先 電話番号")
    parser.add_argument("--to-honorific", default="様", help="お届け先 敬称（デフォルト: 様）")

    # ご依頼主
    parser.add_argument("--from-name", help="ご依頼主 氏名")
    parser.add_argument("--from-postal", help="ご依頼主 郵便番号")
    parser.add_argument("--from-address1", help="ご依頼主 住所1行目")
    parser.add_argument("--from-address2", help="ご依頼主 住所2行目（任意）")
    parser.add_argument("--from-address3", help="ご依頼主 住所3行目（任意）")
    parser.add_argument("--from-phone", help="ご依頼主 電話番号")
    parser.add_argument("--from-honorific", default="", help="ご依頼主 敬称（デフォルト: なし）")

    # フォント
    parser.add_argument("--font", help="日本語フォントファイルのパス（.ttf）")

    # 設定ファイル
    parser.add_argument(
        "--config", help="レイアウト設定ファイルのパス（.yaml）。4丁付レイアウトなどの設定が可能"
    )

    # CSV一括生成
    parser.add_argument("--csv", help="CSVファイルからの一括生成（4upレイアウトで複数ページPDF）")

    # サンプルCSV出力
    parser.add_argument(
        "--sample",
        action="store_true",
        help="ヘッダーとサンプル行を含むCSVを標準出力に出力",
    )

    args = parser.parse_args()

    try:
        # サンプルCSV出力モード
        if args.sample:
            # ヘッダーとサンプル行を定義
            fieldnames = [
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

            sample_rows = [
                {
                    "to_postal": "123-4567",
                    "to_address1": "東京都渋谷区XXX 1-2-3",
                    "to_address2": "XXXビル4F",
                    "to_address3": "",
                    "to_name": "山田 太郎",
                    "to_phone": "03-1234-5678",
                    "to_honorific": "",
                    "from_postal": "987-6543",
                    "from_address1": "大阪府大阪市YYY 4-5-6",
                    "from_address2": "",
                    "from_address3": "",
                    "from_name": "田中 花子",
                    "from_phone": "06-9876-5432",
                    "from_honorific": "",
                },
                {
                    "to_postal": "111-2222",
                    "to_address1": "京都府京都市ZZZ 7-8-9",
                    "to_address2": "",
                    "to_address3": "",
                    "to_name": "佐藤 次郎",
                    "to_phone": "075-111-2222",
                    "to_honorific": "様",
                    "from_postal": "555-6666",
                    "from_address1": "福岡県福岡市AAA 10-11-12",
                    "from_address2": "",
                    "from_address3": "",
                    "from_name": "鈴木 美咲",
                    "from_phone": "092-555-6666",
                    "from_honorific": "一郎",
                },
            ]

            # 標準出力にCSVを出力
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_rows)
            return 0

        # CSVモード
        if args.csv:
            print("=" * 60)
            print("CSVファイルからの一括生成")
            print("=" * 60)
            print(f"CSVファイル: {args.csv}")
            print()

            # CSVを読み込み＆バリデーション
            print("CSVファイルを読み込み中...")
            labels = parse_csv(args.csv)

            print(f"✓ {len(labels)} 件のラベルを読み込みました")
            print()

            # PDF生成
            print(f"PDFを生成中: {args.output}")
            print(f"  ページ数: {(len(labels) + 3) // 4} ページ（4upレイアウト）")

            # (to_address, from_address) のタプルのリストに変換
            label_pairs = [(label.to_address, label.from_address) for label in labels]

            result_path = create_label_batch(
                label_pairs=label_pairs,
                output_path=args.output,
                font_path=args.font,
                config_path=args.config,
            )

            print(f"✓ PDFを生成しました: {result_path}")
            return 0

        # 通常モード（1件のみ）
        # 引数チェック: 必須フィールドが全て指定されているか、全て未指定か
        to_args = [args.to_name, args.to_postal, args.to_address1]
        from_args = [args.from_name, args.from_postal, args.from_address1]
        all_args = to_args + from_args

        all_specified = all(arg is not None for arg in all_args)
        none_specified = all(arg is None for arg in all_args)

        if all_specified:
            # 引数から生成
            to_info = AddressInfo(
                postal_code=args.to_postal,
                address1=args.to_address1,
                address2=args.to_address2,
                address3=args.to_address3,
                name=args.to_name,
                phone=args.to_phone,
                honorific=args.to_honorific,
            )
            from_info = AddressInfo(
                postal_code=args.from_postal,
                address1=args.from_address1,
                address2=args.from_address2,
                address3=args.from_address3,
                name=args.from_name,
                phone=args.from_phone,
                honorific=args.from_honorific,
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
            to_address=to_info,
            from_address=from_info,
            output_path=output_path,
            font_path=args.font,
            config_path=args.config,
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
