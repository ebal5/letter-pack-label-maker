#!/usr/bin/env python3
"""
レターパックラベル用のテストCSVデータを生成するスクリプト

このスクリプトは、CSV一括生成機能のテスト、デモ、ストレステストなどで使用する
多様なテストデータを自動生成します。

使用例:
    python tools/generate_test_csv.py standard 10
    python tools/generate_test_csv.py stress 1000
    python tools/generate_test_csv.py edge_case
    python tools/generate_test_csv.py invalid
"""

import csv
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 都道府県リスト（47都道府県）
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]

# 市区町村の例（各都道府県の代表例）
CITIES = [
    "中央区", "千代田区", "港区", "新宿区", "渋谷区", "豊島区", "台東区",
    "北区", "品川区", "目黒区", "大田区", "世田谷区", "杉並区", "中野区",
    "西東京市", "横浜市西区", "横浜市中区", "川崎市", "相模原市",
    "大阪市北区", "大阪市中央区", "大阪市東淀川区", "堺市",
    "名古屋市中区", "名古屋市東区", "名古屋市西区",
    "札幌市中央区", "札幌市北区",
    "福岡市博多区", "福岡市中央区",
    "仙台市青葉区", "仙台市宮城野区",
    "広島市中区", "広島市東区",
    "京都市中京区", "京都市下京区", "京都市左京区",
    "神戸市中央区", "神戸市東灘区",
]

# 姓のリスト（一般的な日本人の姓）
LAST_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "山本", "中村", "小林", "加藤",
    "吉田", "山田", "佐々木", "山口", "松本", "井上", "木村", "林", "斉藤", "清水",
    "久保", "長谷川", "新井", "村上", "藤田", "野田", "福田", "太田", "水田", "片岡",
    "橋本", "梅田", "中島", "菊池", "石田", "森", "佐藤", "武田", "青木", "岡部",
]

# 名前のリスト（一般的な日本人の名前）
FIRST_NAMES = [
    "太郎", "花子", "一郎", "美咲", "健太", "さくら", "翔太", "優子", "大輔", "真理子",
    "拓也", "恵美", "雄一", "由美", "和也", "智子", "誠", "紀子", "修", "明美",
    "次郎", "三郎", "真也", "亮介", "慎吾", "智也", "徳也", "正人", "勇気", "智彦",
    "百合", "由紀", "沙織", "麻里", "涼子", "瑞希", "美優", "千秋", "瑠美", "由実",
]

# 敬称のリスト
HONORIFICS = ["様", "殿", ""]

# 建物名の例
BUILDING_NAMES = [
    "", "XXXビル", "YYYマンション", "第一ビル", "第二ビル", "パークタワー",
    "プラザビル", "シティービル", "グランドビル", "メゾン",
    "アパート", "コーポ", "ハイツ", "レジデンス",
]


def generate_postal_code() -> str:
    """郵便番号を生成（XXX-XXXX形式）"""
    return f"{random.randint(0, 999):03d}-{random.randint(0, 9999):04d}"


def generate_name() -> str:
    """名前を生成（姓名形式）"""
    last_name = random.choice(LAST_NAMES)
    first_name = random.choice(FIRST_NAMES)
    return f"{last_name}{first_name}"


def generate_address() -> Dict[str, str]:
    """住所データを生成"""
    prefecture = random.choice(PREFECTURES)
    city = random.choice(CITIES)
    street = f"{random.randint(1, 99)}-{random.randint(1, 99)}"

    # 建物名は60%の確率で付与
    if random.random() < 0.6:
        building = random.choice(BUILDING_NAMES[1:])  # 空文字列を除外
        building += f"{random.randint(1, 20)}F"
    else:
        building = ""

    return {
        "postal_code": generate_postal_code(),
        "prefecture": prefecture,
        "city": city,
        "street": street,
        "building": building,
    }


def generate_standard_data(count: int = 10) -> List[Dict[str, str]]:
    """
    標準的なテストデータを生成

    Args:
        count: 生成するレコード数

    Returns:
        生成されたデータのリスト
    """
    data = []
    for _ in range(count):
        to_addr = generate_address()
        from_addr = generate_address()

        address_parts = [to_addr["prefecture"], to_addr["city"], to_addr["street"]]
        if to_addr["building"]:
            address_parts.append(to_addr["building"])
        to_address = " ".join(address_parts)

        from_address_parts = [from_addr["prefecture"], from_addr["city"], from_addr["street"]]
        if from_addr["building"]:
            from_address_parts.append(from_addr["building"])
        from_address = " ".join(from_address_parts)

        data.append({
            "to_postal": to_addr["postal_code"],
            "to_address": to_address,
            "to_name": generate_name(),
            "to_phone": "",
            "to_honorific": random.choice(HONORIFICS),
            "from_postal": from_addr["postal_code"],
            "from_address": from_address,
            "from_name": generate_name(),
            "from_phone": "",
            "from_honorific": random.choice(["", ""]),  # 差出人は敬称なし90%、様10%
        })

    return data


def generate_edge_case_data() -> List[Dict[str, str]]:
    """
    エッジケースのテストデータを生成

    Returns:
        エッジケースデータのリスト
    """
    data = [
        # 長い住所（3行に渡る）
        {
            "to_postal": "100-0001",
            "to_address": "東京都千代田区千代田丸の内パークタワー15階1501号室",
            "to_name": "株式会社テスト会社代表取締役会長兼CEO太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "150-0001",
            "from_address": "東京都渋谷区渋谷スクランブルスクエア",
            "from_name": "株式会社ABC",
            "from_phone": "",
            "from_honorific": "",
        },
        # 短い住所
        {
            "to_postal": "000-0000",
            "to_address": "東京都千代田区1-1",
            "to_name": "田中",
            "to_phone": "",
            "to_honorific": "",
            "from_postal": "999-9999",
            "from_address": "大阪府大阪市2-2",
            "from_name": "山田",
            "from_phone": "",
            "from_honorific": "",
        },
        # 敬称バリエーション
        {
            "to_postal": "101-0001",
            "to_address": "東京都千代田区神田",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "殿",
            "from_postal": "160-0001",
            "from_address": "東京都新宿区西新宿",
            "from_name": "佐藤花子",
            "from_phone": "",
            "from_honorific": "",
        },
        # 建物名が長い
        {
            "to_postal": "102-0001",
            "to_address": "東京都千代田区丸の内超大型複合施設XXXビル",
            "to_name": "国際商事株式会社営業部長伊藤次郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "161-0001",
            "from_address": "東京都新宿区西新宿テスト施設YYY棟10階",
            "from_name": "テスト太郎",
            "from_phone": "",
            "from_honorific": "",
        },
        # 特殊な敬称（御中）
        {
            "to_postal": "103-0001",
            "to_address": "東京都中央区日本橋",
            "to_name": "山田商事",
            "to_phone": "",
            "to_honorific": "御中",
            "from_postal": "162-0001",
            "from_address": "東京都新宿区四谷",
            "from_name": "テスト会社",
            "from_phone": "",
            "from_honorific": "",
        },
    ]

    return data


def generate_stress_data(count: int = 100) -> List[Dict[str, str]]:
    """
    ストレステスト用の大量データを生成

    Args:
        count: 生成するレコード数

    Returns:
        生成されたデータのリスト
    """
    return generate_standard_data(count)


def generate_invalid_data() -> List[Dict[str, str]]:
    """
    バリデーションテスト用の不正データを生成

    Returns:
        不正データのリスト
    """
    data = [
        # 郵便番号の形式エラー（ハイフンなし）
        {
            "to_postal": "1000001",
            "to_address": "東京都千代田区千代田",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "150-0001",
            "from_address": "東京都渋谷区渋谷",
            "from_name": "佐藤花子",
            "from_phone": "",
            "from_honorific": "",
        },
        # 郵便番号の形式エラー（不正な形式）
        {
            "to_postal": "123456789",
            "to_address": "東京都千代田区千代田",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "150-0001",
            "from_address": "東京都渋谷区渋谷",
            "from_name": "佐藤花子",
            "from_phone": "",
            "from_honorific": "",
        },
        # 必須フィールドの欠落（住所なし）
        {
            "to_postal": "100-0001",
            "to_address": "",
            "to_name": "山田太郎",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "150-0001",
            "from_address": "東京都渋谷区渋谷",
            "from_name": "佐藤花子",
            "from_phone": "",
            "from_honorific": "",
        },
        # 必須フィールドの欠落（名前なし）
        {
            "to_postal": "100-0001",
            "to_address": "東京都千代田区千代田",
            "to_name": "",
            "to_phone": "",
            "to_honorific": "様",
            "from_postal": "150-0001",
            "from_address": "東京都渋谷区渋谷",
            "from_name": "佐藤花子",
            "from_phone": "",
            "from_honorific": "",
        },
    ]

    return data


def save_csv(data: List[Dict[str, str]], filename: str) -> Path:
    """
    CSVファイルに保存

    Args:
        data: 保存するデータ
        filename: ファイル名

    Returns:
        保存されたファイルパス
    """
    output_dir = Path("examples")
    output_dir.mkdir(exist_ok=True)

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    return filepath


def calculate_pages(record_count: int) -> int:
    """
    4upレイアウトでのページ数を計算

    Args:
        record_count: レコード数

    Returns:
        推定ページ数
    """
    return (record_count + 3) // 4


def print_summary(pattern: str, data: List[Dict[str, str]], filepath: Path):
    """
    生成結果のサマリーを表示

    Args:
        pattern: パターン名
        data: 生成されたデータ
        filepath: 出力ファイルパス
    """
    print("\n✅ テストCSVデータを生成しました\n")
    print(f"【ファイル情報】")
    print(f"- ファイル: {filepath}")
    print(f"- 件数: {len(data)}件")
    print(f"- パターン: {pattern}")
    print(f"- 推定ページ数: {calculate_pages(len(data))}ページ（4upレイアウト）")
    print(f"- 生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if data:
        # 敬称の統計
        to_honorifics = {}
        from_honorifics = {}

        for row in data:
            to_h = row.get("to_honorific", "") or "なし"
            from_h = row.get("from_honorific", "") or "なし"

            to_honorifics[to_h] = to_honorifics.get(to_h, 0) + 1
            from_honorifics[from_h] = from_honorifics.get(from_h, 0) + 1

        # 都道府県の統計
        prefectures = set()
        for row in data:
            address = row.get("to_address", "")
            for pref in PREFECTURES:
                if pref in address:
                    prefectures.add(pref)
                    break

        print(f"【内容サマリー】")
        print(f"- 宛先敬称分布: {', '.join([f'{k}: {v}件' for k, v in sorted(to_honorifics.items())])}")
        print(f"- ご依頼主敬称分布: {', '.join([f'{k}: {v}件' for k, v in sorted(from_honorifics.items())])}")
        print(f"- 都道府県種類: {len(prefectures)}種類\n")

    print(f"【次のステップ】")
    print(f"以下のコマンドでラベルを生成できます：\n")
    print(f"```bash")
    print(f"uv run python -m letterpack.cli --csv {filepath} --output output/test_labels.pdf")
    print(f"```\n")


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        pattern = "standard"
        count = 10
    else:
        pattern = sys.argv[1]
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    # パターンに応じてデータを生成
    if pattern == "standard":
        data = generate_standard_data(count)
        filename = f"test_addresses_standard_{count}.csv"
    elif pattern == "edge_case":
        data = generate_edge_case_data()
        filename = "test_addresses_edge_case.csv"
    elif pattern == "stress":
        data = generate_stress_data(count)
        filename = f"test_addresses_stress_{count}.csv"
    elif pattern == "invalid":
        data = generate_invalid_data()
        filename = "test_addresses_invalid.csv"
    else:
        print(f"❌ エラー: 不明なパターン '{pattern}'")
        print("\n使用可能なパターン:")
        print("  standard     - 標準的なテストデータ")
        print("  edge_case    - エッジケースデータ")
        print("  stress       - ストレステスト用データ")
        print("  invalid      - バリデーションテスト用の不正データ")
        sys.exit(1)

    # ファイルに保存
    filepath = save_csv(data, filename)

    # サマリーを表示
    print_summary(pattern, data, filepath)


if __name__ == "__main__":
    main()
